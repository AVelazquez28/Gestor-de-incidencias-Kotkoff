from flask import Blueprint, redirect, url_for, session
from google_auth_oauthlib.flow import Flow
import os
import pathlib

auth = Blueprint("auth", __name__)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "TU_CLIENT_ID"
GOOGLE_CLIENT_SECRET = "TU_CLIENT_SECRET"

SCOPES = ["https://www.googleapis.com/auth/userinfo.email", "openid"]

# Esta ruta la vas a usar en Google Cloud:
REDIRECT_URI = "http://127.0.0.1:5000/callback"


@auth.route("/login")
def login():
    flow = Flow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    authorization_url, _ = flow.authorization_url(
        prompt="consent",
        include_granted_scopes="true"
    )

    return redirect(authorization_url)


@auth.route("/callback")
def callback():
    flow = Flow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    request_session = google.auth.transport.requests.Request()

    id_info = google.oauth2.id_token.verify_oauth2_token(
        credentials._id_token,
        request_session,
        GOOGLE_CLIENT_ID
    )

    session["email"] = id_info.get("email")

    return redirect("/")
    

@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/")
