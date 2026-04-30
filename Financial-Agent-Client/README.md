# FinAgent OS Client

`Financial-Agent-Client` is a local-first financial research Agent OS client. It orchestrates research roles, calls approved tools through a Tool Bus, builds source-aware context, and returns a structured report with risks, citations, trace id and a non-investment-advice disclosure.

It is research-only. It does not place orders, read brokerage credentials, transfer money, or make final investment decisions for the user.

## Architecture

- `gateway/`: unified UI / CLI / test entry through `AppGateway`.
- `runtime/`: financial research runtime and compatibility workflow adapter.
- `agents/`: router, fundamental, sentiment, risk, chief analyst and compliance roles.
- `tools/`: Tool Bus, policy checks, RAG MCP, news, market data and evaluator adapters.
- `context/`: `ContextBundle`, source mapping and missing-data assembly.
- `reports/`: structured report schema, renderer and validators.
- `safety/`: research-only guardrails and default disclosures.
- `observability/`: trace events, tool records and JSONL audit writing.
- `config/`: settings, tool policy, agent profiles and prompt files.

`MODULAR-RAG-MCP-SERVER/` remains the RAG base. The client only accesses it through adapter boundaries, not by importing server internals.

## Quick Start

```powershell
cd Financial-Agent-Client
pip install -r requirements.txt
```

Run a deterministic local smoke test with mock tools:

```powershell
python .\scripts\main.py --query "分析 AAPL 的基本面和舆情" --mock-tools
```

Run the Streamlit UI:

```powershell
python .\run_app.py
```

Run tests:

```powershell
python -m pytest -q -m "not llm and not external"
```

Run batch evaluation with mock tools:

```powershell
python .\scripts\evaluate_agent.py
```

## Configuration

- `config/client_settings.yaml`: app, tool, model and trace settings.
- `config/tool_policy.yaml`: allowed and denied tools/actions.
- `config/agents/*.yaml`: role profiles and allowed tools.
- `config/prompts/*.md`: prompt templates.

Environment variable overrides are supported for `DASHSCOPE_MODEL`, `DASHSCOPE_ROUTER_MODEL`, `FINAGENT_MOCK_TOOLS`, `RAG_SERVER_PATH` and `RAG_PYTHON_PATH`.

Do not commit API keys, account credentials, passwords, verification codes or trading secrets.

## Safety Boundary

Allowed:

- Generate research reports, risk summaries and source-backed follow-up tasks.
- Produce mock market observations and paper-trading research plans when clearly marked as simulated.
- Degrade gracefully when RAG, news, market data or evaluator tools fail.

Prohibited:

- Submit, cancel or modify real orders.
- Read or request trading passwords, verification codes or payment credentials.
- Promise returns, guarantee stop-loss outcomes, or claim an investment is risk-free.

Every final report must include risks, source notes, data gaps when applicable, and the non-investment-advice disclosure.

## Legacy Compatibility

Older imports such as `core.graph.workflow`, `core.router.intent_router` and `agents.nodes` remain available as compatibility shims. New code should use `gateway.app_gateway.AppGateway`.
