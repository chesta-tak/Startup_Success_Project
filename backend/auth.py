# backend/auth.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from database.models import create_user, find_user_by_email, verify_user_password

auth_bp = Blueprint("auth", __name__)

# SIGNUP
@auth_bp.post("/signup")
def signup():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not (name and email and password):
        return jsonify({"error": "All fields are required"}), 400

    if find_user_by_email(email):
        return jsonify({"error": "Email already exists"}), 400

    create_user(name, email, password)
    return jsonify({"message": "Signup successful!"}), 201


# LOGIN
@auth_bp.post("/login")
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = find_user_by_email(email)

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    if not verify_user_password(user["password"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    # Create JWT token
    token = create_access_token(identity=str(user["_id"]))

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "name": user["name"],
            "email": user["email"]
        }
    }), 200
