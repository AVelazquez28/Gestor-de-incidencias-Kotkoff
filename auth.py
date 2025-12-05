from flask import Blueprint, redirect, session, request
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
import os

auth = Blueprint("auth", __name__)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "TU_CLIENT_ID"
SCOPES = ["https://www.googleapis.com/auth/userinfo.email", "openid"]

# IMPORTANTE → actualiza por tu URL de Render
REDIRECT_URI = "https://tu-proyecto.onrender.com/callback"


@auth.route("/login")
def login():
    flow = Flow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    auth_url, _ = flow.authorization_url(
        prompt="consent",
        include_granted_scopes="true"
    )

    return redirect(auth_url)


@auth.route("/callback")
def callback():
    flow = Flow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    token_request = requests.Request()

    info = id_token.verify_oauth2_token(
        credentials._id_token,
        token_request,
        GOOGLE_CLIENT_ID
    )

    session["email"] = info.get("email")

    return redirect("/")


@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
