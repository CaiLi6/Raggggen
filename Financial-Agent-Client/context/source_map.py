"""Source mapping and citation helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from reports.schema import ReportSource


@dataclass
class SourceRecord:
    source_id: str
    title: str
    source_type: str
    url: str | None = None
    snippet: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_report_source(self) -> ReportSource:
        return ReportSource(
            source_id=self.source_id,
            title=self.title,
            source_type=self.source_type,
            url=self.url,
            snippet=self.snippet,
            metadata=dict(self.metadata),
        )


class SourceMap:
    """Stable source ids for report citations."""

    def __init__(self) -> None:
        self._records: list[SourceRecord] = []

    def add(
        self,
        title: str,
        source_type: str,
        url: str | None = None,
        snippet: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SourceRecord:
        source_id = f"S{len(self._records) + 1}"
        record = SourceRecord(
            source_id=source_id,
            title=title or source_id,
            source_type=source_type,
            url=url,
            snippet=snippet,
            metadata=metadata or {},
        )
        self._records.append(record)
        return record

    def to_dict(self) -> dict[str, Any]:
        return {record.source_id: asdict(record) for record in self._records}

    def to_report_sources(self) -> list[ReportSource]:
        return [record.to_report_source() for record in self._records]
