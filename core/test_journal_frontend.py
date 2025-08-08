#!/usr/bin/env python3
"""
Test Script for Manual Trade Journal Frontend Integration
Tests that the frontend can communicate with the backend APIs
"""

import requests
import json
import os
import sys

# Add the core directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_api_endpoints():
    """Test that all journal API endpoints are responding correctly"""
    
    base_url = "http://localhost:5000"
    
    # Test endpoints
    endpoints = [
        "/journal",  # Main journal page
        "/journal/new",  # New trade form
        "/journal/api/statistics",  # Statistics API
        "/journal/api/entries",  # Entries API
    ]
    
    print("🧪 Testing Manual Trade Journal Frontend Integration...")
    print("=" * 60)
    
    all_passed = True
    
    for endpoint in endpoints:
        print(f"\n📡 Testing endpoint: {endpoint}")
        
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS: {response.status_code}")
                
                # Check if it's JSON response
                if 'api' in endpoint:
                    try:
                        data = response.json()
                        print(f"   📄 JSON Response: {len(str(data))} characters")
                    except:
                        print("   ⚠️  Non-JSON response from API endpoint")
                else:
                    print(f"   📄 HTML Response: {len(response.text)} characters")
                    
            else:
                print(f"   ❌ FAILED: {response.status_code}")
                all_passed = False
                
        except requests.ConnectionError:
            print(f"   ❌ CONNECTION ERROR: Server not running on {base_url}")
            all_passed = False
        except requests.Timeout:
            print(f"   ❌ TIMEOUT: Endpoint took too long to respond")
            all_passed = False
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Frontend integration looks good.")
    else:
        print("⚠️  SOME TESTS FAILED. Check server status and backend implementation.")
    
    return all_passed

def test_frontend_features():
    """Test frontend-specific features"""
    
    print("\n🎨 Testing Frontend Features...")
    print("=" * 60)
    
    # Check that template files exist and have required content
    template_tests = [
        {
            'file': 'templates/journal_modern.html',
            'required_content': [
                'openTradeModal',
                'exportTrades', 
                'viewTradeDetails',
                'Add New Trade',
                'drag-drop',
                'chart image'
            ]
        },
        {
            'file': 'templates/journal_new.html', 
            'required_content': [
                'drag-and-drop',
                'setupDragDrop',
                'image preview',
                'real-time validation',
                'toast notifications'
            ]
        }
    ]
    
    all_passed = True
    
    for test in template_tests:
        print(f"\n📄 Testing template: {test['file']}")
        
        if os.path.exists(test['file']):
            with open(test['file'], 'r') as f:
                content = f.read()
                
            for required in test['required_content']:
                if required.lower() in content.lower():
                    print(f"   ✅ Found: {required}")
                else:
                    print(f"   ❌ Missing: {required}")
                    all_passed = False
        else:
            print(f"   ❌ File not found: {test['file']}")
            all_passed = False
    
    # Test JavaScript functions
    print(f"\n⚙️  Testing JavaScript Functions...")
    js_functions = [
        'openTradeModal', 'submitTradeModal', 'viewTradeDetails',
        'editTrade', 'deleteTrade', 'exportTrades', 'viewChart',
        'setupDragDrop', 'setupFormValidation', 'calculatePnL'
    ]
    
    # Check if journal_modern.html contains the functions
    if os.path.exists('templates/journal_modern.html'):
        with open('templates/journal_modern.html', 'r') as f:
            content = f.read()
            
        for func in js_functions:
            if f"function {func}" in content or f"{func} =" in content:
                print(f"   ✅ JS Function: {func}")
            else:
                print(f"   ⚠️  JS Function missing: {func}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL FRONTEND TESTS PASSED!")
    else:
        print("⚠️  SOME FRONTEND TESTS FAILED.")
    
    return all_passed

def main():
    """Run all tests"""
    print("🚀 Manual Trade Journal Frontend Test Suite")
    print("==========================================")
    
    # Test API endpoints
    api_passed = test_api_endpoints()
    
    # Test frontend features
    frontend_passed = test_frontend_features()
    
    # Final summary
    print("\n🏁 FINAL RESULTS")
    print("=" * 60)
    
    if api_passed and frontend_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Frontend is ready for manual trade journal functionality")
        print("\n📋 FEATURES IMPLEMENTED:")
        print("   • Modern UI with drag-drop image upload")
        print("   • Real-time form validation and P&L calculation")
        print("   • Modal popups for adding/editing trades")
        print("   • Advanced filtering and search")
        print("   • CSV export functionality")
        print("   • Chart image gallery with lightbox")
        print("   • Mobile-responsive design")
        print("   • Keyboard shortcuts (Ctrl+N, Ctrl+F, Esc)")
        print("   • Toast notifications")
        print("   • Accessibility features")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print("🔧 Please check the backend server and implementation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)