# Financial-Agent-Client

简要说明
----------------
这是一个以多 agent 为中心的金融/股票分析客户端示例工程。它包含若干 agent 节点、演示脚本和一个简单 UI（`ui/app.py`），用于演示如何组合多个分析 agent 来完成信息检索、模型推理与结果汇总。

主要功能
----------------
- 多 agent 协作框架与路由（见 `core/router.py`、`agents/`）。
- 演示脚本：`run_app.py`、`testollama.py`。
- 集成常见工具与评估脚本（`scripts/`）。

快速开始
----------------
1. 创建并激活虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. 安装依赖：

```powershell
pip install -r requirements.txt
```

3. 运行演示：

```powershell
python run_app.py
```

目录结构（概要）
----------------
- `agents/`：agent 定义与节点。
- `core/`：路由、状态与评估逻辑。
- `infrastructure/`：MCP 客户端、工具适配器。
- `ui/`：示例前端（Flask/Tk 等轻量演示）。

注意事项
----------------
- 请在运行前确认虚拟环境与依赖已正确安装。
- 根据需要配置外部 LLM 与密钥（不应直接提交到仓库）。
