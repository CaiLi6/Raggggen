# FinAgent RAG Suite

This repository combines two local-first financial research components:

- `Financial-Agent-Client/`: FinAgent OS Client for UI / CLI research orchestration, source-aware reports, safety guardrails and trace records.
- `MODULAR-RAG-MCP-SERVER/`: modular RAG + MCP server for ingestion, retrieval and knowledge hub tools.

The client is research-only. It does not execute real trades, read brokerage credentials or make final investment decisions.

## Quick Links

- Client docs: [Financial-Agent-Client/README.md](Financial-Agent-Client/README.md)
- Client implementation plan: [Financial-Agent-Client/plan.md](Financial-Agent-Client/plan.md)
- RAG server docs: [MODULAR-RAG-MCP-SERVER/README.md](MODULAR-RAG-MCP-SERVER/README.md)

## Client Smoke

```powershell
cd Financial-Agent-Client
python .\scripts\main.py --query "分析 AAPL 的基本面和舆情" --mock-tools
python -m pytest -q -m "not llm and not external"
```
