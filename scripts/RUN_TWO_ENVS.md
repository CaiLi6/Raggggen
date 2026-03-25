示例：分别在两个独立虚拟环境中启动 Client 与 RAG Server

目的：在同一机器上用两个独立的 Python 解释器隔离依赖，避免前端/交互库与 RAG 后端产生依赖冲突。

文件：
- `scripts/run_two_envs.ps1` — PowerShell 示例（Windows）
- `scripts/run_two_envs.sh`  — Bash 示例（类 Unix）

PowerShell 使用：
1. 在 PowerShell 中执行（需要 Python 在 PATH）：

```powershell
.\scripts\run_two_envs.ps1
```

2. 若已安装依赖并只想启动：

```powershell
.\scripts\run_two_envs.ps1 -NoInstall
```

Bash 使用：
1. 给予可执行权限并运行（Linux / macOS / WSL）：

```bash
chmod +x scripts/run_two_envs.sh
NO_INSTALL=1 ./scripts/run_two_envs.sh
```

注意：
- 脚本会在仓库根目录下创建两个 venv：`.venv_client` 和 `.venv_server`。
- Client 使用：`Financial-Agent-Client/requirements.txt`。
- Server 使用：对 `MODULAR-RAG-MCP-SERVER` 目录执行 `pip install -e`（基于其 `pyproject.toml`）。
- 脚本尽量保持简单，可能需要根据你的具体启动入口（参数/环境变量/配置文件）做小的调整。
- 脚本在后台启动进程；请在 Task Manager / `ps` 中查看或用 `kill` 停止。

如需，我可以把脚本改为使用 Docker Compose 示例（更适合生产隔离）。
