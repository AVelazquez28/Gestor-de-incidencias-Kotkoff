import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import re
import os
from database import crear_base_datos, guardar_incidencia
from database import crear_base_datos, guardar_incidencia, existe_incidencia



# Permisos necesarios
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    creds = None

    # Si ya existe token.json, úsalo
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # Si no existe o está vencido, genera uno nuevo
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())   # RENUEVA AUTOMÁTICO SIN PEDIR PERMISOS
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

        # Guardamos el token para no volver a pedir permisos
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def leer_correos_usuario(access_token):
    creds = Credentials(token=access_token)

    service = build("gmail", "v1", credentials=creds)

    results = service.users().messages().list(
        userId='me',
        q="is:inbox"
    ).execute()

    mensajes = results.get("messages", [])

    return mensajes

def leer_correos(service, max_correos=5):
    """
    Lee los últimos correos de la bandeja de entrada de Gmail.
    """
    results = service.users().messages().list(
        userId='me',
        q="is:inbox",
        includeSpamTrash=False
    ).execute()

    mensajes = results.get('messages', [])[:max_correos]


    incidencias_detectadas = []

    if not mensajes:
        print("No hay mensajes para leer.")
        return []

    print(f"\nLeyendo los últimos {max_correos} correos...\n")
    for msg in mensajes:
        mensaje = service.users().messages().get(userId='me', id=msg['id']).execute()
        payload = mensaje['payload']
        headers = payload.get("headers")
        message_id = msg["id"]

        asunto = ""
        remitente = ""
        fecha = ""

        for h in headers:
            if h['name'] == 'Subject':
                asunto = h['value']
            elif h['name'] == 'From':
                remitente = h['value']
            elif h['name'] == 'Date':
                fecha = h['value']

        # Cuerpo del correo
        partes = payload.get("parts", [])
        cuerpo = ""

        if partes:
            data = partes[0]['body'].get('data')
            if data:
                cuerpo = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

        print("======================================")
        print(f"Asunto: {asunto}")
        print(f"Remitente: {remitente}")
        print(f"Fecha: {fecha}")
        print(f"Cuerpo:\n{cuerpo}")
        print("======================================\n")

        # BLOQUEAR REMITENTES AUTOMÁTICOS
        bloquear = [
            "godaddy", "no-reply", "noreply",
            "notification", "notificaciones", "alerts",
            "amazon", "microsoft", "apple",
            "facebook", "instagram", "paypal", "mercadolibre",
            "linkedin", "teams", "zoom", "slack",
        ]

        if any(b in remitente.lower() for b in bloquear):
            print(f"✖ Correo ignorado por remitente automático: {remitente}")
            continue

        # PALABRAS CLAVE
        palabras_clave = [
            "error", "falla", "fallo", "problema", "daño", "incidencia",
            "no funciona", "no prende", "no enciende", "no responde",
            "no abre", "pantalla azul", "bloqueado", "congelado", 
            "se traba", "lento", "tarda mucho", "descompuesto",
            "servidor caído", "inaccesible", "no tengo acceso",
            "desconectado", "red caída", "problemas de red", "ups"
        ]

        # DETECCIÓN CORRECTA DE INCIDENCIA
        if any(palabra in cuerpo.lower() for palabra in palabras_clave):
            incidencias_detectadas.append({
                "message_id": message_id,
                "asunto": asunto,
                "remitente": remitente,
                "fecha": fecha,
                "descripcion": cuerpo
                
            })
        if existe_incidencia(message_id):
            print(f"⚠ Incidencia YA EXISTE, no se guarda: {message_id}")
            continue
        guardar_incidencia(message_id, remitente, asunto, cuerpo, fecha)
        print("✔ Incidencia guardada en la BD.")

    # ESTE RETURN VA FUERA DEL FOR
    return incidencias_detectadas

def sincronizar_correos_desde_gmail():
    crear_base_datos()
    servicio = authenticate_gmail()

    nuevas = 0
    incidencias = leer_correos(servicio)

    for inc in incidencias:
        if not existe_incidencia(inc["message_id"]):
            guardar_incidencia(
                inc["message_id"],
                inc["remitente"],
                inc["asunto"],
                inc["descripcion"],
                inc["fecha"]
            )
            nuevas += 1

    return nuevas


if __name__ == "__main__":
    crear_base_datos()
    servicio = authenticate_gmail()
    incidencias = leer_correos(servicio)

    print("\n=== INCIDENCIAS DETECTADAS ===")
    for inc in incidencias:
        print(f"- {inc['asunto']} ({inc['remitente']})")
