#!/usr/bin/env python3
"""
Simple Discord Test Script
Bypasses the problematic discord_post.py file and tests Discord directly
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../.env')

def test_discord_simple():
    """Simple Discord connection test"""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    print("=== BFI Signals Discord Connection Test ===")
    print(f"Webhook URL configured: {bool(webhook_url)}")
    if webhook_url:
        print(f"Webhook URL: {webhook_url[:60]}...")
    
    if not webhook_url:
        print("❌ ERROR: DISCORD_WEBHOOK_URL not found in environment")
        return False
    
    # Test with a simple message
    test_payload = {
        "content": "🔧 **BFI Signals Test** - Dashboard connection working!"
    }
    
    try:
        print("Sending test message to Discord...")
        response = requests.post(
            webhook_url,
            json=test_payload,
            timeout=10
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code in [200, 204]:
            print("✅ SUCCESS: Discord connection working!")
            return True
        else:
            print(f"❌ ERROR: Discord returned status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Network error: {str(e)}")
        return False

if __name__ == "__main__":
    test_discord_simple() 