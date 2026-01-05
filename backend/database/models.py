# backend/database/models.py

from database.db import users_collection, predictions_collection
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


# --------------------------------------------
# USER FUNCTIONS
# --------------------------------------------

# Create new user
def create_user(name, email, password):
    hashed = generate_password_hash(password)
    user = {
        "name": name,
        "email": email,
        "password": hashed
    }
    users_collection.insert_one(user)
    return user


# Find user by email
def find_user_by_email(email):
    return users_collection.find_one({"email": email})


# Verify password
def verify_user_password(hashed_password, plain_password):
    return check_password_hash(hashed_password, plain_password)


# --------------------------------------------
# SAVE PREDICTION (NEW FUNCTION)
# --------------------------------------------
def save_prediction(user_email, industry, city, amount, rounds, prob, pred):
    entry = {
        "email": user_email,
        "industry": industry,
        "city": city,
        "funding_amount": amount,
        "funding_rounds": rounds,
        "probability": prob,
        "prediction": pred,
        "timestamp": datetime.utcnow()
    }
    predictions_collection.insert_one(entry)
    return entry
