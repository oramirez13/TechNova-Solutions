# Guia Tecnica de TechNova Solutions

## 1. Objetivo de esta guia

Este documento esta pensado para estudiar el proyecto `technova_solutions` a fondo.
No explica solo "que hace" el sistema, sino tambien:

- como estan conectadas sus partes
- por que existen ciertas validaciones
- que tecnologias participan en cada proceso
- que ocurre desde que el usuario hace clic hasta que la base de datos cambia
- que cambios se agregaron durante la evolucion del proyecto

La mejor forma de estudiar este sistema es leer esta guia primero y despues abrir el codigo con ella al lado.

## 2. Vision general del sistema

TechNova Solutions es una aplicacion web de gestion interna construida con Flask y MySQL.
Permite:

- registrar usuarios
- iniciar sesion
- administrar proyectos
- administrar sprints por proyecto
- administrar tareas en formato kanban
- registrar avances dentro de los sprints

En terminos funcionales, la app modela una empresa de desarrollo de software:

- un usuario entra al sistema
- ve proyectos
- cada proyecto tiene sprints
- cada sprint y proyecto tienen tareas
- los avances documentan trabajo realizado dentro del sprint

## 3. Arquitectura general

La arquitectura es una app web clasica de servidor renderizado con una capa API JSON.

Capas principales:

1. Backend Flask:
   maneja rutas, sesiones, validaciones, permisos y acceso a base de datos.
2. Base de datos MySQL:
   almacena usuarios, proyectos, sprints, tareas y avances.
3. Templates HTML:
   renderizan las pantallas base.
4. JavaScript del frontend:
   consume la API y actualiza la interfaz sin recargar toda la pagina.
5. CSS:
   define la presentacion visual.

## 4. Tecnologias usadas y por que se usan

### Flask

Flask es el framework web principal.
Se usa para:

- definir rutas como `/`, `/dashboard` o `/api/login`
- renderizar templates HTML
- devolver respuestas JSON
- manejar sesiones de usuario
- ejecutar logica de negocio

En este proyecto Flask actua como servidor de paginas y como servidor API.

### Jinja2

Jinja2 es el motor de plantillas que usa Flask.
Permite:

- insertar variables del backend en HTML
- incluir componentes reutilizables
- cargar archivos estaticos con `url_for`

Ejemplos claros:

- `{{ usuario.nombre }}`
- `{% include '_navbar.html' %}`
- `{{ url_for('static', filename='css/style.css') }}`

### MySQL

Es la base de datos relacional del sistema.
Aqui se usa para guardar:

- usuarios
- proyectos
- sprints
- tareas
- avances

MySQL es importante porque el proyecto tiene relaciones reales entre tablas, restricciones e indices.

### mysql-connector-python

Es el conector entre Python y MySQL.
Permite:

- abrir conexiones
- ejecutar consultas SQL
- hacer `commit` y `rollback`
- recuperar filas como diccionarios

### Werkzeug security

Se usa para proteger contrasenas:

- `generate_password_hash(password)`
- `check_password_hash(hash, password)`

Esto evita guardar contrasenas en texto plano.

### Bootstrap 4

Se usa como base de componentes visuales:

- modales
- formularios
- grillas
- botones
- alertas

### jQuery

Se usa para:

- escuchar eventos del usuario
- hacer llamadas AJAX
- abrir o cerrar modales
- actualizar partes de la interfaz

### React UMD

Se usa solo como capa ligera para construir el encabezado moderno del dashboard.
No domina toda la aplicacion. La mayor parte del dashboard sigue viva en jQuery.

Esto significa que el proyecto hoy tiene un modelo mixto:

- React para el resumen visual del dashboard
- jQuery para la logica operativa del tablero

## 5. Estructura real del proyecto

### Backend

- `app.py`

### Base de datos

- `database/schema.sql`

### Templates

- `templates/index.html`
- `templates/dashboard.html`
- `templates/blog.html`
- `templates/404.html`
- `templates/_navbar.html`

### Frontend

- `static/js/script.js`
- `static/js/dashboard.js`
- `static/js/dashboard-react.js`
- `static/js/site.js`
- `static/css/style.css`

### Configuracion

- `requirements.txt`
- `.env.example`
- `.env` si existe localmente

## 6. Flujo de arranque del sistema

Cuando ejecutas:

```bash
python app.py
```

sucede esto:

1. Python carga `app.py`.
2. Se importan librerias.
3. Se ejecuta `cargar_variables_locales()`.
4. Flask se configura con `secret_key` y opciones de cookies.
5. Se declaran constantes de negocio:
   estados, prioridades, roles privilegiados, tipos de avance.
6. Se registran rutas y funciones.
7. Cada request pasa por `@app.before_request`.
8. `preparar_aplicacion()` llama `asegurar_estructura()`.

`asegurar_estructura()` intenta garantizar que ciertos elementos del esquema existan aunque la base ya este creada.

Esto es importante porque el sistema hace una pequena autoverificacion estructural antes de atender requests.

## 7. Configuracion por variables de entorno

El sistema evita hardcodear credenciales.
Lee:

- `TECHNOVA_DB_HOST`
- `TECHNOVA_DB_USER`
- `TECHNOVA_DB_PASSWORD`
- `TECHNOVA_DB_NAME`
- `TECHNOVA_SECRET_KEY`

La funcion `cargar_variables_locales()` carga `.env` manualmente si el archivo existe.

Eso permite:

- usar configuracion distinta segun el entorno
- no mezclar claves en el codigo
- hacer el proyecto mas portable

## 8. Modelo de datos y relaciones

### usuarios

Representa personas que usan el sistema.

Campos importantes:

- `nombre`
- `correo`
- `password`
- `rol`
- `activo`

### proyectos

Representa iniciativas o productos.

Cada proyecto tiene:

- nombre
- descripcion
- estado
- fechas
- responsable

Relacion:

- muchos proyectos pueden pertenecer a distintos usuarios responsables

### sprints

Representan ciclos de trabajo de un proyecto.

Cada sprint pertenece a un proyecto.
Tiene:

- numero
- nombre
- estado
- rango de fechas
- porcentaje de avance

### tareas

Representan trabajo operativo.

Cada tarea:

- pertenece a un proyecto
- puede o no pertenecer a un sprint
- puede o no estar asignada a un usuario
- tiene prioridad
- vive en una columna del kanban
- tiene posicion dentro de esa columna

### avances

Representan registros narrativos de trabajo realizado en un sprint.

Cada avance:

- pertenece a un sprint
- lo registra un usuario
- contiene descripcion
- tipo de avance
- horas trabajadas
- estado relacionado de tarea

## 9. Procesos principales del sistema

### Registro de usuario

Archivo implicado:

- `templates/index.html`
- `static/js/script.js`
- `app.py`
- tabla `usuarios`

Secuencia:

1. El usuario llena el formulario de registro.
2. `script.js` valida nombre, correo, rol y contrasena.
3. Se hace `POST /api/registro`.
4. Flask recibe JSON.
5. Se validan reglas:
   nombre minimo, correo valido, contrasena minima.
6. Se verifica si el correo ya existe.
7. Se guarda la contrasena con hash.
8. Se hace `commit`.
9. El frontend muestra exito y vuelve a la vista login.

### Login

Archivos implicados:

- `templates/index.html`
- `static/js/script.js`
- `app.py`

Secuencia:

1. El usuario envia correo y contrasena.
2. `script.js` hace `POST /api/login`.
3. Flask busca el usuario activo por correo.
4. Compara la contrasena usando `check_password_hash`.
5. Si es correcta, crea `session["usuario"]`.
6. Devuelve JSON con datos basicos del usuario.
7. El frontend redirige a `/dashboard`.

### Carga del dashboard

Archivos implicados:

- `templates/dashboard.html`
- `static/js/dashboard.js`
- `static/js/dashboard-react.js`
- `app.py`

Secuencia:

1. Flask renderiza `dashboard.html`.
2. Inyecta datos del usuario en atributos `data-*` del `<body>`.
3. `dashboard-react.js` usa esos datos para pintar el encabezado y KPIs.
4. `dashboard.js` carga usuarios y proyectos via AJAX.
5. Cuando el usuario expande un proyecto, se cargan sprints, tareas y avances.

### Creacion de proyecto

1. Se abre `modalProyecto`.
2. El frontend envia `POST /api/proyectos`.
3. Backend valida:
   nombre, fechas, estado, responsable.
4. Revisa permisos para asignar responsable.
5. Inserta el proyecto.
6. El frontend vuelve a cargar datos.

### Creacion de sprint

1. Se abre `modalSprint`.
2. Se envia `POST /api/sprints/<proyecto_id>`.
3. Backend valida fechas, estado y avance.
4. Si no se envio numero valido, calcula el siguiente.
5. Valida que el numero no se repita dentro del mismo proyecto.
6. Inserta el sprint.

### Creacion de tarea

1. Se abre `modalTarea`.
2. Se envia `POST /api/tareas/<proyecto_id>`.
3. Backend valida titulo, prioridad, estado y fecha.
4. Si hay sprint, verifica que pertenezca al proyecto.
5. Si hay asignado, verifica que exista y este activo.
6. Calcula la siguiente posicion dentro de la columna kanban.
7. Inserta la tarea.

### Movimiento kanban

Este es uno de los procesos mas interesantes del sistema.

Cuando una tarea cambia de columna:

1. El frontend envia `PATCH /api/tarea/<tarea_id>/kanban`.
2. Se identifica el estado origen y el estado destino.
3. Si cambia de columna, se normalizan las posiciones del origen.
4. Se reconstruye el orden del destino.
5. Se recalculan todas las posiciones de la columna destino.

La funcion clave es `normalizar_posiciones()`.

### Registro de avance

1. El usuario elige un sprint.
2. Abre `modalAvance`.
3. Se hace `POST /api/avances/<sprint_id>`.
4. Backend valida descripcion, tipo y estado relacionado.
5. Verifica que el sprint exista y que el usuario tenga permisos.
6. Inserta el avance asociandolo al usuario en sesion.

## 10. Permisos y seguridad

El proyecto agrego varias defensas que son parte de su logica importante.

### Sesiones

La sesion vive en `session["usuario"]`.
Si no existe:

- no puedes ver dashboard
- no puedes usar APIs internas

### Roles privilegiados

`ROLES_PRIVILEGIADOS = {"Admin", "Manager"}`

Estos roles tienen mas capacidad para reasignar responsables o gestionar recursos ajenos.

### Autorizacion por proyecto

La funcion `obtener_proyecto_autorizado()` es central.
Decide si un usuario puede tocar un proyecto.

Permite acceso si:

- el usuario es `Admin` o `Manager`
- o es el `responsable_id` del proyecto

Esa funcion se reutiliza en:

- proyectos
- sprints
- tareas
- avances

### Validaciones de fecha

`parsear_fecha()` y `validar_rango_fechas()` evitan:

- formatos invalidos
- fechas de fin anteriores al inicio

### Hash de contrasenas

Antes el sistema validaba texto plano.
Ahora:

- registra hashes
- verifica hashes
- incluso migra contrasenas antiguas si detecta una no hasheada en login

## 11. Archivo por archivo

### `app.py`

Es el cerebro del sistema.

Responsabilidades:

- configuracion
- lectura de entorno
- conexion a BD
- helpers de validacion
- helpers de permisos
- rutas HTML
- API JSON
- operaciones CRUD

Bloques mentales para estudiarlo:

1. configuracion y entorno
2. helpers reutilizables
3. proteccion y permisos
4. rutas de pantalla
5. autenticacion
6. CRUD de proyectos
7. CRUD de sprints
8. CRUD de tareas
9. CRUD de avances

### `database/schema.sql`

Define el modelo persistente.

Es importante estudiarlo junto con `app.py` porque:

- el backend valida cosas
- pero la base representa la verdad estructural

Puntos clave:

- claves primarias
- claves foraneas
- `ON DELETE`
- `ENUM`
- indice unico por `proyecto_id + numero` en sprints
- insercion de datos de ejemplo

### `templates/index.html`

Es la pantalla de acceso del sistema.

Un detalle importante:
esta plantilla ya contiene login y registro en una sola vista.
Por eso es mejor que las versiones antiguas separadas.

### `templates/dashboard.html`

No contiene el tablero completo renderizado desde Flask.
Contiene:

- la estructura base
- los modales
- el contenedor donde JS inyecta el contenido del dashboard

Es un shell de interfaz.

### `templates/blog.html`

Es una pagina informativa.
No participa en la logica de negocio principal, pero si en navegacion autenticada y en consistencia visual.

### `templates/_navbar.html`

Componente reutilizable para navegacion.
Centraliza el menu.

### `templates/404.html`

Pantalla de error amigable.

### `static/js/script.js`

Es la logica real de autenticacion actual.

Hace:

- alternar entre vista login y vista registro
- validaciones basicas en cliente
- `POST /api/login`
- `POST /api/registro`
- manejo de alertas visuales

### `static/js/dashboard.js`

Es la logica operativa mas grande del frontend.

Hace:

- cargar proyectos
- cargar usuarios
- cargar detalle por proyecto
- renderizar el tablero
- abrir modales
- guardar proyectos, sprints, tareas y avances
- eliminar elementos
- mover tareas por drag and drop
- sincronizar datos con `dashboard-react.js`

### `static/js/dashboard-react.js`

Construye la capa de resumen visual del dashboard:

- hero
- barra de busqueda
- filtros
- KPI cards
- resumen de carga del equipo

No administra el CRUD.
Recibe datos via eventos personalizados del navegador.

### `static/js/site.js`

Tiene una responsabilidad muy concreta:

- cerrar sesion desde cualquier vista que use la clase `.js-logout`

### `static/css/style.css`

Contiene el lenguaje visual del sistema:

- pantalla de login
- dashboard
- blog
- modales
- kanban
- tarjetas de avances

## 12. Cambios importantes agregados al proyecto

Estos son de los cambios mas relevantes y conviene entenderlos porque muestran evolucion tecnica:

### 1. Hash de contrasenas

Antes:

- contrasenas en texto plano

Ahora:

- hash con Werkzeug
- verificacion segura
- migracion de contrasenas antiguas al iniciar sesion

### 2. Variables de entorno

Antes:

- credenciales embebidas en el codigo

Ahora:

- `.env`
- `.env.example`
- validacion de faltantes

### 3. Permisos por proyecto

Antes:

- cualquier autenticado podia manipular recursos ajenos

Ahora:

- control por responsable o rol privilegiado

### 4. Restriccion unica de sprint

Antes:

- se podian repetir numeros de sprint dentro de un proyecto

Ahora:

- validacion en backend
- indice unico en base de datos

### 5. Validacion de fechas

Antes:

- podian existir rangos inconsistentes

Ahora:

- el backend lo rechaza explicitamente

### 6. Avances de sprint

Ahora existe un modulo especifico para:

- registrar trabajo realizado
- tipificar el avance
- guardar horas
- editar y eliminar avances

### 7. Dashboard enriquecido

Se agregaron:

- filtros
- KPIs
- capa React
- tarjetas de avances
- mejor presentacion del trabajo del equipo

## 13. Unificacion de codigo y limpieza

Durante la revision del proyecto habia codigo duplicado en autenticacion.

Versiones duplicadas detectadas:

- `templates/register.html`
- `static/js/login.js`
- `static/js/register.js`

Esos archivos representaban un flujo anterior separado.
La implementacion vigente y mas completa ya vive en:

- `templates/index.html`
- `static/js/script.js`

Por eso la forma correcta de unificar no es mezclar mas codigo, sino conservar el flujo activo y retirar los restos que ya no participan.

## 14. Como estudiar este proyecto de forma didactica

Orden recomendado:

1. Lee esta guia completa.
2. Abre `database/schema.sql` y entiende las tablas.
3. Revisa `app.py` solo por bloques, no linea por linea.
4. Sigue el flujo login -> dashboard -> proyecto -> sprint -> tarea -> avance.
5. Revisa `dashboard.js` con la interfaz abierta.
6. Haz cambios pequenos y observa el resultado.

## 15. Ruta de aprendizaje recomendada

### Fase 1: entender el mapa

Debes poder responder:

- que entidades existen
- como se relacionan
- quien llama a quien
- que parte corre en backend y cual en frontend

### Fase 2: entender procesos

Debes poder explicar:

- como inicia sesion un usuario
- como se crea un proyecto
- como se mueve una tarea en kanban
- como se registra un avance

### Fase 3: entender decisiones tecnicas

Debes poder justificar:

- por que usar hash
- por que validar fechas en backend
- por que usar permisos por proyecto
- por que existe `normalizar_posiciones()`

### Fase 4: mantenimiento

Debes poder modificar:

- un formulario
- una validacion
- un endpoint
- una tabla

sin romper el resto.

## 16. Preguntas de control para saber si ya lo dominaste

Si puedes responder esto sin mirar mucho el codigo, ya vas muy bien:

- donde se crea la sesion?
- donde se valida un correo?
- como se decide si alguien puede editar un proyecto?
- como se calcula el siguiente numero de sprint?
- como sabe el frontend que proyectos mostrar?
- donde se cargan usuarios para asignaciones?
- como se guarda el orden de una columna kanban?
- que diferencia hay entre una tarea y un avance?

## 17. Siguiente paso ideal

Despues de esta guia, lo mejor ya no es comentar todo el codigo.
Lo mejor es hacer una lectura guiada de `app.py` y `dashboard.js` por secciones.

Si quieres, el siguiente paso puede ser uno de estos dos:

1. Te explico `app.py` bloque por bloque con referencias exactas.
2. Te explico todo el flujo "desde que el usuario hace login hasta que crea una tarea" siguiendo codigo real.
