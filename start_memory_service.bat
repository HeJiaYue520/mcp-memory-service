@echo off
chcp 65001 >nul
echo ========================================
echo  MCP Memory Service (v11, Qdrant backend)
echo ========================================

echo [1/2] 停止占用 8888 的旧进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8888 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul

cd /d "%~dp0"

rem 端口对齐 Claude MCP 配置(.claude.json -> 127.0.0.1:8888)
set MCP_HTTP_PORT=8888
rem MCP_API_KEY 不在此硬编码, 由 .env 提供(.env 已被 gitignore)
rem 固定 embedding 模型为本机已缓存的 all-MiniLM-L6-v2(384维, 与已迁移数据匹配)
set MCP_MEMORY_EMBEDDING_MODEL=C:\Users\嘉悦\.cache\torch\sentence_transformers\models--sentence-transformers--all-MiniLM-L6-v2\snapshots\c9745ed1d9f207416be6d2e6f8de32d1f16199bf
rem 离线加载, 避免去连 HuggingFace 镜像
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1

echo [2/2] 启动服务 (端口 8888, Qdrant 嵌入式)...
echo   仪表盘: http://127.0.0.1:8888/
echo.
uv run python run_server.py
