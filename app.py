from decimal import Decimal
from pathlib import Path
import os
import re
import sqlite3

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

try:
    import mysql.connector
except ImportError:  # pragma: no cover - depende del entorno
    mysql = None

try:
    import psycopg2
    import psycopg2.extras
except ImportError:  # pragma: no cover - depende del entorno
    psycopg2 = None


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_SQLITE_PATH = PROJECT_DIR / "database" / "technova.sqlite3"
DEFAULT_SQLITE_SCHEMA = PROJECT_DIR / "database" / "schema_sqlite.sql"

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "technova_secret_2026")

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DB_ENGINE = os.getenv("TECHNOVA_DB_ENGINE", "").strip().lower()
SQLITE_PATH = Path(os.getenv("TECHNOVA_SQLITE_PATH", str(DEFAULT_SQLITE_PATH))).expanduser()

if not DB_ENGINE:
    if DATABASE_URL.startswith(("postgres://", "postgresql://")):
        DB_ENGINE = "postgres"
    else:
        DB_ENGINE = "sqlite"

MYSQL_CONFIG = {
    "host": os.getenv("TECHNOVA_DB_HOST", "localhost"),
    "user": os.getenv("TECHNOVA_DB_USER", "technova_app"),
    "password": os.getenv("TECHNOVA_DB_PASSWORD", "technova_app_2026"),
    "database": os.getenv("TECHNOVA_DB_NAME", "technova"),
    "charset": "utf8mb4",
}


def construir_database_url():
    """Construye una URL de PostgreSQL si no existe DATABASE_URL."""
    return "postgresql://{user}:{password}@{host}:{port}/{dbname}".format(
        user=os.getenv("TECHNOVA_DB_USER", "technova_app"),
        password=os.getenv("TECHNOVA_DB_PASSWORD", "technova_app_2026"),
        host=os.getenv("TECHNOVA_DB_HOST", "localhost"),
        port=os.getenv("TECHNOVA_DB_PORT", "5432"),
        dbname=os.getenv("TECHNOVA_DB_NAME", "technova"),
    )


if DB_ENGINE == "postgres" and not DATABASE_URL:
    DATABASE_URL = construir_database_url()


def preparar_sql(sql):
    """Adapta placeholders para SQLite."""
    if DB_ENGINE == "sqlite":
        return sql.replace("%s", "?")
    return sql


def inicializar_sqlite_si_hace_falta():
    """Crea la base SQLite con datos iniciales en el primer arranque."""
    if DB_ENGINE != "sqlite":
        return

    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(SQLITE_PATH)
    try:
        existe = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'"
        ).fetchone()
        if existe:
            return

        script = DEFAULT_SQLITE_SCHEMA.read_text(encoding="utf-8")
        conn.executescript(script)
        conn.commit()
    finally:
        conn.close()


def obtener_conexion():
    """Abre una conexion a la base de datos configurada."""
    if DB_ENGINE == "postgres":
        if psycopg2 is None:
            raise RuntimeError("psycopg2 no esta instalado en este entorno.")
        return psycopg2.connect(DATABASE_URL)

    if DB_ENGINE == "mysql":
        if mysql is None:
            raise RuntimeError("mysql-connector-python no esta instalado en este entorno.")
        return mysql.connector.connect(**MYSQL_CONFIG)

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def obtener_cursor(conn):
    """Devuelve un cursor que retorna filas como diccionarios."""
    if DB_ENGINE == "postgres":
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if DB_ENGINE == "mysql":
        return conn.cursor(dictionary=True)
    return conn.cursor()


def obtener_error_bd():
    """Devuelve la excepcion base del motor configurado."""
    if DB_ENGINE == "postgres" and psycopg2 is not None:
        return psycopg2.Error
    if DB_ENGINE == "mysql" and mysql is not None:
        return mysql.connector.Error
    return sqlite3.Error


DB_ERROR = obtener_error_bd()


def ejecutar(cursor, sql, params=()):
    """Ejecuta una sentencia respetando el placeholder del motor."""
    cursor.execute(preparar_sql(sql), params)


def ejecutar_insert(cursor, sql, params):
    """Ejecuta un INSERT y devuelve el id generado."""
    if DB_ENGINE == "postgres":
        cursor.execute(f"{sql}\nRETURNING id", params)
        return cursor.fetchone()["id"]

    cursor.execute(preparar_sql(sql), params)
    return cursor.lastrowid


def serializar_fila(fila):
    """Convierte filas, fechas y decimales para que jsonify los soporte."""
    item = dict(fila)
    for clave, valor in item.items():
        if isinstance(valor, Decimal):
            item[clave] = float(valor)
        elif hasattr(valor, "isoformat"):
            item[clave] = valor.isoformat()
    return item


def validar_email(email):
    """Valida formato de email."""
    patron = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    return bool(re.match(patron, email))


def validar_contrasena(password):
    """Valida que la contrasena tenga minimo 6 caracteres."""
    return len(password) >= 6


inicializar_sqlite_si_hace_falta()


@app.route("/")
def pagina_inicio():
    """Pagina de inicio con opcion de login o registro."""
    if "usuario" in session:
        return redirect(url_for("pagina_dashboard"))
    return render_template("index.html")


@app.route("/dashboard")
def pagina_dashboard():
    """Panel principal de proyectos protegido."""
    if "usuario" not in session:
        return redirect(url_for("pagina_inicio"))
    return render_template("dashboard.html", usuario=session["usuario"])


@app.route("/api/registro", methods=["POST"])
def api_registro():
    """Registra un nuevo usuario."""
    datos = request.get_json() or {}

    nombre = (datos.get("nombre") or "").strip()
    correo = (datos.get("correo") or "").strip()
    password = (datos.get("password") or "").strip()
    rol = (datos.get("rol") or "Developer").strip()

    if not nombre or len(nombre) < 3:
        return jsonify({"ok": False, "mensaje": "El nombre debe tener al menos 3 caracteres."}), 400

    if not correo or not validar_email(correo):
        return jsonify({"ok": False, "mensaje": "Correo electronico invalido."}), 400

    if not password or not validar_contrasena(password):
        return jsonify({"ok": False, "mensaje": "La contrasena debe tener al menos 6 caracteres."}), 400

    roles_validos = ["Manager", "Developer", "Designer", "QA", "Admin"]
    if rol not in roles_validos:
        rol = "Developer"

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = obtener_cursor(conn)

        ejecutar(cursor, "SELECT id FROM usuarios WHERE correo = %s", (correo,))
        if cursor.fetchone():
            return jsonify({"ok": False, "mensaje": "El correo ya esta registrado."}), 409

        sql = """
            INSERT INTO usuarios (nombre, correo, password, rol)
            VALUES (%s, %s, %s, %s)
        """
        nuevo_id = ejecutar_insert(cursor, sql, (nombre, correo, password, rol))
        conn.commit()

        return jsonify({
            "ok": True,
            "mensaje": "Usuario registrado correctamente.",
            "id": nuevo_id,
        }), 201

    except DB_ERROR as err:
        if conn:
            conn.rollback()
        return jsonify({"ok": False, "mensaje": "Error de base de datos: " + str(err)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/login", methods=["POST"])
def api_login():
    """Verifica credenciales de login."""
    datos = request.get_json() or {}

    correo = (datos.get("correo") or "").strip()
    password = (datos.get("password") or "").strip()

    if not correo or not password:
        return jsonify({"ok": False, "mensaje": "Correo y contrasena son obligatorios."}), 400

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = obtener_cursor(conn)

        sql = """
            SELECT id, nombre, correo, rol
            FROM usuarios
            WHERE correo = %s AND password = %s AND activo = %s
        """
        ejecutar(cursor, sql, (correo, password, 1))
        usuario = cursor.fetchone()

        if not usuario:
            return jsonify({"ok": False, "mensaje": "Correo o contrasena incorrectos."}), 401

        datos_sesion = {
            "id": usuario["id"],
            "nombre": usuario["nombre"],
            "correo": usuario["correo"],
            "rol": usuario["rol"],
        }
        session["usuario"] = datos_sesion

        return jsonify({"ok": True, "usuario": datos_sesion}), 200

    except DB_ERROR as err:
        return jsonify({"ok": False, "mensaje": "Error de base de datos: " + str(err)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/logout", methods=["POST"])
def api_logout():
    """Cierra la sesion del usuario."""
    session.clear()
    return jsonify({"ok": True, "mensaje": "Sesion cerrada."}), 200


@app.route("/api/proyectos", methods=["GET", "POST"])
def api_proyectos():
    """GET: lista proyectos. POST: crea nuevo proyecto."""
    if not session.get("usuario"):
        return jsonify({"ok": False, "mensaje": "No autorizado."}), 401

    if request.method == "GET":
        return _get_proyectos()
    return _post_proyecto()


def _get_proyectos():
    """Obtiene todos los proyectos."""
    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = obtener_cursor(conn)

        sql = """
            SELECT p.id, p.nombre, p.descripcion, p.estado,
                   p.fecha_inicio, p.fecha_fin_estimada, p.responsable_id,
                   u.nombre AS responsable_nombre
            FROM proyectos p
            LEFT JOIN usuarios u ON p.responsable_id = u.id
            ORDER BY p.creado_en DESC
        """
        ejecutar(cursor, sql)
        proyectos = [serializar_fila(fila) for fila in cursor.fetchall()]

        return jsonify({"ok": True, "proyectos": proyectos}), 200

    except DB_ERROR as err:
        return jsonify({"ok": False, "mensaje": str(err)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _post_proyecto():
    """Crea un nuevo proyecto."""
    datos = request.get_json() or {}

    nombre = (datos.get("nombre") or "").strip()
    descripcion = (datos.get("descripcion") or "").strip()
    fecha_inicio = datos.get("fecha_inicio")
    fecha_fin_estimada = datos.get("fecha_fin_estimada")
    responsable_id = session["usuario"]["id"]

    if not nombre:
        return jsonify({"ok": False, "mensaje": "El nombre del proyecto es obligatorio."}), 400

    if not fecha_inicio:
        return jsonify({"ok": False, "mensaje": "La fecha de inicio es obligatoria."}), 400

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = obtener_cursor(conn)

        sql = """
            INSERT INTO proyectos (nombre, descripcion, fecha_inicio, fecha_fin_estimada, responsable_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        nuevo_id = ejecutar_insert(
            cursor,
            sql,
            (nombre, descripcion, fecha_inicio, fecha_fin_estimada, responsable_id),
        )
        conn.commit()

        return jsonify({"ok": True, "mensaje": "Proyecto creado correctamente.", "id": nuevo_id}), 201

    except DB_ERROR as err:
        if conn:
            conn.rollback()
        return jsonify({"ok": False, "mensaje": str(err)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/sprints/<int:proyecto_id>", methods=["GET", "POST"])
def api_sprints(proyecto_id):
    """GET: lista sprints del proyecto. POST: crea nuevo sprint."""
    if not session.get("usuario"):
        return jsonify({"ok": False, "mensaje": "No autorizado."}), 401

    if request.method == "GET":
        return _get_sprints(proyecto_id)
    return _post_sprint(proyecto_id)


def _get_sprints(proyecto_id):
    """Obtiene sprints de un proyecto."""
    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = obtener_cursor(conn)

        sql = """
            SELECT id, proyecto_id, numero, nombre, descripcion, estado,
                   fecha_inicio, fecha_fin, objetivo_completado
            FROM sprints
            WHERE proyecto_id = %s
            ORDER BY numero ASC
        """
        ejecutar(cursor, sql, (proyecto_id,))
        sprints = [serializar_fila(fila) for fila in cursor.fetchall()]

        return jsonify({"ok": True, "sprints": sprints}), 200

    except DB_ERROR as err:
        return jsonify({"ok": False, "mensaje": str(err)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _post_sprint(proyecto_id):
    """Crea un nuevo sprint en un proyecto."""
    datos = request.get_json() or {}

    numero = datos.get("numero")
    nombre = (datos.get("nombre") or "").strip()
    descripcion = (datos.get("descripcion") or "").strip()
    fecha_inicio = datos.get("fecha_inicio")
    fecha_fin = datos.get("fecha_fin")

    if not numero or not nombre or not fecha_inicio or not fecha_fin:
        return jsonify({"ok": False, "mensaje": "Todos los campos son obligatorios."}), 400

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = obtener_cursor(conn)

        sql = """
            INSERT INTO sprints (proyecto_id, numero, nombre, descripcion, fecha_inicio, fecha_fin)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        nuevo_id = ejecutar_insert(
            cursor,
            sql,
            (proyecto_id, numero, nombre, descripcion, fecha_inicio, fecha_fin),
        )
        conn.commit()

        return jsonify({"ok": True, "mensaje": "Sprint creado correctamente.", "id": nuevo_id}), 201

    except DB_ERROR as err:
        if conn:
            conn.rollback()
        return jsonify({"ok": False, "mensaje": str(err)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/avances/<int:sprint_id>", methods=["GET", "POST"])
def api_avances(sprint_id):
    """GET: lista avances del sprint. POST: registra nuevo avance."""
    if not session.get("usuario"):
        return jsonify({"ok": False, "mensaje": "No autorizado."}), 401

    if request.method == "GET":
        return _get_avances(sprint_id)
    return _post_avance(sprint_id)


def _get_avances(sprint_id):
    """Obtiene avances de un sprint."""
    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = obtener_cursor(conn)

        sql = """
            SELECT a.id, a.sprint_id, a.usuario_id, a.descripcion, a.tipo_avance,
                   a.horas_trabajadas, a.estado_tarea, a.fecha_reporte,
                   u.nombre AS usuario_nombre
            FROM avances a
            LEFT JOIN usuarios u ON a.usuario_id = u.id
            WHERE a.sprint_id = %s
            ORDER BY a.fecha_reporte DESC
        """
        ejecutar(cursor, sql, (sprint_id,))
        avances = [serializar_fila(fila) for fila in cursor.fetchall()]

        return jsonify({"ok": True, "avances": avances}), 200

    except DB_ERROR as err:
        return jsonify({"ok": False, "mensaje": str(err)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _post_avance(sprint_id):
    """Registra un nuevo avance en un sprint."""
    datos = request.get_json() or {}

    descripcion = (datos.get("descripcion") or "").strip()
    tipo_avance = (datos.get("tipo_avance") or "caracteristica").strip()
    horas_trabajadas = datos.get("horas_trabajadas")
    estado_tarea = (datos.get("estado_tarea") or "completada").strip()
    usuario_id = session["usuario"]["id"]

    if not descripcion:
        return jsonify({"ok": False, "mensaje": "La descripcion del avance es obligatoria."}), 400

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = obtener_cursor(conn)

        sql = """
            INSERT INTO avances (sprint_id, usuario_id, descripcion, tipo_avance, horas_trabajadas, estado_tarea)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        nuevo_id = ejecutar_insert(
            cursor,
            sql,
            (sprint_id, usuario_id, descripcion, tipo_avance, horas_trabajadas, estado_tarea),
        )
        conn.commit()

        return jsonify({"ok": True, "mensaje": "Avance registrado correctamente.", "id": nuevo_id}), 201

    except DB_ERROR as err:
        if conn:
            conn.rollback()
        return jsonify({"ok": False, "mensaje": str(err)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
