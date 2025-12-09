import sqlite3

DB_NAME = "incidencias.db"


def obtener_conexion():
    return sqlite3.connect(DB_NAME)


def crear_base_datos():
    conn = obtener_conexion()
    cursor = conn.cursor()

    # Tabla completa con columna usuario_email
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidencias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id TEXT,
        remitente TEXT,
        asunto TEXT,
        descripcion TEXT,
        fecha TEXT,
        estado TEXT DEFAULT 'abierto',
        usuario_email TEXT
    )
    """)

    # Si la tabla es vieja, aseguramos que exista usuario_email
    cursor.execute("PRAGMA table_info(incidencias)")
    columnas = [fila[1] for fila in cursor.fetchall()]
    if "usuario_email" not in columnas:
        cursor.execute("ALTER TABLE incidencias ADD COLUMN usuario_email TEXT")

    conn.commit()
    conn.close()


def existe_incidencia(message_id, usuario_email):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1 FROM incidencias
        WHERE message_id = ? AND usuario_email = ?
        LIMIT 1
    """, (message_id, usuario_email))
    existe = cursor.fetchone() is not None
    conn.close()
    return existe


def guardar_incidencia(message_id, remitente, asunto, descripcion, fecha, usuario_email):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO incidencias (message_id, remitente, asunto, descripcion, fecha, usuario_email)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (message_id, remitente, asunto, descripcion, fecha, usuario_email))
    conn.commit()
    conn.close()


def obtener_incidencias_por_usuario(usuario_email):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, message_id, remitente, asunto, descripcion, fecha, estado
        FROM incidencias
        WHERE usuario_email = ?
        ORDER BY id DESC
    """, (usuario_email,))
    datos = cursor.fetchall()
    conn.close()
    return datos


def obtener_incidencia_por_id(id_incidencia, usuario_email):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, message_id, remitente, asunto, descripcion, fecha, estado
        FROM incidencias
        WHERE id = ? AND usuario_email = ?
        LIMIT 1
    """, (id_incidencia, usuario_email))
    dato = cursor.fetchone()
    conn.close()
    return dato


def actualizar_estado(id_incidencia, estado, usuario_email):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE incidencias
        SET estado = ?
        WHERE id = ? AND usuario_email = ?
    """, (estado, id_incidencia, usuario_email))
    conn.commit()
    conn.close()


def borrar_incidencia(id_incidencia, usuario_email):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM incidencias
        WHERE id = ? AND usuario_email = ?
    """, (id_incidencia, usuario_email))
    conn.commit()
    conn.close()
