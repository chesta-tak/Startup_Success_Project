from pymongo import MongoClient

# Local MongoDB Compass connection
client = MongoClient("mongodb://localhost:27017/")

# Database name
db = client["startup_prediction"]

# Collections
users_collection = db["users"]
predictions_collection = db["predictions"]
