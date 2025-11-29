import sqlite3

DB_NAME = "incidencias.db"


def crear_base_datos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidencias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id TEXT UNIQUE,
        remitente TEXT,
        asunto TEXT,
        descripcion TEXT,
        fecha TEXT,
        estado TEXT DEFAULT 'abierto'
    )
    """)

    conn.commit()
    conn.close()

def existe_incidencia(message_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM incidencias WHERE message_id = ?", (message_id,))
    existe = cursor.fetchone() is not None

    conn.close()
    return existe


def guardar_incidencia(message_id, remitente, asunto, cuerpo, fecha):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO incidencias (message_id, remitente, asunto, descripcion, fecha)
            VALUES (?, ?, ?, ?, ?)
        """, (message_id, remitente, asunto, cuerpo, fecha))

        print("✔ Incidencia guardada en la BD.")

    except sqlite3.IntegrityError:
        # YA EXISTE, NO DUPLICAR
        print("✖ Incidencia ignorada (ya registrada previamente).")

    finally:
        conn.commit()
        conn.close()

