"""Runtime orchestration for FinAgent OS Client."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from agents.chief_analyst_agent import ChiefAnalystAgent
from agents.compliance_agent import ComplianceReviewerAgent
from agents.fundamental_agent import FundamentalAnalystAgent
from agents.risk_agent import RiskAnalystAgent
from agents.router_agent import RouterAgent
from agents.sentiment_agent import SentimentAnalystAgent
from context.engine import ContextEngine
from gateway.request import GatewayRequest
from observability.trace import ExecutionTrace
from reports.renderer import ReportRenderer
from reports.schema import ResearchReport
from safety.guardrails import SafetyGuardrails
from tools import create_default_tool_bus
from tools.bus import ToolBus
from tools.records import ToolCallRecord


@dataclass
class RuntimeResult:
    report: ResearchReport
    markdown: str
    tool_records: list[ToolCallRecord] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class FinancialResearchRuntime:
    """Orchestrate router, role agents, context, report and compliance."""

    def __init__(
        self,
        settings: dict[str, Any] | None = None,
        tool_bus: ToolBus | None = None,
        renderer: ReportRenderer | None = None,
    ):
        self.settings = settings or {}
        self.tool_bus = tool_bus or create_default_tool_bus(self.settings)
        self.renderer = renderer or ReportRenderer()
        self.guardrails = SafetyGuardrails()
        self.router = RouterAgent()
        self.fundamental = FundamentalAnalystAgent()
        self.sentiment = SentimentAnalystAgent()
        self.risk = RiskAnalystAgent()
        self.chief = ChiefAnalystAgent()
        self.compliance = ComplianceReviewerAgent(self.guardrails)

    async def run(
        self,
        request: GatewayRequest,
        conversation: list[dict[str, str]],
        trace: ExecutionTrace,
    ) -> RuntimeResult:
        query_check = self.guardrails.validate_query(request.normalized_query)
        if not query_check.ok:
            raise PermissionError("; ".join(query_check.violations))

        tool_settings = self.settings.get("tools", {})
        app_settings = self.settings.get("app", {})
        state: dict[str, Any] = {
            "query": request.normalized_query,
            "thread_id": trace.thread_id,
            "collection": request.collection or app_settings.get("default_collection", "default"),
            "conversation": conversation,
            "tool_outputs": {},
            "tool_records": [],
            "warnings": [],
            "errors": [],
            "trace_id": trace.trace_id,
            "rag_top_k": int(tool_settings.get("rag_top_k", 5)),
            "rag_timeout_seconds": float(tool_settings.get("rag_timeout_seconds", 90)),
            "news_max_results": int(tool_settings.get("news_max_results", 3)),
            "news_timeout_seconds": float(tool_settings.get("news_timeout_seconds", 20)),
        }

        route = self.router.route(request.normalized_query)
        state["route_intent"] = route.intent
        state["route_plan"] = route.route_plan
        trace.event("router", intent=route.intent, route_plan=route.route_plan)

        if "fundamental" in route.route_plan:
            state = await self.fundamental.run(state, self.tool_bus)
            trace.add_tool_record(state["tool_records"][-1])
        if "sentiment" in route.route_plan:
            state = await self.sentiment.run(state, self.tool_bus)
            trace.add_tool_record(state["tool_records"][-1])
        if "market_data" in route.route_plan:
            result = await self.tool_bus.call(
                "market_data",
                {"query": request.normalized_query},
                role="market_data",
            )
            state["tool_outputs"]["market_data"] = result.data
            state["tool_records"].append(result.record)
            trace.add_tool_record(result.record)

        context_engine = ContextEngine(token_budget=int(app_settings.get("token_budget", 6000)))
        state["context_bundle"] = context_engine.build(
            query=request.normalized_query,
            conversation=conversation,
            tool_outputs=state["tool_outputs"],
            tool_records=state["tool_records"],
        )
        state["errors"].extend(
            record.error_code
            for record in state["tool_records"]
            if record.error_code
        )
        trace.event("context_engine", source_count=len(state["context_bundle"].source_map))

        state = self.risk.run(state)
        state = self.chief.run(state)
        state = self.compliance.run(state)
        trace.safety_results = state.get("safety_result", {})

        report = state["report"]
        markdown = self.renderer.render_markdown(report)

        eval_result: dict[str, Any] | None = None
        if request.enable_eval:
            eval_call = await self.tool_bus.call(
                "evaluate_report",
                {
                    "query": request.normalized_query,
                    "report_markdown": markdown,
                    "sources": [source.__dict__ for source in report.sources],
                },
                role="evaluator",
            )
            state["tool_records"].append(eval_call.record)
            trace.add_tool_record(eval_call.record)
            eval_result = eval_call.data

        return RuntimeResult(
            report=report,
            markdown=markdown,
            tool_records=state["tool_records"],
            warnings=state.get("warnings", []),
            errors=state.get("errors", []),
            metadata={
                "route_intent": route.intent,
                "route_plan": route.route_plan,
                "evaluation": eval_result,
            },
        )


class RuntimeWorkflow:
    """Small compatibility adapter for the old `workflow.compile().invoke()` API."""

    def __init__(self, runtime: FinancialResearchRuntime | None = None):
        self.runtime = runtime or FinancialResearchRuntime()

    def compile(self, *args: Any, **kwargs: Any) -> "RuntimeWorkflow":
        return self

    def invoke(self, state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
        return asyncio.run(self.ainvoke(state, config=config))

    async def ainvoke(self, state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
        from langchain_core.messages import AIMessage

        messages = list(state.get("messages", []))
        query = str(messages[-1].content) if messages else str(state.get("query", ""))
        thread_id = (
            ((config or {}).get("configurable") or {}).get("thread_id")
            or state.get("thread_id")
            or "compat-thread"
        )
        request = GatewayRequest(query=query, thread_id=thread_id, metadata={"mock_tools": True})
        trace = ExecutionTrace.start(thread_id=thread_id, query=query)
        result = await self.runtime.run(request, conversation=[{"role": "user", "content": query}], trace=trace)
        trace.finish()
        return {
            "messages": [AIMessage(content=result.markdown)],
            "research_intent": result.metadata.get("route_intent"),
            "historical_context": [str(result.report.fundamental)],
            "realtime_news": [str(result.report.sentiment)],
            "errors": [record.error_code for record in result.tool_records if record.error_code],
            "tool_records": result.tool_records,
            "trace_id": trace.trace_id,
        }


workflow = RuntimeWorkflow()
