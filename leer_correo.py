import base64

from database import crear_base_datos, existe_incidencia, guardar_incidencia
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from flask import session

PALABRAS_CLAVE = [
    "error", "falla", "fallo", "problema", "daño", "incidencia",
    "no funciona", "no prende", "no enciende", "no responde",
    "no abre", "pantalla azul", "bloqueado", "congelado",
    "se traba", "lento", "tarda mucho", "descompuesto",
    "servidor caído", "inaccesible", "no tengo acceso",
    "desconectado", "red caída", "problemas de red", "ups"
]

BLOQUEAR_REMITENTES = [
    "godaddy", "no-reply", "noreply",
    "notification", "notificaciones", "alerts",
    "amazon", "microsoft", "apple",
    "facebook", "instagram", "paypal", "mercadolibre",
    "linkedin", "teams", "zoom", "slack",
]


def extraer_cuerpo(payload: dict) -> str:
    """Saca el texto del cuerpo del correo (versión simple)."""
    partes = payload.get("parts", [])
    cuerpo = ""

    if partes:
        for parte in partes:
            data = parte.get("body", {}).get("data")
            if data:
                cuerpo = base64.urlsafe_b64decode(data).decode(
                    "utf-8", errors="ignore"
                )
                break
    else:
        data = payload.get("body", {}).get("data")
        if data:
            cuerpo = base64.urlsafe_b64decode(data).decode(
                "utf-8", errors="ignore"
            )

    return cuerpo


def leer_correos(service, max_correos=10):
    """
    Lee correos desde un servicio Gmail ya autenticado.
    NO escribe en la BD, solo regresa una lista de incidencias detectadas.
    """
    results = service.users().messages().list(
        userId="me",
        q="is:inbox",
        maxResults=max_correos,
        includeSpamTrash=False
    ).execute()

    mensajes = results.get("messages", [])
    incidencias = []

    if not mensajes:
        print("No hay mensajes para leer.")
        return incidencias

    print(f"\nLeyendo hasta {max_correos} correos...\n")

    for msg in mensajes:
        message_id = msg["id"]
        mensaje = service.users().messages().get(
            userId="me", id=message_id
        ).execute()
        payload = mensaje.get("payload", {})
        headers = payload.get("headers", [])

        asunto = ""
        remitente = ""
        fecha = ""

        for h in headers:
            name = h.get("name")
            value = h.get("value", "")
            if name == "Subject":
                asunto = value
            elif name == "From":
                remitente = value
            elif name == "Date":
                fecha = value

        cuerpo = extraer_cuerpo(payload)

        print("======================================")
        print(f"ID: {message_id}")
        print(f"Asunto: {asunto}")
        print(f"Remitente: {remitente}")
        print(f"Fecha: {fecha}")
        print(f"Cuerpo (inicio):\n{cuerpo[:300]}...")
        print("======================================\n")

        # Filtrar remitentes automáticos
        if any(b in remitente.lower() for b in BLOQUEAR_REMITENTES):
            print(f"✖ Correo ignorado por remitente automático: {remitente}")
            continue

        # Detectar incidencias por palabras clave
        cuerpo_lower = cuerpo.lower()
        if any(p in cuerpo_lower for p in PALABRAS_CLAVE):
            incidencias.append({
                "message_id": message_id,
                "remitente": remitente,
                "asunto": asunto,
                "descripcion": cuerpo,
                "fecha": fecha
            })

    return incidencias


def sincronizar_correos_desde_gmail(service, usuario_email, max_correos=10):
    """
    Usa leer_correos() y guarda en la BD solo las incidencias NUEVAS
    para el usuario indicado.
    """
    crear_base_datos()

    incidencias = leer_correos(service, max_correos=max_correos)
    nuevas = 0

    for inc in incidencias:
        mid = inc["message_id"]

        if existe_incidencia(mid, usuario_email):
            print(f"⚠ Incidencia YA EXISTE para {usuario_email}, no se guarda: {mid}")
            continue

        guardar_incidencia(
            mid,
            inc["remitente"],
            inc["asunto"],
            inc["descripcion"],
            inc["fecha"],
            usuario_email
        )
        nuevas += 1
        print(f"✔ Incidencia guardada para {usuario_email}: {mid}")

    return nuevas
