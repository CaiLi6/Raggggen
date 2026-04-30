# FinAgent OS Client DEV_SPEC

| 项 | 值 |
| --- | --- |
| 文档版本 | 3.1 |
| 覆盖范围 | `Financial-Agent-Client/` |
| 基座依赖 | `MODULAR-RAG-MCP-SERVER/` |
| 目标形态 | OpenClaw 式本地金融 Agent OS |
| 资产范围 | A 股 + 美股 |
| 动作边界 | 仅研究 / 建议，不执行真实交易 |
| 主要入口 | Streamlit UI + CLI |
| 目标读者 | AI 编码 Agent、项目维护者、面试讲解者 |

---

## 目录

1. 项目定位
2. 目标与边界
3. 目标架构
4. 核心模块
5. 数据契约
6. 技术选型
7. 测试与评估
8. 实施排期
9. 附录

---

## 1. 项目定位

### 1.1 一句话定位

FinAgent OS Client 是一个本地优先的金融投研 Agent 客户端。它读取私有知识库、实时新闻、行情摘要和用户上下文，编排多个金融角色生成带来源、风险披露和非投资建议声明的研究报告。

它不是券商交易终端、自动下单系统、投资顾问合规系统，也不是公网 SaaS 平台。系统永远不接管真实账户，不提交订单，不替用户做最终投资决策。

### 1.2 设计原则

| 原则 | 含义 |
| --- | --- |
| 厚基座 | RAG 摄取、索引、召回、重排和评估继续由 `MODULAR-RAG-MCP-SERVER` 承担。 |
| 薄应用 | 客户端只负责金融 Agent 编排、上下文组装、工具治理、报告生成和交互入口。 |
| 强治理 | 所有金融输出必须具备来源标注、风险提示、权限边界、审计轨迹和合规声明。 |
| 本地优先 | 第一版以 Windows 本地运行、Streamlit 展示、CLI 回归和 MCP stdio 通信为主。 |
| 渐进重构 | 每个阶段必须保留可运行状态，避免一次性推倒现有 demo。 |

### 1.3 与现有项目关系

| 项目 | 职责 |
| --- | --- |
| `Financial-Agent-Client/` | 金融问题理解、角色协作、工具选择、报告生成、UI / CLI 入口。 |
| `MODULAR-RAG-MCP-SERVER/` | PDF 摄取、切块、embedding、Chroma、BM25、RRF、Rerank、Dashboard、MCP 工具。 |

客户端只通过 MCP 协议或稳定 CLI / API 访问服务端能力，不直接导入服务端内部 Python 类。当前核心服务端工具是 `query_knowledge_hub`。

### 1.4 成功标准

| 类别 | 标准 |
| --- | --- |
| 可执行性 | 本文档可作为后续 AI 自动编码输入；每个阶段都有 1 小时左右可验收增量。 |
| 兼容性 | 重构后仍可运行现有 Streamlit 入口，并新增 CLI 单次投研问题入口。 |
| 可追溯性 | 每次报告包含来源分层、风险提示、非投资建议声明和 trace id。 |
| 降级能力 | RAG MCP Server、Tavily 或市场数据不可用时，系统优雅降级并记录错误。 |
| 测试覆盖 | 覆盖工具失败、无数据、意图路由、报告生成、安全边界和来源校验。 |
| 安全边界 | 文档和代码不包含 API Key，不包含绕过人工确认或执行真实交易的指令。 |

---

## 2. 目标与边界

### 2.1 业务目标

1. 把当前 demo 式多 Agent 客户端重构成可维护的金融 Agent OS。
2. 建立 Gateway、Runtime、Tool Bus、Context Engine、Safety Layer 的清晰分层。
3. 让每一次投研回答都具备来源可追溯性和工具调用审计记录。
4. 让每个金融角色具备独立职责边界、可配置 profile 和可测试输出契约。
5. 保持 Streamlit UI 轻量，同时增加执行过程、来源、风险和 trace 展示。
6. 增加 CLI，用于自动化回归、批量评估和本地调试。

### 2.2 技术目标

| 对象 | 用途 |
| --- | --- |
| `GatewayRequest` | UI / CLI 统一输入。 |
| `GatewayResponse` | UI / CLI 统一输出。 |
| `ContextBundle` | 模型上下文、来源映射、token budget、缺失信息和冲突提示。 |
| `ToolCallRecord` | 工具调用审计、耗时、错误码和输出摘要。 |
| `ToolPolicy` | 工具权限、禁用动作、人工确认策略。 |
| `AgentProfile` | 角色 prompt、允许工具、输出契约和风险边界。 |
| `ResearchReport` | 最终报告结构化对象。 |
| `RiskDisclosure` | 风险披露与非投资建议声明。 |
| `ExecutionTrace` | 请求、角色、工具和报告生成轨迹。 |

### 2.3 非目标

- 不实现真实交易、券商下单 API、账户读取、支付、转账或融资融券动作。
- 不做公网 SaaS 多租户、复杂权限后台或投资顾问合规系统。
- 不重写 RAG Server 的摄取链路，也不把 Chroma、BM25、Rerank 迁到客户端。
- 不引入重型前端框架；第一版继续使用 Streamlit。
- 不强制接入真实行情 API；市场数据 provider 第一版允许 mock。
- 不把所有能力堆进一个 Agent prompt；职责必须拆分到模块、profile 和工具层。

---

## 3. 目标架构

### 3.1 分层架构

```text
                                   FinAgent OS Client

  +-----------------------+        +---------------------------------------+
  | 用户入口 Entrypoints  |        | 本地配置 Config / Profiles           |
  |-----------------------|        |---------------------------------------|
  | Streamlit UI          |        | config/client_settings.yaml          |
  | CLI scripts/main.py   |        | config/agents/*.yaml                 |
  | 测试 / Eval Runner    |        | config/prompts/*.md                  |
  +-----------+-----------+        | config/tool_policy.yaml              |
              |                    +-------------------+-------------------+
              | GatewayRequest                         |
              v
  +-----------+-------------------------------------------------------------+
  | Gateway 层：统一入口、会话、配置、Trace                                 |
  |-------------------------------------------------------------------------|
  | AppGateway                                                              |
  |   +-- Request validation：校验 query、thread_id、collection             |
  |   +-- SessionManager：管理 thread_id、history、请求级状态               |
  |   +-- ConfigLoader：加载 settings、provider config、profile 路径        |
  |   +-- Trace bootstrap：生成 trace_id，记录耗时、warning、error          |
  +-----------+-------------------------------------------------------------+
              |
              | AgentRuntimeState
              v
  +-----------+-------------------------------------------------------------+
  | Agent Runtime 层：LangGraph 多角色执行流                                |
  |-------------------------------------------------------------------------|
  |                                                                         |
  |   START                                                                 |
  |     |                                                                   |
  |     v                                                                   |
  |   Router Agent：识别问题类型，决定 route plan                           |
  |     |                                                                   |
  |     +------------------+------------------+------------------+          |
  |     |                  |                  |                  |          |
  |     v                  v                  v                  v          |
  | Fundamental       Sentiment          Market Data          Risk          |
  | Analyst           Analyst            Collector            Analyst       |
  | 基本面 / 研报     新闻 / 舆情       行情 / 估值       风险 / 缺口       |
  |     |                  |                  |                  |          |
  |     +------------------+------------------+------------------+          |
  |                            |                                            |
  |                            v                                            |
  |                    Context Engine：统一组装模型上下文                  |
  |                    +-- ContextBundle：用户问题、检索、新闻、行情        |
  |                    +-- SourceMap：来源映射与 citation                  |
  |                    +-- missing_data：缺失数据                           |
  |                    +-- conflicts：来源冲突                              |
  |                    +-- token_budget：上下文预算                         |
  |                            |                                            |
  |                            v                                            |
  |                    Chief Analyst：生成 ResearchReport 初稿              |
  |                            |                                            |
  |                            v                                            |
  |                    Compliance Reviewer：合规与安全复核                 |
  |                            |                                            |
  |                            v                                            |
  |                          END                                            |
  +-----------+-------------------------------------------------------------+
              |
              | ResearchReport + ExecutionTrace
              v
  +-----------+-------------------------------------------------------------+
  | Safety / Report 层：金融安全边界与最终输出                              |
  |-------------------------------------------------------------------------|
  | Safety Guardrails                                                       |
  |   +-- 禁止真实交易动作：no real trading actions                         |
  |   +-- 禁止处理账户凭据：no account credential handling                  |
  |   +-- 检查来源、风险、不确定性、免责声明                                |
  |                                                                         |
  | Report Renderer                                                         |
  |   +-- Markdown：给 UI / CLI 展示与下载                                  |
  |   +-- JSON：给测试、评估、自动化流程使用                                |
  |   +-- UI display / file download payload                                |
  +-----------+-------------------------------------------------------------+
              |
              | GatewayResponse
              v
  +-----------+-------------------------------------------------------------+
  | 输出 Outputs                                                            |
  |-------------------------------------------------------------------------|
  | 最终投研报告 Final research report                                      |
  | 来源与引用 Sources and citations                                        |
  | 风险披露 Risk disclosure + 非投资建议声明                               |
  | Tool records、warnings、errors、trace_id                                |
  +-------------------------------------------------------------------------+


  横切平面：工具治理 Tool Bus + 可观测性 Observability
  ====================================================

  +-----------------------------+        +----------------------------------+
  | Tool Bus：所有工具唯一入口  |        | Observability：审计与日志        |
  |-----------------------------|        |----------------------------------|
  | register(name, handler)     |        | logs/client_traces.jsonl         |
  | call(name, args, role)      |        | logs/eval_results.jsonl          |
  | ToolPolicy 权限检查         |        | tool latency / error_code        |
  | timeout / retry / errors    |        | source count / safety results    |
  | ToolCallRecord 审计记录     |        | request and agent timings        |
  +--------------+--------------+        +----------------------------------+
                 |
                 | Tool adapters：工具适配层
                 v
  +--------------+----------------------------------------------------------+
  | 外部与本地 Provider                                                     |
  |-------------------------------------------------------------------------|
  | RAGMCPAdapter：内部知识库检索                                           |
  |   --> MCP stdio                                                         |
  |   --> MODULAR-RAG-MCP-SERVER                                            |
  |   --> query_knowledge_hub                                               |
  |   --> Chroma / BM25 / RRF / Rerank / document citations                 |
  |                                                                         |
  | NewsSearchAdapter：实时新闻与舆情                                       |
  |   --> Tavily or future news provider                                    |
  |                                                                         |
  | MarketDataAdapter：行情与财务摘要                                       |
  |   --> Mock provider in v1                                               |
  |   --> future yfinance / AKShare / Tushare / Polygon                     |
  |                                                                         |
  | LLMProvider：模型调用                                                   |
  |   --> DashScope / Qwen by default                                       |
  |   --> future OpenAI-compatible client                                   |
  |                                                                         |
  | EvaluatorTool：报告评估                                                 |
  |   --> faithfulness / relevance / source coverage / safety metrics       |
  +-------------------------------------------------------------------------+

  硬边界 Hard boundary:
  Client tools 只能生成研究报告、摘要、mock 行情数据和 paper trading 计划。
  系统绝不能提交、撤销或修改真实订单。
```

### 3.2 模块职责

| 模块 | 职责 | 不负责 |
| --- | --- | --- |
| Gateway | 接收 UI / CLI 请求、创建 session、调用 runtime、聚合响应、记录 trace。 | 拼 prompt、直接调第三方 SDK、写具体金融逻辑。 |
| Runtime | 基于 LangGraph 运行角色节点，支持路由、fan-out、fan-in 和降级。 | 处理 Streamlit 状态、下载按钮等 UI 细节。 |
| Agents | 执行角色职责，读取 profile，调用 Tool Bus，产出结构化片段。 | 绕过工具层直接访问外部服务。 |
| Tool Bus | 统一工具注册、权限检查、超时、重试、错误码和审计记录。 | 保存业务状态或生成最终报告。 |
| Context Engine | 组装用户问题、历史、RAG、新闻、行情、错误和风险约束。 | 最终写作或安全复核。 |
| Safety Layer | 禁止真实交易，检查免责声明、风险提示、来源和不确定性。 | 判断投资收益或替用户决策。 |
| Observability | 记录 JSONL trace、工具耗时、错误码、来源数量和安全检查结果。 | 记录完整密钥、密码、验证码或账户敏感信息。 |

### 3.3 目标目录结构

```text
Financial-Agent-Client/
  agents/
    router_agent.py
    fundamental_agent.py
    sentiment_agent.py
    risk_agent.py
    chief_analyst_agent.py
    compliance_agent.py
    profiles.py
  config/
    agents/
    prompts/
    client_settings.yaml
    loader.py
    tool_policy.yaml
  context/
    bundle.py
    engine.py
    source_map.py
  gateway/
    app_gateway.py
    request.py
    response.py
    session.py
  observability/
    audit.py
    trace.py
  reports/
    renderer.py
    schema.py
    validators.py
  runtime/
    graph.py
    registry.py
    state.py
  safety/
    disclosures.py
    guardrails.py
    policy.py
  tools/
    bus.py
    evaluator_tool.py
    market_data.py
    news_search.py
    rag_mcp.py
    records.py
  ui/
    app.py
  scripts/
    main.py
    evaluate_agent.py
  tests/
    unit/
    integration/
    e2e/
    fixtures/
```

### 3.4 现有目录迁移关系

| 当前位置 | 目标位置 / 处理方式 |
| --- | --- |
| `run_app.py` | 保留为 Streamlit 启动入口，内部只调用 `ui.app.render_app()`。 |
| `ui/` | 保留 UI 代码，但改为调用 `AppGateway`。 |
| `agents/` | 拆分为角色节点、profile 加载和 prompt 模板。 |
| `core/` | 逐步迁移到 `gateway/`、`runtime/`、`context/`、`reports/`。 |
| `infrastructure/` | 工具、provider、MCP 调用迁移到 `tools/`。 |
| `tests/` | 拆为 `unit/`、`integration/`、`e2e/`、`fixtures/`。 |

---

## 4. 核心模块

### 4.1 Gateway 控制平面

Gateway 是客户端统一入口，负责接收请求、加载配置、创建 session、调用 runtime、聚合输出、记录 trace 并返回结构化响应。UI、CLI 和测试脚本都必须通过 Gateway 进入系统。

### 4.2 Agent Runtime 执行平面

Runtime 基于 LangGraph，保留 `StateGraph`、`START`、`END` 和条件边。它负责确定性拓扑和角色编排，不承载所有业务规则。业务规则下沉到 profile、context、tool policy 和 safety 模块。

### 4.3 默认金融角色

| 角色 | 职责 |
| --- | --- |
| Router Agent | 识别问题类型，生成 route plan。 |
| Fundamental Analyst | 检索内部知识库、财报、公告、研报和调研纪要。 |
| Sentiment Analyst | 检索新闻、舆情、催化剂和市场事件。 |
| Risk Analyst | 汇总风险因素、数据缺口、工具错误和来源冲突。 |
| Chief Analyst | 整合上下文并生成结构化研究报告。 |
| Compliance Reviewer | 复核真实交易措辞、免责声明、来源和风险提示。 |

后续可扩展 Portfolio、Macro、Industry、Event、Earnings 等角色。

### 4.4 Tool Bus

所有工具调用必须通过 Tool Bus。Agent 不直接调用第三方 SDK，也不直接访问 MCP Session。Tool Bus 负责：

- 工具注册和列表查询。
- 权限检查和禁止动作拦截。
- 超时、重试、异常捕获和错误码映射。
- `ToolCallRecord` 生成。
- 测试中的整体 mock。

默认研究工具包括 RAG、news search、market data 和 evaluator。第一版默认禁止 broker、bank、payment、credential 类工具。

### 4.5 Skills / Prompts 工程化

每个角色都应有独立 `AgentProfile`，包含 role name、system prompt、allowed tools、output contract 和 safety boundary。第一版推荐：

- profile：`config/agents/*.yaml`
- prompt：`config/prompts/*.md`
- tool policy：`config/tool_policy.yaml`

profile、prompt 和 skill 文档不得包含密钥、账户凭据或自动交易指令。

### 4.6 Context Engine

Context Engine 将用户问题、会话历史、RAG 片段、实时新闻、行情摘要、工具错误、风险约束和报告模板组装为 `ContextBundle`。它必须保留 source map、token budget、missing data 和 conflict hints。

### 4.7 Safety Layer

Safety Layer 是金融 Agent 的硬边界。它必须在报告生成前和生成后检查：

- 禁止真实买入、卖出、下单、撤单或修改真实账户。
- 禁止请求或处理交易密码、验证码、支付信息。
- 禁止承诺收益、保证止损或声称无风险。
- 必须标注数据来源、不确定性、数据缺失和来源冲突。
- 必须输出风险提示和非投资建议声明。

### 4.8 Observability

第一版使用普通 logging + JSONL trace。推荐路径：

- 请求 trace：`logs/client_traces.jsonl`
- 评估结果：`logs/eval_results.jsonl`

trace 应记录 trace id、session id、agent 开始 / 结束时间、工具名、输入摘要、输出摘要、错误码、耗时、引用来源数量和安全检查结果。

---

## 5. 数据契约

### 5.1 GatewayRequest

```python
@dataclass
class GatewayRequest:
    query: str
    thread_id: str | None = None
    collection: str | None = None
    enable_eval: bool = False
    output_format: str = "markdown"
    metadata: dict[str, Any] = field(default_factory=dict)
```

### 5.2 GatewayResponse

```python
@dataclass
class GatewayResponse:
    trace_id: str
    thread_id: str
    markdown: str
    report: ResearchReport | None = None
    tool_records: list[ToolCallRecord] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
```

### 5.3 ContextBundle

```python
@dataclass
class ContextBundle:
    query: str
    conversation: list[dict[str, str]]
    rag_chunks: list[dict[str, Any]]
    news_items: list[dict[str, Any]]
    market_snapshot: dict[str, Any]
    source_map: dict[str, Any]
    missing_data: list[str]
    conflicts: list[str]
    token_budget: int
```

### 5.4 ToolCallRecord

```python
@dataclass
class ToolCallRecord:
    tool_name: str
    status: Literal["success", "error"]
    started_at: str
    ended_at: str
    elapsed_ms: int
    input_summary: str
    output_summary: str | None = None
    error_code: str | None = None
    error_message: str | None = None
```

### 5.5 ResearchReport

```python
@dataclass
class ResearchReport:
    title: str
    query: str
    thesis: list[str]
    fundamental: str
    sentiment: str
    market_observation: str
    risks: list[str]
    missing_data: list[str]
    next_steps: list[str]
    sources: list[ReportSource]
    disclosure: RiskDisclosure
```

---

## 6. 技术选型

| 领域 | 选型 | 说明 |
| --- | --- | --- |
| 主语言 | Python 3.10+，推荐 3.11 | 贴合现有项目和 LangGraph / MCP 生态。 |
| Agent 编排 | LangGraph | 用于确定性拓扑、条件边和多角色执行。 |
| LLM Provider | DashScope / Qwen 默认 | Router 使用轻量模型，Chief / Evaluator 使用质量模型；模型名来自配置。 |
| RAG 接入 | MCP stdio | 客户端调用 `query_knowledge_hub`，不直接依赖服务端内部模块。 |
| 新闻舆情 | Tavily 第一版 | 通过 Tool Bus 包装，错误映射到统一错误码。 |
| 行情数据 | Provider 接口 + mock provider | 真实 provider 后续可接 yfinance、AKShare、Tushare、Polygon。 |
| UI | Streamlit | 保持薄 UI，只调用 Gateway。 |
| CLI | `scripts/main.py` | 支持 smoke、回归、评估和 JSON / Markdown 输出。 |
| 配置 | YAML + 环境变量覆盖 | 推荐 `config/client_settings.yaml`、`config/agents/*.yaml`、`config/tool_policy.yaml`。 |
| 类型 | dataclass / TypedDict | 核心对象用 dataclass，LangGraph state 用 TypedDict。 |
| 日志 | logging + JSONL | 禁止输出完整 API Key 或账户敏感信息。 |
| 依赖 | `requirements.txt` | 新增依赖必须有明确用途；可新增 `PyYAML`。 |

---

## 7. 测试与评估

### 7.1 测试分层

| 层级 | 覆盖内容 | 示例命令 |
| --- | --- | --- |
| Unit | 数据契约、配置加载、ToolPolicy、ContextBundle、报告渲染、安全函数。 | `pytest tests/unit -q` |
| Integration | Gateway + Runtime、Tool Bus + mock adapter、RAG adapter mock MCP。 | `pytest tests/integration -q` |
| E2E | CLI smoke、Streamlit import、工具降级、黄金问题集。 | `pytest tests/e2e -q` |
| Eval | faithfulness、answer relevance、source coverage、risk disclosure coverage、prohibited action rate。 | `python scripts/evaluate_agent.py` |

### 7.2 Mock 策略

- LLM 调用默认 mock，除非测试显式标记 `llm`。
- Tavily / news 默认 mock，除非测试显式标记 `external`。
- RAG MCP adapter 使用 fake `ClientSession`。
- Market data 第一版使用 `MockMarketDataProvider`。
- Tool Bus 支持整体替换为 fake bus。

### 7.3 测试标记

| 标记 | 含义 |
| --- | --- |
| `llm` | 真实或半真实 LLM 调用。 |
| `external` | 真实外部网络或第三方 API。 |
| `e2e` | 端到端流程。 |
| `slow` | 慢测试。 |

默认快速验证命令：

```powershell
pytest -q -m "not llm and not external"
```

### 7.4 验收门槛

- 快速测试通过。
- CLI mock smoke 通过。
- `import ui.app` 不触发执行。
- 报告包含用户问题、核心观点、风险、来源和非投资建议声明。
- 工具失败不会导致系统崩溃，错误进入 response / trace。

---

## 8. 实施排期

### 8.1 阶段总览

| 阶段 | 目的 | 状态 |
| --- | --- | --- |
| A | 文档与契约基线 | Planned |
| B | Gateway 与 Session | Planned |
| C | Context Engine | Planned |
| D | Tool Bus 与安全策略 | Planned |
| E | RAG MCP 与市场数据适配 | Planned |
| F | Agent Runtime 与角色拆分 | Planned |
| G | 报告生成与评估 | Planned |
| H | Streamlit + CLI 体验 | Planned |
| I | E2E、回归与收口 | Planned |

### 8.2 任务清单

| ID | 子任务 | 主要文件 | 交付物 | 验收 / 测试 |
| --- | --- | --- | --- | --- |
| A1 | 整理 DEV_SPEC | `DEV_SPEC.md` | 清晰、可执行的规格文档。 | 手动检查结构、边界和任务清单。 |
| A2 | 目标目录骨架 | `gateway/`、`runtime/`、`context/`、`tools/`、`reports/`、`safety/`、`observability/` | 包含 `__init__.py` 的目录骨架。 | `python -m compileall .` |
| A3 | 核心契约 | `gateway/request.py`、`gateway/response.py`、`reports/schema.py`、`tools/records.py` | dataclass / TypedDict 合约。 | `pytest tests/unit/test_contracts.py -q` |
| A4 | 配置加载基线 | `config/loader.py`、`config/client_settings.yaml` | 读取 YAML、解析相对路径、环境变量覆盖。 | `pytest tests/unit/test_config_loader.py -q` |
| A5 | 测试目录分层 | `tests/unit/`、`tests/integration/`、`tests/e2e/`、`tests/fixtures/` | 测试结构和 pytest 标记。 | `pytest --collect-only -q` |
| B1 | GatewayRequest | `gateway/request.py` | `GatewayRequest.from_ui()`、`from_cli()`、`validate()`。 | `pytest tests/unit/test_gateway_request.py -q` |
| B2 | GatewayResponse | `gateway/response.py` | `GatewayResponse.ok()`、`error()`、`to_dict()`。 | `pytest tests/unit/test_gateway_response.py -q` |
| B3 | SessionManager | `gateway/session.py` | thread id、session state、history 管理。 | `pytest tests/unit/test_session_manager.py -q` |
| B4 | AppGateway | `gateway/app_gateway.py` | `AppGateway.handle(request)` 串起 runtime 和 response。 | `pytest tests/integration/test_gateway_smoke.py -q` |
| C1 | ContextBundle | `context/bundle.py` | 上下文 dataclass、缺失数据、冲突提示。 | `pytest tests/unit/test_context_bundle.py -q` |
| C2 | SourceMap | `context/source_map.py` | source id、source type、citation 映射。 | `pytest tests/unit/test_source_map.py -q` |
| C3 | ContextEngine | `context/engine.py` | 从工具结果构建 `ContextBundle`。 | `pytest tests/unit/test_context_engine.py -q` |
| C4 | Context Compaction | `context/engine.py` | token budget 裁剪和来源保留。 | `pytest tests/unit/test_context_compaction.py -q` |
| D1 | ToolPolicy | `tools/policy.py` | allowed / denied tools、prohibited actions。 | `pytest tests/unit/test_tool_policy.py -q` |
| D2 | ToolCallRecord | `tools/records.py` | started / success / failure 记录。 | `pytest tests/unit/test_tool_records.py -q` |
| D3 | ToolBus | `tools/bus.py` | register、call、list_tools、异常捕获。 | `pytest tests/unit/test_tool_bus.py -q` |
| D4 | Safety Guardrails | `safety/policy.py`、`safety/guardrails.py` | 真实交易措辞、免责声明、来源校验。 | `pytest tests/unit/test_safety_guardrails.py -q` |
| D5 | Risk Disclosures | `safety/disclosures.py` | 默认免责声明和风险披露构造。 | `pytest tests/unit/test_disclosures.py -q` |
| E1 | RAG MCP Adapter | `tools/rag_mcp.py` | 迁移现有 RAG 调用，统一错误码。 | `pytest tests/unit/test_rag_mcp_adapter.py -q` |
| E2 | News Search Adapter | `tools/news_search.py` | Tavily 包装、结果归一化、错误码。 | `pytest tests/unit/test_news_search_adapter.py -q` |
| E3 | Market Data Adapter | `tools/market_data.py` | provider 接口和 mock quote summary。 | `pytest tests/unit/test_market_data_adapter.py -q` |
| E4 | 默认 Tool Bus | `tools/__init__.py`、`tools/bus.py` | 注册 RAG、news、market、policy。 | `pytest tests/integration/test_runtime_tool_bus.py -q` |
| F1 | AgentProfile | `agents/profiles.py`、`config/agents/*.yaml` | 加载六个默认角色 profile。 | `pytest tests/unit/test_agent_profiles.py -q` |
| F2 | Runtime State | `runtime/state.py` | `AgentRuntimeState`、reducers、route plan。 | `pytest tests/unit/test_runtime_state.py -q` |
| F3 | Router Agent | `agents/router_agent.py` | intent 分类和 route plan。 | `pytest tests/unit/test_router_agent.py -q` |
| F4 | Fundamental Agent | `agents/fundamental_agent.py` | 通过 Tool Bus 调 RAG，写入上下文。 | `pytest tests/unit/test_fundamental_agent.py -q` |
| F5 | Sentiment Agent | `agents/sentiment_agent.py` | 通过 Tool Bus 调 news，失败可降级。 | `pytest tests/unit/test_sentiment_agent.py -q` |
| F6 | Risk Agent | `agents/risk_agent.py` | 汇总 missing data、conflicts、tool errors。 | `pytest tests/unit/test_risk_agent.py -q` |
| F7 | Compliance Agent | `agents/compliance_agent.py` | 检查交易措辞、免责声明、来源。 | `pytest tests/unit/test_compliance_agent.py -q` |
| F8 | Chief Analyst Agent | `agents/chief_analyst_agent.py` | 读取 `ContextBundle` 并生成 `ResearchReport`。 | `pytest tests/unit/test_chief_analyst_agent.py -q` |
| F9 | Runtime Graph | `runtime/graph.py`、`runtime/registry.py` | 编译完整 LangGraph workflow。 | `pytest tests/integration/test_agent_report_flow.py -q` |
| G1 | ResearchReport Schema | `reports/schema.py` | report、source、disclosure schema。 | `pytest tests/unit/test_report_schema.py -q` |
| G2 | Markdown Renderer | `reports/renderer.py` | 报告 Markdown 渲染。 | `pytest tests/unit/test_report_renderer.py -q` |
| G3 | Report Validators | `reports/validators.py` | 必需章节、来源、免责声明校验。 | `pytest tests/unit/test_report_validators.py -q` |
| G4 | Evaluator Tool | `tools/evaluator_tool.py`、`scripts/evaluate_agent.py` | 指标评估和 golden evaluation。 | `pytest tests/unit/test_evaluator_tool.py -q` |
| H1 | CLI Gateway | `scripts/main.py` | `--query`、`--thread-id`、`--collection`、`--mock-tools`、`--format`。 | `pytest tests/e2e/test_cli_smoke.py -q` |
| H2 | Streamlit Gateway | `ui/app.py`、`run_app.py` | UI 调用 Gateway，展示报告和 trace id。 | `pytest tests/e2e/test_streamlit_import.py -q` |
| H3 | UI Trace Display | `ui/app.py`、`observability/trace.py` | UI 事件格式化和阶段展示。 | `pytest tests/unit/test_trace_events.py -q` |
| I1 | Degradation E2E | `tests/e2e/test_degradation.py` | RAG / news / market 失败仍返回报告。 | `pytest tests/e2e/test_degradation.py -q` |
| I2 | Golden Queries | `tests/fixtures/golden_queries.json`、`tests/e2e/test_golden_queries.py` | 至少 20 条覆盖 A 股、美股、无数据、风险。 | `pytest tests/e2e/test_golden_queries.py -q` |
| I3 | README 更新 | `README.md` | 更新定位、启动命令、测试命令、安全边界。 | 手动检查。 |
| I4 | Final Smoke | 无特定文件 | 快速测试、CLI mock、UI import 全部通过。 | `pytest -q -m "not llm and not external"` |

### 8.3 阶段执行纪律

1. 每次只执行一个子任务。
2. 执行前阅读该子任务的主要文件列表。
3. 执行前确认不会覆盖用户未授权改动。
4. 优先写测试，保持每个阶段可运行。
5. 执行后运行指定测试方法。
6. 测试失败不得进入下一任务。
7. 阶段完成后只更新状态标记，不夹带无关重写。
8. 不在文档、prompt 或配置中写入 API Key、账户凭据或绕过人工确认的指令。

---

## 9. 附录

### 9.1 推荐报告结构

1. 标题：标的 + 研究主题。
2. 用户问题。
3. 核心观点。
4. 基本面支撑。
5. 短期情绪与事件。
6. 行情与估值观察。
7. 主要风险。
8. 数据缺口与不确定性。
9. 后续研究清单。
10. 信息来源。
11. 非投资建议声明。

### 9.2 错误码规范

| 错误码 | 含义 |
| --- | --- |
| `RAG_SERVER_UNAVAILABLE` | RAG Server 不可用。 |
| `RAG_TOOL_MISSING` | MCP tool 缺失。 |
| `RAG_TIMEOUT` | RAG 查询超时。 |
| `RAG_EMPTY_RESULT` | RAG 返回空。 |
| `WEB_SEARCH_FAILED` | 新闻搜索失败。 |
| `WEB_SEARCH_TIMEOUT` | 新闻搜索超时。 |
| `MARKET_DATA_UNAVAILABLE` | 行情数据不可用。 |
| `LLM_ROUTER_FAILED` | 路由模型失败。 |
| `LLM_REPORT_FAILED` | 报告模型失败。 |
| `POLICY_DENIED` | 工具策略拒绝。 |
| `SAFETY_VIOLATION` | 安全检查失败。 |
| `CONFIG_ERROR` | 配置错误。 |
| `UNKNOWN_ERROR` | 未知错误。 |

### 9.3 金融安全红线

禁止：

- 执行真实买入、卖出、提交订单、取消订单或修改真实账户。
- 读取交易密码、验证码、支付信息或账户敏感凭据。
- 承诺收益、保证止损、声称无风险或替用户做最终投资决定。

允许：

- 生成研究报告、风险提示、模拟观察清单和后续资料收集任务。
- 生成 paper trading 计划，但必须明确标注“模拟”。
- 给出待人工复核的研究假设。

所有输出必须包含非投资建议声明。

### 9.4 OpenClaw 思路映射

| OpenClaw 概念 | 本项目映射 |
| --- | --- |
| Gateway | Financial Gateway |
| Agent Runtime | LangGraph Runtime |
| Tools | Tool Bus adapters |
| Skills | AgentProfile + Prompt templates |
| Plugins | future provider packages |
| Context Engine | ContextBundle builder |
| Multi-agent routing | financial role routing |
| Local-first | Streamlit + CLI + MCP stdio |
| Security posture | research-only guardrails |
| Auditability | client JSONL trace |

### 9.5 后续扩展方向

- 多入口：Telegram、Slack、WebSocket、FastAPI Gateway。
- 数据：真实行情 provider、财务指标 provider、公告抓取 provider、行业知识图谱。
- 研究：paper portfolio、回测模块、报告版本管理、团队审阅流程。
- 可观测性：LangSmith tracing、Dashboard agent observability、模型成本统计。
- 工程化：缓存、prompt 版本管理、eval trend 面板、更细粒度权限模型。

---

## 结束语

本 DEV_SPEC 是 `Financial-Agent-Client` 的重构执行蓝图。目标不是写一个更大的 demo，而是把现有金融多 Agent 客户端升级为可治理、可测试、可扩展的本地金融 Agent OS。

后续实现必须始终遵守三条边界：

1. RAG 能力继续由服务端提供。
2. 客户端专注 Agent 编排与金融研究体验。
3. 系统永远不执行真实交易。
