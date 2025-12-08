from flask import Blueprint, redirect, request, session
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
import os

auth = Blueprint("auth", __name__)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly"
]

def build_flow(state=None):
    return Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uris": [GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=SCOPES,
        state=state
    )

@auth.route("/login")
def login():
    flow = build_flow()
    flow.redirect_uri = GOOGLE_REDIRECT_URI

    auth_url, state = flow.authorization_url(
    access_type="offline",
    prompt="consent",
    include_granted_scopes=True  # ← ESTA LÍNEA FALTABA


    )

    session["state"] = state
    return redirect(auth_url)

@auth.route("/callback")
def callback():
    state = session.get("state")
    if not state:
        return redirect("/login")

    flow = build_flow(state)
    flow.redirect_uri = GOOGLE_REDIRECT_URI

    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    idinfo = id_token.verify_oauth2_token(
        credentials.id_token,
        requests.Request(),
        GOOGLE_CLIENT_ID
    )

    session["email"] = idinfo["email"]
    session["google_token"] = credentials.token

    return redirect("/")
