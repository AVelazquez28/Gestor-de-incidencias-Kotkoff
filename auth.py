from flask import Blueprint, redirect, request, session
import requests
import os

auth = Blueprint("auth", __name__)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
GOOGLE_AUTH_URI = os.getenv("GOOGLE_AUTH_URI")
GOOGLE_TOKEN_URI = os.getenv("GOOGLE_TOKEN_URI")

SCOPES = "email profile openid"


@auth.route("/login")
def login():
    google_auth_url = (
        f"{GOOGLE_AUTH_URI}"
        f"?response_type=code"
        f"&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&scope={SCOPES}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    return redirect(google_auth_url)


@auth.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "No code from Google", 400

    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    # Intercambio de code → token
    token_response = requests.post(GOOGLE_TOKEN_URI, data=data)
    token_json = token_response.json()

    access_token = token_json.get("access_token")

    # Info del usuario
    userinfo = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    session["email"] = userinfo["email"]
    print("Usuario logeado:", session["email"])

    return redirect("/")
