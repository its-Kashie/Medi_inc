# db.py
from pymongo import MongoClient
from datetime import datetime

# === MongoDB Configuration ===
# ⚠️ Replace <username> and <password> with your actual credentials
MONGO_URI = "mongodb+srv://<username>:<password>@cluster0.mongodb.net/agentia"

# --- Connect to MongoDB ---
client = MongoClient(MONGO_URI)
db = client["agentia"]  # Main database

# === Core Collections ===
hospitals_col = db["hospitals"]
maternal_col = db["maternal_records"]
pharmacy_col = db["pharmacy_stock"]
crime_col = db["crime_cases"]
mental_col = db["mental_health"]
waste_col = db["waste_bins"]
traffic_col = db["traffic_data"]

# === Tracking Module Collections ===
ambulances_col = db["ambulances"]
incidents_col = db["incidents"]
tracking_metrics_col = db["tracking_metrics"]

# --- Optional: Create initial indexes for faster lookups ---
def init_indexes():
    hospitals_col.create_index("name")
    ambulances_col.create_index("id", unique=True)
    ambulances_col.create_index([("lat", 1), ("lon", 1)])
    incidents_col.create_index("id", unique=True)
    incidents_col.create_index("status")
    traffic_col.create_index([("source", 1), ("dest", 1)])
    tracking_metrics_col.create_index("timestamp")

# --- Utility Functions ---
def log_metric(event: str, data: dict):
    """Log system-level tracking metrics"""
    tracking_metrics_col.insert_one({
        "event": event,
        "data": data,
        "timestamp": datetime.utcnow()
    })

def get_collection_stats():
    """Return document counts for all major collections"""
    return {
        "hospitals": hospitals_col.count_documents({}),
        "maternal": maternal_col.count_documents({}),
        "pharmacy": pharmacy_col.count_documents({}),
        "crime": crime_col.count_documents({}),
        "mental_health": mental_col.count_documents({}),
        "waste": waste_col.count_documents({}),
        "traffic": traffic_col.count_documents({}),
        "ambulances": ambulances_col.count_documents({}),
        "incidents": incidents_col.count_documents({}),
        "tracking_metrics": tracking_metrics_col.count_documents({}),
    }

# --- Initialization ---
if __name__ == "__main__":
    try:
        init_indexes()
        print("✅ MongoDB indexes initialized successfully!")
        print("📊 Collection Stats:")
        for name, count in get_collection_stats().items():
            print(f"  {name}: {count} docs")
    except Exception as e:
        print(f"❌ MongoDB initialization failed: {e}")
