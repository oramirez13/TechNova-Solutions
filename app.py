# app.py — TechNova Solutions
# Servidor Flask para gestión de proyectos, sprints y avances
#
# Funcionalidades:
#   1. Registro e login de usuarios
#   2. Gestión de proyectos (CRUD)
#   3. Gestión de sprints por proyecto
#   4. Registro de avances en sprints


from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import mysql.connector
import os
import re


# ════════════════════════════════════════════
# CONFIGURACIÓN
# ════════════════════════════════════════════

app = Flask(__name__)
app.secret_key = "technova_secret_2026"

# Configuración de MySQL
DB_CONFIG = {
    "host": os.getenv("TECHNOVA_DB_HOST", "localhost"),
    "user": os.getenv("TECHNOVA_DB_USER", "technova_app"),
    "password": os.getenv("TECHNOVA_DB_PASSWORD", "technova_app_2026"),
    "database": os.getenv("TECHNOVA_DB_NAME", "technova"),
    "charset": "utf8mb4",
}


# ════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ════════════════════════════════════════════


def obtener_conexion():
    """Abre una conexión a MySQL."""
    conexion = mysql.connector.connect(**DB_CONFIG)
    return conexion


def validar_email(email):
    """Valida formato de email."""
    patron = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    return bool(re.match(patron, email))


def validar_contraseña(password):
    """Valida que la contraseña tenga mínimo 6 caracteres."""
    return len(password) >= 6


# ════════════════════════════════════════════
# RUTAS DE PÁGINAS HTML
# ════════════════════════════════════════════


@app.route("/")
def pagina_inicio():
    """Página de inicio con opción de login o registro."""
    if "usuario" in session:
        return redirect(url_for("pagina_dashboard"))
    return render_template("index.html")


@app.route("/dashboard")
def pagina_dashboard():
    """Panel principal de proyectos (protegido)."""
    if "usuario" not in session:
        return redirect(url_for("pagina_inicio"))
    return render_template("dashboard.html", usuario=session["usuario"])


# ════════════════════════════════════════════
# API: AUTENTICACIÓN
# ════════════════════════════════════════════


@app.route("/api/registro", methods=["POST"])
def api_registro():
    """
    Registra un nuevo usuario.
    Body JSON: { "nombre": "...", "correo": "...", "password": "...", "rol": "..." }
    """
    datos = request.get_json() or {}

    nombre = (datos.get("nombre") or "").strip()
    correo = (datos.get("correo") or "").strip()
    password = (datos.get("password") or "").strip()
    rol = (datos.get("rol") or "Developer").strip()

    # ── Validaciones ──
    if not nombre or len(nombre) < 3:
        return (
            jsonify(
                {"ok": False, "mensaje": "El nombre debe tener al menos 3 caracteres."}
            ),
            400,
        )

    if not correo or not validar_email(correo):
        return jsonify({"ok": False, "mensaje": "Correo electrónico inválido."}), 400

    if not password or not validar_contraseña(password):
        return (
            jsonify(
                {
                    "ok": False,
                    "mensaje": "La contraseña debe tener al menos 6 caracteres.",
                }
            ),
            400,
        )

    roles_validos = ["Manager", "Developer", "Designer", "QA", "Admin"]
    if rol not in roles_validos:
        rol = "Developer"

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)

        # Verificar si el correo ya existe
        cursor.execute("SELECT id FROM usuarios WHERE correo = %s", (correo,))
        if cursor.fetchone():
            return (
                jsonify({"ok": False, "mensaje": "El correo ya está registrado."}),
                409,
            )

        # Insertar nuevo usuario
        sql = """
            INSERT INTO usuarios (nombre, correo, password, rol)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (nombre, correo, password, rol))
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
            jsonify({"ok": False, "mensaje": "Error de base de datos: " + str(err)}),
            500,
        )

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/login", methods=["POST"])
def api_login():
    """
    Verifica credenciales de login.
    Body JSON: { "correo": "...", "password": "..." }
    """
    datos = request.get_json() or {}

    correo = (datos.get("correo") or "").strip()
    password = (datos.get("password") or "").strip()

    # ── Validaciones ──
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

        # Buscar usuario por correo
        sql = "SELECT id, nombre, correo, rol FROM usuarios WHERE correo = %s AND password = %s AND activo = 1"
        cursor.execute(sql, (correo, password))
        usuario = cursor.fetchone()

        if not usuario:
            return (
                jsonify({"ok": False, "mensaje": "Correo o contraseña incorrectos."}),
                401,
            )

        # Guardar en sesión (sin contraseña)
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
            jsonify({"ok": False, "mensaje": "Error de base de datos: " + str(err)}),
            500,
        )

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/logout", methods=["POST"])
def api_logout():
    """Cierra la sesión del usuario."""
    session.clear()
    return jsonify({"ok": True, "mensaje": "Sesión cerrada."}), 200


# ════════════════════════════════════════════
# API: PROYECTOS
# ════════════════════════════════════════════


@app.route("/api/proyectos", methods=["GET", "POST"])
def api_proyectos():
    """GET: lista proyectos. POST: crea nuevo proyecto."""
    if not session.get("usuario"):
        return jsonify({"ok": False, "mensaje": "No autorizado."}), 401

    if request.method == "GET":
        return _get_proyectos()
    else:
        return _post_proyecto()


def _get_proyectos():
    """Obtiene todos los proyectos."""
    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)

        sql = """
            SELECT p.id, p.nombre, p.descripcion, p.estado,
                   p.fecha_inicio, p.fecha_fin_estimada, p.responsable_id,
                   u.nombre as responsable_nombre
            FROM proyectos p
            LEFT JOIN usuarios u ON p.responsable_id = u.id
            ORDER BY p.creado_en DESC
        """
        cursor.execute(sql)
        proyectos = cursor.fetchall()

        return jsonify({"ok": True, "proyectos": proyectos}), 200

    except mysql.connector.Error as err:
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
        return (
            jsonify({"ok": False, "mensaje": "El nombre del proyecto es obligatorio."}),
            400,
        )

    if not fecha_inicio:
        return (
            jsonify({"ok": False, "mensaje": "La fecha de inicio es obligatoria."}),
            400,
        )

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor()

        sql = """
            INSERT INTO proyectos (nombre, descripcion, fecha_inicio, fecha_fin_estimada, responsable_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(
            sql, (nombre, descripcion, fecha_inicio, fecha_fin_estimada, responsable_id)
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
        return jsonify({"ok": False, "mensaje": str(err)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ════════════════════════════════════════════
# API: SPRINTS
# ════════════════════════════════════════════


@app.route("/api/sprints/<int:proyecto_id>", methods=["GET", "POST"])
def api_sprints(proyecto_id):
    """GET: lista sprints del proyecto. POST: crea nuevo sprint."""
    if not session.get("usuario"):
        return jsonify({"ok": False, "mensaje": "No autorizado."}), 401

    if request.method == "GET":
        return _get_sprints(proyecto_id)
    else:
        return _post_sprint(proyecto_id)


def _get_sprints(proyecto_id):
    """Obtiene sprints de un proyecto."""
    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)

        sql = """
            SELECT id, proyecto_id, numero, nombre, descripcion, estado,
                   fecha_inicio, fecha_fin, objetivo_completado
            FROM sprints
            WHERE proyecto_id = %s
            ORDER BY numero ASC
        """
        cursor.execute(sql, (proyecto_id,))
        sprints = cursor.fetchall()

        return jsonify({"ok": True, "sprints": sprints}), 200

    except mysql.connector.Error as err:
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
        return (
            jsonify({"ok": False, "mensaje": "Todos los campos son obligatorios."}),
            400,
        )

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor()

        sql = """
            INSERT INTO sprints (proyecto_id, numero, nombre, descripcion, fecha_inicio, fecha_fin)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            sql, (proyecto_id, numero, nombre, descripcion, fecha_inicio, fecha_fin)
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
        return jsonify({"ok": False, "mensaje": str(err)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ════════════════════════════════════════════
# API: AVANCES
# ════════════════════════════════════════════


@app.route("/api/avances/<int:sprint_id>", methods=["GET", "POST"])
def api_avances(sprint_id):
    """GET: lista avances del sprint. POST: registra nuevo avance."""
    if not session.get("usuario"):
        return jsonify({"ok": False, "mensaje": "No autorizado."}), 401

    if request.method == "GET":
        return _get_avances(sprint_id)
    else:
        return _post_avance(sprint_id)


def _get_avances(sprint_id):
    """Obtiene avances de un sprint."""
    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)

        sql = """
            SELECT a.id, a.sprint_id, a.usuario_id, a.descripcion, a.tipo_avance,
                   a.horas_trabajadas, a.estado_tarea, a.fecha_reporte,
                   u.nombre as usuario_nombre
            FROM avances a
            LEFT JOIN usuarios u ON a.usuario_id = u.id
            WHERE a.sprint_id = %s
            ORDER BY a.fecha_reporte DESC
        """
        cursor.execute(sql, (sprint_id,))
        avances = cursor.fetchall()

        return jsonify({"ok": True, "avances": avances}), 200

    except mysql.connector.Error as err:
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
        return (
            jsonify(
                {"ok": False, "mensaje": "La descripción del avance es obligatoria."}
            ),
            400,
        )

    conn = None
    cursor = None

    try:
        conn = obtener_conexion()
        cursor = conn.cursor()

        sql = """
            INSERT INTO avances (sprint_id, usuario_id, descripcion, tipo_avance, horas_trabajadas, estado_tarea)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            sql,
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
        return jsonify({"ok": False, "mensaje": str(err)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ════════════════════════════════════════════
# PUNTO DE ENTRADA
# ════════════════════════════════════════════

if __name__ == "__main__":
    app.run(debug=True, port=5000)
