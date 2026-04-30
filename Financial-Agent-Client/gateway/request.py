"""Gateway request contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GatewayRequest:
    """Unified request object for Streamlit, CLI and tests."""

    query: str
    thread_id: str | None = None
    collection: str | None = None
    enable_eval: bool = False
    output_format: str = "markdown"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_ui(
        cls,
        query: str,
        thread_id: str | None = None,
        collection: str | None = None,
        enable_eval: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> "GatewayRequest":
        return cls(
            query=query,
            thread_id=thread_id,
            collection=collection,
            enable_eval=enable_eval,
            output_format="markdown",
            metadata=metadata or {},
        )

    @classmethod
    def from_cli(
        cls,
        query: str,
        thread_id: str | None = None,
        collection: str | None = None,
        enable_eval: bool = False,
        output_format: str = "markdown",
        mock_tools: bool = False,
    ) -> "GatewayRequest":
        return cls(
            query=query,
            thread_id=thread_id,
            collection=collection,
            enable_eval=enable_eval,
            output_format=output_format,
            metadata={"mock_tools": mock_tools},
        )

    def validate(self) -> None:
        if not (self.query or "").strip():
            raise ValueError("query must not be empty")
        if self.output_format not in {"markdown", "json"}:
            raise ValueError("output_format must be 'markdown' or 'json'")

    @property
    def normalized_query(self) -> str:
        return (self.query or "").strip()
