"""Graph retriever for lightweight Graph-RAG style retrieval.

This retriever does not require a dedicated graph database. It builds a
query-time subgraph approximation from chunk metadata and text, then ranks
chunks by entity overlap and optional neighborhood expansion.

Design goals:
- Pluggable: same contract style as Dense/Sparse retrievers.
- Backward compatible: can run with existing Chroma-backed data.
- Explainable: returns graph hit hints in metadata for citations/debugging.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from src.core.types import RetrievalResult

if TYPE_CHECKING:
    from src.ingestion.storage.bm25_indexer import BM25Indexer
    from src.core.settings import Settings
    from src.libs.vector_store.base_vector_store import BaseVectorStore

logger = logging.getLogger(__name__)


class GraphRetriever:
    """Graph-inspired retriever using entity overlap and neighbor expansion.

    Retrieval strategy:
    1. Extract query entities/keywords.
    2. Candidate fetch through vector store query using original query vector path
       is intentionally avoided here to keep this component provider-agnostic.
       Instead, it uses metadata/text scan from top candidates fetched by
       vector store's text fallback path.
    3. Score by direct entity overlap + 1-hop neighborhood hints (tags/title).
    """

    ENTITY_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_\-]{1,}|[\u4e00-\u9fff]{2,}")

    def __init__(
        self,
        settings: Optional[Settings] = None,
        bm25_indexer: Optional[BM25Indexer] = None,
        vector_store: Optional[BaseVectorStore] = None,
        default_top_k: int = 20,
        default_hops: int = 1,
    ) -> None:
        self.bm25_indexer = bm25_indexer
        self.vector_store = vector_store
        self.default_top_k = default_top_k
        self.default_hops = default_hops

        graph_cfg = getattr(settings, "graph", None)
        if graph_cfg is not None:
            self.default_top_k = getattr(graph_cfg, "top_k", default_top_k)
            self.default_hops = getattr(graph_cfg, "hops", default_hops)

        logger.info(
            "GraphRetriever initialized with default_top_k=%s, default_hops=%s",
            self.default_top_k,
            self.default_hops,
        )

    def retrieve(
        self,
        query: str,
        keywords: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        hops: Optional[int] = None,
        trace: Optional[Any] = None,
    ) -> List[RetrievalResult]:
        if self.vector_store is None or self.bm25_indexer is None:
            raise RuntimeError("GraphRetriever requires both vector_store and bm25_indexer")

        if not query or not query.strip():
            return []

        effective_top_k = top_k if top_k is not None else self.default_top_k
        effective_hops = hops if hops is not None else self.default_hops
        collection = filters.get("collection") if filters else "default"

        try:
            self.bm25_indexer.load(collection=collection)
        except Exception:
            # Best effort reload; query call below handles missing index.
            pass

        query_entities = self._extract_entities(query)
        if keywords:
            query_entities.update(k for k in keywords if k)

        try:
            bm25_hits = self.bm25_indexer.query(
                query_terms=list(query_entities) if query_entities else (keywords or []),
                top_k=max(50, effective_top_k * 5),
                trace=trace,
            )
        except Exception:
            bm25_hits = []

        if not bm25_hits:
            return []

        chunk_ids = [hit.get("chunk_id", "") for hit in bm25_hits if hit.get("chunk_id")]
        if not chunk_ids:
            return []

        records = self.vector_store.get_by_ids(chunk_ids, trace=trace)

        scored: List[RetrievalResult] = []
        for rec in records or []:
            if not rec:
                continue
            text = str(rec.get("text", ""))
            metadata = rec.get("metadata", {}) or {}
            local_entities = self._extract_entities(" ".join([
                text,
                str(metadata.get("title", "")),
                " ".join(metadata.get("tags", []) if isinstance(metadata.get("tags"), list) else []),
            ]))

            overlap = query_entities & local_entities
            if not overlap:
                continue

            score = float(len(overlap))
            if effective_hops > 1:
                # Lightweight neighborhood signal: summary/heading words.
                neighborhood_text = " ".join([
                    str(metadata.get("summary", "")),
                    str(metadata.get("heading", "")),
                    str(metadata.get("heading_outline", "")),
                ])
                neighbor_entities = self._extract_entities(neighborhood_text)
                score += 0.5 * float(len(query_entities & neighbor_entities))

            merged_meta = dict(metadata)
            merged_meta["graph_overlap_entities"] = sorted(list(overlap))
            merged_meta["graph_hops"] = effective_hops

            scored.append(
                RetrievalResult(
                    chunk_id=str(rec.get("id", "")),
                    score=score,
                    text=text,
                    metadata=merged_meta,
                )
            )

        scored.sort(key=lambda r: (-r.score, r.chunk_id))
        results = scored[:effective_top_k]

        if trace is not None:
            trace.record_stage(
                "graph_retrieval",
                {
                    "method": "entity_overlap_graph",
                    "query_entities": sorted(list(query_entities)),
                    "hops": effective_hops,
                    "result_count": len(results),
                },
                elapsed_ms=0.0,
            )

        return results

    def _extract_entities(self, text: str) -> Set[str]:
        entities = set()
        for token in self.ENTITY_PATTERN.findall(text or ""):
            token = token.strip()
            if len(token) < 2:
                continue
            entities.add(token)
        return entities


def create_graph_retriever(
    settings: Settings,
    bm25_indexer: Optional[BM25Indexer] = None,
    vector_store: Optional[BaseVectorStore] = None,
) -> GraphRetriever:
    if bm25_indexer is None:
        from src.core.settings import resolve_path
        from src.ingestion.storage.bm25_indexer import BM25Indexer

        bm25_indexer = BM25Indexer(index_dir=str(resolve_path("data/db/bm25/default")))
        bm25_indexer.load(collection="default")

    if vector_store is None:
        from src.libs.vector_store.vector_store_factory import VectorStoreFactory

        vector_store = VectorStoreFactory.create(settings)

    return GraphRetriever(
        settings=settings,
        bm25_indexer=bm25_indexer,
        vector_store=vector_store,
    )
