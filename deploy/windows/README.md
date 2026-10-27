# Distribución local para Windows

Esta variante instala NacAgencyCRM para un solo computador sin requerir Docker, PostgreSQL, Node.js ni Python en el equipo del cliente.

## Arquitectura

- Django + Waitress en `127.0.0.1:8000`.
- Frontend de Next.js exportado como archivos estáticos y servido por Django.
- API REST bajo `/api/` en el mismo origen.
- SQLite persistente y privada por usuario en `%LOCALAPPDATA%\NacAgencyCRM\data\crm.sqlite3`.
- Secretos generados durante la primera ejecución en `%LOCALAPPDATA%\NacAgencyCRM\config\secrets.json`.
- Respaldos atómicos en `%LOCALAPPDATA%\NacAgencyCRM\backups`; cada ZIP incluye la base, su configuración criptográfica y un manifiesto de integridad.

## Construcción

Desde PowerShell, en un computador de desarrollo con Python 3.11.5, Node.js 26.7.0 y npm 11.19.0:

```powershell
.\deploy\windows\build-windows.ps1
```

El script limpia las variables `NEXT_PUBLIC_*`, fija la API en `/api`, ejecuta pruebas/lint/build del frontend, instala dependencias en `.build\windows`, corre las pruebas backend y genera:

```text
dist\windows\NacAgencyCRM\NacAgencyCRM.exe
```

Después de instalar Inno Setup 6.7.3:

```powershell
.\deploy\installer\build-installer.ps1
```

El instalador queda en:

```text
deploy\installer\Output\NacAgencyCRM-Setup-1.0.0.exe
```

## Accesos directos instalados

- **Abrir CRM**: inicia la aplicación sin mostrar consola y abre el navegador.
- **Crear administrador**: solicita usuario, correo y contraseña mediante el comando seguro de Django.
- **Respaldar datos**: crea una copia consistente de SQLite.
- **Detener CRM**: detiene el proceso local.
- **Abrir carpeta de datos**: abre datos, configuración, logs y respaldos.

No existen credenciales administrativas predeterminadas. Después de instalar, use **Crear administrador** antes del primer inicio de sesión.

## Actualización y desinstalación

Antes de actualizar o desinstalar, el instalador mantiene mutexes de mantenimiento locales y globales durante toda la operación para impedir nuevos arranques y serializar setup, actualización y desinstalación incluso entre sesiones de Windows. En una actualización, primero extrae y valida el candidato en una carpeta temporal; solo después detiene la instancia autenticada, exige un respaldo verificable y conserva una copia de la aplicación anterior. El candidato prepara y valida la base canónica antes de que Inno Setup confirme archivos, accesos directos o metadatos de desinstalación. Si la preparación, las migraciones o el reemplazo fallan, se revierten los archivos y se restauran conjuntamente la base y los secretos desde el respaldo retenido; el instalador devuelve un código de error. La desinstalación también detiene, respalda y conserva los datos antes de eliminar binarios. La carpeta `%LOCALAPPDATA%\NacAgencyCRM` no se elimina durante una actualización ni durante la desinstalación. Esto conserva la base, secretos, logs y respaldos. Para borrar los datos definitivamente se requiere una acción manual explícita.

Los ZIP de respaldo incluyen `secrets.json` porque ese material es imprescindible para restaurar contraseñas SMTP cifradas. Trátelos como datos confidenciales y manténgalos únicamente en almacenamiento privado del propietario de la cuenta Windows.

## Límites

SQLite es apropiado para una instalación local y pocos usuarios concurrentes. Para uso multiusuario intensivo o acceso remoto debe migrarse a la variante PostgreSQL en un servidor privado o VPS.

Los artefactos internos de desarrollo no se firman automáticamente. Para distribución pública, firme `NacAgencyCRM.exe` y el instalador con un certificado Authenticode confiable y sello de tiempo antes de entregarlos.

`requirements-windows.lock.txt` fija versiones exactas, pero todavía no incorpora hashes de los paquetes. Esto limita la reproducibilidad y verificación de la cadena de suministro hasta que el lock se regenere con hashes.
