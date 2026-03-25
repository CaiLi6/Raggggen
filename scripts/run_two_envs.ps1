<#
Example PowerShell script to create two virtual environments and run
the Client (Financial-Agent-Client) and the RAG Server (MODULAR-RAG-MCP-SERVER)
in separate interpreters.

Usage (PowerShell):
  .\scripts\run_two_envs.ps1
#>
param(
    [switch]$NoInstall
)

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ClientVenv = Join-Path $RepoRoot ".venv_client"
$ServerVenv = Join-Path $RepoRoot ".venv_server"

function Ensure-Venv($venvPath) {
    if (-not (Test-Path $venvPath)) {
        Write-Host "Creating venv: $venvPath"
        python -m venv $venvPath
    } else {
        Write-Host "Venv exists: $venvPath"
    }
}

# Create venvs
Ensure-Venv $ClientVenv
Ensure-Venv $ServerVenv

if (-not $NoInstall) {
    Write-Host "Installing dependencies into client venv..."
    & "$ClientVenv\Scripts\Activate.ps1"
    pip install --upgrade pip
    pip install -r "${RepoRoot}\Financial-Agent-Client\requirements.txt"
    & "$ClientVenv\Scripts\deactivate.ps1" 2>$null

    Write-Host "Installing server package into server venv..."
    & "$ServerVenv\Scripts\Activate.ps1"
    pip install --upgrade pip
    pip install -e "${RepoRoot}\MODULAR-RAG-MCP-SERVER"
    & "$ServerVenv\Scripts\deactivate.ps1" 2>$null
}

Write-Host "Starting RAG Server in background..."
$serverPython = Join-Path $ServerVenv "Scripts\python.exe"
# Start server main.py from repo root so relative imports work
Start-Process -FilePath $serverPython -ArgumentList "${RepoRoot}\MODULAR-RAG-MCP-SERVER\main.py" -WorkingDirectory $RepoRoot -NoNewWindow

Start-Sleep -Milliseconds 500

Write-Host "Starting Client in background..."
$clientPython = Join-Path $ClientVenv "Scripts\python.exe"
Start-Process -FilePath $clientPython -ArgumentList "${RepoRoot}\Financial-Agent-Client\run_app.py" -WorkingDirectory $RepoRoot -NoNewWindow

Write-Host "Launched processes. Use Task Manager or `Get-Process` to inspect." 
Write-Host "To stop, kill the python processes started from the venvs or use their PIDs." 
