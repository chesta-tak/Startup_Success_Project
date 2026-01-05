import joblib
import numpy as np
import pandas as pd

# -----------------------------------------
# LOAD YOUR NEW ULTRA MODEL + ENCODERS
# -----------------------------------------
model = joblib.load("ml_model/startup_model_ULTRA.pkl")
le_industry = joblib.load("ml_model/industry_encoder_ULTRA.pkl")
le_city = joblib.load("ml_model/city_encoder_ULTRA.pkl")

# -----------------------------------------
# FUNCTION TO TEST ONE STARTUP INPUT
# -----------------------------------------
def test_one(industry, city, amount, rounds):
    try:
        ind = le_industry.transform([industry])[0]
        ct = le_city.transform([city])[0]
    except:
        print(f"\n❌ ERROR: '{industry}' or '{city}' not found in encoder classes.\n")
        return

    X = np.array([[ind, ct, amount, rounds]])

    pred = model.predict(X)[0]
    prob = model.predict_proba(X)[0][1]

    print("\n----------------------------------------")
    print(f" Industry: {industry}")
    print(f" City: {city}")
    print(f" Funding: {amount}")
    print(f" Funding Rounds: {rounds}")
    print("----------------------------------------")
    print(" Prediction:", "SUCCESS (1) 🎉" if pred == 1 else "FAILURE (0) ❌")
    print(f" Probability of Success: {prob:.4f}")
    print("----------------------------------------\n")


# -----------------------------------------
# TEST CASES (FEEL FREE TO ADD MORE)
# -----------------------------------------
cases = [
    ("FinTech", "Bangalore", 80000000, 4),
    ("SaaS", "Delhi", 90000000, 5),
    ("HealthTech", "Mumbai", 70000000, 3),
    ("EdTech", "Bangalore", 65000000, 4),
    ("E-Commerce", "Delhi", 20000000, 2),
    ("FinTech", "Pune", 15000000, 1),
]

for c in cases:
    test_one(*c)
