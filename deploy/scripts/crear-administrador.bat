@echo off
setlocal

cd /d "%~dp0.."

docker compose ^
  --env-file .env ^
  -f compose.client.yml ^
  ps --status running backend | findstr /C:"backend" >nul

if errorlevel 1 (
  echo El backend no esta disponible.
  echo Ejecuta primero "Iniciar NacAgencyCRM" y revisa los registros.
  pause
  exit /b 1
)

docker compose ^
  --env-file .env ^
  -f compose.client.yml ^
  exec backend ^
  python manage.py createsuperuser

if errorlevel 1 (
  echo.
  echo No fue posible crear el administrador.
  pause
  exit /b 1
)

echo.
echo Administrador creado correctamente.
pause
