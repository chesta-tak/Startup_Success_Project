# backend/app.py

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from auth import auth_bp
from database.models import save_prediction
from config import JWT_SECRET_KEY
from flask import render_template
import joblib
import pandas as pd




# Flask App
app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
jwt = JWTManager(app)
CORS(app)

# Register auth
app.register_blueprint(auth_bp, url_prefix="/api/auth")

# ------------------------------------------
# LOAD NEW MODEL + NEW DATASET
# ------------------------------------------
model = joblib.load("ml_model/startup_model.pkl")

# Load corrected dataset for dashboard + optional rules
df = pd.read_csv("data/startup2020_2025_corrected_success_labels.csv")

# ------------------------------------------
# GET categories for dropdown
# ------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/signup")
def signup_page():
    return render_template("signup.html")

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

@app.route("/predict")
def predict_page():
    return render_template("predict.html")

@app.route("/profile")
def profile_page():
    return render_template("profile.html")

@app.route("/history")
def history_page():
    return render_template("history.html")


@app.get("/api/categories")
def categories():
    industries = sorted(df["industry"].dropna().unique().tolist())
    cities = sorted(df["city"].dropna().unique().tolist())

    return jsonify({
        "industries": industries,
        "cities": cities
    })

def generate_recommendations(industry, city, amount, rounds):
    rec = []

    median_fund = df["funding_amount_inr"].median()
    median_rounds = df["funding_rounds_count"].median() if "funding_rounds_count" in df else 1

    if amount < median_fund:
        rec.append("Consider raising more funding to reach market competitiveness.")
    
    if rounds < median_rounds:
        rec.append("Try securing additional funding rounds for higher investor confidence.")
    
    if df.groupby("industry")["is_success"].mean().get(industry, 0) < 0.5:
        rec.append("This industry has a lower success rate. Improve differentiation or innovation.")
    
    if df.groupby("city")["is_success"].mean().get(city, 0) < 0.5:
        rec.append("Consider partnering or expanding to a stronger startup ecosystem.")

    if not rec:
        rec.append("Your startup looks strong overall! Continue growth strategy.")

    return rec

# ------------------------------------------
# SIMILAR STARTUPS SUGGESTION
# ------------------------------------------
def get_similar_startups(industry, city, amount):
    # Normalize the incoming values
    industry = industry.strip().lower()
    city = city.strip().lower()

    # Normalize dataset values
    df_norm = df.copy()
    df_norm["industry_norm"] = df_norm["industry"].astype(str).str.strip().str.lower()
    df_norm["city_norm"] = df_norm["city"].astype(str).str.strip().str.lower()

    subset = df_norm[(df_norm["industry_norm"] == industry) & (df_norm["city_norm"] == city)]

    if subset.empty:
        return []

    subset["difference"] = abs(subset["funding_amount_inr"] - amount)

    result = subset.sort_values("difference").head(3)[
        ["startup_name", "funding_amount_inr", "is_success"]
    ]

    return result.to_dict(orient="records")


# ------------------------------------------
# PREDICT API
# ------------------------------------------
@app.post("/api/predict")
def predict():
    data = request.get_json()

    industry = data.get("industry")
    city = data.get("city")
    amount = float(data.get("funding_amount"))
    rounds = int(data.get("funding_rounds"))
    user_email = data.get("email")  # <- get user email

    input_df = pd.DataFrame([{
        "industry": industry,
        "city": city,
        "funding_amount_inr": amount
    }])

    prob = float(model.predict_proba(input_df)[0][1])
    pred = int(prob >= 0.50)
    success_score = round(prob * 100)

    recommendations = generate_recommendations(industry, city, amount, rounds)
    similar_startups = get_similar_startups(industry, city, amount)

    save_prediction(
        user_email=user_email,
        industry=industry,
        city=city,
        amount=amount,
        rounds=rounds,
        prob=prob,
        pred=pred
    )

    return jsonify({
        "prediction": pred,
        "probability_success": prob,
        "success_score": success_score,
        "recommendations": recommendations,
        "similar_startups": similar_startups
    })

# ------------------------------------------
# DASHBOARD API
# ------------------------------------------
@app.get("/api/dashboard")
def dashboard():
    top_ind_count = df.groupby("industry").size().sort_values(ascending=False).head(10)
    top_city_count = df.groupby("city").size().sort_values(ascending=False).head(10)

    top_ind_success = df.groupby("industry")["is_success"].mean().sort_values(ascending=False).head(10)
    top_city_success = df.groupby("city")["is_success"].mean().sort_values(ascending=False).head(10)

    return jsonify({
        "top_industries_count": [{"industry": i, "count": int(c)} for i, c in top_ind_count.items()],
        "top_cities_count": [{"city": c, "count": int(v)} for c, v in top_city_count.items()],
        "top_industries_success": [{"industry": i, "success_rate": float(v)} for i, v in top_ind_success.items()],
        "top_cities_success": [{"city": c, "success_rate": float(v)} for c, v in top_city_success.items()]
    })


# ------------------------------------------
# FUNDING DISTRIBUTION API
# ------------------------------------------
@app.get("/api/funding_distribution")
def funding_distribution():
    try:
        bins = pd.qcut(df["funding_amount_inr"], q=10, duplicates="drop")
        dist = bins.value_counts().sort_index()

        return jsonify({
            "ranges": [str(i) for i in dist.index],
            "counts": dist.values.tolist()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------------------------------
# TOP INVESTORS API
# ------------------------------------------
@app.get("/api/top_investors")
def top_investors():
    try:
        investor_list = []

        for row in df["investors"].dropna():
            for inv in row.split(","):
                investor_list.append(inv.strip())

        counts = pd.Series(investor_list).value_counts().head(10)

        return jsonify({
            "investors": counts.index.tolist(),
            "counts": counts.values.tolist()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# ------------------------------------------
# USER PREDICTION HISTORY API
# ------------------------------------------
@app.get("/api/history")
def history():
    email = request.args.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    from database.db import predictions_collection

    records = list(predictions_collection.find({"email": email}).sort("timestamp", -1))

    for r in records:
        r["_id"] = str(r["_id"])
        r["timestamp"] = r["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

    return jsonify(records)


# ------------------------------------------
# SUCCESS FACTOR IMPORTANCE API
# ------------------------------------------
@app.get("/api/factors")
def factors():
    try:
        clf = model.named_steps.get("classifier")

        # If model has no importances, or importances mismatch length, use a fallback
        if not hasattr(clf, "feature_importances_") or len(clf.feature_importances_) != 3:
            return jsonify([
                {"feature": "industry", "importance": 0.33},
                {"feature": "city", "importance": 0.33},
                {"feature": "funding_amount_inr", "importance": 0.34}
            ])

        # Else if model actually has 3 values
        feature_names = ["industry", "city", "funding_amount_inr"]
        importances = clf.feature_importances_

        return jsonify([
            {"feature": feature_names[i], "importance": float(importances[i])}
            for i in range(3)
        ])

    except:
        # Final fallback
        return jsonify([
            {"feature": "industry", "importance": 0.33},
            {"feature": "city", "importance": 0.33},
            {"feature": "funding_amount_inr", "importance": 0.34}
        ])


# ------------------------------------------
# PROFILE SUMMARY API  ✅ NEWLY ADDED
# ------------------------------------------
from database.db import predictions_collection
from datetime import datetime

@app.get("/api/profile_summary")
def profile_summary():
    email = request.args.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    records = list(predictions_collection.find({"email": email}).sort("timestamp", -1))

    total = len(records)
    success_count = sum(1 for r in records if r.get("prediction") == 1)
    fail_count = sum(1 for r in records if r.get("prediction") == 0)

    last_preds = []
    for r in records[:10]:
        last_preds.append({
            "_id": str(r.get("_id")),
            "industry": r.get("industry"),
            "city": r.get("city"),
            "funding_amount": r.get("funding_amount"),
            "funding_rounds": r.get("funding_rounds"),
            "probability": float(r.get("probability")),
            "prediction": int(r.get("prediction")),
            "timestamp": r["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        })

    trend_records = list(reversed(records[-12:]))

    trend = {
        "timestamps": [
            (r["timestamp"].strftime("%Y-%m-%d") if isinstance(r["timestamp"], datetime) else str(r["timestamp"]))
            for r in trend_records
        ],
        "scores": [ round(float(r["probability"]) * 100, 1) for r in trend_records ]
    }

    return jsonify({
        "total": total,
        "success_count": success_count,
        "fail_count": fail_count,
        "last_predictions": last_preds,
        "trend": trend
    })


# ------------------------------------------
# RUN SERVER
# ------------------------------------------
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )
