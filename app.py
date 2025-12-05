from flask import Flask, jsonify, request, render_template, session, redirect
import sqlite3
from leer_correo import sincronizar_correos_desde_gmail
from auth import auth   # Blueprint de login

DB_NAME = "incidencias.db"

app = Flask(__name__)
app.secret_key = "clave_super_secreta"

# Registrar blueprint correctamente
app.register_blueprint(auth)

ADMINS = [
    "al2276xxxx@ite.edu.mx",
    "sistemas@kotkoff.com"
]


@app.before_request
def verificar_acceso():
    rutas_publicas = ("auth.login", "auth.callback", "static")

    if request.endpoint not in rutas_publicas:
        if "email" not in session:
            return redirect("/login")
        if session["email"] not in ADMINS:
            return "Acceso denegado", 403


def obtener_conexion():
    return sqlite3.connect(DB_NAME)


def obtener_incidencias():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidencias ORDER BY id DESC")
    datos = cursor.fetchall()
    conn.close()
    return datos


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


@app.route("/sincronizar", methods=["POST"])
def api_sincronizar():
    nuevas = sincronizar_correos_desde_gmail()
    return jsonify({"mensaje": f"{nuevas} incidencias nuevas"})


@app.route("/")
def panel_incidencias():
    return render_template("index.html")


if __name__ == "__main__":
    app.run()
