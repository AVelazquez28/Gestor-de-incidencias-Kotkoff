from flask import Flask, jsonify, request, render_template, session, redirect
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json
import os

from auth import auth
from database import (
    crear_base_datos,
    obtener_incidencias_por_usuario,
    obtener_incidencia_por_id,
    actualizar_estado,
    borrar_incidencia,
)
from leer_correo import sincronizar_correos_desde_gmail

app = Flask(__name__)

# Clave de sesión (en Render la pones en FLASK_SECRET_KEY)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")

# Registrar blueprint de autenticación
app.register_blueprint(auth)

# Crear BD al inicio
crear_base_datos()

# Correos que SÍ pueden entrar al panel
ADMINS = [
    "al2276xxxx@ite.edu.mx",
    "sistemas@kotkoff.com",
]


def build_gmail_service_from_session():
    """Construye un servicio Gmail usando las credenciales guardadas en sesión."""
    creds_json = session.get("google_credentials")
    if not creds_json:
        return None

    info = json.loads(creds_json)
    creds = Credentials.from_authorized_user_info(info)

    return build("gmail", "v1", credentials=creds)


@app.before_request
def verificar_acceso():
    print("Before_request ejecutado:", request.endpoint)

    # Rutas públicas
    if request.endpoint in ("auth.login", "auth.callback", "static"):
        return

    # Si no hay login → login
    if "email" not in session:
        print("NO HAY LOGIN → REDIRECT")
        return redirect("/login")

    # Solo admins (si quieres permitir a cualquiera, comenta este bloque)
    if session["email"] not in ADMINS:
        return "Acceso denegado", 403


# ================================
#           RUTAS
# ================================

@app.route("/")
def panel_incidencias():
    return render_template("index.html")


@app.route("/incidencias", methods=["GET"])
def api_incidencias():
    usuario = session.get("email")
    datos = obtener_incidencias_por_usuario(usuario)

    lista = []
    for row in datos:
        lista.append({
            "id": row[0],
            "message_id": row[1],
            "remitente": row[2],
            "asunto": row[3],
            "descripcion": row[4],
            "fecha": row[5],
            "estado": row[6],
        })

    return jsonify(lista)


@app.route("/incidencias/<int:id_incidencia>", methods=["GET"])
def api_incidencia(id_incidencia):
    usuario = session.get("email")
    fila = obtener_incidencia_por_id(id_incidencia, usuario)

    if not fila:
        return jsonify({"error": "Incidencia no encontrada"}), 404

    return jsonify({
        "id": fila[0],
        "message_id": fila[1],
        "remitente": fila[2],
        "asunto": fila[3],
        "descripcion": fila[4],
        "fecha": fila[5],
        "estado": fila[6],
    })


@app.route("/incidencias/<int:id_incidencia>", methods=["PUT"])
def api_actualizar(id_incidencia):
    usuario = session.get("email")
    datos = request.get_json()
    nuevo_estado = datos.get("estado", "abierto")

    actualizar_estado(id_incidencia, nuevo_estado, usuario)

    return jsonify({"mensaje": "Estado actualizado correctamente"})


@app.route("/incidencias/<int:id_incidencia>", methods=["DELETE"])
def api_borrar(id_incidencia):
    usuario = session.get("email")
    borrar_incidencia(id_incidencia, usuario)
    return jsonify({"mensaje": "Incidencia eliminada"})


@app.route("/sincronizar", methods=["POST"])
def api_sincronizar():
    usuario = session.get("email")
    service = build_gmail_service_from_session()

    if service is None:
        return jsonify({"mensaje": "No hay credenciales de Gmail válidas"}), 400

    nuevas = sincronizar_correos_desde_gmail(service, usuario)
    return jsonify({"mensaje": f"{nuevas} incidencias sincronizadas desde Gmail"})


if __name__ == "__main__":
    # Para desarrollo local
    app.run(host="0.0.0.0", port=5000, debug=True)
