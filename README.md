# CRM ANC - Aplicación Web Desacoplada

Este proyecto es un sistema CRM moderno y desacoplado, estructurado en un backend robusto con **Django Rest Framework** y un frontend dinámico con **Next.js (React)**. Todo el entorno de desarrollo está completamente dockerizado para facilitar su despliegue local con un solo comando.

---

## Arquitectura y Tecnologías

El proyecto se divide en tres servicios principales gestionados por Docker:

*   **Frontend (`/frontendcrm`):** Next.js (Node v20) corriendo en el puerto `3000`.
*   **Backend (`/CRM`):** Django Rest Framework (Python 3.11) corriendo en el puerto `8000`.
*   **Base de Datos (`db`):** PostgreSQL para el almacenamiento persistente de datos.

---

## Requisitos Previos

Antes de empezar, asegúrate de tener instalado en tu máquina:

*   [Docker](https://www.docker.com/products/docker-desktop/)
*   [Docker Compose](https://docs.docker.com/compose/install/)

---

## Configuración y Despliegue

Sigue estos pasos para clonar el proyecto y ponerlo en marcha:

### 1. Clonar el repositorio
```bash
git clone https://github.com/AnimeCommunity/NacAgencyCRM.git
cd NacAgencyCRM
```

### 2. Construir y levantar los contenedores
Docker se encargará de descargar las imágenes necesarias, instalar las dependencias de Python y Node, y enlazar los servicios.

```bash
docker-compose up --build
```

> **Nota:** Si prefieres correr los contenedores en segundo plano (detached mode), puedes añadir la bandera `-d`:
> ```bash
> docker-compose up -d --build
> ```

Una vez que termine el proceso, podrás acceder a los servicios en tu navegador:
*   **Frontend (Next.js):** [http://localhost:3000](http://localhost:3000)
*   **Backend (Django API):** [http://localhost:8000](http://localhost:8000)

---

## Migraciones y Comandos Útiles

Dado que la base de datos se ejecuta dentro de un contenedor, debes ejecutar los comandos de Django a través de Docker. Abre una nueva terminal en la raíz del proyecto para ejecutar lo siguiente:

### Crear migraciones (cuando hagas cambios en los modelos)
```bash
docker-compose exec backend python manage.py makemigrations
```

### Aplicar migraciones en la base de datos
```bash
docker-compose exec backend python manage.py migrate
```

### Crear un superusuario para el panel de administración
```bash
docker-compose exec backend python manage.py createsuperuser
```

---

## Estructura del Proyecto

La raíz del repositorio tiene la siguiente distribución:

```text
├── CRM/                  # Directorio del Backend (Django)
│   ├── Dockerfile        # Configuración de Docker para Python/Django
│   ├── requirements.txt  # Dependencias de Python
│   └── ...               
├── frontendcrm/          # Directorio del Frontend (Next.js)
│   ├── Dockerfile        # Configuración de Docker para Node/Next.js
│   ├── package.json      # Dependencias de npm
│   └── ...
└── docker-compose.yml    # Orquestación de contenedores (Multi-container)
```

---

## Detalles de Desarrollo

### Recarga Rápida (Hot Reload)
*   **Backend:** Los cambios en el código de Django se reflejarán inmediatamente gracias al volumen enlazado `./CRM:/code`.
*   **Frontend:** Para asegurar que Next.js detecte los cambios de archivos dentro de Docker de manera fluida, la variable de entorno `WATCHPACK_POLLING=true` está activa en el archivo de configuración.

---

## Apagar el Entorno

Para detener todos los servicios y liberar los puertos de tu máquina local, presiona `Ctrl + C` en la terminal donde se está ejecutando Docker, o corre el siguiente comando desde la raíz del proyecto:

```bash
docker-compose down
```

---

## Autor

Este proyecto ha sido desarrollado y es mantenido por:

*   **Daniel Santiago Pineda Garnica**
    *   Correo electrónico: [tu.email@ejemplo.com](mailto:dspinedaga@unad.com)
    *   LinkedIn: [@tu-usuario](https://co.linkedin.com/in/daniel-santiago-pineda-garnica-ab214894)
    *   GitHub: [@tu-usuario](https://github.com/AnimeCommunity)
    *   Portafolio / Web: [tudominio.com](https://aniokku.netlify.app/)

---

## Licencia

Este proyecto está bajo la Licencia [MIT](LICENSE).
