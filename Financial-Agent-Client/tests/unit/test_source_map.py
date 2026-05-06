"""Tests for context/source_map.py (task C2)."""

from __future__ import annotations

from context.source_map import SourceMap, SourceRecord
from reports.schema import ReportSource


def test_add_returns_source_record() -> None:
    sm = SourceMap()
    record = sm.add(title="Test", source_type="internal_knowledge")
    assert isinstance(record, SourceRecord)
    assert record.source_id == "S1"


def test_add_increments_source_id() -> None:
    sm = SourceMap()
    r1 = sm.add("src1", "internal_knowledge")
    r2 = sm.add("src2", "external_news")
    assert r1.source_id == "S1"
    assert r2.source_id == "S2"


def test_add_with_url() -> None:
    sm = SourceMap()
    record = sm.add("Article", "external_news", url="https://example.com")
    assert record.url == "https://example.com"


def test_add_with_snippet() -> None:
    sm = SourceMap()
    record = sm.add("src", "internal_knowledge", snippet="excerpt text")
    assert record.snippet == "excerpt text"


def test_add_with_metadata() -> None:
    sm = SourceMap()
    record = sm.add("src", "internal_knowledge", metadata={"tool": "rag_search"})
    assert record.metadata["tool"] == "rag_search"


def test_to_dict_keys_are_source_ids() -> None:
    sm = SourceMap()
    sm.add("A", "t1")
    sm.add("B", "t2")
    d = sm.to_dict()
    assert "S1" in d
    assert "S2" in d


def test_to_dict_contains_source_fields() -> None:
    sm = SourceMap()
    sm.add("My Source", "internal_knowledge", snippet="snip")
    d = sm.to_dict()
    assert d["S1"]["title"] == "My Source"
    assert d["S1"]["snippet"] == "snip"


def test_to_report_sources_returns_list() -> None:
    sm = SourceMap()
    sm.add("S", "t")
    sources = sm.to_report_sources()
    assert len(sources) == 1
    assert isinstance(sources[0], ReportSource)


def test_to_report_source_conversion() -> None:
    sm = SourceMap()
    sm.add("Title X", "external_news", url="http://x.com")
    rs = sm.to_report_sources()[0]
    assert rs.title == "Title X"
    assert rs.source_type == "external_news"
    assert rs.url == "http://x.com"


def test_empty_map_returns_empty_structures() -> None:
    sm = SourceMap()
    assert sm.to_dict() == {}
    assert sm.to_report_sources() == []


def test_title_fallback_when_empty() -> None:
    sm = SourceMap()
    record = sm.add("", "t")
    assert record.title == record.source_id
