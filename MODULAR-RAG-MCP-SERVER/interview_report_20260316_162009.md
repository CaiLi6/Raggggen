# 模拟面试报告

**项目**：Modular RAG MCP Server
**面试时间**：2026-03-16 16:20:09
**评分**：6/10

---

## 一、面试记录（原文逐字记录）

### 方向 1：项目综述

| 轮次 | 问题（原文） | 候选人回答（原文） |
|-----:|-------------|-------------------|
| Q1 | 这个系统里 MCP 协议起什么作用？为什么不直接暴露 REST API？ | mcp主要是用于连接整个项目和比如用户使用的agent client，当用户发起mcp tool调用时，mcp server会接受到这样一个json rpc的信息格式， |

### 方向 2：简历深挖

| 轮次 | 问题（原文） | 候选人回答（原文） |
|-----:|-------------|-------------------|
| Q2 | 你简历里写“端到端查询延迟控制在 500–1200ms”，这个延迟是在什么硬件环境下测的？并发量是多少？这是 P50 还是 P99？ | 是在dashboead中显示的，我对项目可以通过这样一个可视化平台进行监控整个端到端的延迟情况 |
| Q3.1 | 在项目代码或配置里，精排候选集大小 K 是哪个文件和哪个参数控制的？ | 是在config文件夹下的settiongs.yaml文件下的topk控制k |

### 方向 3：技术深挖

| 轮次 | 问题（原文） | 候选人回答（原文） |
|-----:|-------------|-------------------|
| Q3 | 精排候选集多大合适？K 开太大会有什么问题？ | 我不知道 |
| Q4 | Dashboard 上显示的是哪个分位数的延迟指标？是 P50、P95 还是 P99？ | 我不知道 |
| Q5 | 如果 Reranker 超时导致延迟激增，系统如何保证可用性？具体有哪些超时/回退策略？这些策略在代码或配置里具体是怎样实现的？ | 系统采用了fallback机制好像是，就是如果rerank阶段因为一些延迟或者什么原因导致了rerank失败会使用dense和sparse两路检索召回的融合过后的结果，这样来保持可用性。 |
| Q6 | Stdio Transport 的 stdin/stdout/stderr 分别承担什么职责？如果支持远程多客户端并发，为什么要改用 HTTP Transport？两者在安全性与运维上有什么权衡？ | 完全不转到 |
| Q7 | 如果项目中某个 LLM Provider 挂了，系统如何检测并降级？配置或代码里哪里控制这些策略？请具体说明超时时间、重试、回退到哪个 Provider、以及相关配置/代码位置 | 不转到 |

---

## 二、参考答案（按需复制自预置库，保留锚点）

<a id="a-mcp协议"></a>
Q: MCP 是什么规范？暴露了哪些 Tool？

**参考答案**：
MCP（Model Context Protocol）是 Anthropic 提出的开放协议，基于 JSON-RPC 2.0，定义 AI Client 与外部工具/数据源之间的标准通信接口。任何合规 Client（Copilot、Claude Desktop）即插即用。

本项目采用 **Stdio Transport**：Client 以子进程启动 Server，stdin/stdout 通信，日志走 stderr，零网络依赖。

对外暴露 3 个 Tool：

| Tool | 功能 | 关键参数 |
|------|------|---------|
| `query_knowledge_hub` | 主检索入口（Hybrid Search + Rerank） | `query`, `top_k?`, `collection?` |
| `list_collections` | 列举可用文档集合 | 无 |
| `get_document_summary` | 获取文档摘要与元信息 | `doc_id` |

每条检索结果携带结构化 Citation（来源文件名、页码、chunk 摘要），可选返回 Base64 图片。

---

<a id="a-cross-encoder"></a>
Q: Cross-Encoder 和 Bi-Encoder 的区别？为什么不能做粗排召回？

**参考答案**：

| | Bi-Encoder | Cross-Encoder |
|--|-----------|--------------|
| 编码方式 | Query 和 Document **分别**编码为向量，算相似度 | Query 和 Document **拼接**一起输入模型，联合建模 |
| Document 向量 | 可**离线预计算**，查询时 O(1) | 每对 (Query, Chunk) 必须**实时推理**，O(n) |
| 精度 | 较低（无交互） | 更高（充分建模交互特征） |
| 适合场景 | 粗排召回（大规模） | 精排（10-30 条小候选集） |

说明：Cross-Encoder 不适合用于大候选集的粗排，因为实时推理成本高；常见实践是先用 Bi-Encoder/Hybrid Search 粗召回 Top-N（例如 N=50），再用 Cross-Encoder 对 M≤30 的子集精排。

---

<a id="a-可观测性"></a>
Q: Trace 与 Dashboard 如何支持延迟监控？

**参考答案**：

Trace 体系：
- **双链路**：Ingestion Trace（Load→Split→Transform→Embed→Upsert）+ Query Trace（QueryProcess→DenseRecall→SparseRecall→Fusion→Rerank）
- **存储**：JSON Lines 结构化日志，低侵入，供 Dashboard 动态渲染。

Dashboard 页面包括 Query 追踪（Dense/Sparse 召回对比、Rerank 前后排名变化）和 Ingestion 追踪（阶段耗时瀵布图），可显示分位数（P50/P95/P99）或平均耗时，用于观察端到端延迟变化与回退触发情况。

---

## 三、简历包装点评

### 包装合理 ✅
- **"实现 LLM/Embedding/Reranker/VectorStore 全链路可插拔"**：候选人在回答中指出配置文件中可控制 `topk`（`config/settings.yaml`），显示对配置驱动思想有一定理解。

### 露馅点 ❌
- **"端到端延迟 500–1200ms"** → 面试中无法给出测试环境、并发或分位数（P50/P99）等复现信息（Q2/Q4 回答为“在 dashboard 显示”/“我不知道”），无法验证量化指标来源。**严重性：中**
- **精排候选集大小与原理** → 对于精排候选集为何选 M≈10–30、K 设置的影响未能阐明（Q3 回答“我不知道”），体现实现细节掌握不足。**严重性：中**
- **Stdio Transport 与并发/运维权衡** → 无法回答 Stdio 的 stdin/stdout/stderr 角色及为何切换到 HTTP（Q6 回答“完全不转到”），体现对 MCP 传输与运维场景理解薄弱。**严重性：高**
- **Provider 故障检测与降级策略** → 未能说明具体超时/重试/回退实现（Q7 回答“不转到”），对高可用策略缺乏细节。**严重性：高**

### 改进建议
- 熟记并能解释 RRF 公式与 Cross-Encoder 的使用场景（能说明候选集大小为何通常限制在几十条）。
- 准备一份可复现的性能测量说明（硬件规格、并发数、P50/P95/P99 区别、测试脚本或代码位置）。
- 能指出配置与代码中具体控制项（例如 `config/settings.yaml` 的相关字段名），并能举例展示重试/回退配置位置。
- 补充 Stdio vs HTTP 的运维与安全权衡说明（stdin/stdout 用法、日志走 stderr、远程访问需 HTTP+鉴权）。

---

## 四、综合评价

**优势**：
- 对项目整体架构与可插拔思想有感知（能指出使用配置控制 `topk`），并对 fallback 思路有基本理解（知道有 RRF/Hybrid 回退）。

**薄弱点**：
- 实现细节掌握不足：对延迟测量复现方法、分位数（P50/P99）、Reranker 退化路径与具体配置位置回答模糊或缺失。
- 对运维/协议细节（Stdio Transport、并发场景切换到 HTTP）的理解不够深入。

**面试官建议**：准备好一两处代码或配置文件的示例（如 `config/settings.yaml` 中的 `reranker.top_k` 与 `timeout` 字段、重试策略实现位置），并能口述性能测试的复现步骤与结果统计方法。

---

## 五、评分（满分 10）

| 维度 | 分数（满分 10） | 评分依据 |
|-----|--------------:|---------|
| 项目架构掌握 | 7 | 能描述 MCP 与可插拔设计、知道配置控制项，但细节表达欠缺 |
| 简历真实性 | 6 | 提供了量化指标，但无法说明复现方法与数据来源，存在部分未验证的陈述 |
| 算法理论深度 | 6 | 对 Hybrid/RRF 有基本认知，对 Cross-Encoder 有概念性理解，但缺少候选集大小和精排成本的量化说明 |
| 实现细节掌握 | 4 | 多处关键实现（分位数测量、超时/回退配置、Stdio 细节）无法说明 |
| 表达清晰度 | 6 | 回答直接，但多为简短或“我不知道”，影响评估深度 |
| **综合** | **6** | 加权汇总，建议加强具体细节和复现能力 |

---

报告文件已保存：`interview_report_20260316_162009.md`
