from flask import Blueprint, redirect, request, session
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
import os

auth = Blueprint("auth", __name__)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.email"]


def build_flow(state=None):
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uris": [GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        state=state
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    return flow


@auth.route("/login")
def login():
    flow = build_flow()
    auth_url, state = flow.authorization_url(prompt="consent", include_granted_scopes="true")
    session["state"] = state
    return redirect(auth_url)


@auth.route("/callback")
def callback():
    if "state" not in session:
        return "Invalid session. Please try logging in again.", 400

    flow = build_flow(session["state"])
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    info = id_token.verify_oauth2_token(
        credentials.id_token,
        requests.Request(),
        GOOGLE_CLIENT_ID
    )

    session["email"] = info["email"]
    session["google_token"] = credentials.token

    return redirect("/")
