@echo off
REM 启动 OpenMontage Studio
REM 首次会装依赖，之后直接启动

chcp 65001 >nul
pushd "%~dp0"

REM 第一次：装依赖
if not exist "backend\__installed__" (
    echo [setup] 首次运行，安装依赖…
    pushd backend
    ..\..\..\..\.venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        popd
        popd
        pause
        exit /b 1
    )
    popd
    echo. > backend\__installed__
)

REM 启动
echo.
echo ============================================================
echo  OpenMontage Studio
echo  打开 http://localhost:8000
echo ============================================================
echo.

..\.venv\Scripts\python.exe -m uvicorn backend.server:app --port 8000 --reload

popd
pause
