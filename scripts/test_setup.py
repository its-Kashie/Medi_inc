#!/usr/bin/env python3
"""
Test script to verify HealthLink360 Backend Core setup
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, '/home/kyim/Medi_inc')

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing module imports...")
    
    try:
        from shared.config import settings
        print("✅ Shared config imported successfully")
        print(f"   Environment: {settings.environment}")
        print(f"   Debug: {settings.debug}")
    except Exception as e:
        print(f"❌ Failed to import shared.config: {e}")
        return False
    
    try:
        from shared.logger import app_logger
        print("✅ Shared logger imported successfully")
        app_logger.info("Logger test message")
    except Exception as e:
        print(f"❌ Failed to import shared.logger: {e}")
        return False
    
    try:
        from shared.pii_redaction import pii_redactor
        print("✅ PII redactor imported successfully")
        # Test redaction
        test_cnic = "12345-1234567-1"
        redacted = pii_redactor.redact_cnic(test_cnic, level=2)
        print(f"   CNIC redaction test: {test_cnic} → {redacted}")
    except Exception as e:
        print(f"❌ Failed to import pii_redactor: {e}")
        return False
    
    try:
        from backend_core.models import User, Patient, UserRole
        print("✅ Backend Core models imported successfully")
        print(f"   Available user roles: {[role.value for role in UserRole]}")
    except Exception as e:
        print(f"❌ Failed to import backend_core.models: {e}")
        return False
    
    return True


def test_utilities():
    """Test utility functions"""
    print("\n🧪 Testing utility functions...")
    
    try:
        from shared.utils import generate_patient_id, calculate_bmi, format_cnic
        
        # Test ID generation
        patient_id = generate_patient_id()
        print(f"✅ Generated patient ID: {patient_id}")
        
        # Test BMI calculation
        bmi = calculate_bmi(70, 1.75)
        print(f"✅ BMI calculation: 70kg / 1.75m = {bmi}")
        
        # Test CNIC formatting
        formatted = format_cnic("1234512345671")
        print(f"✅ CNIC formatting: 1234512345671 → {formatted}")
        
        return True
    except Exception as e:
        print(f"❌ Utility test failed: {e}")
        return False


def test_fastapi():
    """Test FastAPI application"""
    print("\n🧪 Testing FastAPI application...")
    
    try:
        from backend_core.backend import app
        print("✅ FastAPI app imported successfully")
        print(f"   App title: {app.title}")
        print(f"   App version: {app.version}")
        return True
    except Exception as e:
        print(f"❌ Failed to import FastAPI app: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("HealthLink360 Backend Core - Setup Verification")
    print("=" * 60)
    print()
    
    results = []
    
    # Run tests
    results.append(("Module Imports", test_imports()))
    results.append(("Utility Functions", test_utilities()))
    results.append(("FastAPI Application", test_fastapi()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All tests passed! Backend Core is ready.")
        print()
        print("Next steps:")
        print("1. Start the backend: ./scripts/start_backend_core.sh")
        print("2. Visit API docs: http://localhost:8000/docs")
        print("3. Install frontend dependencies: cd frontend && npm install")
        print("4. Start frontend: npm start")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
