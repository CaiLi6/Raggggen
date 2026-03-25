"""Thin Streamlit UI for the financial multi-agent workflow."""

from __future__ import annotations

import asyncio
import uuid

import streamlit as st
from dotenv import load_dotenv

# 加载根目录下的 .env 文件到系统环境变量中
load_dotenv()

from langchain_core.messages import HumanMessage

from core.evaluator import AgentEvaluator
from core.graph import workflow


st.set_page_config(page_title="Financial Agent Client", layout="wide")
st.title("Financial Multi-Agent Research")
st.caption("LangGraph + MCP Client (Thin UI)")

thread_id = st.text_input("Thread ID", value=f"ui-{uuid.uuid4().hex[:8]}")
query = st.text_area("请输入你的投研问题", value="请结合财报和舆情分析特斯拉近期投资价值")
enable_deep_eval = st.sidebar.checkbox("开启 LLM 深度评估 (耗时增加约 10s)", value=False)

if st.button("开始分析", type="primary"):
    with st.status("执行中", expanded=True) as status:
        st.write("Router 正在识别意图...")
        app = workflow.compile()
        st.write("Agent A 正在通过 MCP 工具检索历史上下文...")
        st.write("Agent B 正在通过 Tavily 检索实时舆情...")
        result = asyncio.run(
            app.ainvoke(
                {"messages": [HumanMessage(content=query)]},
                config={"configurable": {"thread_id": thread_id}},
            )
        )
        st.write("Agent C 正在聚合生成报告...")
        status.update(label="执行完成", state="complete")

    messages = result.get("messages", [])
    report_text = ""
    if messages:
        report_text = str(messages[-1].content).strip()
        st.markdown(report_text)
    else:
        st.warning("未生成报告，请检查日志。")

    can_download = bool(report_text)
    st.download_button(
        label="💾 下载 Markdown 研报",
        data=report_text if can_download else "",
        file_name=f"Financial_Report_{thread_id}.md",
        mime="text/markdown",
        disabled=not can_download,
        help="仅当报告非空时可下载。",
    )
    if not can_download:
        st.caption("报告内容为空，下载按钮已灰态禁用。")

    if enable_deep_eval and can_download:
        with st.spinner("正在执行 LLM 深度评估..."):
            historical_context = "\n\n".join([str(x) for x in result.get("historical_context", [])])
            realtime_news = "\n\n".join([str(x) for x in result.get("realtime_news", [])])
            evaluator = AgentEvaluator()
            eval_result = evaluator.evaluate(
                query=query,
                historical_context=historical_context,
                realtime_news=realtime_news,
                final_report=report_text,
            )

        with st.expander("LLM 深度评估结果", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Faithfulness", f"{eval_result.faithfulness.score}/10")
                st.caption(eval_result.faithfulness.reasoning)
            with col2:
                st.metric("Answer Relevance", f"{eval_result.answer_relevance.score}/10")
                st.caption(eval_result.answer_relevance.reasoning)
