@echo off
echo ========================================
echo 重启 MCP Memory Service
echo ========================================
echo.

echo [1/3] 查找并停止运行中的服务...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8888 ^| findstr LISTENING') do (
    echo 找到进程 PID: %%a
    taskkill /F /PID %%a 2>nul
    if %errorlevel% equ 0 (
        echo 成功停止进程 %%a
    ) else (
        echo 进程 %%a 已停止或不存在
    )
)

echo.
echo [2/3] 等待 2 秒...
timeout /t 2 /nobreak >nul

echo.
echo [3/3] 启动 MCP Memory Service (Hybrid 模式)...
cd /d "%~dp0"
set MCP_MEMORY_STORAGE_BACKEND=hybrid
set MCP_API_KEY=mem0ry-shared-key-2024

echo.
echo 配置信息:
echo   - 存储后端: Hybrid (本地 + Cloudflare)
echo   - HTTP 端口: 8888
echo   - 仪表盘: http://127.0.0.1:8888/#
echo.

echo 正在启动服务...
start "MCP Memory Service" cmd /k "uv run python run_server.py"

echo.
echo ========================================
echo 服务重启完成！
echo ========================================
echo.
echo 请验证服务状态:
echo   1. 访问: http://127.0.0.1:8888/#
echo   2. 检查健康状态: curl http://127.0.0.1:8888/api/health
echo.
pause
