"""Overview page – system configuration and data statistics.

Displays:
- Component configuration cards (LLM, Embedding, VectorStore …)
- Collection statistics (document count, chunk count, image count)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import streamlit as st

from src.observability.dashboard.services.config_service import ConfigService


def _safe_collection_stats() -> Dict[str, Any]:
    """Attempt to load collection statistics from ChromaDB.

    Returns empty dict on failure so the page still renders.
    """
    try:
        from src.core.settings import load_settings, resolve_path
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        settings = load_settings()
        persist_dir = str(
            resolve_path(settings.vector_store.persist_directory)
        )
        client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
        )
        stats: Dict[str, Any] = {}
        for col in client.list_collections():
            name = col.name if hasattr(col, "name") else str(col)
            collection = client.get_collection(name)
            stats[name] = {"chunk_count": collection.count()}
        return stats
    except Exception:
        return {}


def render() -> None:
    """Render the Overview page."""
    st.header("📊 System Overview")

    # ── Component configuration cards ──────────────────────────────
    st.subheader("🔧 Component Configuration")

    try:
        config_service = ConfigService()
        cards = config_service.get_component_cards()
    except Exception as exc:
        st.error(f"Failed to load configuration: {exc}")
        return

    cols = st.columns(min(len(cards), 3))
    for idx, card in enumerate(cards):
        with cols[idx % len(cols)]:
            st.markdown(f"**{card.name}**")
            st.caption(f"Provider: `{card.provider}`  \nModel: `{card.model}`")
            with st.expander("Details"):
                for k, v in card.extra.items():
                    st.text(f"{k}: {v}")

    # ── Collection statistics ──────────────────────────────────────
    st.subheader("📁 Collection Statistics")

    stats = _safe_collection_stats()
    if stats:
        stat_cols = st.columns(min(len(stats), 4))
        for idx, (name, info) in enumerate(sorted(stats.items())):
            with stat_cols[idx % len(stat_cols)]:
                count = info.get("chunk_count", "?")
                st.metric(label=name, value=count)
                if count == 0 or count == "?":
                    st.caption("⚠️ Empty")
    else:
        st.warning(
            "**No collections found or ChromaDB unavailable.** "
            "Go to the Ingestion Manager page to upload and ingest documents."
        )

    # ── Trace file statistics ──────────────────────────────────────
    st.subheader("📈 Trace Statistics")

    from src.core.settings import resolve_path
    traces_path = resolve_path("logs/traces.jsonl")
    if traces_path.exists():
        line_count = sum(1 for _ in traces_path.open(encoding="utf-8"))
        if line_count > 0:
            st.metric("Total traces", line_count)

            # Query mode breakdown helps distinguish classic RAG vs Graph-RAG runs.
            try:
                from src.observability.dashboard.services.trace_service import TraceService

                query_traces = TraceService().list_traces(trace_type="query", limit=500)
                if query_traces:
                    mode_counts = {"hybrid": 0, "graph": 0, "hybrid_graph": 0, "unknown": 0}
                    for tr in query_traces:
                        mode = str((tr.get("metadata") or {}).get("retrieval_mode", "hybrid") or "hybrid").lower()
                        if mode not in mode_counts:
                            mode = "unknown"
                        mode_counts[mode] += 1

                    st.markdown("**Query Mode Distribution**")
                    m1, m2, m3, m4 = st.columns(4)
                    with m1:
                        st.metric("Hybrid", mode_counts["hybrid"])
                    with m2:
                        st.metric("Graph", mode_counts["graph"])
                    with m3:
                        st.metric("Hybrid+Graph", mode_counts["hybrid_graph"])
                    with m4:
                        st.metric("Unknown", mode_counts["unknown"])
            except Exception:
                pass
        else:
            st.info("No traces recorded yet. Run a query or ingestion first.")
    else:
        st.info("No traces recorded yet. Run a query or ingestion first.")
