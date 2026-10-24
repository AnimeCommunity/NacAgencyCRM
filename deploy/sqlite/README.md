# Despliegue temporal con SQLite

Esta configuración permite desplegar el backend Django sin PostgreSQL mientras se consigue un servidor definitivo.

## Condición obligatoria

`SQLITE_NAME` debe apuntar a un directorio persistente del proveedor. Si el proveedor elimina el sistema de archivos al reiniciar o redesplegar, también eliminará la base de datos.

No utilices esta variante con varias instancias del backend. Se configura un solo worker mediante `WEB_CONCURRENCY=1` para reducir conflictos de escritura.

## Backend

1. Configura el directorio raíz del servicio como `CRM`.
2. Instala dependencias con:

   ```bash
   pip install -r requirements.txt
   ```

3. Define las variables tomando como base `.env.example`.
4. Usa como comando de inicio:

   ```bash
   sh ../deploy/sqlite/start-backend.sh
   ```

   Si el proveedor copia únicamente la carpeta `CRM`, utiliza:

   ```bash
   python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn CRM.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 60
   ```

5. Crea el administrador en la consola del proveedor:

   ```bash
   python manage.py createsuperuser
   ```

## Frontend

Despliega `frontendcrm` como un servicio separado y configura durante el build:

```text
NEXT_PUBLIC_API_URL=https://DOMINIO-DEL-BACKEND/api
```

En el backend configura:

```text
CORS_ALLOWED_ORIGINS=https://DOMINIO-DEL-FRONTEND
CSRF_TRUSTED_ORIGINS=https://DOMINIO-DEL-FRONTEND
DJANGO_ALLOWED_HOSTS=DOMINIO-DEL-BACKEND
```

## Respaldo

El archivo indicado por `SQLITE_NAME` contiene los datos. Antes de cada actualización, descarga una copia con el backend detenido o utiliza el comando de backup del proveedor.

## Migración futura a PostgreSQL

Esta rama no elimina el soporte PostgreSQL. Para regresar a PostgreSQL cambia `DB_ENGINE=postgresql` y configura `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` y `POSTGRES_PORT`.
