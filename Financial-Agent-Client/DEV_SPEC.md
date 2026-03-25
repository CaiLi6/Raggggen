# Developer Specification (DEV_SPEC)

版本：2.0 — 核心架构与工程化落地指南 (新增可视化与评估系统)

系统定位：基于 LangGraph 与 MCP 协议的金融投研多 Agent 编排系统 (应用层/Client端)

## 目录

项目概述

系统架构图 (Architecture Topology)

状态图定义 (StateGraph & Data Contract)

核心模块设计 (Core Module Design)

可观测性、可视化与评估系统 (Observability, UI & Evaluation)

健壮性与容错测试策略 (Robustness & Testing)

项目排期与验收标准 (Milestones & Acceptance Criteria)

## 1. 项目概述

本项目是一个基于 LangGraph 构建的金融投研多 Agent 协作系统。系统作为应用层 Client，通过 Model Context Protocol (MCP) 标准协议，与本地运行的 Modular RAG Server（底层知识库）进行跨进程通信。

### 1.1 设计理念：厚基座，薄应用 (Thick Foundation, Thin Application)

在企业级 AI 工程实践中，将文档解析、向量化计算、相似度召回与重排序（Rerank）等高 IO/CPU 消耗的逻辑完全下沉至 MCP Server（基座）。

本项目（应用层）的核心代码将被严格控制在 300-500 行，专注于系统级的高维抽象：意图路由 (Intent Routing)、多 Agent 并发协作 (Fan-out/Fan-in)、外部状态编排与持久化。

### 1.2 项目定位：端到端 MCP 生态闭环

本项目旨在与 RAG 项目形成“全栈 AI 架构组合拳”，在简历与面试中展示以下高阶能力：

生态整合能力：展示从数据底层 (RAG) 到标准协议层 (MCP)，再到应用编排层 (LangGraph) 的全链路架构视野。

并发状态机设计：突破低效的单线 Chain 模式，采用有向无环图 (DAG) 结构的并行分支 (Fan-out) 与节点聚合 (Fan-in)，最大化系统吞吐率。

确定性状态管理：利用强类型约束全局 State，结合 SQLite 实现跨 Session 的持久化记忆 (Memory Checkpointing) 与时间回溯 (Time Travel)。

## 2. 系统架构图 (Architecture Topology)

'''
=========================================================================================
                           USER QUERY: "分析一下特斯拉近期的投资价值"
=========================================================================================
                                      |
                                      v
+---------------------------------------------------------------------------------------+
| [ LangGraph App / Multi-Agent Client 进程 ]                                           |
|                                                                                       |
|                     +-----------------------+                                         |
|                     |  Intent Router (LLM)  |                                         |
|                     +-----------------------+                                         |
|                                 | (If intent == "comprehensive")                      |
|           +---------------------+---------------------+                               |
|           |                 [Fan-Out]                 |                               |
|           v              (并行分发线程)               v                               |
| +-------------------+                       +-------------------+                     |
| |      Agent A      |                       |      Agent B      |                     |
| |   (基本面研究员)  |                       |   (舆情研究员)    |                     |
| +-------------------+                       +-------------------+                     |
|           |                                           |                               |
| [Tool: mcp_query_hub]                       [Tool: web_search]                        |
|           |                                           |                               |
+-----------|-------------------------------------------|-------------------------------+
            | (跨进程 stdio)                            | (HTTP/REST)
+-----------|--------------------+       +--------------|-------------------------------+
| [ Local MCP Server 进程 ]      |       | [ External API 网络层 ]                      |
|           |                    |       |              |                               |
|           v                    |       |              v                               |
| +-------------------+          |       |    +-------------------+                     |
| | MCP Stdio Handler |          |       |    |   Tavily Search   |                     |
| +-------------------+          |       |    +-------------------+                     |
|           |                    |       +--------------|-------------------------------+
|           v                    |                      |
| +-------------------+          |                      |
| | Chroma Vector DB  |          |                      |
| +-------------------+          |                      |
+-----------|--------------------+                      |
            | (返回 historical_context)                 | (返回 realtime_news)
+-----------|-------------------------------------------|-------------------------------+
|           v                                           v                               |
|           +---------------------+---------------------+                               |
|                                 |                                                     |
|                             [Fan-In]                                                  |
|                           (节点聚合)                                                  |
|                                 |                                                     |
|         +-------------------------------------------------------+                     |
|         | << StateDB (SQLite) : 增量聚合并持久化全局 State >>   |                     |
|         +-------------------------------------------------------+                     |
|                                 |                                                     |
|                     +-----------------------+                                         |
|                     |        Agent C        |                                         |
|                     |     (首席分析师)      |                                         |
|                     +-----------------------+                                         |
|                                 | (综合推理与降级容错检查)                            |
+---------------------------------|-----------------------------------------------------+
                                  v
=========================================================================================
                           [ Markdown 深度研报 (含风险提示) ]
=========================================================================================
```

系统整体物理部署与逻辑流转架构如下。核心体现了 Client 端的动态路由、异步并发拓扑、状态增量聚合机制，以及通过官方 `mcp.client.stdio` 与 MCP Server 的跨进程通信 (IPC)。

graph TD
    %% 样式定义
    classDef user fill:#f9f9f9,stroke:#333,stroke-width:2px;
    classDef router fill:#ffe0b2,stroke:#f57c00,stroke-width:2px;
    classDef agent fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;
    classDef tool fill:#e3f2fd,stroke:#1976d2,stroke-width:2px;
    classDef db fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef boundary fill:none,stroke:#9e9e9e,stroke-width:2px,stroke-dasharray: 5 5;

    User([用户查询 / User Query]):::user --> Router
    
    subgraph LangGraph_App [LangGraph Multi-Agent Client 进程]
        direction TB
        Router{意图路由器<br>Intent Router}:::router
        
        Router -- Macro + Micro --> FanOut((并发分发<br>Fan-Out))
        Router -- Only Micro --> AgentA
        Router -- Only Macro --> AgentB
        
        FanOut --> AgentA[Agent A: 基本面研究员]:::agent
        FanOut --> AgentB[Agent B: 舆情研究员]:::agent
        
        AgentA -.-> |Update State| StateDB[(SQLite<br>MemorySaver)]:::db
        AgentB -.-> |Update State| StateDB
        
        AgentA --> FanIn((节点聚合<br>Fan-In))
        AgentB --> FanIn
        
        FanIn --> AgentC[Agent C: 首席分析师<br>Summary Node]:::agent
        AgentC -.-> |Update State| StateDB
    end

    subgraph External_Tools [外部工具调用层]
      AgentB -- API Request --> WebSearch[Tavily Search Results<br>实时数据 API]:::tool
        AgentA -- Native Function Calling --> MCPClient[MCP Stdio Client<br>协议封装层]:::tool
    end
    
    subgraph Local_RAG_Server [Modular RAG MCP Server 进程]
        MCPClient -- JSON-RPC over Stdio --> MCPServer[MCP Server Handler]:::tool
        MCPServer --> ChromaDB[(Chroma Vector DB)]:::db
    end
    
    AgentC --> Output([Markdown 深度研报]):::user
    
    class LangGraph_App boundary;
    class Local_RAG_Server boundary;



## 3. 状态图定义 (StateGraph & Data Contract)

LangGraph 架构的基石是强类型的数据契约。本系统使用 Python 3.10+ 的 `typing.TypedDict(total=False)` 配合 Annotated Reducers 定义全局 State，确保状态在 DAG 流转中的确定性与隔离性，同时允许节点按需增量写入字段。

### 3.1 全局 State 结构定义

import operator
from typing import TypedDict, Annotated, Sequence, Literal
from langchain_core.messages import BaseMessage

class AgentState(TypedDict, total=False):
    # 对话历史：使用 operator.add 确保每次图流转时增量追加，避免状态覆盖
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # 研究意图：由 Router 节点解析写入，决定 DAG 的拓扑走向
    research_intent: Literal["fundamental", "sentiment", "comprehensive", "unknown"]
    
    # 历史财报上下文：Agent A 通过调用 MCP 工具获取并写入
    historical_context: Annotated[list[str], operator.add]
    
    # 实时舆情数据：Agent B 通过调用 Web Search 获取并写入
    realtime_news: Annotated[list[str], operator.add]
    
    # 系统异常或降级标记：用于实现 Graceful Degradation (如 ["MCP_SERVER_UNAVAILABLE", "WEB_SEARCH_FAILED"])
    errors: Annotated[list[str], operator.add]


### 3.2 动态路由逻辑 (Conditional Edges)

Router 节点通过轻量级 DashScope 模型（默认 `qwen-turbo`）进行 Intent Classification，产出 `research_intent`，并由 `add_conditional_edges` 决定分支走向：

comprehensive (宏微观结合)：触发 Fan-out，返回 ["agent_a", "agent_b"]，并发执行 Agent A 与 Agent B（异步节点）。

fundamental (仅基本面)：流转至 ["agent_a"]。

sentiment (仅看情绪/大盘)：流转至 ["agent_b"]。

unknown / 兜底：当前实现为双路并发兜底，返回 ["agent_a", "agent_b"]，确保在意图不确定时仍可给出可用报告。

聚合机制 (Fan-in)：`agent_a` 与 `agent_b` 的出边均收敛至 `agent_c`（Summary Node）。在综合意图下，A/B 并发完成后由 C 进行统一聚合与降级提示注入。

## 4. 核心模块设计 (Core Module Design)

### 4.1 MCP 工具接入层 (Client-side Wrapper)

系统通过官方 MCP Python SDK（`mcp.client.stdio` + `ClientSession`）建立与 RAG Server 的 stdio 连接，并在工具层完成协议调用封装。

当前工程实现采用“每次调用独立会话”模式：

- `get_rag_context` 在单次请求内创建 `stdio_client(...)` 与 `ClientSession(...)` 上下文，调用 `query_knowledge_hub` 后自动清理资源，避免跨任务共享连接导致的清理竞争。
- 通过独立解释器路径 `RAG_PYTHON_PATH` 启动 RAG 进程，并显式注入 `PYTHONPATH=rag_root`，实现应用层与知识库层环境隔离，降低依赖冲突风险。
- 在调用前执行 `list_tools()` 校验服务端能力；若缺失目标工具，返回 `MCP_CONNECTED_BUT_TOOL_MISSING`，避免静默失败。

兼容层：`mcp_query_knowledge_hub(...)` 保留同步包装接口（兼容旧调用点），底层统一委派至异步 `get_rag_context(...)`。

### 4.2 LLM 模型分级选型策略

为兼顾系统吞吐率、成本与推理质量，采用**“高低搭配”**策略：



| 节点 (Node) | 职责 | 推荐模型 | 选型理由 |

| --- | --- | --- | --- |

| Router | 意图分类 | DashScope qwen-turbo（默认） | 当前实现使用 `ChatDashScope`，温度为 0，强调稳定分类与低延迟。 |

| Agent A / B | Tool Use / 信息抽取 | 工具优先（MCP + Tavily），LLM 仅参与 Router/总结 | A/B 节点核心是异步工具编排与结构化结果回填，不依赖节点内 LLM Function Calling。 |

| Agent C | 信息聚合与合成 | DashScope qwen-plus（默认） | 在汇总阶段执行报告生成、来源分层标注与降级提示融合。 |

### 4.3 节点 System Prompt 设定准则

每个 Agent 必须设定严格的行为边界与责任域 (Domain of Responsibility)：

Agent A (基本面研究员)"你是一位资深的量化与基本面分析师。你的唯一职责是使用 query_knowledge_hub 工具查阅本地研报与财报数据库。你必须逐字引用检索到的核心财务指标数据。如果工具未返回数据，严禁凭空捏造，必须记录 '数据缺失'。"

Agent B (舆情研究员)"你是一位敏锐的市场观察员。你的职责是使用网络搜索工具，获取标的最近 48 小时内的突发新闻、政策导向与大盘情绪。请过滤噪音，仅提取最核心的利好/利空催化剂。"

Agent C (首席分析师)"你是负责最终研报定稿的首席分析师。请综合 historical_context 与 realtime_news。如果历史基本面与短期情绪发生冲突（如财报优异但突发巨大利空），请在报告中进行逻辑调和。输出必须是专业 Markdown 格式，包含：1. 核心观点 2. 基本面支撑 3. 短期情绪扰动 4. 风险提示。"

## 5. 可观测性、可视化与评估系统 (Observability, UI & Evaluation)

鉴于 Agent 系统的“非确定性”特征，本应用层必须配备独立于 RAG Server 的白盒化监控与评估体系，展示高阶的 AI 工程化能力。

### 5.1 开发者视角的图可视化 (Graph Observability)

当前落地形态：结构化日志可观测（已上线）+ 图追踪平台（可扩展项）。

已实现能力：

节点级日志：`agents/nodes.py` 与 `infrastructure/tools.py` 输出统一格式日志（入口、出口、异常、结果规模），覆盖 Router/Agent A/Agent B/Agent C 全链路。

状态增量可审计：通过 `historical_context`、`realtime_news`、`errors` 的 reducer 累加结果，可直接在执行结果中回放每个分支贡献。

可扩展方向：后续可无缝接入 LangSmith / LangGraph Studio 做甘特图级时序追踪。

### 5.2 用户视角的交互可视化 (Thin UI Layer)

技术选型：Streamlit (极简聊天界面)

实现目标：不需要像底层 RAG 那样做复杂的 6 页面管理后台，但需要一个轻量级的 C 端展示窗。

交互体验设计：利用 Streamlit 的 `st.status` 组件实时渲染流转过程，并提供评估开关与报告下载能力。

🟢 “Router 已识别意图：综合投研”

🔄 “Agent A 正在通过 MCP 协议查阅本地财报...” (并行)

🔄 “Agent B 正在检索互联网实时舆情...” (并行)

📝 “Agent C 正在聚合生成最终 Markdown 简报...”

附加能力（已实现）：

- 侧边栏 `开启 LLM 深度评估` 开关：控制是否执行双指标质量评估（默认关闭以保障交互时延）。
- 报告下载：生成后支持一键下载 Markdown 研报，便于审阅与归档。

### 5.3 投研报告自动化评估系统 (Agentic Evaluation)

传统的召回率 (Hit Rate) 评估属于 RAG Server 层，Agent 层的评估必须采用 LLM-as-a-Judge (LLM 裁判) 模式。

黄金测试集 (Golden Test Set)：沉淀 20 条高频高难度的投研查询（如：“对比宁德时代的历史毛利率和今天的固态电池新闻”）。

评估实现：`scripts/evaluate_agent.py` 调用 `core.evaluator.AgentEvaluator`，按测试集批量执行图并输出汇总报表。

当前核心指标（双指标）：

无幻觉性 (Faithfulness)：评估最终报告是否可被 `historical_context` 与 `realtime_news` 证据支撑，识别编造与越界推断。

答案相关性 (Answer Relevance)：评估最终报告是否直接、完整、聚焦回答用户问题。

工程化产出：每个样本输出 `latency_seconds`、双指标分数与推理理由，并计算平均分与平均时延，便于回归对比。

## 6. 健壮性与容错测试策略 (Robustness & Testing)

### 6.1 优雅降级 (Graceful Degradation) 设计

由于高度依赖外部网络 (Web Search) 与跨进程调用 (MCP Stdio)，系统不可避免会遇到调用失败。严禁因单一 Tool 失败导致整个 Graph 崩溃。

节点级捕获：Agent A/B 调用 Tool 时使用 `try-except` 包裹，确保单点故障不扩散为全局崩溃。

超时熔断：

- MCP 调用在 `session.call_tool(..., read_timeout_seconds=90s)` 下执行，超时映射为 `MCP_CONNECTED_BUT_QUERY_TIMEOUT` 并降级记录为 `MCP_SERVER_UNAVAILABLE`。
- Tavily 调用使用 `asyncio.wait_for(..., timeout=20s)` 包裹线程化请求，超时统一映射 `WEB_SEARCH_FAILED`。

日志留痕：工具层与节点层统一记录 `info/error/exception`，便于线上问题追踪与 SLA 复盘。

状态熔断记录：

若 MCP Server 宕机：Agent A 捕获异常，将空列表写入 historical_context，并将 "MCP_SERVER_UNAVAILABLE" 写入全局 State 的 errors 字段。

若 Tavily API 限流：Agent B 将 "WEB_SEARCH_FAILED" 写入 errors。

末端降级渲染：Agent C 在生成报告前检查 `errors` 数组。若非空，强制在报告顶部注入：`⚠️ 容错降级提示：外部数据源异常...`，并继续输出完整 Markdown 结构，实现优雅降级而非失败中断。

### 6.2 质量保证与测试策略 (QA Strategy)

Mock 隔离测试 (Unit Testing)：

使用 `unittest.mock.patch` 同时拦截 MCP 与 Tavily 调用，主动抛出异常，验证 `errors` 字段会追加 `MCP_SERVER_UNAVAILABLE` 与 `WEB_SEARCH_FAILED`。

端到端降级闭环断言：即使双工具同时失败，Graph 仍能流转至 Agent C，并输出带“⚠️ 容错降级提示”的最终报告。

持久化验证：主入口使用 `SqliteSaver`（`checkpoints.db`）进行 thread 级状态保存，用于跨轮对话恢复与问题复盘。

## 7. 项目排期与验收标准 (Milestones & Acceptance Criteria)

采用 TDD (测试驱动开发) 模式，分 6 个 Phase 小步快跑落地。核心架构代码需保持扁平化。

| 阶段 | 核心任务目标 | 输出文件 | 验收标准 (Acceptance Criteria) |

| --- | --- | --- | --- |

| Phase 1 | 环境基建与 State 定义  搭建 LangGraph 骨架，定义 TypedDict 与 Router 函数。 | state.py  router.py | 1. 成功定义 AgentState 及其 Reducers。  2. 注入各类 Mock 问题，断言 Router 能返回准确的单节点或并发分发列表。 |

| Phase 2 | MCP Client 联调与 Tool 封装  建立 stdio 进程通信，封装 MCP Tool 与 Web Search API。 | mcp_client.py  tools.py | 1. 成功拉起本地 RAG Server 子进程而不挂起。  2. 将 Server tool 转换为 LangChain 格式，完成跨进程 Function Calling。 |

| Phase 3 | Agent 开发与图连线  实现 A/B/C 节点逻辑及 System Prompt，完成 StateGraph 编译。 | agents.py  graph.py | 1. 3 个 Node 函数编写完成，能够正确读取、调用工具并更新 State。  2. 成功调用 workflow.compile() 并打印出完整的 DAG 图拓扑结构。 |

| Phase 4 | 并发逻辑与持久化验证  验证 Fan-out 耗时，挂载 SqliteSaver 检查点。 | main.py | 1. 验证并发度：Fan-out 模式下，整体耗时约为 Max(A耗时, B耗时)。  2. 传入相同 thread_id 重启应用，能够无缝追问上一轮的历史上下文。 |

| Phase 5 | 容错处理与 E2E 测试  实现 Try-Catch 降级机制，完成端到端容错闭环。 | tests/ | 1. 断开外部网络触发执行，系统未崩溃，Agent C 成功渲染出带有“降级免责提示”的研报。  2. 核心代码严格控制在 500 行左右。 |

| Phase 6 | UI与自动化评估接入  开发 Streamlit UI 与 LLM-as-a-judge 评估脚本。 | app.py  eval.py | 1. 启动 app.py 能在网页端看到实时的节点流转状态 (st.status)。  2. 评估脚本能自动化跑通黄金测试集，输出无幻觉率 (Faithfulness) 得分。 |


## 🤖 AI 自动化执行追踪表 (AI Execution Tracker) Autonomy-Token: my-sleep-token-2026
Autonomy-Token: my-sleep-token-2026

> **[SYSTEM DIRECTIVE TO AI AGENT / @ProjectDirector]**
> 你是本项目的自动化执行监工。你必须严格遵守以下执行纪律：
> 1. **单步执行原则**：每次只能执行一个未打钩 `[ ]` 的 Phase。
> 2. **强制边界**：绝对不允许修改或创建属于下一个 Phase 的文件。
> 3. **验证即打卡**：完成代码编写后，必须执行该 Phase 对应的 `[CLI 验证命令]`。只有命令成功且无报错，才能将 `[ ]` 修改为 `[x]`。
> 4. **强制暂停 (Halt)**：打卡完成后，**必须立即停止生成**，向用户输出：“✅ Phase X 已完成并验证。请 Code Review。输入 `继续` 执行下一阶段。” 未经人类明确授权，严禁进入下一阶段。

---

- [x] **Phase 1: 环境基建与 State 定义**
  - **核心目标**: 建立强类型的全局状态契约与意图路由机制。
  - **文件范围**: 创建 `state.py`, 创建 `router.py`
  - **关键约束**: 
    - `AgentState` 必须使用 `typing.TypedDict`，且对 `messages`, `historical_context`, `realtime_news`, `errors` 必须使用 `Annotated[..., operator.add]` 保证并发下的增量更新。
    - `router.py` 不涉及具体工具调用，仅负责输出 `"fundamental"`, `"sentiment"`, `"comprehensive"` 或 `"unknown"`。
  - **CLI 验证命令**: 
    `python -c "from state import AgentState; from router import intent_router; print('Phase 1 Syntax OK')"`

- [x] **Phase 2: MCP Client 联调与 Tool 封装**
  - **核心目标**: 实现跨进程通信封装，并暴露为 LangChain 工具。
  - **文件范围**: 创建 `mcp_client.py`, 创建 `tools.py`
  - **关键约束**: 
    - `mcp_client.py` 必须包含管理 stdio 子进程生命周期的机制（例如上下文管理器）。
    - 必须在工具调用中加入 `try-except` 块。若 MCP 离线，返回字符串 `"MCP_SERVER_UNAVAILABLE"`；若网络搜索失败，返回 `"WEB_SEARCH_FAILED"`。
  - **CLI 验证命令**: 
    `python -c "from tools import mcp_query_knowledge_hub; print('Phase 2 Tools Imported OK')"`

- [x] **Phase 3: Agent 节点逻辑与图拓扑构建**
  - **核心目标**: 填充三大 Agent 的业务逻辑，并编译 StateGraph。
  - **文件范围**: 创建 `agents.py`, 创建 `graph.py`
  - **关键约束**: 
    - **Agent C 强制逻辑**: 必须读取 `state.get("errors", [])`。若不为空，强制在输出文本开头追加：`"⚠️ 容错降级提示：外部数据源异常..."`。
    - `graph.py` 必须使用 `add_conditional_edges` 根据 Router 结果返回 ["agent_a", "agent_b"] 实现 Fan-out。
  - **CLI 验证命令**: 
    `python -c "from graph import workflow; compiled = workflow.compile(); print('Phase 3 Graph Compiled OK')"`

- [x] **Phase 4: 并发逻辑与持久化验证**
  - **核心目标**: 组装主入口，挂载 SQLite 记忆，验证并发执行。
  - **文件范围**: 创建 `main.py`
  - **关键约束**: 
    - 实例化 `from langgraph.checkpoint.sqlite import SqliteSaver`。
    - `main.py` 需要提供一个简单的 CLI 交互循环或单次执行入口，能够接收 `thread_id` 以验证持久化。
  - **CLI 验证命令**: 
    `python -c "import sqlite3; from main import main; print('Phase 4 Main Entry OK')"`

- [x] **Phase 5: 容错处理与 E2E 单元测试**
  - **核心目标**: 验证系统的健壮性，防止单点故障引发全局崩溃。
  - **文件范围**: 创建 `tests/test_degradation.py`
  - **关键约束**: 
    - 使用 `unittest.mock` 强制拦截 `tools.py` 的网络请求和 MCP 请求，抛出异常。
    - 断言 (Assert) 最终执行到达了 Agent C 且 `errors` 状态被正确写入。
  - **CLI 验证命令**: 
    `pytest tests/test_degradation.py -v`

- [x] **Phase 6: UI 与自动化评估接入**
  - **核心目标**: 套壳 Streamlit 并接入 LLM 评估脚本。
  - **文件范围**: 创建 `app.py`, 创建 `eval.py`
  - **关键约束**: 
    - `app.py` 保持极致轻量（Thin Layer），仅使用 `st.status` 或 `st.spinner` 渲染图节点的执行进度。
    - `eval.py` 需实现基于 LLM-as-a-judge 的 Faithfulness（无幻觉性）指标检验。
  - **CLI 验证命令**: 
    `streamlit run app.py --server.headless true` (启动并检查无语法报错即可)

- [x] **Phase 7: 工程架构重构 (Architecture Refactoring)**
  - **核心目标**: 消除扁平化结构，建立 `core`, `agents`, `infrastructure`, `ui`, `scripts` 五大核心模块，并确保模块间绝对导入 (Absolute Import) 正确无误。
  - **文件范围**: 所有 `.py` 文件及 `DEV_SPEC.md`。
  - **关键约束**: 
    1. 必须创建对应文件夹并在每个文件夹下生成 `__init__.py`。
    2. 移动文件：`state.py/router.py/graph.py` -> `core/`；`agents.py` 移至 `agents/` 并重命名为 `nodes.py`；`mcp_client.py/tools.py` -> `infrastructure/`；`app.py` -> `ui/`；`main.py/eval.py` -> `scripts/`。
    3. 必须扫描并重写所有移动后文件内部的 `import` 路径（如 `from core.state import AgentState`）。
  - **CLI 验证命令**: 
    `python -c "from core.graph import workflow; workflow.compile(); print('Phase 7 Refactor Import OK')"`

- [x] Phase 7: 工程架构重构 (拆分 core, agents, infrastructure, ui, scripts 包并修复跨目录绝对导入)
