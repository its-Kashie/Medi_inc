# # cnic_ocr_service.py - CNIC OCR Microservice (Separate from Agents)
# """
# 🔒 PRIVACY-FIRST DESIGN:
# - CNIC data NEVER goes to hospital_agents
# - Only confirmation status sent to maternal agent
# - Data stored encrypted in MongoDB
# """
#
# from fastapi import FastAPI, File, UploadFile, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# import easyocr
# import cv2
# import numpy as np
# from pymongo import MongoClient
# from datetime import datetime
# import hashlib
# import os
# from cryptography.fernet import Fernet
#
# app = FastAPI(title="CNIC OCR Service")
#
# # CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
# # MongoDB
# mongo_client = MongoClient("mongodb://localhost:27017/")
# db = mongo_client["healthcare360"]
# cnic_collection = db["cnic_records"]
#
# # Encryption (store key securely in production)
# ENCRYPTION_KEY = os.environ.get("CNIC_ENCRYPTION_KEY", Fernet.generate_key())
# cipher = Fernet(ENCRYPTION_KEY)
#
# # EasyOCR Reader
# reader = easyocr.Reader(['en', 'ur'], gpu=False)
#
# # Your trained YOLO model
# from ultralytics import YOLO
#
# model = YOLO("cnic_model/best.pt")  # Path to your trained model
#
#
# def encrypt_data(data: str) -> str:
#     """Encrypt sensitive data"""
#     return cipher.encrypt(data.encode()).decode()
#
#
# def decrypt_data(encrypted: str) -> str:
#     """Decrypt sensitive data"""
#     return cipher.decrypt(encrypted.encode()).decode()
#
#
# def extract_cnic_fields(image_bytes: bytes) -> dict:
#     """
#     Extract CNIC fields using your trained YOLO + EasyOCR
#
#     Returns: {
#         'cnic_number': '35202-1234567-1',
#         'name': 'Fatima Ahmed',
#         'father_name': 'Ahmed Khan',
#         'date_of_birth': '01-01-1990',
#         'gender': 'Female',
#         'address': 'House 123, Lahore'
#     }
#     """
#
#     # Convert bytes to image
#     nparr = np.frombuffer(image_bytes, np.uint8)
#     img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#
#     # YOLO detection
#     results = model(img, conf=0.4)[0]
#
#     extracted = {}
#
#     for box in results.boxes:
#         x1, y1, x2, y2 = map(int, box.xyxy[0])
#         label = results.names[int(box.cls[0])]
#
#         # Crop field
#         crop = img[y1:y2, x1:x2]
#
#         # OCR
#         text_lines = reader.readtext(crop, detail=0, paragraph=True)
#         text = " ".join(text_lines).strip()
#         text = " ".join(text.split())
#
#         # Clean field name
#         field_name = label.replace("_", " ").lower()
#
#         extracted[field_name] = text
#
#     return extracted
#
#
# @app.post("/api/cnic/extract")
# async def extract_cnic(file: UploadFile = File(...)):
#     """
#     📸 Upload CNIC image → Extract fields → Store encrypted
#
#     Returns ONLY registration_id (NOT the actual CNIC data)
#     """
#
#     try:
#         # Read image
#         contents = await file.read()
#
#         # Extract fields
#         fields = extract_cnic_fields(contents)
#
#         if not fields.get("cnic number"):
#             raise HTTPException(status_code=400, detail="CNIC number not detected")
#
#         # Generate registration ID
#         registration_id = f"REG-{int(datetime.now().timestamp() * 1000)}"
#
#         # Encrypt sensitive fields
#         encrypted_record = {
#             "registration_id": registration_id,
#             "cnic_number_encrypted": encrypt_data(fields.get("cnic number", "")),
#             "name_encrypted": encrypt_data(fields.get("name", "")),
#             "father_name_encrypted": encrypt_data(fields.get("father name", "")),
#             "dob_encrypted": encrypt_data(fields.get("date of birth", "")),
#             "gender": fields.get("gender", "Female"),  # Not sensitive
#             "address_encrypted": encrypt_data(fields.get("address", "")),
#             "uploaded_at": datetime.now().isoformat(),
#             "status": "pending_verification"
#         }
#
#         # Store in MongoDB
#         cnic_collection.insert_one(encrypted_record)
#
#         # Return ONLY registration_id (hospital_agents will use this)
#         return {
#             "status": "success",
#             "registration_id": registration_id,
#             "message": "CNIC data extracted and stored securely",
#             "detected_fields": list(fields.keys())  # Just field names, not values
#         }
#
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @app.get("/api/cnic/verify/{registration_id}")
# async def verify_cnic(registration_id: str):
#     """
#     ✅ Verify if registration exists (for hospital_agents)
#     Returns ONLY non-sensitive info
#     """
#
#     record = cnic_collection.find_one({"registration_id": registration_id})
#
#     if not record:
#         raise HTTPException(status_code=404, detail="Registration not found")
#
#     return {
#         "registration_id": registration_id,
#         "status": record["status"],
#         "uploaded_at": record["uploaded_at"],
#         "verified": True
#     }
#
#
# @app.get("/api/cnic/details/{registration_id}")
# async def get_cnic_details(registration_id: str, authorized: bool = False):
#     """
#     🔐 Get CNIC details (ONLY for authorized hospital staff)
#
#     In production: Add JWT authentication
#     """
#
#     if not authorized:
#         raise HTTPException(status_code=403, detail="Unauthorized access")
#
#     record = cnic_collection.find_one({"registration_id": registration_id})
#
#     if not record:
#         raise HTTPException(status_code=404, detail="Registration not found")
#
#     # Decrypt for authorized access
#     return {
#         "registration_id": registration_id,
#         "name": decrypt_data(record["name_encrypted"]),
#         "cnic_number": decrypt_data(record["cnic_number_encrypted"]),
#         "father_name": decrypt_data(record["father_name_encrypted"]),
#         "dob": decrypt_data(record["dob_encrypted"]),
#         "gender": record["gender"],
#         "address": decrypt_data(record["address_encrypted"]),
#         "uploaded_at": record["uploaded_at"]
#     }
#
#
# @app.get("/")
# async def root():
#     return {
#         "service": "CNIC OCR Microservice",
#         "version": "1.0.0",
#         "status": "online",
#         "endpoints": {
#             "extract": "/api/cnic/extract (POST - upload CNIC image)",
#             "verify": "/api/cnic/verify/{registration_id}",
#             "details": "/api/cnic/details/{registration_id}"
#         }
#     }
#
#
# if __name__ == "__main__":
#     import uvicorn
#
#     uvicorn.run(app, host="0.0.0.0", port=8001)  # Different port from main backend



# cnic_ocr_service.py - CNIC OCR Microservice (GPU Enabled)
"""
🔒 PRIVACY-FIRST DESIGN:
- CNIC data NEVER goes to hospital_agents
- Only confirmation status sent to maternal agent
- Data stored encrypted in MongoDB
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import easyocr
import cv2
import numpy as np
from pymongo import MongoClient
from datetime import datetime
import hashlib
import os
from cryptography.fernet import Fernet

app = FastAPI(title="CNIC OCR Service")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["healthcare360"]
cnic_collection = db["cnic_records"]

# Encryption (store key securely in production)
ENCRYPTION_KEY = os.environ.get("CNIC_ENCRYPTION_KEY", Fernet.generate_key())
cipher = Fernet(ENCRYPTION_KEY)

# ===== GPU CHECK & SETUP =====
import torch

USE_GPU = torch.cuda.is_available()
print(f"🖥️  GPU Available: {USE_GPU}")
if USE_GPU:
    print(f"   GPU Device: {torch.cuda.get_device_name(0)}")
else:
    print(f"   Using CPU (slower)")

# EasyOCR Reader with GPU support
print("📚 Loading EasyOCR (English + Urdu)...")
reader = easyocr.Reader(['en', 'ur'], gpu=USE_GPU)
print("✅ EasyOCR loaded")

# Your trained YOLO model
from ultralytics import YOLO

print("🔍 Loading YOLO model...")
model = YOLO("cnic_model/best.pt")
print("✅ YOLO model loaded successfully")


def encrypt_data(data: str) -> str:
    """Encrypt sensitive data"""
    return cipher.encrypt(data.encode()).decode()


def decrypt_data(encrypted: str) -> str:
    """Decrypt sensitive data"""
    return cipher.decrypt(encrypted.encode()).decode()


def extract_cnic_fields(image_bytes: bytes) -> dict:
    """
    Extract CNIC fields using your trained YOLO + EasyOCR

    Returns: {
        'cnic_number': '35202-1234567-1',
        'name': 'Fatima Ahmed',
        'father_name': 'Ahmed Khan',
        'date_of_birth': '01-01-1990',
        'gender': 'Female',
        'address': 'House 123, Lahore'
    }
    """

    print(f"📸 Processing CNIC image ({len(image_bytes)} bytes)...")

    # Convert bytes to image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Failed to decode image")

    print(f"   Image shape: {img.shape}")

    # YOLO detection
    print("🔍 Running YOLO detection...")
    results = model(img, conf=0.4)[0]

    extracted = {}

    print(f"   Detected {len(results.boxes)} fields")

    for i, box in enumerate(results.boxes):
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        label = results.names[int(box.cls[0])]

        print(f"   Field {i + 1}: {label} at ({x1},{y1})-({x2},{y2})")

        # Crop field
        crop = img[y1:y2, x1:x2]

        # OCR
        text_lines = reader.readtext(crop, detail=0, paragraph=True)
        text = " ".join(text_lines).strip()
        text = " ".join(text.split())

        # Clean field name
        field_name = label.replace("_", " ").lower()

        extracted[field_name] = text
        print(f"      Extracted: {text[:50]}...")

    print(f"✅ Extraction complete: {list(extracted.keys())}")
    return extracted


@app.post("/api/cnic/extract")
async def extract_cnic(file: UploadFile = File(...)):
    """
    📸 Upload CNIC image → Extract fields → Store encrypted

    Returns ONLY registration_id (NOT the actual CNIC data)
    """

    try:
        print(f"\n{'=' * 60}")
        print(f"📥 New CNIC upload: {file.filename}")

        # Read image
        contents = await file.read()

        # Extract fields
        fields = extract_cnic_fields(contents)

        # Check if CNIC number was detected
        cnic_field = fields.get("cnic number") or fields.get("cnic no") or fields.get("cnic")

        if not cnic_field:
            print("❌ CNIC number not detected")
            print(f"   Detected fields: {list(fields.keys())}")
            raise HTTPException(
                status_code=400,
                detail=f"CNIC number not detected. Found: {list(fields.keys())}"
            )

        # Generate registration ID
        registration_id = f"REG-{int(datetime.now().timestamp() * 1000)}"

        print(f"🆔 Generated registration ID: {registration_id}")

        # Encrypt sensitive fields
        encrypted_record = {
            "registration_id": registration_id,
            "cnic_number_encrypted": encrypt_data(cnic_field),
            "name_encrypted": encrypt_data(fields.get("name", "")),
            "father_name_encrypted": encrypt_data(fields.get("father name", "")),
            "dob_encrypted": encrypt_data(fields.get("date of birth", "")),
            "gender": fields.get("gender", "Female"),
            "address_encrypted": encrypt_data(fields.get("address", "")),
            "uploaded_at": datetime.now().isoformat(),
            "status": "pending_verification"
        }

        # Store in MongoDB
        cnic_collection.insert_one(encrypted_record)
        print(f"💾 Stored in MongoDB")

        print(f"✅ Success!")
        print(f"{'=' * 60}\n")

        # Return ONLY registration_id (hospital_agents will use this)
        return {
            "status": "success",
            "registration_id": registration_id,
            "message": "CNIC data extracted and stored securely",
            "detected_fields": list(fields.keys())
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"{'=' * 60}\n")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cnic/verify/{registration_id}")
async def verify_cnic(registration_id: str):
    """
    ✅ Verify if registration exists (for hospital_agents)
    Returns ONLY non-sensitive info
    """

    record = cnic_collection.find_one({"registration_id": registration_id})

    if not record:
        raise HTTPException(status_code=404, detail="Registration not found")

    return {
        "registration_id": registration_id,
        "status": record["status"],
        "uploaded_at": record["uploaded_at"],
        "verified": True
    }


@app.get("/api/cnic/details/{registration_id}")
async def get_cnic_details(registration_id: str, authorized: bool = True):
    """
    🔐 Get CNIC details (ONLY for authorized hospital staff)

    In production: Add JWT authentication
    """

    if not authorized:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    record = cnic_collection.find_one({"registration_id": registration_id})

    if not record:
        raise HTTPException(status_code=404, detail="Registration not found")

    # Decrypt for authorized access
    return {
        "registration_id": registration_id,
        "name": decrypt_data(record["name_encrypted"]),
        "cnic_number": decrypt_data(record["cnic_number_encrypted"]),
        "father_name": decrypt_data(record["father_name_encrypted"]),
        "dob": decrypt_data(record["dob_encrypted"]),
        "gender": record["gender"],
        "address": decrypt_data(record["address_encrypted"]),
        "uploaded_at": record["uploaded_at"]
    }


@app.get("/")
async def root():
    return {
        "service": "CNIC OCR Microservice",
        "version": "1.0.1",
        "status": "online",
        "gpu_enabled": USE_GPU,
        "gpu_device": torch.cuda.get_device_name(0) if USE_GPU else "CPU",
        "endpoints": {
            "extract": "/api/cnic/extract (POST - upload CNIC image)",
            "verify": "/api/cnic/verify/{registration_id}",
            "details": "/api/cnic/details/{registration_id}"
        }
    }


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 60)
    print("🚀 Starting CNIC OCR Service with GPU support")
    print("=" * 60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8001)