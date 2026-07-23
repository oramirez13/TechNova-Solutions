from datetime import date
import os
import re
import secrets

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def cargar_variables_locales():
    ruta_env = os.path.join(BASE_DIR, ".env")

    if not os.path.exists(ruta_env):
        return

    with open(ruta_env, encoding="utf-8") as archivo_env:
        for linea in archivo_env:
            linea = linea.strip()

            if not linea or linea.startswith("#") or "=" not in linea:
                continue

            clave, valor = linea.split("=", 1)
            clave = clave.strip()
            valor = valor.strip().strip('"').strip("'")

            if clave and clave not in os.environ:
                os.environ[clave] = valor


cargar_variables_locales()


app = Flask(__name__)

# Secret key: en produccion debe ser una clave real de 64+ caracteres
_secret = os.getenv("TECHNOVA_SECRET_KEY", "")
if not _secret or len(_secret) < 32:
    _secret = secrets.token_hex(32)
app.secret_key = _secret

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("TECHNOVA_COOKIE_SECURE", "0") == "1",
    SESSION_COOKIE_NAME="technova_session",
    PERMANENT_SESSION_Lifetime=3600,
)

# Rate limiting global
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per minute"],
    storage_uri="memory://",
)

ESTADOS_SPRINT = {"planificado", "en_progreso", "completado"}
ESTADOS_TAREA = {"pendiente", "en_progreso", "en_revision", "avances", "completada"}
PRIORIDADES_TAREA = {"baja", "media", "alta"}
TIPOS_AVANCE = {"caracteristica", "bugfix", "mejora", "documentacion", "testing"}
ESTADOS_AVANCE_TAREA = {
    "pendiente",
    "en_progreso",
    "en_revision",
    "avances",
    "completada",
}
ROLES_PRIVILEGIADOS = {"Admin", "Manager"}
ROLES_SELLO_REGISTRO = {"Developer", "Designer", "QA"}
schema_asegurado = False


@app.after_request
def agregar_headers_seguridad(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


def generar_token_csrf():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]


@app.context_processor
def inyectar_csrf_token():
    return {"csrf_token": generar_token_csrf()}


def verificar_token_csrf(token):
    return secrets.compare_digest(token, session.get("_csrf_token", ""))


def requiere_csrf():
    """Verifica token CSRF en requests que modifican datos (POST, PUT, DELETE, PATCH)."""
    if request.method not in ("POST", "PUT", "DELETE", "PATCH"):
        return None
    if request.content_type and "application/json" in request.content_type:
        datos = request.get_json(silent=True) or {}
        token = datos.pop("csrf_token", None)
    else:
        token = request.form.get("csrf_token")
    if not token:
        token = request.headers.get("X-CSRF-Token")
    if not token or not verificar_token_csrf(token):
        return jsonify({"ok": False, "mensaje": "Token CSRF invalido."}), 403
    return None


class ConfiguracionError(RuntimeError):
    pass


def obtener_conexion():
    usuario = os.getenv("TECHNOVA_DB_USER")
    password = os.getenv("TECHNOVA_DB_PASSWORD")
    base_datos = os.getenv("TECHNOVA_DB_NAME")
    faltantes = []

    if not usuario:
        faltantes.append("TECHNOVA_DB_USER")
    if not password:
        faltantes.append("TECHNOVA_DB_PASSWORD")
    if not base_datos:
        faltantes.append("TECHNOVA_DB_NAME")

    if faltantes:
        raise ConfiguracionError(
            "Faltan variables de entorno de base de datos: " + ", ".join(faltantes)
        )

    return mysql.connector.connect(
        host=os.getenv("TECHNOVA_DB_HOST", "127.0.0.1"),
        user=usuario,
        password=password,
        database=base_datos,
        port=int(os.getenv("TECHNOVA_DB_PORT", 3307)),
        charset="utf8mb4",
    )


def validar_email(email):
    patron = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    return bool(re.match(patron, email))


def validar_contraseña(password):
    """Valida que el password tenga al menos 8 caracteres, una mayuscula, una minuscula, un numero y un caracter especial."""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[!@#$%^&*]", password):
        return False
    return True


def normalizar_correo(correo):
    return (correo or "").strip().lower()


def password_tiene_hash(password):
    return isinstance(password, str) and (
        password.startswith("scrypt:") or password.startswith("pbkdf2:")
    )


def generar_hash_password(password):
    return generate_password_hash(password)


def verificar_password(password_guardado, password_ingresado):
    if not password_guardado:
        return False

    if password_tiene_hash(password_guardado):
        return check_password_hash(password_guardado, password_ingresado)

    return password_guardado == password_ingresado


def parsear_fecha(valor, nombre_campo, permitir_nulo=False):
    if valor in (None, ""):
        return None if permitir_nulo else None

    try:
        return date.fromisoformat(valor)
    except ValueError as err:
        raise ValueError(
            f"La fecha de {nombre_campo} no tiene un formato válido."
        ) from err


def validar_rango_fechas(fecha_inicio, fecha_fin, etiqueta_fin):
    if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
        raise ValueError(
            f"La fecha de {etiqueta_fin} no puede ser anterior a la fecha de inicio."
        )


def convertir_entero(valor, permitir_nulo=False):
    if valor in (None, ""):
        return None if permitir_nulo else 0

    try:
        return int(valor)
    except (TypeError, ValueError):
        return None if permitir_nulo else 0


def existe_registro(cursor, tabla, registro_id, filtro_activo=False):
    sql = f"SELECT id FROM {tabla} WHERE id = %s"
    if filtro_activo:
        sql += " AND activo = 1"
    cursor.execute(sql, (registro_id,))
    return cursor.fetchone() is not None


def obtener_siguiente_numero_sprint(cursor, proyecto_id):
    cursor.execute(
        "SELECT COALESCE(MAX(numero), 0) + 1 AS siguiente FROM sprints WHERE proyecto_id = %s",
        (proyecto_id,),
    )
    fila = cursor.fetchone() or {}
    return fila.get("siguiente", 1)


def obtener_siguiente_posicion_tarea(cursor, proyecto_id, estado):
    cursor.execute(
        """
        SELECT COALESCE(MAX(posicion), 0) + 1 AS siguiente
        FROM tareas
        WHERE proyecto_id = %s AND estado = %s
        """,
        (proyecto_id, estado),
    )
    fila = cursor.fetchone() or {}
    return fila.get("siguiente", 1)


def normalizar_posiciones(cursor, proyecto_id, estado, excluir_id=None):
    sql = """
        SELECT id
        FROM tareas
        WHERE proyecto_id = %s AND estado = %s
    """
    params = [proyecto_id, estado]

    if excluir_id is not None:
        sql += " AND id <> %s"
        params.append(excluir_id)

    sql += " ORDER BY posicion ASC, id ASC"
    cursor.execute(sql, tuple(params))
    filas = cursor.fetchall()

    for indice, fila in enumerate(filas, start=1):
        cursor.execute(
            "UPDATE tareas SET posicion = %s WHERE id = %s",
            (indice, fila["id"]),
        )

    return [fila["id"] for fila in filas]


def crear_indice_si_no_existe(cursor, tabla, nombre_indice, definicion_sql):
    cursor.execute(
        """
        SELECT 1
        FROM information_schema.statistics
        WHERE table_schema = %s
          AND table_name = %s
          AND index_name = %s
        LIMIT 1
        """,
        (os.getenv("TECHNOVA_DB_NAME"), tabla, nombre_indice),
    )
    if cursor.fetchone() is None:
        cursor.execute(definicion_sql)


def crear_indice_unico_sprints_si_no_existe(cursor):
    cursor.execute(
        """
        SELECT proyecto_id, numero
        FROM sprints
        GROUP BY proyecto_id, numero
        HAVING COUNT(*) > 1
        LIMIT 1
        """
    )
    if cursor.fetchone() is None:
        crear_indice_si_no_existe(
            cursor,
            "sprints",
            "uq_sprints_proyecto_numero",
            "CREATE UNIQUE INDEX uq_sprints_proyecto_numero ON sprints(proyecto_id, numero)",
        )


def usuario_actual():
    return session.get("usuario") or {}


def usuario_es_privilegiado():
    return usuario_actual().get("rol") in ROLES_PRIVILEGIADOS


def obtener_proyecto_autorizado(cursor, proyecto_id):
    cursor.execute(
        "SELECT id, responsable_id FROM proyectos WHERE id = %s",
        (proyecto_id,),
    )
    proyecto = cursor.fetchone()

    if not proyecto:
        return None, (
            jsonify({"ok": False, "mensaje": "Proyecto no encontrado."}),
            404,
        )

    if usuario_es_privilegiado() or proyecto["responsable_id"] == usuario_actual().get(
        "id"
    ):
        return proyecto, None

    return None, (
        jsonify(
            {
                "ok": False,
                "mensaje": "No tienes permisos para gestionar este proyecto.",
            }
        ),
        403,
    )


def asegurar_estructura():
    global schema_asegurado

    if schema_asegurado:
        return

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tareas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                proyecto_id INT NOT NULL,
                sprint_id INT NULL,
                titulo VARCHAR(150) NOT NULL,
                descripcion TEXT,
                asignado_id INT NULL,
                prioridad ENUM('baja','media','alta') NOT NULL DEFAULT 'media',
                estado ENUM('pendiente','en_progreso','en_revision','avances','completada') NOT NULL DEFAULT 'pendiente',
                posicion INT NOT NULL DEFAULT 1,
                fecha_limite DATE NULL,
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                CONSTRAINT fk_tarea_proyecto
                    FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE,
                CONSTRAINT fk_tarea_sprint
                    FOREIGN KEY (sprint_id) REFERENCES sprints(id) ON DELETE SET NULL,
                CONSTRAINT fk_tarea_asignado
                    FOREIGN KEY (asignado_id) REFERENCES usuarios(id) ON DELETE SET NULL
            ) ENGINE=InnoDB
            """
        )

        cursor.execute(
            """
            ALTER TABLE tareas
            MODIFY COLUMN estado
            ENUM('pendiente','en_progreso','en_revision','avances','completada')
            NOT NULL DEFAULT 'pendiente'
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS avances (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sprint_id INT NOT NULL,
                usuario_id INT NOT NULL,
                descripcion TEXT NOT NULL,
                tipo_avance ENUM('caracteristica','bugfix','mejora','documentacion','testing') NOT NULL DEFAULT 'caracteristica',
                horas_trabajadas DECIMAL(5,2),
                estado_tarea ENUM('pendiente','en_progreso','en_revision','avances','completada') NOT NULL DEFAULT 'completada',
                fecha_reporte DATE NOT NULL DEFAULT (CURDATE()),
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                CONSTRAINT fk_avance_sprint
                    FOREIGN KEY (sprint_id) REFERENCES sprints(id) ON DELETE CASCADE,
                CONSTRAINT fk_avance_usuario
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT
            ) ENGINE=InnoDB
            """
        )

        cursor.execute(
            """
            ALTER TABLE avances
            MODIFY COLUMN estado_tarea
            ENUM('pendiente','en_progreso','en_revision','avances','completada')
            NOT NULL DEFAULT 'completada'
            """
        )

        crear_indice_si_no_existe(
            cursor,
            "tareas",
            "idx_tareas_proyecto",
            "CREATE INDEX idx_tareas_proyecto ON tareas(proyecto_id)",
        )
        crear_indice_si_no_existe(
            cursor,
            "tareas",
            "idx_tareas_sprint",
            "CREATE INDEX idx_tareas_sprint ON tareas(sprint_id)",
        )
        crear_indice_si_no_existe(
            cursor,
            "tareas",
            "idx_tareas_asignado",
            "CREATE INDEX idx_tareas_asignado ON tareas(asignado_id)",
        )
        crear_indice_si_no_existe(
            cursor,
            "tareas",
            "idx_tareas_kanban",
            "CREATE INDEX idx_tareas_kanban ON tareas(proyecto_id, estado, posicion)",
        )
        crear_indice_si_no_existe(
            cursor,
            "avances",
            "idx_avances_sprint",
            "CREATE INDEX idx_avances_sprint ON avances(sprint_id)",
        )
        crear_indice_si_no_existe(
            cursor,
            "avances",
            "idx_avances_usuario",
            "CREATE INDEX idx_avances_usuario ON avances(usuario_id)",
        )
        crear_indice_unico_sprints_si_no_existe(cursor)

        conn.commit()
        schema_asegurado = True

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.before_request
def preparar_aplicacion():
    if request.endpoint != "static":
        asegurar_estructura()
    # Verificar CSRF en requests que modifican datos
    error = requiere_csrf()
    if error:
        return error


@app.errorhandler(ConfiguracionError)
def manejar_configuracion_error(error):
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "mensaje": "Error de configuracion del servidor."}), 500
    return "Error de configuracion del servidor.", 500


@app.route("/")
def pagina_inicio():
    if "usuario" in session:
        return redirect(url_for("pagina_dashboard"))
    return render_template("index.html")


@app.route("/dashboard")
def pagina_dashboard():
    if "usuario" not in session:
        return redirect(url_for("pagina_inicio"))
    return render_template(
        "dashboard.html", usuario=session["usuario"], pagina_activa="dashboard"
    )


@app.route("/blog")
def pagina_blog():
    if "usuario" not in session:
        return redirect(url_for("pagina_inicio"))
    return render_template(
        "blog.html", usuario=session["usuario"], pagina_activa="blog"
    )


@app.errorhandler(404)
def pagina_no_encontrada(error):
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "mensaje": "Recurso no encontrado."}), 404

    return (
        render_template(
            "404.html",
            usuario=session.get("usuario"),
            pagina_activa=None,
        ),
        404,
    )


@app.route("/api/registro", methods=["POST"])
@limiter.limit("5 per minute")
def api_registro():
    datos = request.get_json() or {}

    nombre = (datos.get("nombre") or "").strip()
    correo = normalizar_correo(datos.get("correo"))
    password = (datos.get("password") or "").strip()
    rol = (datos.get("rol") or "Developer").strip()

    if not nombre or len(nombre) < 3:
        return (
            jsonify(
                {"ok": False, "mensaje": "El nombre debe tener al menos 3 caracteres."}
            ),
            400,
        )

    if not correo or not validar_email(correo):
        return jsonify({"ok": False, "mensaje": "Correo electronico invalido."}), 400

    if not password or not validar_contraseña(password):
        return (
            jsonify(
                {
                    "ok": False,
                    "mensaje":                 "La contraseña debe tener al menos 8 caracteres, una mayuscula, una minuscula, un numero y un caracter especial (!@#$%^&*).",
                }
            ),
            400,
        )

    # Solo roles seguros para auto-registro (Admin/Manager no se puede asignar solo)
    if rol not in ROLES_SELLO_REGISTRO:
        rol = "Developer"

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM usuarios WHERE correo = %s", (correo,))

        if cursor.fetchone():
            return (
                jsonify({"ok": False, "mensaje": "El correo ya está registrado."}),
                409,
            )

        cursor.execute(
            """
            INSERT INTO usuarios (nombre, correo, password, rol)
            VALUES (%s, %s, %s, %s)
            """,
            (nombre, correo, generar_hash_password(password), rol),
        )
        conn.commit()

        return (
            jsonify(
                {
                    "ok": True,
                    "mensaje": "Usuario registrado correctamente.",
                    "id": cursor.lastrowid,
                }
            ),
            201,
        )

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return (
            jsonify({"ok": False, "mensaje": "Error interno del servidor."}),
            500,
        )

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/login", methods=["POST"])
@limiter.limit("10 per minute")
def api_login():
    datos = request.get_json() or {}

    correo = normalizar_correo(datos.get("correo"))
    password = (datos.get("password") or "").strip()

    if not correo or not password:
        return (
            jsonify({"ok": False, "mensaje": "Correo y contraseña son obligatorios."}),
            400,
        )

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, nombre, correo, rol, password
            FROM usuarios
            WHERE correo = %s AND activo = 1
            """,
            (correo,),
        )
        usuario = cursor.fetchone()

        if not usuario or not verificar_password(usuario["password"], password):
            return (
                jsonify({"ok": False, "mensaje": "Correo o contraseña incorrectos."}),
                401,
            )

        if not password_tiene_hash(usuario["password"]):
            cursor.execute(
                "UPDATE usuarios SET password = %s WHERE id = %s",
                (generar_hash_password(password), usuario["id"]),
            )
            conn.commit()

        datos_sesion = {
            "id": usuario["id"],
            "nombre": usuario["nombre"],
            "correo": usuario["correo"],
            "rol": usuario["rol"],
        }
        session["usuario"] = datos_sesion

        return jsonify({"ok": True, "usuario": datos_sesion}), 200

    except mysql.connector.Error as err:
        return (
            jsonify({"ok": False, "mensaje": "Error interno del servidor."}),
            500,
        )

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/logout", methods=["POST"])
@limiter.limit("10 per minute")
def api_logout():
    error = requiere_csrf()
    if error:
        return error
    session.clear()
    return jsonify({"ok": True, "mensaje": "Sesion cerrada."}), 200


@app.route("/api/usuarios", methods=["GET"])
def api_usuarios():
    if not session.get("usuario"):
        return jsonify({"ok": False, "mensaje": "No autorizado."}), 401

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, nombre, correo, rol
            FROM usuarios
            WHERE activo = 1
            ORDER BY nombre ASC
            """
        )
        return jsonify({"ok": True, "usuarios": cursor.fetchall()}), 200

    except mysql.connector.Error as err:
        return jsonify({"ok": False, "mensaje": "Error interno del servidor."}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/proyectos", methods=["GET", "POST"])
@limiter.limit("60 per minute")
def api_proyectos():
    if not session.get("usuario"):
        return jsonify({"ok": False, "mensaje": "No autorizado."}), 401

    if request.method == "GET":
        return _get_proyectos()

    return _post_proyecto()


@app.route("/api/proyectos/<int:proyecto_id>", methods=["PUT", "DELETE"])
def api_proyecto_item(proyecto_id):
    if not session.get("usuario"):
        return jsonify({"ok": False, "mensaje": "No autorizado."}), 401

    if request.method == "PUT":
        return _put_proyecto(proyecto_id)

    return _delete_proyecto(proyecto_id)


def _delete_proyecto(proyecto_id):
    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        _, error = obtener_proyecto_autorizado(cursor, proyecto_id)
        if error:
            return error

        cursor.execute("DELETE FROM proyectos WHERE id = %s", (proyecto_id,))

        conn.commit()
        return (
            jsonify({"ok": True, "mensaje": "Proyecto eliminado correctamente."}),
            200,
        )

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"ok": False, "mensaje": "Error interno del servidor."}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _put_proyecto(proyecto_id):
    datos = request.get_json() or {}

    nombre = (datos.get("nombre") or "").strip()
    descripcion = (datos.get("descripcion") or "").strip()
    fecha_inicio = datos.get("fecha_inicio")
    fecha_fin_estimada = datos.get("fecha_fin_estimada")
    estado = (datos.get("estado") or "activo").strip()
    responsable_id = convertir_entero(datos.get("responsable_id"), permitir_nulo=True)

    if not nombre:
        return (
            jsonify({"ok": False, "mensaje": "El nombre del proyecto es obligatorio."}),
            400,
        )

    if not fecha_inicio:
        return (
            jsonify({"ok": False, "mensaje": "La fecha de inicio es obligatoria."}),
            400,
        )

    if estado not in {"activo", "pausado", "completado", "cancelado"}:
        return jsonify({"ok": False, "mensaje": "Estado de proyecto inválido."}), 400

    if responsable_id is None:
        return (
            jsonify({"ok": False, "mensaje": "Selecciona un responsable válido."}),
            400,
        )

    try:
        fecha_inicio = parsear_fecha(fecha_inicio, "inicio")
        fecha_fin_estimada = parsear_fecha(
            fecha_fin_estimada, "fin estimada", permitir_nulo=True
        )
        validar_rango_fechas(fecha_inicio, fecha_fin_estimada, "fin estimada")
    except ValueError as err:
        return jsonify({"ok": False, "mensaje": str(err)}), 400

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)

        _, error = obtener_proyecto_autorizado(cursor, proyecto_id)
        if error:
            return error

        if not existe_registro(cursor, "usuarios", responsable_id, filtro_activo=True):
            return jsonify({"ok": False, "mensaje": "Responsable inválido."}), 400

        if not usuario_es_privilegiado() and responsable_id != usuario_actual().get(
            "id"
        ):
            return (
                jsonify(
                    {
                        "ok": False,
                        "mensaje": "Solo un Manager o Admin puede reasignar responsables.",
                    }
                ),
                403,
            )

        cursor.execute(
            """
            UPDATE proyectos
            SET nombre = %s,
                descripcion = %s,
                estado = %s,
                fecha_inicio = %s,
                fecha_fin_estimada = %s,
                responsable_id = %s
            WHERE id = %s
            """,
            (
                nombre,
                descripcion,
                estado,
                fecha_inicio,
                fecha_fin_estimada,
                responsable_id,
                proyecto_id,
            ),
        )
        conn.commit()

        return (
            jsonify({"ok": True, "mensaje": "Proyecto actualizado correctamente."}),
            200,
        )

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"ok": False, "mensaje": "Error interno del servidor."}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/proyectos/<int:proyecto_id>/estado", methods=["PATCH"])
@limiter.limit("30 per minute")
def api_proyecto_estado(proyecto_id):
    if not session.get("usuario"):
        return jsonify({"ok": False, "mensaje": "No autorizado."}), 401

    datos = request.get_json() or {}
    estado = (datos.get("estado") or "").strip()
    estados_validos = {"activo", "pausado"}

    if estado not in estados_validos:
        return jsonify({"ok": False, "mensaje": "Estado de proyecto inválido."}), 400

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        _, error = obtener_proyecto_autorizado(cursor, proyecto_id)
        if error:
            return error
        cursor.execute(
            "UPDATE proyectos SET estado = %s WHERE id = %s",
            (estado, proyecto_id),
        )

        conn.commit()
        return (
            jsonify(
                {
                    "ok": True,
                    "mensaje": "Estado del proyecto actualizado correctamente.",
                }
            ),
            200,
        )

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"ok": False, "mensaje": "Error interno del servidor."}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _get_proyectos():
    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                p.id,
                p.nombre,
                p.descripcion,
                p.estado,
                p.fecha_inicio,
                p.fecha_fin_estimada,
                p.responsable_id,
                u.nombre AS responsable_nombre,
                (
                    SELECT COUNT(*)
                    FROM sprints s
                    WHERE s.proyecto_id = p.id
                ) AS total_sprints,
                (
                    SELECT COUNT(*)
                    FROM tareas t
                    WHERE t.proyecto_id = p.id
                ) AS total_tareas
            FROM proyectos p
            LEFT JOIN usuarios u ON p.responsable_id = u.id
            ORDER BY p.creado_en DESC
            """
        )
        return jsonify({"ok": True, "proyectos": cursor.fetchall()}), 200

    except mysql.connector.Error as err:
        return jsonify({"ok": False, "mensaje": "Error interno del servidor."}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _post_proyecto():
    datos = request.get_json() or {}

    nombre = (datos.get("nombre") or "").strip()
    descripcion = (datos.get("descripcion") or "").strip()
    fecha_inicio = datos.get("fecha_inicio")
    fecha_fin_estimada = datos.get("fecha_fin_estimada")
    estado = (datos.get("estado") or "activo").strip()
    responsable_id = convertir_entero(datos.get("responsable_id"), permitir_nulo=True)

    if responsable_id is None:
        responsable_id = session["usuario"]["id"]

    if not nombre:
        return (
            jsonify({"ok": False, "mensaje": "El nombre del proyecto es obligatorio."}),
            400,
        )

    if not fecha_inicio:
        return (
            jsonify({"ok": False, "mensaje": "La fecha de inicio es obligatoria."}),
            400,
        )

    if estado not in {"activo", "pausado", "completado", "cancelado"}:
        return jsonify({"ok": False, "mensaje": "Estado de proyecto inválido."}), 400

    try:
        fecha_inicio = parsear_fecha(fecha_inicio, "inicio")
        fecha_fin_estimada = parsear_fecha(
            fecha_fin_estimada, "fin estimada", permitir_nulo=True
        )
        validar_rango_fechas(fecha_inicio, fecha_fin_estimada, "fin estimada")
    except ValueError as err:
        return jsonify({"ok": False, "mensaje": str(err)}), 400

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)

        if not existe_registro(cursor, "usuarios", responsable_id, filtro_activo=True):
            return jsonify({"ok": False, "mensaje": "Responsable inválido."}), 400

        if not usuario_es_privilegiado() and responsable_id != usuario_actual().get(
            "id"
        ):
            return (
                jsonify(
                    {
                        "ok": False,
                        "mensaje": "Solo un Manager o Admin puede asignar otro responsable.",
                    }
                ),
                403,
            )

        cursor.execute(
            """
            INSERT INTO proyectos (nombre, descripcion, estado, fecha_inicio, fecha_fin_estimada, responsable_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                nombre,
                descripcion,
                estado,
                fecha_inicio,
                fecha_fin_estimada,
                responsable_id,
            ),
        )
        conn.commit()

        return (
            jsonify(
                {
                    "ok": True,
                    "mensaje": "Proyecto creado correctamente.",
                    "id": cursor.lastrowid,
                }
            ),
            201,
        )

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"ok": False, "mensaje": "Error interno del servidor."}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/sprints/<int:proyecto_id>", methods=["GET", "POST"])
@limiter.limit("60 per minute")
def api_sprints(proyecto_id):
    if not session.get("usuario"):
        return jsonify({"ok": False, "mensaje": "No autorizado."}), 401

    if request.method == "GET":
        return _get_sprints(proyecto_id)

    return _post_sprint(proyecto_id)


def _get_sprints(proyecto_id):
    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, proyecto_id, numero, nombre, descripcion, estado,
                   fecha_inicio, fecha_fin, objetivo_completado
            FROM sprints
            WHERE proyecto_id = %s
            ORDER BY numero ASC, fecha_inicio ASC
            """,
            (proyecto_id,),
        )
        return jsonify({"ok": True, "sprints": cursor.fetchall()}), 200

    except mysql.connector.Error as err:
        return jsonify({"ok": False, "mensaje": "Error interno del servidor."}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/sprint/<int:sprint_id>", methods=["PUT"])
@limiter.limit("30 per minute")
def api_sprint_item(sprint_id):
    if not session.get("usuario"):
        return jsonify({"ok": False, "mensaje": "No autorizado."}), 401

    return _put_sprint(sprint_id)


def _put_sprint(sprint_id):
    datos = request.get_json() or {}

    numero = convertir_entero(datos.get("numero"), permitir_nulo=True)
    nombre = (datos.get("nombre") or "").strip()
    descripcion = (datos.get("descripcion") or "").strip()
    fecha_inicio = datos.get("fecha_inicio")
    fecha_fin = datos.get("fecha_fin")
    estado = (datos.get("estado") or "planificado").strip()
    objetivo_completado = convertir_entero(
        datos.get("objetivo_completado"), permitir_nulo=True
    )

    if not nombre or not fecha_inicio or not fecha_fin:
        return (
            jsonify(
                {"ok": False, "mensaje": "Completa el nombre y las fechas del sprint."}
            ),
            400,
        )

    if numero is None or numero <= 0:
        return (
            jsonify({"ok": False, "mensaje": "El numero de sprint es obligatorio."}),
            400,
        )

    if estado not in ESTADOS_SPRINT:
        return jsonify({"ok": False, "mensaje": "Estado de sprint inválido."}), 400

    if objetivo_completado is None:
        objetivo_completado = 0

    if objetivo_completado < 0 or objetivo_completado > 100:
        return (
            jsonify(
                {
                    "ok": False,
                    "mensaje": "El avance del sprint debe estar entre 0 y 100.",
                }
            ),
            400,
        )

    try:
        fecha_inicio = parsear_fecha(fecha_inicio, "inicio")
        fecha_fin = parsear_fecha(fecha_fin, "fin")
        validar_rango_fechas(fecha_inicio, fecha_fin, "fin")
    except ValueError as err:
        return jsonify({"ok": False, "mensaje": str(err)}), 400

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, proyecto_id FROM sprints WHERE id = %s",
            (sprint_id,),
        )
        sprint_actual = cursor.fetchone()

        if not sprint_actual:
            return jsonify({"ok": False, "mensaje": "Sprint no encontrado."}), 404

        _, error = obtener_proyecto_autorizado(cursor, sprint_actual["proyecto_id"])
        if error:
            return error

        cursor.execute(
            """
            SELECT id
            FROM sprints
            WHERE proyecto_id = %s AND numero = %s AND id <> %s
            """,
            (sprint_actual["proyecto_id"], numero, sprint_id),
        )
        if cursor.fetchone():
            return (
                jsonify(
                    {
                        "ok": False,
                        "mensaje": "Ese numero de sprint ya existe para el proyecto.",
                    }
                ),
                409,
            )

        cursor.execute(
            """
            UPDATE sprints
            SET numero = %s,
                nombre = %s,
                descripcion = %s,
                estado = %s,
                fecha_inicio = %s,
                fecha_fin = %s,
                objetivo_completado = %s
            WHERE id = %s
            """,
            (
                numero,
                nombre,
                descripcion,
                estado,
                fecha_inicio,
                fecha_fin,
                objetivo_completado,
                sprint_id,
            ),
        )
        conn.commit()

        return (
            jsonify({"ok": True, "mensaje": "Sprint actualizado correctamente."}),
            200,
        )

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        if err.errno == 1062:
            return (
                jsonify(
                    {
                        "ok": False,
                        "mensaje": "Ese numero de sprint ya existe para el proyecto.",
                    }
                ),
                409,
            )
        return jsonify({"ok": False, "mensaje": "Error interno del servidor."}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _post_sprint(proyecto_id):
    datos = request.get_json() or {}

    numero = convertir_entero(datos.get("numero"), permitir_nulo=True)
    nombre = (datos.get("nombre") or "").strip()
    descripcion = (datos.get("descripcion") or "").strip()
    fecha_inicio = datos.get("fecha_inicio")
    fecha_fin = datos.get("fecha_fin")
    estado = (datos.get("estado") or "planificado").strip()
    objetivo_completado = convertir_entero(
        datos.get("objetivo_completado"), permitir_nulo=True
    )

    if not nombre or not fecha_inicio or not fecha_fin:
        return (
            jsonify(
                {"ok": False, "mensaje": "Completa el nombre y las fechas del sprint."}
            ),
            400,
        )

    if estado not in ESTADOS_SPRINT:
        return jsonify({"ok": False, "mensaje": "Estado de sprint inválido."}), 400

    if objetivo_completado is None:
        objetivo_completado = 0

    if objetivo_completado < 0 or objetivo_completado > 100:
        return (
            jsonify(
                {
                    "ok": False,
                    "mensaje": "El avance del sprint debe estar entre 0 y 100.",
                }
            ),
            400,
        )

    try:
        fecha_inicio = parsear_fecha(fecha_inicio, "inicio")
        fecha_fin = parsear_fecha(fecha_fin, "fin")
        validar_rango_fechas(fecha_inicio, fecha_fin, "fin")
    except ValueError as err:
        return jsonify({"ok": False, "mensaje": str(err)}), 400

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)

        _, error = obtener_proyecto_autorizado(cursor, proyecto_id)
        if error:
            return error

        if numero is None or numero <= 0:
            numero = obtener_siguiente_numero_sprint(cursor, proyecto_id)

        cursor.execute(
            "SELECT id FROM sprints WHERE proyecto_id = %s AND numero = %s",
            (proyecto_id, numero),
        )
        if cursor.fetchone():
            return (
                jsonify(
                    {
                        "ok": False,
                        "mensaje": "Ese numero de sprint ya existe para el proyecto.",
                    }
                ),
                409,
            )

        cursor.execute(
            """
            INSERT INTO sprints (
                proyecto_id, numero, nombre, descripcion, estado,
                fecha_inicio, fecha_fin, objetivo_completado
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                proyecto_id,
                numero,
                nombre,
                descripcion,
                estado,
                fecha_inicio,
                fecha_fin,
                objetivo_completado,
            ),
        )
        conn.commit()

        return (
            jsonify(
                {
                    "ok": True,
                    "mensaje": "Sprint creado correctamente.",
                    "id": cursor.lastrowid,
                }
            ),
            201,
        )

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        if err.errno == 1062:
            return (
                jsonify(
                    {
                        "ok": False,
                        "mensaje": "Ese numero de sprint ya existe para el proyecto.",
                    }
                ),
                409,
            )
        return jsonify({"ok": False, "mensaje": "Error interno del servidor."}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/tareas/<int:proyecto_id>", methods=["GET", "POST"])
@limiter.limit("60 per minute")
def api_tareas(proyecto_id):
    if not session.get("usuario"):
        return jsonify({"ok": False, "mensaje": "No autorizado."}), 401

    if request.method == "GET":
        return _get_tareas(proyecto_id)

    return _post_tarea(proyecto_id)


@app.route("/api/tarea/<int:tarea_id>", methods=["PUT", "DELETE"])
@limiter.limit("30 per minute")
def api_tarea_item(tarea_id):
    if not session.get("usuario"):
        return jsonify({"ok": False, "mensaje": "No autorizado."}), 401

    if request.method == "PUT":
        return _put_tarea(tarea_id)

    return _delete_tarea(tarea_id)


@app.route("/api/tarea/<int:tarea_id>/kanban", methods=["PATCH"])
@limiter.limit("30 per minute")
def api_tarea_kanban(tarea_id):
    if not session.get("usuario"):
        return jsonify({"ok": False, "mensaje": "No autorizado."}), 401

    datos = request.get_json() or {}
    estado_destino = (datos.get("estado") or "").strip()
    posicion_destino = convertir_entero(datos.get("posicion"), permitir_nulo=True) or 1

    if estado_destino not in ESTADOS_TAREA:
        return jsonify({"ok": False, "mensaje": "Columna kanban inválida."}), 400

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, proyecto_id, estado FROM tareas WHERE id = %s",
            (tarea_id,),
        )
        tarea = cursor.fetchone()

        if not tarea:
            return jsonify({"ok": False, "mensaje": "Tarea no encontrada."}), 404

        proyecto_id = tarea["proyecto_id"]
        estado_origen = tarea["estado"]
        _, error = obtener_proyecto_autorizado(cursor, proyecto_id)
        if error:
            return error

        if estado_origen != estado_destino:
            normalizar_posiciones(
                cursor, proyecto_id, estado_origen, excluir_id=tarea_id
            )

        tareas_destino = normalizar_posiciones(
            cursor, proyecto_id, estado_destino, excluir_id=tarea_id
        )
        maximo = len(tareas_destino) + 1
        posicion_destino = max(1, min(posicion_destino, maximo))
        tareas_destino.insert(posicion_destino - 1, tarea_id)

        for indice, tarea_lista_id in enumerate(tareas_destino, start=1):
            if tarea_lista_id == tarea_id:
                cursor.execute(
                    "UPDATE tareas SET estado = %s, posicion = %s WHERE id = %s",
                    (estado_destino, indice, tarea_id),
                )
            else:
                cursor.execute(
                    "UPDATE tareas SET posicion = %s WHERE id = %s",
                    (indice, tarea_lista_id),
                )

        conn.commit()
        return jsonify({"ok": True, "mensaje": "Tarea actualizada en el kanban."}), 200

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"ok": False, "mensaje": "Error interno del servidor."}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _get_tareas(proyecto_id):
    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                t.id,
                t.proyecto_id,
                t.sprint_id,
                t.titulo,
                t.descripcion,
                t.asignado_id,
                t.prioridad,
                t.estado,
                t.posicion,
                t.fecha_limite,
                u.nombre AS asignado_nombre,
                s.nombre AS sprint_nombre,
                s.numero AS sprint_numero
            FROM tareas t
            LEFT JOIN usuarios u ON t.asignado_id = u.id
            LEFT JOIN sprints s ON t.sprint_id = s.id
            WHERE t.proyecto_id = %s
            ORDER BY
                FIELD(t.estado, 'pendiente', 'en_progreso', 'en_revision', 'avances', 'completada'),
                t.posicion ASC,
                t.id ASC
            """,
            (proyecto_id,),
        )
        return jsonify({"ok": True, "tareas": cursor.fetchall()}), 200

    except mysql.connector.Error as err:
        return jsonify({"ok": False, "mensaje": "Error interno del servidor."}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _post_tarea(proyecto_id):
    datos = request.get_json() or {}

    titulo = (datos.get("titulo") or "").strip()
    descripcion = (datos.get("descripcion") or "").strip()
    sprint_id = convertir_entero(datos.get("sprint_id"), permitir_nulo=True)
    asignado_id = convertir_entero(datos.get("asignado_id"), permitir_nulo=True)
    prioridad = (datos.get("prioridad") or "media").strip()
    estado = (datos.get("estado") or "pendiente").strip()
    fecha_limite = datos.get("fecha_limite") or None

    if not titulo:
        return (
            jsonify({"ok": False, "mensaje": "El titulo de la tarea es obligatorio."}),
            400,
        )

    if prioridad not in PRIORIDADES_TAREA:
        return jsonify({"ok": False, "mensaje": "Prioridad inválida."}), 400

    if estado not in ESTADOS_TAREA:
        return jsonify({"ok": False, "mensaje": "Estado de tarea inválido."}), 400

    try:
        fecha_limite = parsear_fecha(fecha_limite, "limite", permitir_nulo=True)
    except ValueError as err:
        return jsonify({"ok": False, "mensaje": str(err)}), 400

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)

        _, error = obtener_proyecto_autorizado(cursor, proyecto_id)
        if error:
            return error

        if sprint_id is not None:
            cursor.execute(
                "SELECT id FROM sprints WHERE id = %s AND proyecto_id = %s",
                (sprint_id, proyecto_id),
            )
            if cursor.fetchone() is None:
                return (
                    jsonify(
                        {
                            "ok": False,
                            "mensaje": "El sprint seleccionado no pertenece al proyecto.",
                        }
                    ),
                    400,
                )

        if asignado_id is not None and not existe_registro(
            cursor, "usuarios", asignado_id, filtro_activo=True
        ):
            return jsonify({"ok": False, "mensaje": "Usuario asignado inválido."}), 400

        posicion = obtener_siguiente_posicion_tarea(cursor, proyecto_id, estado)
        cursor.execute(
            """
            INSERT INTO tareas (
                proyecto_id, sprint_id, titulo, descripcion, asignado_id,
                prioridad, estado, posicion, fecha_limite
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                proyecto_id,
                sprint_id,
                titulo,
                descripcion,
                asignado_id,
                prioridad,
                estado,
                posicion,
                fecha_limite,
            ),
        )
        conn.commit()

        return (
            jsonify(
                {
                    "ok": True,
                    "mensaje": "Tarea creada correctamente.",
                    "id": cursor.lastrowid,
                }
            ),
            201,
        )

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"ok": False, "mensaje": "Error interno del servidor."}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _put_tarea(tarea_id):
    datos = request.get_json() or {}

    titulo = (datos.get("titulo") or "").strip()
    descripcion = (datos.get("descripcion") or "").strip()
    sprint_id = convertir_entero(datos.get("sprint_id"), permitir_nulo=True)
    asignado_id = convertir_entero(datos.get("asignado_id"), permitir_nulo=True)
    prioridad = (datos.get("prioridad") or "media").strip()
    estado = (datos.get("estado") or "pendiente").strip()
    fecha_limite = datos.get("fecha_limite") or None

    if not titulo:
        return (
            jsonify({"ok": False, "mensaje": "El titulo de la tarea es obligatorio."}),
            400,
        )

    if prioridad not in PRIORIDADES_TAREA:
        return jsonify({"ok": False, "mensaje": "Prioridad inválida."}), 400

    if estado not in ESTADOS_TAREA:
        return jsonify({"ok": False, "mensaje": "Estado de tarea inválido."}), 400

    try:
        fecha_limite = parsear_fecha(fecha_limite, "limite", permitir_nulo=True)
    except ValueError as err:
        return jsonify({"ok": False, "mensaje": str(err)}), 400

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, proyecto_id, estado FROM tareas WHERE id = %s",
            (tarea_id,),
        )
        tarea_actual = cursor.fetchone()

        if not tarea_actual:
            return jsonify({"ok": False, "mensaje": "Tarea no encontrada."}), 404

        proyecto_id = tarea_actual["proyecto_id"]
        _, error = obtener_proyecto_autorizado(cursor, proyecto_id)
        if error:
            return error

        if sprint_id is not None:
            cursor.execute(
                "SELECT id FROM sprints WHERE id = %s AND proyecto_id = %s",
                (sprint_id, proyecto_id),
            )
            if cursor.fetchone() is None:
                return (
                    jsonify(
                        {
                            "ok": False,
                            "mensaje": "El sprint seleccionado no pertenece al proyecto.",
                        }
                    ),
                    400,
                )

        if asignado_id is not None and not existe_registro(
            cursor, "usuarios", asignado_id, filtro_activo=True
        ):
            return jsonify({"ok": False, "mensaje": "Usuario asignado inválido."}), 400

        posicion = None
        if estado != tarea_actual["estado"]:
            normalizar_posiciones(
                cursor, proyecto_id, tarea_actual["estado"], excluir_id=tarea_id
            )
            posicion = obtener_siguiente_posicion_tarea(cursor, proyecto_id, estado)

        cursor.execute(
            """
            UPDATE tareas
            SET titulo = %s,
                descripcion = %s,
                sprint_id = %s,
                asignado_id = %s,
                prioridad = %s,
                estado = %s,
                fecha_limite = %s
                {posicion_sql}
            WHERE id = %s
            """.format(
                posicion_sql=", posicion = %s" if posicion is not None else ""
            ),
            (
                (
                    titulo,
                    descripcion,
                    sprint_id,
                    asignado_id,
                    prioridad,
                    estado,
                    fecha_limite,
                    posicion,
                    tarea_id,
                )
                if posicion is not None
                else (
                    titulo,
                    descripcion,
                    sprint_id,
                    asignado_id,
                    prioridad,
                    estado,
                    fecha_limite,
                    tarea_id,
                )
            ),
        )
        conn.commit()

        return jsonify({"ok": True, "mensaje": "Tarea actualizada correctamente."}), 200

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"ok": False, "mensaje": "Error interno del servidor."}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _delete_tarea(tarea_id):
    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT proyecto_id, estado FROM tareas WHERE id = %s",
            (tarea_id,),
        )
        tarea = cursor.fetchone()

        if not tarea:
            return jsonify({"ok": False, "mensaje": "Tarea no encontrada."}), 404

        _, error = obtener_proyecto_autorizado(cursor, tarea["proyecto_id"])
        if error:
            return error

        cursor.execute("DELETE FROM tareas WHERE id = %s", (tarea_id,))
        normalizar_posiciones(cursor, tarea["proyecto_id"], tarea["estado"])
        conn.commit()

        return jsonify({"ok": True, "mensaje": "Tarea eliminada correctamente."}), 200

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"ok": False, "mensaje": "Error interno del servidor."}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/avances/<int:sprint_id>", methods=["GET", "POST"])
@limiter.limit("60 per minute")
def api_avances(sprint_id):
    if not session.get("usuario"):
        return jsonify({"ok": False, "mensaje": "No autorizado."}), 401

    if request.method == "GET":
        return _get_avances(sprint_id)

    return _post_avance(sprint_id)


@app.route("/api/avance/<int:avance_id>", methods=["PUT", "DELETE"])
@limiter.limit("30 per minute")
def api_avance_item(avance_id):
    if not session.get("usuario"):
        return jsonify({"ok": False, "mensaje": "No autorizado."}), 401

    if request.method == "PUT":
        return _put_avance(avance_id)

    return _delete_avance(avance_id)


def _get_avances(sprint_id):
    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, proyecto_id FROM sprints WHERE id = %s",
            (sprint_id,),
        )
        sprint = cursor.fetchone()
        if not sprint:
            return jsonify({"ok": False, "mensaje": "Sprint no encontrado."}), 404

        _, error = obtener_proyecto_autorizado(cursor, sprint["proyecto_id"])
        if error:
            return error

        cursor.execute(
            """
            SELECT a.id, a.sprint_id, a.usuario_id, a.descripcion, a.tipo_avance,
                   a.horas_trabajadas, a.estado_tarea, a.fecha_reporte,
                   u.nombre AS usuario_nombre
            FROM avances a
            LEFT JOIN usuarios u ON a.usuario_id = u.id
            WHERE a.sprint_id = %s
            ORDER BY a.fecha_reporte DESC
            """,
            (sprint_id,),
        )
        return jsonify({"ok": True, "avances": cursor.fetchall()}), 200

    except mysql.connector.Error as err:
        return jsonify({"ok": False, "mensaje": "Error interno del servidor."}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _post_avance(sprint_id):
    datos = request.get_json() or {}

    descripcion = (datos.get("descripcion") or "").strip()
    tipo_avance = (datos.get("tipo_avance") or "caracteristica").strip()
    horas_trabajadas = datos.get("horas_trabajadas")
    estado_tarea = (datos.get("estado_tarea") or "avances").strip()
    usuario_id = session["usuario"]["id"]

    if not descripcion:
        return (
            jsonify(
                {"ok": False, "mensaje": "La descripción del avance es obligatoria."}
            ),
            400,
        )

    if tipo_avance not in TIPOS_AVANCE:
        return jsonify({"ok": False, "mensaje": "Tipo de avance inválido."}), 400

    if estado_tarea not in ESTADOS_AVANCE_TAREA:
        return jsonify({"ok": False, "mensaje": "Estado de tarea inválido."}), 400

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, proyecto_id FROM sprints WHERE id = %s",
            (sprint_id,),
        )
        sprint = cursor.fetchone()
        if not sprint:
            return jsonify({"ok": False, "mensaje": "Sprint no encontrado."}), 404

        _, error = obtener_proyecto_autorizado(cursor, sprint["proyecto_id"])
        if error:
            return error

        cursor.execute(
            """
            INSERT INTO avances (sprint_id, usuario_id, descripcion, tipo_avance, horas_trabajadas, estado_tarea)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                sprint_id,
                usuario_id,
                descripcion,
                tipo_avance,
                horas_trabajadas,
                estado_tarea,
            ),
        )
        conn.commit()

        return (
            jsonify(
                {
                    "ok": True,
                    "mensaje": "Avance registrado correctamente.",
                    "id": cursor.lastrowid,
                }
            ),
            201,
        )

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"ok": False, "mensaje": "Error interno del servidor."}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _put_avance(avance_id):
    datos = request.get_json() or {}

    descripcion = (datos.get("descripcion") or "").strip()
    tipo_avance = (datos.get("tipo_avance") or "caracteristica").strip()
    horas_trabajadas = datos.get("horas_trabajadas")
    estado_tarea = (datos.get("estado_tarea") or "avances").strip()

    if not descripcion:
        return (
            jsonify(
                {"ok": False, "mensaje": "La descripción del avance es obligatoria."}
            ),
            400,
        )

    if tipo_avance not in TIPOS_AVANCE:
        return jsonify({"ok": False, "mensaje": "Tipo de avance inválido."}), 400

    if estado_tarea not in ESTADOS_AVANCE_TAREA:
        return jsonify({"ok": False, "mensaje": "Estado de tarea inválido."}), 400

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT a.id, a.sprint_id, s.proyecto_id
            FROM avances a
            INNER JOIN sprints s ON a.sprint_id = s.id
            WHERE a.id = %s
            """,
            (avance_id,),
        )
        avance_actual = cursor.fetchone()

        if not avance_actual:
            return jsonify({"ok": False, "mensaje": "Avance no encontrado."}), 404

        _, error = obtener_proyecto_autorizado(cursor, avance_actual["proyecto_id"])
        if error:
            return error

        cursor.execute(
            """
            UPDATE avances
            SET descripcion = %s,
                tipo_avance = %s,
                horas_trabajadas = %s,
                estado_tarea = %s
            WHERE id = %s
            """,
            (
                descripcion,
                tipo_avance,
                horas_trabajadas,
                estado_tarea,
                avance_id,
            ),
        )
        conn.commit()

        return (
            jsonify({"ok": True, "mensaje": "Avance actualizado correctamente."}),
            200,
        )

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"ok": False, "mensaje": "Error interno del servidor."}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _delete_avance(avance_id):
    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT a.id, s.proyecto_id
            FROM avances a
            INNER JOIN sprints s ON a.sprint_id = s.id
            WHERE a.id = %s
            """,
            (avance_id,),
        )
        avance = cursor.fetchone()

        if not avance:
            return jsonify({"ok": False, "mensaje": "Avance no encontrado."}), 404

        _, error = obtener_proyecto_autorizado(cursor, avance["proyecto_id"])
        if error:
            return error

        cursor.execute("DELETE FROM avances WHERE id = %s", (avance_id,))
        conn.commit()

        return jsonify({"ok": True, "mensaje": "Avance eliminado correctamente."}), 200

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"ok": False, "mensaje": "Error interno del servidor."}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1", port=5000)
