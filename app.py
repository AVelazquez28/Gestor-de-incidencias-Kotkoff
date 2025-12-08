from flask import Flask, jsonify, request, render_template, session, redirect
import sqlite3
from leer_correo import sincronizar_correos_desde_gmail

print("=== APP LOADED ===")

app = Flask(__name__)
app.secret_key = "supersecret"
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")


# Ahora sí puedes importar y registrar el blueprint
from auth import auth
app.register_blueprint(auth)

DB_NAME = "incidencias.db"

def obtener_conexion():
    return sqlite3.connect(DB_NAME)

def obtener_incidencias():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidencias ORDER BY id DESC")
    datos = cursor.fetchall()
    conn.close()
    return datos

@app.before_request
def validar_sesion():
    print("Before_request ejecutado:", request.endpoint)

    if request.endpoint in ("auth.login", "auth.callback", "static"):
        return None

    if "email" not in session:
        print("NO HAY LOGIN → REDIRECT")
        return redirect("/login")

@app.route("/")
def panel_incidencias():
    print("Cargando panel para:", session.get("email"))
    return render_template("index.html")

@app.route("/incidencias", methods=["GET"])
def api_incidencias():
    datos = obtener_incidencias()
    lista = []
    for row in datos:
        lista.append({
            "id": row[0],
            "message_id": row[1],
            "remitente": row[2],
            "asunto": row[3],
            "descripcion": row[4],
            "fecha": row[5],
            "estado": row[6]
        })
    return jsonify(lista)

@app.route("/sincronizar", methods=["POST"])
def api_sincronizar():
    if "email" not in session or "google_token" not in session:
        return jsonify({"error": "No autenticado"}), 403

    mensajes = leer_correos_usuario(session["google_token"])

    # Procesar mensajes...
    
    return jsonify({"mensaje": f"{len(mensajes)} correos encontrados"})


if __name__ == "__main__":
    print("=== RUNNING LOCAL SERVER ===")
    app.run(host="0.0.0.0", port=5000)
