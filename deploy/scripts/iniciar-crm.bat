@echo off
setlocal

cd /d "%~dp0.."

echo Iniciando NacAgencyCRM...

docker info >nul 2>&1

if errorlevel 1 (
    if exist "%LOCALAPPDATA%\Programs\Docker\Docker\Docker Desktop.exe" (
        start "" "%LOCALAPPDATA%\Programs\Docker\Docker\Docker Desktop.exe"
    ) else if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
        start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
    ) else (
        echo No se encontro Docker Desktop.
        pause
        exit /b 1
    )

    echo Esperando a Docker Desktop...

    for /L %%I in (1,1,60) do (
        timeout /t 3 /nobreak >nul
        docker info >nul 2>&1
        if not errorlevel 1 goto docker_ready
    )

    echo Docker Desktop no respondio.
    pause
    exit /b 1
)

:docker_ready

docker compose ^
  --env-file .env ^
  -f compose.client.yml ^
  up -d --pull never

if errorlevel 1 (
    echo No fue posible iniciar el CRM.
    pause
    exit /b 1
)

echo Abriendo NacAgencyCRM...
start "" http://localhost:3000/login

exit /b 0