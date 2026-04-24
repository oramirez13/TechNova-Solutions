# TechNova Solutions for PythonAnywhere

Esta version de `technova_solutions_render` quedo adaptada para desplegarse en PythonAnywhere con MySQL, sin tocar el proyecto original fuera de `flask/`.

La app tambien conserva compatibilidad con PostgreSQL si defines `DATABASE_URL` o `TECHNOVA_DB_ENGINE=postgres`.

## Archivos clave

- `app.py`: ahora detecta si debe usar MySQL o PostgreSQL
- `database/schema_pythonanywhere.sql`: esquema listo para importar en MySQL de PythonAnywhere
- `pythonanywhere_wsgi.py`: plantilla de WSGI para copiar al panel de PythonAnywhere
- `requirements.txt`: incluye dependencias para ambos motores

## 1. Subir o clonar el proyecto

En la consola Bash de PythonAnywhere:

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

## 3. Crear la base MySQL

En la pestaña `Databases` de PythonAnywhere:

1. define tu password de MySQL
2. crea una base llamada `technova`
3. anota:
   - tu usuario de PythonAnywhere
   - el host MySQL
   - el nombre real de la base, que sera `tuusuario$technova`

## 4. Importar el esquema

Desde Bash:

```bash
mysql -u tuusuario -h tuusuario.mysql.pythonanywhere-services.com -p 'tuusuario$technova' < database/schema_pythonanywhere.sql
```

## 5. Crear la web app

En la pestaña `Web`:

1. `Add a new web app`
2. elige `Manual configuration`
3. usa la misma version de Python del virtualenv
4. en `Virtualenv` coloca:

```text
/home/tuusuario/.virtualenvs/technova-pa
```

## 6. Configurar WSGI

Abre el archivo WSGI de PythonAnywhere y usa como base el contenido de `pythonanywhere_wsgi.py`.

Debes ajustar estos valores:

- `PROJECT_HOME`
- `TECHNOVA_DB_HOST`
- `TECHNOVA_DB_USER`
- `TECHNOVA_DB_PASSWORD`
- `TECHNOVA_DB_NAME`
- `SECRET_KEY`

La importacion final debe quedar asi:

```python
from app import app as application
```

## 7. Configurar archivos estaticos

En `Static files` agrega:

- URL: `/static/`
- Directory: `/home/tuusuario/TechNova-Solutions/flask/technova_solutions_render/static`

Luego pulsa `Reload`.

## 8. Variables de entorno que usa la app

### Para PythonAnywhere con MySQL

```text
TECHNOVA_DB_ENGINE=mysql
TECHNOVA_DB_HOST=tuusuario.mysql.pythonanywhere-services.com
TECHNOVA_DB_USER=tuusuario
TECHNOVA_DB_PASSWORD=tu-password-mysql
TECHNOVA_DB_NAME=tuusuario$technova
SECRET_KEY=una-clave-secreta-segura
```

### Para PostgreSQL

Opciones validas:

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

## 9. Usuarios de ejemplo

- `orami@technova.cr` / `017240`
- `maria@technova.cr` / `123456`
- `carlos@technova.cr` / `123456`
- `ana@technova.cr` / `123456`

## Notas

- Esta adaptacion no modifica nada fuera de `flask/`.
- PythonAnywhere no publica la app ejecutando `python app.py`; la publica via WSGI.
- Si tu cuenta gratuita no tiene MySQL disponible, necesitaras un plan compatible o cambiar de motor.
