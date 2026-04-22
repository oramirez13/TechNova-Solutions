# TechNova Solutions

Aplicación web en Flask para gestión de usuarios, proyectos, sprints y avances, usando MySQL como base de datos.

## Requisitos

- Python 3.10 o superior
- MySQL Server 8.x o compatible
- `pip`
- Terminal con acceso a `mysql`

## Estructura importante

- `app.py`: servidor Flask
- `database/schema.sql`: creación de base de datos, tablas y datos de ejemplo
- `requirements.txt`: dependencias del proyecto

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

La app, por defecto, intenta conectarse con estas credenciales:

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

- crea las tablas `usuarios`, `proyectos`, `sprints` y `avances`
- agrega índices
- inserta datos de ejemplo
- ejecuta consultas de verificación al final

## 6. Configurar variables de entorno

La aplicación ya trae valores por defecto, así que si usaste el usuario `technova_app`, este paso es opcional.

Si quieres definirlas manualmente en Linux o macOS:

```bash
export TECHNOVA_DB_HOST=localhost
export TECHNOVA_DB_USER=technova_app
export TECHNOVA_DB_PASSWORD=technova_app_2026
export TECHNOVA_DB_NAME=technova
```

En Windows con PowerShell:

```powershell
$env:TECHNOVA_DB_HOST="localhost"
$env:TECHNOVA_DB_USER="technova_app"
$env:TECHNOVA_DB_PASSWORD="technova_app_2026"
$env:TECHNOVA_DB_NAME="technova"
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

Puedes iniciar sesión con cualquiera desde la pantalla principal.

## 9. Verificación rápida si algo falla

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

## 10. Problemas comunes

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
python app.py
```
