#!/usr/bin/env python3
"""
Simple script to test if we can access the Flask test endpoint
"""
import requests
import time

def test_flask_endpoint():
    try:
        print("🧪 Testing Flask journal data endpoint...")
        response = requests.get('http://localhost:5000/api/test_journal_data', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Flask app responded successfully!")
            print(f"📊 Response: {data}")
            
            if data.get('success'):
                print(f"✅ Total signals: {data.get('total_signals')}")
                print(f"✅ Wins: {data.get('wins')}")
                print(f"✅ Signal count: {data.get('signals_count')}")
                return True
            else:
                print(f"❌ API error: {data.get('error')}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask app - is it running on localhost:5000?")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_flask_endpoint()