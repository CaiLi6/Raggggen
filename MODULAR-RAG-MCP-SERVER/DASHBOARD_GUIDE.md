# Dashboard 启动指南

## 前置条件

1. 已创建 `.venv_server` 虚拟环境并安装好依赖（`pip install -e .`）
2. Ollama 正在运行（`ollama serve`）
3. 已通过 `ingest.py` 构建过知识库

## 启动 Dashboard

### 方式一：直接用完整路径（推荐）

打开 PowerShell 终端，依次输入：

```powershell
cd C:\Users\mech-mind\Desktop\test\Rag-Agent\MODULAR-RAG-MCP-SERVER
..\.venv_server\Scripts\python.exe -m streamlit run src/observability/dashboard/app.py
```

### 方式二：先激活虚拟环境

```powershell
cd C:\Users\mech-mind\Desktop\test\Rag-Agent\MODULAR-RAG-MCP-SERVER
..\.venv_server\Scripts\Activate.ps1
python -m streamlit run src/observability/dashboard/app.py
```

激活成功后，命令行前面会显示 `(.venv_server)`，表示当前终端已进入虚拟环境。

> **注意**：如果激活时报错"无法运行脚本"，先执行：
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

### 方式三：用项目自带脚本

```powershell
cd C:\Users\mech-mind\Desktop\test\Rag-Agent\MODULAR-RAG-MCP-SERVER
..\.venv_server\Scripts\python.exe scripts/start_dashboard.py
```

## 访问 Dashboard

启动后终端会显示：

```
Local URL: http://localhost:8501
```

在浏览器中打开 **http://localhost:8501** 即可。

## Dashboard 功能说明

| 页面 | 功能 |
|------|------|
| Overview | 系统概览，知识库统计 |
| Ingestion Manager | 管理文档，上传/删除/重新导入 |
| Ingestion Traces | 查看每次 ingestion 的详细处理过程（6 个阶段） |
| Query Traces | 查看每次查询的检索过程（Dense/Sparse/Fusion/Rerank） |
| Data Browser | 浏览已存储的 chunks 和向量数据 |
| Evaluation Panel | 检索质量评估 |

## 停止 Dashboard

在启动 Dashboard 的终端中按 `Ctrl + C` 即可停止。

## 常见问题

### Q: 报错 `chromadb package is required`
**原因**：用了系统全局 Python 而不是 `.venv_server` 的 Python。  
**解决**：确保用 `..\.venv_server\Scripts\python.exe` 启动，而不是直接 `python`。

### Q: 如何确认当前用的是哪个 Python？
```powershell
# 查看当前 python 路径
Get-Command python | Select-Object -ExpandProperty Source
```
如果显示的不是 `.venv_server` 下的路径，需要激活虚拟环境或使用完整路径。

### Q: 端口被占用
指定其他端口：
```powershell
..\.venv_server\Scripts\python.exe -m streamlit run src/observability/dashboard/app.py --server.port 8502
```
