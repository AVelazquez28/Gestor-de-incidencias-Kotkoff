from flask import Blueprint, redirect, session

print("=== AUTH BLUEPRINT LOADED ===")

auth = Blueprint("auth", __name__)

@auth.route("/login")
def login():
    return "LOGIN AQUÍ"

@auth.route("/callback")
def callback():
    session["email"] = "prueba@gmail.com"
    return redirect("/")
