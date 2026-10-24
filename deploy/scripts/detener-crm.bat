@echo off
setlocal

cd /d "%~dp0.."

echo Deteniendo NacAgencyCRM...

docker compose ^
  --env-file .env ^
  -f compose.client.yml ^
  stop

echo NacAgencyCRM fue detenido.
pause
