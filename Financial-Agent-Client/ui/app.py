"""Streamlit UI for FinAgent OS Client."""

from __future__ import annotations

import uuid

try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv() -> None:
        return None

from gateway.app_gateway import AppGateway
from gateway.request import GatewayRequest


LANGUAGE_OPTIONS = {
    "bi": "中文 + English",
    "zh": "中文",
    "en": "English",
}

TEXT = {
    "title": {
        "zh": "FinAgent OS Client",
        "en": "FinAgent OS Client",
    },
    "subtitle": {
        "zh": "本地优先的金融投研 Agent 工作台",
        "en": "Local-first financial research Agent workspace",
    },
    "purpose": {
        "zh": "把私有知识库、新闻舆情、行情摘要和多角色分析编排成一份带来源、风险披露和审计轨迹的研究报告。",
        "en": "Turns private knowledge, news, market snapshots and role-based analysis into a cited research report with risk disclosure and audit trace.",
    },
    "research_only": {
        "zh": "研究辅助，不执行真实交易",
        "en": "Research only, no real trading",
    },
    "what_it_is": {
        "zh": "它是什么",
        "en": "What it is",
    },
    "what_it_is_body": {
        "zh": "一个本地金融投研 Agent 客户端。它通过 Gateway 统一接入 UI / CLI，再由 Runtime 编排多个分析角色。",
        "en": "A local financial research client. Gateway receives UI / CLI requests, while Runtime coordinates specialist analyst roles.",
    },
    "what_it_uses": {
        "zh": "它调用什么",
        "en": "What it calls",
    },
    "what_it_uses_body": {
        "zh": "所有 RAG、新闻、行情和评估工具都经过 Tool Bus，统一做权限、超时、错误和审计记录。",
        "en": "RAG, news, market data and evaluation tools all go through the Tool Bus for policy, timeout, error and audit handling.",
    },
    "what_it_outputs": {
        "zh": "它输出什么",
        "en": "What it outputs",
    },
    "what_it_outputs_body": {
        "zh": "最终输出 Markdown 研报、信息来源、风险提示、非投资建议声明、trace id 和工具调用记录。",
        "en": "It returns a Markdown report, sources, risk notes, non-investment-advice disclosure, trace id and tool call records.",
    },
    "workflow": {
        "zh": "执行流程",
        "en": "Workflow",
    },
    "input": {
        "zh": "研究问题",
        "en": "Research question",
    },
    "input_help": {
        "zh": "输入你要研究的公司、行业或事件。系统会生成研究报告，不会执行交易。",
        "en": "Enter a company, sector or event. The system creates a research report and never executes trades.",
    },
    "run": {
        "zh": "开始分析",
        "en": "Run analysis",
    },
    "settings": {
        "zh": "运行设置",
        "en": "Run settings",
    },
    "language": {
        "zh": "语言",
        "en": "Language",
    },
    "thread_id": {
        "zh": "会话 ID",
        "en": "Thread ID",
    },
    "collection": {
        "zh": "知识库集合",
        "en": "Collection",
    },
    "mock_tools": {
        "zh": "演示模式：使用 mock 工具",
        "en": "Demo mode: use mock tools",
    },
    "mock_help": {
        "zh": "打开后不依赖真实 RAG / Tavily / 行情服务，适合先看完整流程。",
        "en": "When enabled, the full flow works without real RAG, Tavily or market data services.",
    },
    "eval": {
        "zh": "运行轻量评估",
        "en": "Run lightweight evaluation",
    },
    "status_gateway": {
        "zh": "Gateway 正在创建 trace 和 session...",
        "en": "Gateway is creating trace and session...",
    },
    "status_runtime": {
        "zh": "Runtime 正在编排 Router、分析角色、Tool Bus 和合规复核...",
        "en": "Runtime is coordinating Router, analyst roles, Tool Bus and compliance review...",
    },
    "status_done": {
        "zh": "执行完成",
        "en": "Completed",
    },
    "report_tab": {
        "zh": "研报",
        "en": "Report",
    },
    "sources_tab": {
        "zh": "来源与风险",
        "en": "Sources & Risk",
    },
    "trace_tab": {
        "zh": "Trace 与工具审计",
        "en": "Trace & Tool Audit",
    },
    "download": {
        "zh": "下载 Markdown 研报",
        "en": "Download Markdown report",
    },
}


WORKFLOW_STEPS = [
    ("Gateway", "统一入口 / Unified entry"),
    ("Router", "识别问题 / Route intent"),
    ("Tool Bus", "治理工具 / Govern tools"),
    ("Context", "组装来源 / Build context"),
    ("Compliance", "安全复核 / Safety review"),
    ("Report", "输出研报 / Render report"),
]


def _text(key: str, mode: str) -> str:
    item = TEXT[key]
    if mode == "zh":
        return item["zh"]
    if mode == "en":
        return item["en"]
    if item["zh"] == item["en"]:
        return item["zh"]
    return f"{item['zh']}\n\n{item['en']}"


def _inline(key: str, mode: str) -> str:
    item = TEXT[key]
    if mode == "zh":
        return item["zh"]
    if mode == "en":
        return item["en"]
    if item["zh"] == item["en"]:
        return item["zh"]
    return f"{item['zh']} / {item['en']}"


def _inject_styles(st) -> None:
    st.markdown(
        """
        <style>
        .main .block-container {
            padding-top: 1.3rem;
            max-width: 1220px;
        }
        .fa-hero {
            border: 1px solid #d8dde8;
            border-radius: 8px;
            padding: 22px 24px;
            background: #f8fafc;
        }
        .fa-eyebrow {
            color: #0f766e;
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .fa-hero h1 {
            margin: 0 0 8px 0;
            font-size: 2.05rem;
            line-height: 1.2;
            letter-spacing: 0;
            color: #111827;
        }
        .fa-hero p {
            margin: 0;
            color: #3f4a5a;
            line-height: 1.55;
            max-width: 900px;
        }
        .fa-pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 16px;
        }
        .fa-pill {
            border: 1px solid #cbd5e1;
            border-radius: 999px;
            padding: 5px 10px;
            background: #ffffff;
            color: #263244;
            font-size: 0.86rem;
            white-space: nowrap;
        }
        .fa-info-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 14px;
            margin: 16px 0 8px 0;
        }
        .fa-info-card {
            border: 1px solid #d8dde8;
            border-radius: 8px;
            padding: 15px 16px;
            min-height: 134px;
            background: #ffffff;
        }
        .fa-info-card h3 {
            margin: 0 0 8px 0;
            font-size: 1rem;
            color: #111827;
            letter-spacing: 0;
        }
        .fa-info-card p {
            margin: 0;
            color: #4b5563;
            line-height: 1.5;
            font-size: 0.92rem;
        }
        .fa-workflow {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 8px;
            margin: 10px 0 18px 0;
        }
        .fa-step {
            border-left: 4px solid #0f766e;
            background: #ffffff;
            border-radius: 8px;
            border-top: 1px solid #d8dde8;
            border-right: 1px solid #d8dde8;
            border-bottom: 1px solid #d8dde8;
            padding: 11px 10px;
            min-height: 82px;
        }
        .fa-step strong {
            display: block;
            color: #111827;
            font-size: 0.92rem;
            margin-bottom: 5px;
        }
        .fa-step span {
            color: #556273;
            font-size: 0.82rem;
            line-height: 1.35;
        }
        .fa-section-title {
            margin: 20px 0 8px 0;
            font-size: 1.05rem;
            font-weight: 700;
            color: #111827;
        }
        .fa-boundary {
            border: 1px solid #f1c27d;
            border-radius: 8px;
            background: #fff8ed;
            padding: 12px 14px;
            color: #5c3b08;
            margin: 8px 0 16px 0;
        }
        @media (max-width: 900px) {
            .fa-info-grid {
                grid-template-columns: 1fr;
            }
            .fa-workflow {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_header(st, mode: str) -> None:
    st.markdown(
        f"""
        <div class="fa-hero">
            <div class="fa-eyebrow">{_inline("research_only", mode)}</div>
            <h1>{_text("title", mode)}</h1>
            <p><strong>{_inline("subtitle", mode)}</strong></p>
            <p>{_text("purpose", mode)}</p>
            <div class="fa-pill-row">
                <span class="fa-pill">RAG MCP</span>
                <span class="fa-pill">Tool Bus</span>
                <span class="fa-pill">Multi-Agent Runtime</span>
                <span class="fa-pill">Trace JSONL</span>
                <span class="fa-pill">Risk Disclosure</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_context(st, mode: str) -> None:
    cards = [
        ("what_it_is", "what_it_is_body"),
        ("what_it_uses", "what_it_uses_body"),
        ("what_it_outputs", "what_it_outputs_body"),
    ]
    card_html = "".join(
        f"""
        <div class="fa-info-card">
            <h3>{_inline(title_key, mode)}</h3>
            <p>{_text(body_key, mode)}</p>
        </div>
        """
        for title_key, body_key in cards
    )
    workflow_html = "".join(
        f"""
        <div class="fa-step">
            <strong>{title}</strong>
            <span>{caption}</span>
        </div>
        """
        for title, caption in WORKFLOW_STEPS
    )
    st.markdown(f'<div class="fa-info-grid">{card_html}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="fa-section-title">{_inline("workflow", mode)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="fa-workflow">{workflow_html}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="fa-boundary">{_text("research_only", mode)}. '
        'No broker order, no password handling, no return guarantee.</div>',
        unsafe_allow_html=True,
    )


def _tool_record_rows(response) -> list[dict[str, object]]:
    rows = []
    for record in response.tool_records:
        rows.append(
            {
                "tool": record.tool_name,
                "status": record.status,
                "role": record.role or "",
                "elapsed_ms": record.elapsed_ms,
                "error_code": record.error_code or "",
                "summary": record.output_summary or record.error_message or "",
            }
        )
    return rows


def _render_response(st, response, mode: str) -> None:
    tab_report, tab_sources, tab_trace = st.tabs(
        [_inline("report_tab", mode), _inline("sources_tab", mode), _inline("trace_tab", mode)]
    )

    with tab_report:
        st.markdown(response.markdown)
        st.download_button(
            label=_inline("download", mode),
            data=response.markdown,
            file_name=f"Financial_Report_{response.thread_id}.md",
            mime="text/markdown",
            disabled=not bool(response.markdown),
        )

    with tab_sources:
        report = response.report
        if report:
            st.subheader("Sources / 信息来源")
            if report.sources:
                for source in report.sources:
                    st.markdown(
                        f"**[{source.source_id}] {source.source_type}**  \n"
                        f"{source.title}  \n"
                        f"{source.snippet or ''}"
                    )
            else:
                st.info("暂无来源 / No sources")

            st.subheader("Risk Disclosure / 风险披露")
            st.markdown(report.disclosure.text)
            st.markdown(report.disclosure.non_investment_advice)
            if report.missing_data:
                st.subheader("Missing Data / 数据缺口")
                for item in report.missing_data:
                    st.warning(item)

    with tab_trace:
        col1, col2, col3 = st.columns(3)
        col1.metric("Trace ID", response.trace_id)
        col2.metric("Tool Calls", len(response.tool_records))
        col3.metric("Warnings", len(response.warnings))

        rows = _tool_record_rows(response)
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("暂无工具调用记录 / No tool records")

        if response.metadata:
            with st.expander("Runtime metadata / 运行元数据", expanded=False):
                st.json(response.metadata)
        if response.warnings:
            with st.expander("Warnings / 警告", expanded=True):
                for warning in response.warnings:
                    st.warning(warning)
        if response.errors:
            with st.expander("Errors / 错误", expanded=True):
                for error in response.errors:
                    st.error(error)


def render_app() -> None:
    import streamlit as st

    load_dotenv()
    st.set_page_config(page_title="FinAgent OS Client", layout="wide", initial_sidebar_state="expanded")
    _inject_styles(st)

    with st.sidebar:
        selected_language = st.radio(
            "语言 / Language",
            options=list(LANGUAGE_OPTIONS.keys()),
            format_func=lambda key: LANGUAGE_OPTIONS[key],
            index=0,
            horizontal=False,
        )
        st.divider()
        st.caption(_inline("settings", selected_language))
        thread_id = st.text_input(_inline("thread_id", selected_language), value=f"ui-{uuid.uuid4().hex[:8]}")
        collection = st.text_input(_inline("collection", selected_language), value="default")
        mock_tools = st.toggle(
            _inline("mock_tools", selected_language),
            value=True,
            help=_text("mock_help", selected_language),
        )
        enable_eval = st.toggle(_inline("eval", selected_language), value=False)

    _render_header(st, selected_language)
    _render_context(st, selected_language)

    query = st.text_area(
        _inline("input", selected_language),
        value="请结合财报和舆情分析特斯拉近期投资价值",
        height=130,
        help=_text("input_help", selected_language),
    )

    if st.button(_inline("run", selected_language), type="primary", use_container_width=True):
        gateway = AppGateway()
        request = GatewayRequest.from_ui(
            query=query,
            thread_id=thread_id,
            collection=collection,
            enable_eval=enable_eval,
            metadata={"mock_tools": mock_tools},
        )
        with st.status(_inline("run", selected_language), expanded=True) as status:
            st.write(_text("status_gateway", selected_language))
            st.write(_text("status_runtime", selected_language))
            response = gateway.handle(request)
            status.update(label=_inline("status_done", selected_language), state="complete")
        st.session_state["last_response"] = response
        st.session_state["last_language"] = selected_language

    response = st.session_state.get("last_response")
    if response:
        _render_response(st, response, selected_language)


if __name__ == "__main__":
    render_app()
