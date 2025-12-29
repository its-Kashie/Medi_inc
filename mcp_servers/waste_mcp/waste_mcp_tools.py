import json
import random
import sys
import os
from pathlib import Path

# ✅ SET TIMEOUT FIRST!
os.environ['MCP_CLIENT_TIMEOUT'] = '300'

from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP


def debug_log(msg):
    print(msg, file=sys.stderr, flush=True)


mcp = FastMCP("Smart Waste Broker MCP")
debug_log("✅ Waste MCP initialized (300s timeout)")

# ===== GPU CHECK & SETUP (SAME AS CNIC SERVICE) =====
import torch

USE_GPU = torch.cuda.is_available()
debug_log(f"🖥️  GPU Available: {USE_GPU}")
if USE_GPU:
    debug_log(f"   GPU Device: {torch.cuda.get_device_name(0)}")
else:
    debug_log(f"   Using CPU (slower)")

# ===== MODEL LOADING WITH ERROR HANDLING =====
PLACENTA_MODEL = None
WASTE_MODEL = None
MODELS_LOADED = False

# try:
#     from ultralytics import YOLO
#     import cv2
#
#     debug_log("📦 Loading AI models...")
#
#     # ✅ CHECK if model files exist
#     placenta_model_path = Path("models/placenta_detector.pt")
#     waste_model_path = Path("models/waste_classifier.pt")
#
#     if not placenta_model_path.exists():
#         debug_log(f"⚠️  Model not found: {placenta_model_path}")
#         debug_log("   Place your model file in models/ directory")
#     elif not waste_model_path.exists():
#         debug_log(f"⚠️  Model not found: {waste_model_path}")
#         debug_log("   Place your model file in models/ directory")
#     else:
#         # ✅ Load models (same as CNIC service approach)
#         device = 'cuda' if USE_GPU else 'cpu'
#
#         debug_log(f"   Loading placenta_detector.pt on {device}...")
#         PLACENTA_MODEL = YOLO(str(placenta_model_path))
#         PLACENTA_MODEL.to(device)
#
#         debug_log(f"   Loading waste_classifier.pt on {device}...")
#         WASTE_MODEL = YOLO(str(waste_model_path))
#         WASTE_MODEL.to(device)
#
#         MODELS_LOADED = True
#         debug_log("✅ Models loaded successfully")
#
# except Exception as e:
#     debug_log(f"⚠️  Model loading failed: {e}")
#     debug_log("   Will use dummy data for analysis")

# ===== DUMMY DATA =====
DISPOSAL_COMPANIES = [
    {
        "id": "COMP-001",
        "name": "LWMC (Lahore Waste Management)",
        "location": "Lahore",
        "pricing": {
            "bio_medical": 75,
            "sharps": 85,
            "pharmaceutical": 145,
            "placenta": 150,
            "general": 15
        },
        "epa_certified": True,
        "who_compliant": True,
        "rating": 4.2,
        "pickup_time": "Next day"
    },
    {
        "id": "COMP-002",
        "name": "EcoWaste Solutions",
        "location": "Lahore",
        "pricing": {
            "bio_medical": 68,
            "sharps": 80,
            "pharmaceutical": 135,
            "placenta": 140,
            "general": 12
        },
        "epa_certified": True,
        "who_compliant": True,
        "rating": 4.7,
        "pickup_time": "Same day"
    },
    {
        "id": "COMP-003",
        "name": "GreenMed Disposal",
        "location": "Lahore",
        "pricing": {
            "bio_medical": 80,
            "sharps": 90,
            "pharmaceutical": 160,
            "placenta": 160,
            "general": 18
        },
        "epa_certified": True,
        "who_compliant": False,
        "rating": 4.0,
        "pickup_time": "Next day"
    }
]

VIDEO_ANALYSIS_CACHE = {}


# ===== MCP TOOLS =====

@mcp.tool()
def analyze_video_waste(video_path: str) -> dict:
    """Analyze hospital waste video using 2 AI models"""

    global PLACENTA_MODEL, WASTE_MODEL, MODELS_LOADED

    # ✅ LAZY LOAD MODELS (only when needed)
    if not MODELS_LOADED:
        try:
            debug_log("📦 Loading AI models (first time)...")
            from ultralytics import YOLO
            import cv2

            device = 'cuda' if USE_GPU else 'cpu'

            placenta_path = Path("../../backend_core/models/placenta_detector.pt")
            waste_path = Path("../../backend_core/models/waste_classifier.pt")

            if placenta_path.exists() and waste_path.exists():
                PLACENTA_MODEL = YOLO(str(placenta_path))
                PLACENTA_MODEL.to(device)

                WASTE_MODEL = YOLO(str(waste_path))
                WASTE_MODEL.to(device)

                MODELS_LOADED = True
                debug_log("✅ Models loaded on demand")
        except Exception as e:
            debug_log(f"⚠️  Model loading failed: {e}")

    debug_log(f"\n{'=' * 60}")
    debug_log(f"🎬 Starting analysis: {video_path}")

    # ... baqi ka code same rahega

    # debug_log(f"\n{'=' * 60}")
    # debug_log(f"🎬 Starting analysis: {video_path}")

    # ✅ Check if video exists
    video_file = Path(video_path)
    if not video_file.exists():
        debug_log(f"❌ Video not found: {video_path}")
        return {
            "error": f"Video file not found: {video_path}",
            "status": "failed"
        }

    debug_log(f"   File size: {video_file.stat().st_size / (1024 * 1024):.2f} MB")

    # ✅ IF MODELS LOADED - USE REAL ANALYSIS
    if MODELS_LOADED and PLACENTA_MODEL and WASTE_MODEL:
        try:
            import cv2

            debug_log("✅ Using REAL AI models for analysis")

            # Open video
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                raise Exception(f"Cannot open video: {video_path}")

            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            debug_log(f"📊 Video: {total_frames} frames @ {fps:.1f} FPS")

            results = {
                "video_path": video_path,
                "analysis_timestamp": datetime.now().isoformat(),
                "duration_seconds": round(total_frames / fps, 2),
                "models_used": ["Placenta Detector v2.1 (GPU)" if USE_GPU else "Placenta Detector v2.1 (CPU)",
                                "Waste Classifier v1.8 (GPU)" if USE_GPU else "Waste Classifier v1.8 (CPU)"],
                "waste_detected": {
                    "bio_medical": 0,
                    "sharps": 0,
                    "pharmaceutical": 0,
                    "placenta": 0,
                    "general": 0
                },
                "detections": [],
                "violations": [],
                "confidence_scores": {}
            }

            frame_count = 0
            placenta_detections = 0
            bio_detections = 0
            sharp_detections = 0
            general_detections = 0
            pharma_detections = 0

            last_log = 0

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # ✅ PROGRESS LOGGING (every 10%)
                progress = (frame_count / total_frames) * 100
                if progress - last_log >= 10:
                    debug_log(f"⏳ Processing: {int(progress)}% complete...")
                    last_log = progress

                # Process every 30th frame
                if frame_count % 30 == 0:
                    timestamp_sec = round(frame_count / fps, 2)

                    # ✅ MODEL 1: Placenta Detector
                    placenta_results = PLACENTA_MODEL(frame, verbose=False)
                    for r in placenta_results:
                        for box in r.boxes:
                            conf = float(box.conf[0])
                            if conf > 0.5:
                                placenta_detections += 1
                                results["detections"].append({
                                    "timestamp": timestamp_sec,
                                    "model": "placenta_detector",
                                    "class": "placenta",
                                    "confidence": round(conf, 3)
                                })

                    # ✅ MODEL 2: Waste Classifier
                    waste_results = WASTE_MODEL(frame, verbose=False)
                    for r in waste_results:
                        for box in r.boxes:
                            conf = float(box.conf[0])
                            if conf > 0.5:
                                cls = int(box.cls[0])
                                class_name = r.names[cls]

                                results["detections"].append({
                                    "timestamp": timestamp_sec,
                                    "model": "waste_classifier",
                                    "class": class_name,
                                    "confidence": round(conf, 3)
                                })

                                # Categorize waste
                                class_lower = class_name.lower()
                                if "bio" in class_lower or "medical" in class_lower:
                                    bio_detections += 1
                                elif "sharp" in class_lower or "needle" in class_lower:
                                    sharp_detections += 1
                                elif "pharma" in class_lower or "medicine" in class_lower:
                                    pharma_detections += 1
                                elif "general" in class_lower:
                                    general_detections += 1

                frame_count += 1

            cap.release()
            debug_log("✅ Video processing complete")

            # Convert detections to kg
            results["waste_detected"]["placenta"] = round(placenta_detections * 2.0, 1)
            results["waste_detected"]["bio_medical"] = round(bio_detections * 0.5, 1)
            results["waste_detected"]["sharps"] = round(sharp_detections * 0.2, 1)
            results["waste_detected"]["pharmaceutical"] = round(pharma_detections * 0.3, 1)
            results["waste_detected"]["general"] = round(general_detections * 0.4, 1)

            # Confidence scores
            if placenta_detections > 0:
                results["confidence_scores"]["placenta_detection"] = 0.94
            if bio_detections + sharp_detections + general_detections > 0:
                results["confidence_scores"]["waste_classification"] = 0.91

            # Detect violations
            if bio_detections > 0 and general_detections > 0:
                results["violations"].append({
                    "type": "waste_mixing",
                    "timestamp": "00:45",
                    "description": "Bio-medical waste mixed with general waste",
                    "severity": "high"
                })

            debug_log(
                f"✅ Results: {placenta_detections} placenta, {bio_detections} bio, {sharp_detections} sharps, {general_detections} general")
            debug_log(f"{'=' * 60}\n")

            return results

        except Exception as e:
            debug_log(f"❌ Model error: {e}")
            debug_log("   Falling back to dummy data...")

    # ✅ FALLBACK - DUMMY DATA
    debug_log("📊 Using dummy data (models not loaded)")
    debug_log(f"{'=' * 60}\n")

    placenta_detected = random.choice([True, True, False])
    placenta_kg = round(random.uniform(2, 8), 1) if placenta_detected else 0

    waste_breakdown = {
        "video_path": video_path,
        "analysis_timestamp": datetime.now().isoformat(),
        "duration_seconds": random.randint(120, 300),
        "models_used": ["Placenta Detector v2.1 (DUMMY)", "Waste Classifier v1.8 (DUMMY)"],
        "waste_detected": {
            "bio_medical": round(random.uniform(10, 25), 1),
            "sharps": round(random.uniform(2, 6), 1),
            "pharmaceutical": round(random.uniform(0, 5), 1),
            "placenta": placenta_kg,
            "general": round(random.uniform(5, 15), 1)
        },
        "violations": [],
        "confidence_scores": {
            "placenta_detection": 0.94 if placenta_detected else None,
            "waste_classification": 0.91
        }
    }

    # Simulate violations
    if random.random() > 0.6:
        waste_breakdown["violations"].append({
            "type": "waste_mixing",
            "timestamp": "00:45",
            "description": "Bio-medical waste mixed with general waste",
            "severity": "high"
        })

    if random.random() > 0.7:
        waste_breakdown["violations"].append({
            "type": "container_overflow",
            "timestamp": "01:20",
            "description": "Container exceeds 90% capacity",
            "severity": "medium"
        })

    VIDEO_ANALYSIS_CACHE[video_path] = waste_breakdown
    return waste_breakdown


@mcp.tool()
def find_disposal_companies(waste_type: str, location: str = "Lahore") -> dict:
    """Find disposal companies for specific waste type and location"""

    matching_companies = []

    for company in DISPOSAL_COMPANIES:
        if company["location"].lower() == location.lower():
            matching_companies.append({
                "id": company["id"],
                "name": company["name"],
                "price_per_kg": company["pricing"].get(waste_type, 0),
                "epa_certified": company["epa_certified"],
                "who_compliant": company["who_compliant"],
                "rating": company["rating"],
                "pickup_time": company["pickup_time"]
            })

    matching_companies.sort(key=lambda x: x["price_per_kg"])

    return {
        "waste_type": waste_type,
        "location": location,
        "companies_found": len(matching_companies),
        "companies": matching_companies
    }


@mcp.tool()
def negotiate_price(company_id: str, waste_kg: float, waste_type: str, is_bulk: bool = False) -> dict:
    """Negotiate price with disposal company"""

    company = next((c for c in DISPOSAL_COMPANIES if c["id"] == company_id), None)

    if not company:
        return {"error": "Company not found"}

    base_price = company["pricing"].get(waste_type, 0)
    total_base = base_price * waste_kg

    discount_percent = 0
    discount_reasons = []

    if is_bulk or waste_kg > 50:
        discount_percent += 10
        discount_reasons.append("Bulk quantity discount (10%)")

    if waste_kg > 100:
        discount_percent += 5
        discount_reasons.append("Large order bonus (5%)")

    if random.random() > 0.5:
        extra_discount = random.randint(2, 5)
        discount_percent += extra_discount
        discount_reasons.append(f"Negotiation success ({extra_discount}%)")

    discount_amount = (total_base * discount_percent) / 100
    final_price = total_base - discount_amount

    return {
        "company_id": company_id,
        "company_name": company["name"],
        "waste_type": waste_type,
        "quantity_kg": waste_kg,
        "base_price_per_kg": base_price,
        "total_base_price": round(total_base, 2),
        "discount_percent": discount_percent,
        "discount_reasons": discount_reasons,
        "discount_amount": round(discount_amount, 2),
        "final_price": round(final_price, 2),
        "savings": round(discount_amount, 2)
    }


@mcp.tool()
def calculate_total_cost(waste_breakdown: dict, company_id: str) -> dict:
    """Calculate total disposal cost for all waste types"""

    company = next((c for c in DISPOSAL_COMPANIES if c["id"] == company_id), None)

    if not company:
        return {"error": "Company not found"}

    cost_details = []
    total_cost = 0

    for waste_type, quantity in waste_breakdown.items():
        if quantity > 0:
            price_per_kg = company["pricing"].get(waste_type, 0)
            cost = price_per_kg * quantity
            total_cost += cost

            cost_details.append({
                "waste_type": waste_type,
                "quantity_kg": quantity,
                "price_per_kg": price_per_kg,
                "subtotal": round(cost, 2)
            })

    return {
        "company_id": company_id,
        "company_name": company["name"],
        "cost_breakdown": cost_details,
        "total_cost": round(total_cost, 2),
        "currency": "PKR"
    }


@mcp.tool()
def schedule_pickup(hospital_id: str, company_id: str, pickup_time: str, waste_kg: float) -> dict:
    """Schedule waste pickup with disposal company"""

    company = next((c for c in DISPOSAL_COMPANIES if c["id"] == company_id), None)

    if not company:
        return {"error": "Company not found"}

    pickup_id = f"PICKUP-{random.randint(10000, 99999)}"

    return {
        "status": "scheduled",
        "pickup_id": pickup_id,
        "hospital_id": hospital_id,
        "company_id": company_id,
        "company_name": company["name"],
        "pickup_time": pickup_time,
        "waste_kg": waste_kg,
        "truck_id": f"BIO-HAZARD-{random.randint(100, 999)}",
        "driver_name": random.choice(["Ahmed Khan", "Ali Raza", "Usman Sheikh"]),
        "driver_contact": "0300-" + str(random.randint(1000000, 9999999)),
        "scheduled_at": datetime.now().isoformat()
    }


@mcp.tool()
def check_compliance(hospital_id: str) -> dict:
    """Check hospital's waste management compliance status"""

    compliance_score = random.randint(60, 95)

    issues = []
    if compliance_score < 70:
        issues.append("Waste segregation violations detected")
    if compliance_score < 80:
        issues.append("Container overflow incidents")
    if random.random() > 0.7:
        issues.append("Staff PPE compliance low")

    return {
        "hospital_id": hospital_id,
        "compliance_score": compliance_score,
        "status": "compliant" if compliance_score >= 75 else "non_compliant",
        "epa_status": "approved" if compliance_score >= 80 else "warning",
        "who_guidelines": "met" if compliance_score >= 85 else "partial",
        "issues": issues,
        "next_inspection": (datetime.now() + timedelta(days=random.randint(30, 90))).strftime("%Y-%m-%d"),
        "checked_at": datetime.now().isoformat()
    }


@mcp.tool()
def generate_cost_report(hospital_id: str, period_days: int = 30) -> dict:
    """Generate cost savings report for hospital"""

    old_vendor_cost = random.uniform(50000, 100000)
    new_vendor_cost = old_vendor_cost * random.uniform(0.75, 0.90)
    savings = old_vendor_cost - new_vendor_cost
    savings_percent = (savings / old_vendor_cost) * 100

    return {
        "hospital_id": hospital_id,
        "period_days": period_days,
        "old_vendor_cost": round(old_vendor_cost, 2),
        "new_vendor_cost": round(new_vendor_cost, 2),
        "total_savings": round(savings, 2),
        "savings_percent": round(savings_percent, 1),
        "projected_annual_savings": round(savings * (365 / period_days), 2),
        "report_generated": datetime.now().isoformat()
    }


@mcp.tool()
def get_disposal_certificate(pickup_id: str) -> dict:
    """Get disposal certificate after waste pickup"""

    return {
        "certificate_id": f"CERT-{random.randint(10000, 99999)}",
        "pickup_id": pickup_id,
        "disposal_method": random.choice(["Incineration", "Autoclaving", "Chemical Treatment"]),
        "disposal_location": "EPA Certified Disposal Site - Lahore",
        "disposal_date": datetime.now().strftime("%Y-%m-%d"),
        "certified_by": "Environmental Protection Agency Pakistan",
        "certificate_issued": datetime.now().isoformat()
    }


# ===== RUN SERVER =====
if __name__ == "__main__":
    debug_log("🚀 Starting waste_mcp_tools.py...")
    debug_log(f"   Models loaded: {MODELS_LOADED}")
    debug_log(f"   GPU enabled: {USE_GPU}")
    mcp.run()