# TechNova Solutions for PythonAnywhere Free

Esta version de `technova_solutions_render` quedo adaptada para funcionar en PythonAnywhere gratis usando SQLite, sin tocar el proyecto original fuera de `flask/`.

La app tambien conserva compatibilidad con PostgreSQL y MySQL si en otro entorno defines `DATABASE_URL` o `TECHNOVA_DB_ENGINE`.

## Archivos clave

- `app.py`: ahora soporta SQLite, PostgreSQL y MySQL
- `database/schema_sqlite.sql`: esquema y datos iniciales para SQLite
- `pythonanywhere_wsgi.py`: plantilla de WSGI para PythonAnywhere gratis
- `requirements.txt`: dependencias del proyecto

## Despliegue en PythonAnywhere gratis

## 1. Clonar el proyecto

En la consola Bash:

```bash
git clone https://github.com/oramirez13/TechNova-Solutions.git
cd TechNova-Solutions/flask/technova_solutions_render
```

## 2. Crear virtualenv

```bash
mkvirtualenv --python=/usr/bin/python3.10 technova-pa
workon technova-pa
pip install -r requirements.txt
```

## 3. Crear la web app

En la pestaña `Web`:

1. `Add a new web app`
2. elige `Manual configuration`
3. usa la misma version de Python del virtualenv
4. en `Virtualenv` coloca:

```text
/home/tuusuario/.virtualenvs/technova-pa
```

## 4. Configurar WSGI

Abre el archivo WSGI de PythonAnywhere y usa como base `pythonanywhere_wsgi.py`.

Debes ajustar:

- `PROJECT_HOME`
- `TECHNOVA_SQLITE_PATH`
- `SECRET_KEY`

Ejemplo:

```python
import os
import sys

PROJECT_HOME = "/home/tuusuario/TechNova-Solutions/flask/technova_solutions_render"
if PROJECT_HOME not in sys.path:
    sys.path.insert(0, PROJECT_HOME)

os.environ["TECHNOVA_DB_ENGINE"] = "sqlite"
os.environ["TECHNOVA_SQLITE_PATH"] = "/home/tuusuario/TechNova-Solutions/flask/technova_solutions_render/database/technova.sqlite3"
os.environ["SECRET_KEY"] = "cambia-esto-por-una-clave-segura"

from app import app as application
```

## 5. Configurar archivos estaticos

En `Static files` agrega:

- URL: `/static/`
- Directory: `/home/tuusuario/TechNova-Solutions/flask/technova_solutions_render/static`

Luego pulsa `Reload`.

## 6. Base de datos SQLite

No necesitas usar la pestaña `Databases`.

La app crea automaticamente `database/technova.sqlite3` en el primer arranque usando `database/schema_sqlite.sql`.

Si quieres inicializarla manualmente antes del reload:

```bash
cd ~/TechNova-Solutions/flask/technova_solutions_render
workon technova-pa
python -c "import app; print(app.SQLITE_PATH)"
```

## 7. Usuarios de ejemplo

- `orami@technova.cr` / `017240`
- `maria@technova.cr` / `123456`
- `carlos@technova.cr` / `123456`
- `ana@technova.cr` / `123456`

## Variables de entorno

### Para PythonAnywhere gratis con SQLite

```text
TECHNOVA_DB_ENGINE=sqlite
TECHNOVA_SQLITE_PATH=/home/tuusuario/TechNova-Solutions/flask/technova_solutions_render/database/technova.sqlite3
SECRET_KEY=una-clave-secreta-segura
```

### Para PostgreSQL

```text
DATABASE_URL=postgresql://usuario:password@host:5432/technova
```

o

```text
TECHNOVA_DB_ENGINE=postgres
TECHNOVA_DB_HOST=localhost
TECHNOVA_DB_PORT=5432
TECHNOVA_DB_USER=technova_app
TECHNOVA_DB_PASSWORD=technova_app_2026
TECHNOVA_DB_NAME=technova
```

### Para MySQL

```text
TECHNOVA_DB_ENGINE=mysql
TECHNOVA_DB_HOST=tu-host
TECHNOVA_DB_USER=tuusuario
TECHNOVA_DB_PASSWORD=tu-password
TECHNOVA_DB_NAME=tu-base
```

## Notas

- Esta adaptacion no modifica nada fuera de `flask/`.
- PythonAnywhere publica la app via WSGI, no con `python app.py`.
- En plan gratis, SQLite es la ruta recomendada porque no requiere MySQL.
