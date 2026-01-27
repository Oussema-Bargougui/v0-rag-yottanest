"""
Quick test script to verify API endpoints are working
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health endpoint: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
        return False

def test_docs_endpoint():
    """Test the Swagger docs endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print(f"✅ Docs endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"   Swagger UI is accessible!")
        return True
    except Exception as e:
        print(f"❌ Docs endpoint failed: {e}")
        return False

def test_openapi_spec():
    """Test the OpenAPI JSON spec"""
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        print(f"✅ OpenAPI spec: {response.status_code}")
        if response.status_code == 200:
            spec = response.json()
            print(f"   Available endpoints: {len(spec.get('paths', {}))}")
            for path in spec.get('paths', {}).keys():
                print(f"   - {path}")
        return True
    except Exception as e:
        print(f"❌ OpenAPI spec failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing API Endpoints")
    print("=" * 60)
    
    print("\n1. Testing health endpoint...")
    test_health_endpoint()
    
    print("\n2. Testing OpenAPI spec...")
    test_openapi_spec()
    
    print("\n3. Testing Swagger docs...")
    test_docs_endpoint()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)