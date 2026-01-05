import joblib

le_industry = joblib.load("ml_model/industry_encoder_ULTRA.pkl")
le_city = joblib.load("ml_model/city_encoder_ULTRA.pkl")

print("\nIndustries:")
print(list(le_industry.classes_))

print("\nCities:")
print(list(le_city.classes_))
