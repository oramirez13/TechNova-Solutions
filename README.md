# TechNova Solutions

Aplicación web en Flask para la gestión de usuarios, proyectos, sprints, tareas tipo kanban y avances, usando MySQL como base de datos.

## Estado actual del proyecto

El sistema implementa actualmente:

- autenticación con Flask sessions
- registro y login con contraseñas hasheadas
- gestión de proyectos con responsable asignado
- gestión de sprints por proyecto
- tablero kanban con tareas, prioridades, responsables y fechas límite
- registro de avances por sprint
- validaciones de permisos para evitar que usuarios no autorizados editen recursos ajenos
- página de dashboard y página informativa de blog

El alcance actual no incluye una pantalla de auditoría ni un módulo visual de reportes con gráficos.

## Errores detectados en la revisión

1. Las contraseñas se almacenaban y validaban en texto plano.
2. La aplicación dependía de secretos y credenciales hardcodeadas en `app.py`.
3. Cualquier usuario autenticado podía editar o eliminar proyectos, sprints y tareas ajenas.
4. El número de sprint no tenía una restricción única en base de datos.
5. El formulario permitía enviar `objetivo_completado`, pero el backend lo ignoraba al crear sprints.
6. Proyectos y sprints aceptaban fechas inconsistentes, incluyendo fin anterior al inicio.
7. El filtro del dashboard mezclaba `sprint_id` y `sprint_numero`, lo que podía mostrar tareas del sprint equivocado.

## Registro de cambios aplicados

- Se migró el registro y login a contraseñas con hash usando `werkzeug.security`.
- Se eliminaron secretos fijos del código y ahora la app exige variables de entorno para la conexión MySQL.
- Se agregaron validaciones de permisos para que solo el responsable del proyecto o un rol `Manager`/`Admin` pueda gestionar proyectos, sprints, tareas y avances.
- Se validan rangos de fechas y formatos antes de escribir en la base de datos.
- Se guarda correctamente el avance inicial de un sprint.
- Se reforzó la consistencia del modelo con un índice único por `proyecto_id + numero` en sprints.
- Se corrigió el filtro de tareas por sprint en el dashboard.
- Se actualizaron los datos de ejemplo del esquema para usar contraseñas hasheadas sin cambiar las credenciales de acceso.

## Requisitos

- Python 3.10 o superior
- MySQL Server 8.x o compatible
- `pip`
- Terminal con acceso a `mysql`

## Estructura importante

- `app.py`: servidor Flask
- `database/schema.sql`: creación de base de datos, tablas, índices y datos de ejemplo
- `requirements.txt`: dependencias del proyecto
- `templates/`: vistas HTML (`index`, `dashboard`, `blog`, `404` y componentes compartidos)
- `static/js/dashboard.js`: lógica del dashboard, proyectos, sprints y kanban
- `static/js/script.js`: login y registro

## Modelo de datos actual

El esquema maneja estas tablas principales:

- `usuarios`
- `proyectos`
- `sprints`
- `tareas`
- `avances`

Relación general:

- un usuario puede ser responsable de varios proyectos
- un proyecto puede tener varios sprints
- un proyecto puede tener varias tareas
- una tarea puede estar asociada a un sprint o permanecer en backlog
- un sprint puede tener varios avances

## Pantallas y rutas principales

Páginas HTML:

- `/`: login y registro
- `/dashboard`: gestión de proyectos, sprints y tablero kanban
- `/blog`: página informativa de TechNova Solutions

API principal:

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

## 1. Entrar al proyecto

Desde la carpeta padre:

```bash
cd technova_solutions
```

## 2. Crear y activar entorno virtual

En Linux o macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

En Windows con PowerShell:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

## 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

Esto instala:

- `Flask`
- `mysql-connector-python`

## 4. Crear la base de datos en MySQL

La app ya no usa credenciales embebidas en el código. Se recomienda crear este usuario:

- Base de datos: `technova`
- Usuario: `technova_app`
- Password: `technova_app_2026`
- Host: `localhost`

### Opción recomendada: crear un usuario específico para la app

Entrar a MySQL como administrador:

```bash
mysql -u root -p
```

Luego ejecutar:

```sql
CREATE DATABASE IF NOT EXISTS technova
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_spanish_ci;

CREATE USER IF NOT EXISTS 'technova_app'@'localhost' IDENTIFIED BY 'technova_app_2026';
GRANT ALL PRIVILEGES ON technova.* TO 'technova_app'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## 5. Cargar el esquema y los datos iniciales

Desde la carpeta `technova_solutions`, ejecutar:

```bash
mysql -u technova_app -p technova < database/schema.sql
```

Cuando MySQL pida la contraseña, ingresar:

```text
technova_app_2026
```

Este script:

- crea las tablas `usuarios`, `proyectos`, `sprints`, `tareas` y `avances`
- agrega índices
- inserta datos de ejemplo
- ejecuta consultas de verificación al final

## 6. Configurar variables de entorno

Este paso ahora es obligatorio.

La aplicacion carga automaticamente un archivo local `technova_solutions/.env` si existe. Puedes partir de `.env.example`.

Si quieres definirlas manualmente en Linux o macOS:

```bash
export TECHNOVA_DB_HOST=localhost
export TECHNOVA_DB_USER=technova_app
export TECHNOVA_DB_PASSWORD=technova_app_2026
export TECHNOVA_DB_NAME=technova
export TECHNOVA_SECRET_KEY="cambia-esta-clave-por-una-segura"
```

En Windows con PowerShell:

```powershell
$env:TECHNOVA_DB_HOST="localhost"
$env:TECHNOVA_DB_USER="technova_app"
$env:TECHNOVA_DB_PASSWORD="technova_app_2026"
$env:TECHNOVA_DB_NAME="technova"
$env:TECHNOVA_SECRET_KEY="cambia-esta-clave-por-una-segura"
```

Tambien puedes copiar el ejemplo:

```bash
cp .env.example .env
```

## 7. Levantar la aplicación Flask

```bash
python app.py
```

La app arranca en:

```text
http://127.0.0.1:5000
```

`app.py` levanta Flask en modo debug y en el puerto `5000`.

## 8. Probar acceso con usuarios de ejemplo

El `schema.sql` inserta estos usuarios:

- `orami@technova.cr` / `017240`
- `maria@technova.cr` / `123456`
- `carlos@technova.cr` / `123456`
- `ana@technova.cr` / `123456`

Puedes iniciar sesión con cualquiera desde la pantalla principal. Las contraseñas ya se almacenan con hash, pero las credenciales de ejemplo siguen siendo las mismas.

## 9. Qué puedes probar en la aplicación

Después de iniciar sesión puedes:

- crear, editar, pausar y eliminar proyectos
- asignar o reasignar responsables de proyecto según permisos
- crear y editar sprints
- registrar el porcentaje de avance del sprint
- crear, editar, mover y eliminar tareas en el tablero kanban
- asignar tareas a usuarios activos
- asociar tareas a un sprint o dejarlas en backlog
- registrar avances dentro de un sprint con tipo de avance, horas trabajadas y estado de tarea
- navegar a la página `/blog`

## 10. Verificación rápida si algo falla

### Verificar que MySQL esté activo

```bash
mysql -u technova_app -p -e "SHOW DATABASES;"
```

### Verificar tablas creadas

```bash
mysql -u technova_app -p technova -e "SHOW TABLES;"
```

### Verificar usuarios cargados

```bash
mysql -u technova_app -p technova -e "SELECT id, nombre, correo, rol FROM usuarios;"
```

### Verificar sprints, tareas y avances

```bash
mysql -u technova_app -p technova -e "SELECT id, proyecto_id, numero, nombre, estado FROM sprints;"
mysql -u technova_app -p technova -e "SELECT id, proyecto_id, sprint_id, titulo, estado, posicion FROM tareas;"
mysql -u technova_app -p technova -e "SELECT id, sprint_id, usuario_id, tipo_avance, horas_trabajadas FROM avances;"
```

## 11. Problemas comunes

### Error de conexión a MySQL

Revisa:

- que el servicio de MySQL esté encendido
- que el usuario y la contraseña coincidan
- que `TECHNOVA_DB_HOST`, `TECHNOVA_DB_USER`, `TECHNOVA_DB_PASSWORD` y `TECHNOVA_DB_NAME` estén correctos

### Error `Access denied for user`

Vuelve a crear el usuario y permisos:

```sql
CREATE USER IF NOT EXISTS 'technova_app'@'localhost' IDENTIFIED BY 'technova_app_2026';
GRANT ALL PRIVILEGES ON technova.* TO 'technova_app'@'localhost';
FLUSH PRIVILEGES;
```

### Error porque las tablas ya existen o ya hay datos

Si quieres reiniciar todo desde cero:

```bash
mysql -u root -p -e "DROP DATABASE IF EXISTS technova;"
mysql -u root -p -e "CREATE DATABASE technova CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci;"
mysql -u technova_app -p technova < database/schema.sql
```

### Error de permisos al editar proyectos, sprints, tareas o avances

Revisa:

- si el usuario autenticado es el responsable del proyecto
- si el usuario tiene rol `Manager` o `Admin`
- si el recurso pertenece al proyecto correcto

La aplicación bloquea cambios sobre proyectos ajenos para usuarios sin privilegios.

## Flujo rápido

Si ya tienes MySQL instalado, el flujo mínimo sería:

```bash
cd technova_solutions
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
mysql -u root -p
```

Dentro de MySQL:

```sql
CREATE DATABASE IF NOT EXISTS technova CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci;
CREATE USER IF NOT EXISTS 'technova_app'@'localhost' IDENTIFIED BY 'technova_app_2026';
GRANT ALL PRIVILEGES ON technova.* TO 'technova_app'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

De vuelta en terminal:

```bash
mysql -u technova_app -p technova < database/schema.sql
export TECHNOVA_DB_HOST=localhost
export TECHNOVA_DB_USER=technova_app
export TECHNOVA_DB_PASSWORD=technova_app_2026
export TECHNOVA_DB_NAME=technova
export TECHNOVA_SECRET_KEY="cambia-esta-clave-por-una-segura"
python app.py
```
