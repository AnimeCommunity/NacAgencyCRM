@echo off
setlocal

cd /d "%~dp0.."

if not exist "backups" mkdir "backups"

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set TIMESTAMP=%%I

set BACKUP_FILE=backups\crm_%TIMESTAMP%.dump

echo Creando respaldo...

docker compose ^
  --env-file .env ^
  -f compose.client.yml ^
  exec -T db ^
  sh -c "PGPASSWORD=$POSTGRES_PASSWORD pg_dump -U $POSTGRES_USER -d $POSTGRES_DB -Fc" ^
  > "%BACKUP_FILE%"

if errorlevel 1 (
    echo No fue posible crear el respaldo.
    if exist "%BACKUP_FILE%" del "%BACKUP_FILE%"
    pause
    exit /b 1
)

echo Respaldo creado:
echo %BACKUP_FILE%

forfiles /p "backups" /m "*.dump" /d -30 /c "cmd /c del @path" >nul 2>&1

pause
