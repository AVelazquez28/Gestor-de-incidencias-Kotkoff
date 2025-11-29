from flask import Flask, jsonify, request
from flask import render_template
import sqlite3
from leer_correo import sincronizar_correos_desde_gmail


DB_NAME = "incidencias.db"

app = Flask(__name__)

# ================================
#  FUNCIONES DE BASE DE DATOS
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

def borrar_incidencia(id):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM incidencias WHERE id = ?", (id,))
    conn.commit()
    conn.close()


# ================================
#            ENDPOINTS
# ================================

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


@app.route("/incidencias/<int:id>", methods=["GET"])
def api_incidencia(id):
    fila = obtener_incidencia(id)

    if not fila:
        return jsonify({"error": "Incidencia no encontrada"}), 404

    return jsonify({
        "id": fila[0],
        "message_id": fila[1],
        "remitente": fila[2],
        "asunto": fila[3],
        "descripcion": fila[4],
        "fecha": fila[5],
        "estado": fila[6]
    })


@app.route("/incidencias", methods=["POST"])
def api_insertar():
    datos = request.json

    insertar_incidencia(
        datos["message_id"],
        datos["remitente"],
        datos["asunto"],
        datos["descripcion"],
        datos["fecha"]
    )

    return jsonify({"mensaje": "Incidencia agregada correctamente"})


@app.route("/incidencias/<int:id>", methods=["PUT"])
def api_actualizar(id):
    datos = request.json
    actualizar_estado(id, datos["estado"])

    return jsonify({"mensaje": "Estado actualizado correctamente"})


@app.route("/sincronizar", methods=["POST"])
def api_sincronizar():
    nuevas = sincronizar_correos_desde_gmail()
    return jsonify({"mensaje": f"{nuevas} incidencias sincronizadas desde Gmail"})


#@app.route("/")
#def home():
#   return """
#   <h1>Gestor de Incidencias Kotkoff</h1>
#    <p>El servidor Flask está funcionando correctamente.</p>
#    <p>Endpoints disponibles:</p>
#    <ul>
#        <li>/incidencias (GET)</li>
#        <li>/incidencias (POST)</li>
#        <li>/incidencias/&lt;id&gt; (GET)</li>
#        <li>/incidencias/&lt;id&gt; (PUT)</li>
#        <li>/incidencias/&lt;id&gt; (DELETE)</li>
#    </ul>
#    """


@app.route("/")
def panel_incidencias():
    return render_template("index.html")


# ================================
#        INICIAR SERVIDOR
# ================================
if __name__ == "__main__":
    app.run(debug=True)
