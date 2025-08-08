#!/usr/bin/env python3
"""
Comprehensive test agent for BFI Signals Dashboard
Tests all major functionality and reports issues
"""

import requests
import json
import sys
import time
from datetime import datetime

class DashboardTestAgent:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, status, message="", data=None):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "data": data
        }
        self.test_results.append(result)
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {message}")
        
    def test_endpoint(self, endpoint, method="GET", data=None, expected_status=200):
        """Generic endpoint test"""
        try:
            if method == "GET":
                response = self.session.get(f"{self.base_url}{endpoint}")
            elif method == "POST":
                response = self.session.post(f"{self.base_url}{endpoint}", json=data)
            else:
                return False, f"Unsupported method: {method}"
                
            if response.status_code == expected_status:
                try:
                    json_data = response.json()
                    return True, json_data
                except:
                    return True, response.text
            else:
                return False, f"Status {response.status_code}: {response.text}"
                
        except Exception as e:
            return False, str(e)
    
    def test_basic_endpoints(self):
        """Test basic API endpoints"""
        endpoints = [
            ("/api/status", "GET"),
            ("/api/dashboard_data", "GET"),
            ("/api/live_market_data", "GET"), 
            ("/api/market_data", "GET"),
            ("/api/live_prices", "GET"),
            ("/api/auto_generation_status", "GET"),
            ("/api/market_timer", "GET"),
        ]
        
        for endpoint, method in endpoints:
            success, result = self.test_endpoint(endpoint, method)
            if success:
                self.log_test(f"Endpoint {endpoint}", "PASS", "Response received successfully")
            else:
                self.log_test(f"Endpoint {endpoint}", "FAIL", result)
    
    def test_journal_functionality(self):
        """Test journal API endpoints"""
        endpoints = [
            ("/journal/api/statistics", "GET"),
            ("/journal/api/entries", "GET"),
        ]
        
        for endpoint, method in endpoints:
            success, result = self.test_endpoint(endpoint, method)
            if success:
                self.log_test(f"Journal {endpoint}", "PASS", "Journal endpoint working")
            else:
                self.log_test(f"Journal {endpoint}", "FAIL", result)
    
    def test_discord_integration(self):
        """Test Discord connection"""
        success, result = self.test_endpoint("/api/test_discord_connection", "POST", {"test": True})
        if success:
            if isinstance(result, dict) and result.get("success"):
                self.log_test("Discord Integration", "PASS", "Discord connection successful")
            else:
                self.log_test("Discord Integration", "WARN", "Discord response unexpected")
        else:
            self.log_test("Discord Integration", "FAIL", result)
    
    def test_auth_protected_endpoints(self):
        """Test endpoints that require authentication"""
        auth_endpoints = [
            "/api/signals/today",
            "/api/signals/stats", 
            "/api/signals/week",
        ]
        
        for endpoint in auth_endpoints:
            success, result = self.test_endpoint(endpoint)
            if not success:
                if "login" in str(result).lower() or "redirect" in str(result).lower():
                    self.log_test(f"Auth Protection {endpoint}", "PASS", "Properly redirecting to login")
                else:
                    self.log_test(f"Auth Protection {endpoint}", "FAIL", result)
            else:
                self.log_test(f"Auth Protection {endpoint}", "WARN", "Endpoint accessible without auth")
    
    def test_market_data_freshness(self):
        """Test if market data is fresh and valid"""
        success, result = self.test_endpoint("/api/live_prices")
        if success and isinstance(result, dict):
            if "timestamp" in result:
                self.log_test("Market Data Freshness", "PASS", "Market data has timestamp")
            else:
                self.log_test("Market Data Freshness", "WARN", "No timestamp in market data")
                
            # Check if we have expected market data
            expected_symbols = ["dow", "nasdaq", "gold"]
            missing_symbols = []
            for symbol in expected_symbols:
                if symbol not in result:
                    missing_symbols.append(symbol)
            
            if not missing_symbols:
                self.log_test("Market Data Completeness", "PASS", "All expected symbols present")
            else:
                self.log_test("Market Data Completeness", "WARN", f"Missing symbols: {missing_symbols}")
        else:
            self.log_test("Market Data Freshness", "FAIL", "Could not retrieve market data")
    
    def test_performance_endpoints(self):
        """Test performance-related endpoints"""
        start_time = time.time()
        success, result = self.test_endpoint("/api/dashboard_data")
        end_time = time.time()
        
        response_time = end_time - start_time
        if success:
            if response_time < 2.0:
                self.log_test("Dashboard Performance", "PASS", f"Response time: {response_time:.2f}s")
            else:
                self.log_test("Dashboard Performance", "WARN", f"Slow response: {response_time:.2f}s")
        else:
            self.log_test("Dashboard Performance", "FAIL", "Dashboard data endpoint failed")
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting comprehensive dashboard tests...")
        print("=" * 60)
        
        self.test_basic_endpoints()
        self.test_journal_functionality() 
        self.test_discord_integration()
        self.test_auth_protected_endpoints()
        self.test_market_data_freshness()
        self.test_performance_endpoints()
        
        # Summary
        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        warnings = len([r for r in self.test_results if r["status"] == "WARN"])
        
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"Total Tests: {len(self.test_results)}")
        
        if failed > 0:
            print(f"\n🔥 FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"   ❌ {result['test']}: {result['message']}")
        
        if warnings > 0:
            print(f"\n⚠️  WARNINGS:")
            for result in self.test_results:
                if result["status"] == "WARN":
                    print(f"   ⚠️  {result['test']}: {result['message']}")
        
        return self.test_results

if __name__ == "__main__":
    agent = DashboardTestAgent()
    results = agent.run_all_tests()
    
    # Save results to file
    with open("dashboard_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Exit with proper code
    failed_count = len([r for r in results if r["status"] == "FAIL"])
    sys.exit(1 if failed_count > 0 else 0)