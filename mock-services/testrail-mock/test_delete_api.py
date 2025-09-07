#!/usr/bin/env python3
"""
Simple test script for TestRail Mock Delete APIs
Tests both single delete and bulk delete functionality
"""

import requests
import json
import sys

BASE_URL = "http://localhost:4002"
HEADERS = {
    "Authorization": "Bearer test-token",
    "Content-Type": "application/json"
}

def test_health():
    """Test if service is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Service is healthy")
            return True
        else:
            print(f"❌ Service health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to service: {e}")
        return False

def create_test_case(section_id=1, title="Test Case for Deletion"):
    """Create a test case for testing deletion"""
    payload = {
        "title": title,
        "template_id": 1,
        "type_id": 1,
        "priority_id": 2,
        "estimate": "5m",
        "custom_steps": "1. Test step\n2. Verify result"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v2/cases/{section_id}",
            headers=HEADERS,
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            case_data = response.json()
            case_id = case_data.get("id")
            print(f"✅ Created test case ID: {case_id}")
            return case_id
        else:
            print(f"❌ Failed to create test case: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating test case: {e}")
        return None

def test_single_delete(case_id):
    """Test single case deletion"""
    print(f"\n🧪 Testing single delete for case ID: {case_id}")
    
    try:
        response = requests.delete(
            f"{BASE_URL}/api/v2/case/{case_id}",
            headers=HEADERS,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Single delete successful: {result.get('message')}")
            return True
        else:
            print(f"❌ Single delete failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during single delete: {e}")
        return False

def test_bulk_delete(case_ids):
    """Test bulk case deletion"""
    print(f"\n🧪 Testing bulk delete for case IDs: {case_ids}")
    
    payload = {
        "case_ids": case_ids
    }
    
    try:
        response = requests.delete(
            f"{BASE_URL}/api/v2/cases/bulk",
            headers=HEADERS,
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Bulk delete successful: {result.get('message')}")
            print(f"   Deleted: {result.get('deleted_case_ids')}")
            print(f"   Not found: {result.get('not_found_case_ids')}")
            if result.get('errors'):
                print(f"   Errors: {result.get('errors')}")
            return True
        else:
            print(f"❌ Bulk delete failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during bulk delete: {e}")
        return False

def test_delete_nonexistent():
    """Test deleting non-existent case"""
    print(f"\n🧪 Testing delete of non-existent case (ID: 99999)")
    
    try:
        response = requests.delete(
            f"{BASE_URL}/api/v2/case/99999",
            headers=HEADERS,
            timeout=5
        )
        
        if response.status_code == 404:
            print("✅ Correctly returned 404 for non-existent case")
            return True
        else:
            print(f"❌ Expected 404, got: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing non-existent case: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing TestRail Mock Delete APIs")
    print("=" * 50)
    
    # Check if service is running
    if not test_health():
        print("\n❌ Service is not running. Please start the TestRail mock service first.")
        print("Run: cd mock-services/testrail-mock && ./start.sh")
        sys.exit(1)
    
    # Test single delete
    print("\n📋 Testing Single Delete API")
    case_id = create_test_case(title="Single Delete Test Case")
    if case_id:
        test_single_delete(case_id)
    
    # Test bulk delete
    print("\n📋 Testing Bulk Delete API")
    case_ids = []
    for i in range(3):
        case_id = create_test_case(title=f"Bulk Delete Test Case {i+1}")
        if case_id:
            case_ids.append(case_id)
    
    if case_ids:
        # Add a non-existent ID to test mixed results
        case_ids.append(88888)
        test_bulk_delete(case_ids)
    
    # Test error handling
    print("\n📋 Testing Error Handling")
    test_delete_nonexistent()
    
    print("\n🎉 Delete API tests completed!")
    print("\n💡 You can also test via Swagger UI at: http://localhost:4002/docs")

if __name__ == "__main__":
    main()
