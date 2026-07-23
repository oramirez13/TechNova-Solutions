# TechNova Solutions

TechNova Solutions es una aplicación web desarrollada con Flask y MariaDB para administrar proyectos de trabajo, sprints, tareas tipo kanban y avances del equipo.

El sistema está pensado como una herramienta sencilla para organizar el flujo de trabajo de un equipo técnico. Permite registrar usuarios, iniciar sesión, crear proyectos, planificar sprints, asignar tareas y guardar avances con horas trabajadas.

## Funcionalidades principales

- Registro e inicio de sesión de usuarios.
- Contraseñas guardadas con hash seguro.
- Dashboard privado para usuarios autenticados.
- Gestión de proyectos con responsable asignado.
- Gestión de sprints por proyecto.
- Tablero kanban para tareas.
- Estados de tareas: backlog, pendiente, en proceso y completada.
- Asignación de tareas a usuarios activos.
- Registro de avances por sprint.
- Control básico de permisos por usuario y rol.
- Página informativa tipo blog.

## Tecnologías usadas

- Python
- Flask
- MariaDB o MySQL compatible
- mysql-connector-python
- HTML
- CSS
- JavaScript

## Estructura del proyecto

```text
technova_solutions/
├── app.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .dockerignore
├── database/
│   └── schema.sql
├── docs/
│   └── GUIA_TECNICA_TECHNOVA.md
├── static/
│   ├── css/
│   ├── img/
│   └── js/
└── templates/
    ├── index.html
    ├── dashboard.html
    ├── blog.html
    ├── 404.html
    └── _navbar.html
```

## Archivos importantes

- `app.py`: contiene la aplicación Flask, rutas HTML, rutas API, validaciones y conexión con la base de datos.
- `database/schema.sql`: crea las tablas, relaciones, índices y datos iniciales.
- `requirements.txt`: lista las dependencias de Python necesarias para ejecutar el proyecto.
- `templates/`: contiene las vistas HTML del login, dashboard, blog y errores.
- `static/css/style.css`: contiene los estilos visuales.
- `static/js/script.js`: maneja el registro y login.
- `static/js/dashboard.js`: maneja proyectos, sprints, tareas, kanban y avances.
- `docs/GUIA_TECNICA_TECHNOVA.md`: explica el proyecto con más detalle técnico.

## Modelo de datos

La base de datos usa estas tablas principales:

- `usuarios`
- `proyectos`
- `sprints`
- `tareas`
- `avances`

Relación general:

- Un usuario puede ser responsable de varios proyectos.
- Un proyecto puede tener varios sprints.
- Un proyecto puede tener varias tareas.
- Una tarea puede estar asignada a un usuario.
- Una tarea puede pertenecer a un sprint o quedar en backlog.
- Un sprint puede tener varios avances.

## Rutas principales

Páginas:

- `/`: pantalla de inicio de sesión y registro.
- `/dashboard`: panel principal para administrar proyectos, sprints, tareas y avances.
- `/blog`: página informativa del proyecto.

API:

- `POST /api/registro`
- `POST /api/login`
- `POST /api/logout`
- `GET /api/usuarios`
- `GET|POST /api/proyectos`
- `PUT|DELETE /api/proyectos/<proyecto_id>`
- `PATCH /api/proyectos/<proyecto_id>/estado`
- `GET|POST /api/sprints/<proyecto_id>`
- `PUT /api/sprint/<sprint_id>`
- `GET|POST /api/tareas/<proyecto_id>`
- `PUT|DELETE /api/tarea/<tarea_id>`
- `PATCH /api/tarea/<tarea_id>/kanban`
- `GET|POST /api/avances/<sprint_id>`
- `PUT|DELETE /api/avance/<avance_id>`

## Requisitos

**Opcion local:**
- Python 3.10 o superior.
- MariaDB o MySQL compatible.
- `pip`.
- Terminal con acceso al comando `mariadb`.

**Opcion Docker:**
- Docker Engine o Docker Desktop.
- Docker Compose v2.

## Instalación

Entrar a la carpeta del proyecto:

```bash
cd technova_solutions
```

Crear un entorno virtual:

```bash
python3 -m venv .venv
```

Activar el entorno virtual en Linux o macOS:

```bash
source .venv/bin/activate
```

Activar el entorno virtual en Windows con PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Configuración de base de datos

El proyecto usa variables de entorno para conectarse a MariaDB. Las credenciales reales no deben publicarse en GitHub.

Crear una copia local del archivo de ejemplo:

```bash
cp .env.example .env
```

Editar `.env` y completar los valores locales:

```bash
TECHNOVA_DB_HOST=localhost
TECHNOVA_DB_PORT=3307
TECHNOVA_DB_USER=technova_app
TECHNOVA_DB_PASSWORD=CAMBIA_ESTA_PASSWORD
TECHNOVA_DB_NAME=technova
TECHNOVA_SECRET_KEY=CAMBIA_ESTA_CLAVE
```

El archivo `.env` está ignorado por Git para evitar publicar información sensible.

## Crear base de datos y usuario

Entrar a MariaDB como administrador:

```bash
mariadb -u root -p
```

Si MariaDB no permite entrar con `root` y muestra `Access denied for user 'root'@'localhost'`, probar:

```bash
sudo mariadb
```

Crear la base de datos y el usuario de la aplicación. Reemplazar `CAMBIA_ESTA_PASSWORD` por la contraseña local privada:

```sql
CREATE DATABASE IF NOT EXISTS technova
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_spanish_ci;

CREATE USER IF NOT EXISTS 'technova_app'@'localhost' IDENTIFIED BY 'CAMBIA_ESTA_PASSWORD';
ALTER USER 'technova_app'@'localhost' IDENTIFIED BY 'CAMBIA_ESTA_PASSWORD';
GRANT ALL PRIVILEGES ON technova.* TO 'technova_app'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## Cargar tablas y datos iniciales

Ejecutar el esquema desde la carpeta del proyecto:

```bash
mariadb -u technova_app -p -h 127.0.0.1 -P 3307 technova < database/schema.sql
```

Cuando MariaDB pida la contraseña, ingresar la contraseña privada configurada localmente.

## Ejecutar la aplicación

### Instalación local

Con el entorno virtual activo:

```bash
python app.py
```

Abrir la aplicación en el navegador:

```text
http://127.0.0.1:5000
```

### Ejecutar con Docker

Clonar el repositorio:

```bash
git clone https://github.com/oramirez13/TechNova-Solutions.git
cd TechNova-Solutions
```

Crear el archivo de credenciales para Docker:

```bash
cp .env.example .env.docker
```

Editar `.env.docker` con las credenciales reales:

```bash
MARIADB_ROOT_PASSWORD=contraseña_root
MARIADB_DATABASE=technova
MARIADB_USER=technova_app
MARIADB_PASSWORD=contraseña_app
TECHNOVA_SECRET_KEY=clave_secreta_flask
```

Levantar los contenedores:

```bash
docker compose up -d
```

Verificar que los servicios estén corriendo:

```bash
docker compose ps
```

Abrir la aplicación en el navegador:

```text
http://127.0.0.1:5000
```

Detener los contenedores:

```bash
docker compose down
```

Detener y eliminar datos (volumen de MariaDB):

```bash
docker compose down -v
```

## Verificación rápida

Verificar conexión a MariaDB:

```bash
mariadb -u technova_app -p -h 127.0.0.1 -P 3307 technova
```

Verificar tablas:

```bash
mariadb -u technova_app -p -h 127.0.0.1 -P 3307 technova -e "SHOW TABLES;"
```

Verificar usuarios:

```bash
mariadb -u technova_app -p -h 127.0.0.1 -P 3307 technova -e "SELECT id, nombre, correo, rol FROM usuarios;"
```

## Archivo privado local

Este repositorio puede tener un archivo local llamado `.credenciales_technova.md` con pasos internos y contraseñas privadas.

Ese archivo está ignorado por Git y no debe subirse a GitHub.

## Problemas comunes

### `mysql: Deprecated program name`

En MariaDB moderno puede aparecer este aviso:

```text
mysql: Deprecated program name. It will be removed in a future release
```

No es un error del proyecto. Usar `mariadb` en vez de `mysql`.

### `Access denied for user 'root'@'localhost'`

Este error significa que MariaDB no aceptó el acceso con el usuario `root`.

En Linux puede solucionarse entrando con:

```bash
sudo mariadb
```

### Error de conexión desde Flask

Revisar:

- Que MariaDB esté encendido.
- Que exista la base de datos `technova`.
- Que exista el usuario `technova_app`.
- Que el puerto configurado coincida con `TECHNOVA_DB_PORT`.
- Que la contraseña local de `.env` coincida con la contraseña configurada en MariaDB.

## Seguridad

- No subir `.env` a GitHub.
- No subir `.credenciales_technova.md` a GitHub.
- No escribir contraseñas reales en el README.
- Cambiar `TECHNOVA_SECRET_KEY` antes de usar el proyecto fuera de un entorno local.
- Usar contraseñas diferentes para cada ambiente.
