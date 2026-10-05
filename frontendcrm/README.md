# Frontend CRM ANC

Aplicación Next.js para operar clientes, interacciones, proyectos, cotizaciones, marketing y reportes del CRM.

## Configuración

Crea `frontendcrm/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

El cliente normaliza esa URL y usa la base `/api`. También acepta una URL que ya termine en `/api`.

## Desarrollo

```bash
cp .env.example .env.local
npm install
npm run dev
```

La aplicación queda disponible en `http://localhost:3000`.

## Verificación

```bash
npm run lint
npx tsc --noEmit --incremental false
npm run build
```

## Contrato de autenticación y permisos

- Registro público: `POST /api/register/` crea una solicitud inactiva con rol `sales`; un administrador debe activarla.
- Inicio y renovación JWT: `/api/token/` y `/api/token/refresh/`.
- Cierre de sesión: `POST /api/logout/` con el refresh token.
- El JWT incluye `user_id`, `username` y `role`; la UI oculta acciones incompatibles y el backend valida los permisos.
