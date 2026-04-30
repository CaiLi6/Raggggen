"""Thin Streamlit UI for FinAgent OS Client."""

from __future__ import annotations

import uuid

try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv() -> None:
        return None

from gateway.app_gateway import AppGateway
from gateway.request import GatewayRequest


def render_app() -> None:
    import streamlit as st

    load_dotenv()
    st.set_page_config(page_title="FinAgent OS Client", layout="wide")
    st.title("FinAgent OS Client")
    st.caption("Local-first financial research Agent OS")

    with st.sidebar:
        thread_id = st.text_input("Thread ID", value=f"ui-{uuid.uuid4().hex[:8]}")
        collection = st.text_input("Collection", value="default")
        mock_tools = st.toggle("Mock tools", value=False)
        enable_eval = st.toggle("Run lightweight eval", value=False)

    query = st.text_area("Research question", value="请结合财报和舆情分析特斯拉近期投资价值", height=120)

    if st.button("开始分析", type="primary"):
        gateway = AppGateway()
        request = GatewayRequest.from_ui(
            query=query,
            thread_id=thread_id,
            collection=collection,
            enable_eval=enable_eval,
            metadata={"mock_tools": mock_tools},
        )
        with st.status("执行中", expanded=True) as status:
            st.write("Gateway 正在创建 trace 和 session...")
            response = gateway.handle(request)
            st.write("Runtime 已完成角色编排和报告生成。")
            status.update(label="执行完成", state="complete")

        st.markdown(response.markdown)

        col1, col2, col3 = st.columns(3)
        col1.metric("Trace", response.trace_id)
        col2.metric("Tools", len(response.tool_records))
        col3.metric("Warnings", len(response.warnings))

        with st.expander("Tool Records", expanded=False):
            for record in response.tool_records:
                st.json(record.__dict__)

        if response.warnings:
            with st.expander("Warnings", expanded=True):
                for warning in response.warnings:
                    st.warning(warning)

        if response.errors:
            with st.expander("Errors", expanded=True):
                for error in response.errors:
                    st.error(error)

        if response.metadata.get("evaluation"):
            with st.expander("Evaluation", expanded=True):
                st.json(response.metadata["evaluation"])

        st.download_button(
            label="下载 Markdown 研报",
            data=response.markdown,
            file_name=f"Financial_Report_{response.thread_id}.md",
            mime="text/markdown",
            disabled=not bool(response.markdown),
        )


if __name__ == "__main__":
    render_app()
