@echo off
setlocal

cd /d "%~dp0.."

docker compose ^
  --env-file .env ^
  -f compose.client.yml ^
  exec backend ^
  python manage.py createsuperuser

echo.
echo Proceso finalizado.
pause
