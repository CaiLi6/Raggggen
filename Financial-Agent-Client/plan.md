# FinAgent OS Client Refactor Plan

> Source: `DEV_SPEC.md` v3.1.
> Rule: finish one scoped item, run its validation, then check it here.

## 0. Preparation

- [x] Confirm worktree is clean before refactor.
- [x] Confirm Git remote points to `https://github.com/kinglyrex/Rag-Agent.git`.
- [x] Confirm GitHub remote is reachable with `git ls-remote --heads origin`.
- [x] Create working branch `codex/finagent-os-refactor`.

## 1. Contract And Skeleton Baseline

- [x] Create target directories: `gateway/`, `runtime/`, `context/`, `tools/`, `reports/`, `safety/`, `observability/`, `config/`.
- [x] Add core dataclass contracts: `GatewayRequest`, `GatewayResponse`, `ToolCallRecord`, `ResearchReport`, `RiskDisclosure`, `ContextBundle`.
- [x] Add config baseline and agent profile prompt files.
- [x] Add pytest directory split and marker configuration.
- [x] Validate with `python -m compileall .`.

## 2. Gateway, Session, Trace

- [x] Implement `SessionManager`.
- [x] Implement `ExecutionTrace` and JSONL audit writer.
- [x] Implement `AppGateway.handle()` as the only UI / CLI entry path.
- [x] Validate gateway smoke flow with mock tools.

## 3. Tool Bus And Adapters

- [x] Implement `ToolPolicy`.
- [x] Implement `ToolBus` with permission checks, timing, error mapping and records.
- [x] Implement RAG MCP adapter for `query_knowledge_hub`.
- [x] Implement news search adapter with Tavily degradation.
- [x] Implement mock market data adapter.
- [x] Validate tool failure returns records instead of crashing.

## 4. Context, Safety, Reports

- [x] Implement `SourceMap`.
- [x] Implement `ContextEngine`.
- [x] Implement financial safety guardrails.
- [x] Implement disclosure builder.
- [x] Implement Markdown / JSON report rendering.
- [x] Validate report contains query, thesis, risks, sources and non-investment advice disclosure.

## 5. Agents And Runtime

- [x] Load six default `AgentProfile` definitions.
- [x] Split router, fundamental, sentiment, risk, chief analyst and compliance agents.
- [x] Implement runtime orchestration behind `FinancialResearchRuntime`.
- [x] Keep compatibility shims for old `core.graph` entry points.
- [x] Validate degradation path still reaches a final report.

## 6. Entrypoints

- [x] Refactor `scripts/main.py` into Gateway CLI with `--query`, `--thread-id`, `--collection`, `--mock-tools`, `--format`.
- [x] Refactor `ui/app.py` into thin Streamlit Gateway UI and keep `import ui.app` side-effect free.
- [x] Keep `run_app.py` as Streamlit launcher.
- [x] Validate CLI smoke and Streamlit import.

## 7. Evaluation, Tests, Docs

- [x] Implement lightweight evaluator tool and evaluation script path.
- [x] Add unit, integration and e2e tests for the main contracts.
- [x] Update README with architecture, commands and safety boundary.
- [x] Run `pytest -q -m "not llm and not external"`.

## 8. Git Delivery

- [x] Review `git status --short`.
- [x] Commit the refactor.
- [x] Push `codex/finagent-os-refactor` to GitHub.
