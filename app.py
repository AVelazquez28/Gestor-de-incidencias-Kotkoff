from flask import Flask, jsonify, request, render_template, session, redirect
import sqlite3
from leer_correo import sincronizar_correos_desde_gmail
from auth import auth   # Blueprint de login

DB_NAME = "incidencias.db"

app = Flask(__name__)
app.secret_key = "super_secret_key_pon_algo_mejor"  # Necesario para sesiones

# Registramos rutas de login ANTES del before_request
app.register_blueprint(auth)


# ================================
#   ACCESO PERMITIDO A ESTOS EMAILS
# ================================
ADMINS = [
    "al2276xxxx@ite.edu.mx",
    "tu_gmail@gmail.com"
]


# ================================
#   FILTRO DE ACCESO
# ================================
@app.before_request
def verificar_acceso():
    rutas_publicas = ("auth.login", "auth.callback", "static")

    if request.endpoint not in rutas_publicas:
        if "email" not in session:
            return redirect("/login")
        if session["email"] not in ADMINS:
            return "Acceso denegado: No tienes permisos", 403


# ================================
#   FUNCIONES BD
# ================================
def obtener_conexion():
    return sqlite3.connect(DB_NAME)

def obtener_incidencias():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidencias ORDER BY id DESC")
    datos = cursor.fetchall()
    conn.close()
    return datos

def obtener_incidencia(id):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidencias WHERE id = ?", (id,))
    dato = cursor.fetchone()
    conn.close()
    return dato

def insertar_incidencia(message_id, remitente, asunto, descripcion, fecha):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO incidencias (message_id, remitente, asunto, descripcion, fecha)
        VALUES (?, ?, ?, ?, ?)
    """, (message_id, remitente, asunto, descripcion, fecha))
    conn.commit()
    conn.close()

def actualizar_estado(id, estado):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("UPDATE incidencias SET estado = ? WHERE id = ?", (estado, id))
    conn.commit()
    conn.close()


# ================================
#            ENDPOINTS
# ================================
@app.route("/incidencias", methods=["GET"])
def api_incidencias():
    datos = obtener_incidencias()
    lista = [{
        "id": row[0],
        "message_id": row[1],
        "remitente": row[2],
        "asunto": row[3],
        "descripcion": row[4],
        "fecha": row[5],
        "estado": row[6]
    } for row in datos]
    return jsonify(lista)


@app.route("/incidencias/<int:id>", methods=["PUT"])
def api_actualizar(id):
    datos = request.json
    actualizar_estado(id, datos["estado"])
    return jsonify({"mensaje": "Estado actualizado correctamente"})


@app.route("/sincronizar", methods=["POST"])
def api_sincronizar():
    nuevas = sincronizar_correos_desde_gmail()
    return jsonify({"mensaje": f"{nuevas} incidencias sincronizadas desde Gmail"})


# ================================
#    PANEL PRINCIPAL (PROTEGIDO)
# ================================
@app.route("/")
def panel_incidencias():
    return render_template("index.html")


# ================================
#    INICIAR SERVIDOR
# ================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
