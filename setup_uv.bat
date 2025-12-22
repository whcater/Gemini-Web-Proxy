@echo off
chcp 65001 >nul
echo ========================================
echo   Gemini Web Proxy - 环境配置脚本
echo   使用 uv 管理 Python 版本
echo ========================================
echo.

:: 检查 uv 是否已安装
where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [1/4] 未检测到 uv，正在安装...
    echo.
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo ❌ uv 安装失败，请手动安装后重试
        echo    参考文档: ENVIRONMENT_SETUP.md
        pause
        exit /b 1
    )
    echo.
    echo ✅ uv 安装成功
    echo.
) else (
    echo [1/4] ✅ uv 已安装
    echo.
)

:: 安装 Python 3.12
echo [2/4] 正在检查 Python 3.12...
uv python install 3.12
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Python 3.12 安装失败
    pause
    exit /b 1
)
echo ✅ Python 3.12 就绪
echo.

:: 删除旧的虚拟环境
if exist .venv (
    echo [3/4] 检测到旧的虚拟环境，正在删除...
    rmdir /s /q .venv
    echo ✅ 旧环境已清理
    echo.
) else (
    echo [3/4] 准备创建虚拟环境...
    echo.
)

:: 创建新的虚拟环境
echo 正在创建基于 Python 3.12 的虚拟环境...
uv venv --python 3.12
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 虚拟环境创建失败
    pause
    exit /b 1
)
echo ✅ 虚拟环境创建成功
echo.

:: 激活虚拟环境并安装依赖
echo [4/4] 正在安装项目依赖...
call .venv\Scripts\activate.bat
uv pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)
echo ✅ 依赖安装成功
echo.

:: 安装 Playwright 浏览器
echo 正在安装 Playwright Chromium...
playwright install chromium
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ⚠️  Playwright 安装失败，请稍后手动运行:
    echo    playwright install chromium
    echo.
) else (
    echo ✅ Playwright Chromium 安装成功
    echo.
)

:: 显示 Python 版本
echo ========================================
echo   环境配置完成！
echo ========================================
echo.
python --version
echo.
echo 💡 下一步：
echo    1. 激活虚拟环境: .venv\Scripts\activate
echo    2. 运行服务: python main.py
echo    3. 或直接运行: run.bat
echo.
echo 📖 详细文档请查看: ENVIRONMENT_SETUP.md
echo.
pause
