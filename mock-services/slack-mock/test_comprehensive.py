#!/usr/bin/env python3
"""Comprehensive test for Slack Mock Service."""

import sys
import time
import requests
import json

def test_service():
    """Test all endpoints of the Slack service."""
    base_url = "http://127.0.0.1:4003"
    headers = {"Authorization": "Bearer test-token"}
    
    print("🧪 Testing Slack Mock Service...")
    
    # Test 1: Health Check
    print("\n1️⃣ Testing health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: UI Home Page
    print("\n2️⃣ Testing UI home page...")
    try:
        response = requests.get(f"{base_url}/ui/", timeout=5)
        if response.status_code == 200:
            print("✅ UI home page loaded")
        else:
            print(f"❌ UI home page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ UI home page error: {e}")
        return False
    
    # Test 3: Post Message
    print("\n3️⃣ Testing post message...")
    try:
        payload = {
            "channel": "qa-reports",
            "text": "Test message from comprehensive test",
            "username": "TestBot"
        }
        response = requests.post(
            f"{base_url}/api/chat.postMessage",
            json=payload,
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print("✅ Message posted successfully")
                message_ts = data.get("ts")
            else:
                print(f"❌ Message post failed: {data}")
                return False
        else:
            print(f"❌ Message post failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Message post error: {e}")
        return False
    
    # Test 4: Get Conversation History
    print("\n4️⃣ Testing conversation history...")
    try:
        response = requests.get(
            f"{base_url}/api/conversations.history?channel=qa-reports&limit=10",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and "messages" in data:
                print(f"✅ Got {len(data['messages'])} messages")
            else:
                print(f"❌ Conversation history failed: {data}")
                return False
        else:
            print(f"❌ Conversation history failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Conversation history error: {e}")
        return False
    
    # Test 5: Channel UI
    print("\n5️⃣ Testing channel UI...")
    try:
        response = requests.get(f"{base_url}/ui/channel/qa-reports", timeout=5)
        if response.status_code == 200:
            print("✅ Channel UI loaded")
        else:
            print(f"❌ Channel UI failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Channel UI error: {e}")
        return False
    
    # Test 6: API Documentation
    print("\n6️⃣ Testing API docs...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API docs loaded")
        else:
            print(f"❌ API docs failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API docs error: {e}")
        return False
    
    print("\n🎉 All tests passed! Slack Mock Service is working correctly.")
    return True

if __name__ == "__main__":
    success = test_service()
    sys.exit(0 if success else 1)
