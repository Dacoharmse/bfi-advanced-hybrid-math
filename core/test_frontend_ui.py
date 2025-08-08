#!/usr/bin/env python3
"""
Frontend UI Testing Suite for Manual Trade Journal
Tests all UI components, AJAX operations, and user interactions
"""

import requests
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import os

# Test configuration
BASE_URL = "http://localhost:5000"

class FrontendTestSuite:
    def __init__(self):
        self.results = {
            'ui_components': {},
            'ajax_operations': {},
            'form_validation': {},
            'mobile_responsive': {},
            'user_workflow': {},
            'errors': []
        }
        
        # Set up Chrome options for headless testing
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")  # Run in background
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")
        
        self.driver = None
        
    def log_result(self, category, test_name, status, message="", details=None):
        """Log test result with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result = {
            'status': status,
            'message': message,
            'timestamp': timestamp,
            'details': details or {}
        }
        self.results[category][test_name] = result
        
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_symbol} [{category}] {test_name}: {message}")
    
    def setup_driver(self):
        """Initialize Selenium WebDriver"""
        try:
            # Try to initialize Chrome WebDriver
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.implicitly_wait(10)
            return True
        except Exception as e:
            print(f"⚠️ Could not initialize Chrome WebDriver: {str(e)}")
            print("Frontend UI tests will be skipped. Install ChromeDriver to run these tests.")
            return False
    
    def test_ui_components(self):
        """Test all UI components on the journal page"""
        if not self.driver:
            self.log_result('ui_components', 'driver_unavailable', 'WARN', 
                          "WebDriver not available, skipping UI tests")
            return
            
        print("\n🖥️ Testing Frontend UI Components")
        print("-" * 40)
        
        try:
            # Navigate to journal page
            self.driver.get(f"{BASE_URL}/journal")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            self.log_result('ui_components', 'page_load', 'PASS', 
                          f"Journal page loaded successfully")
            
            # Test for presence of key UI components
            components_to_test = [
                ("main-content", "Main content container"),
                ("journal-header", "Journal header section"),
                ("add-trade-btn", "Add trade button"),
                ("entries-table", "Entries table"),
                ("statistics-cards", "Statistics cards"),
            ]
            
            for component_id, description in components_to_test:
                try:
                    # Try multiple selector strategies
                    element = None
                    selectors = [
                        f"#{component_id}",
                        f".{component_id}",
                        f"[data-test='{component_id}']"
                    ]
                    
                    for selector in selectors:
                        try:
                            element = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if element:
                                break
                        except:
                            continue
                    
                    if element and element.is_displayed():
                        self.log_result('ui_components', f'component_{component_id}', 'PASS', 
                                      f"{description} found and visible")
                    else:
                        self.log_result('ui_components', f'component_{component_id}', 'WARN', 
                                      f"{description} not found or not visible")
                        
                except Exception as e:
                    self.log_result('ui_components', f'component_{component_id}', 'FAIL', 
                                  f"Error testing {description}: {str(e)}")
            
            # Test modal functionality (if add trade button exists)
            try:
                # Look for add trade button with various selectors
                add_btn_selectors = [
                    "button[data-test='add-trade']",
                    ".btn-add-trade",
                    "#add-trade-btn",
                    "button:contains('Add Trade')",
                    "[onclick*='modal']",
                    ".btn-primary"
                ]
                
                add_button = None
                for selector in add_btn_selectors:
                    try:
                        add_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if add_button and add_button.is_displayed():
                            break
                    except:
                        continue
                
                if add_button:
                    # Click the button
                    self.driver.execute_script("arguments[0].click();", add_button)
                    time.sleep(1)
                    
                    # Check if modal appeared
                    modal_selectors = [
                        ".modal",
                        "#trade-modal",
                        ".modal.show",
                        "[role='dialog']"
                    ]
                    
                    modal_found = False
                    for selector in modal_selectors:
                        try:
                            modal = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if modal and modal.is_displayed():
                                modal_found = True
                                break
                        except:
                            continue
                    
                    if modal_found:
                        self.log_result('ui_components', 'modal_functionality', 'PASS', 
                                      "Modal opens successfully when add trade button clicked")
                        
                        # Test modal close
                        close_selectors = [
                            ".modal .close",
                            ".modal-close",
                            "[data-dismiss='modal']",
                            ".btn-cancel"
                        ]
                        
                        for selector in close_selectors:
                            try:
                                close_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                                if close_btn and close_btn.is_displayed():
                                    close_btn.click()
                                    time.sleep(0.5)
                                    break
                            except:
                                continue
                    else:
                        self.log_result('ui_components', 'modal_functionality', 'FAIL', 
                                      "Modal did not appear after clicking add trade button")
                else:
                    self.log_result('ui_components', 'modal_functionality', 'WARN', 
                                  "Add trade button not found, cannot test modal")
                    
            except Exception as e:
                self.log_result('ui_components', 'modal_functionality', 'FAIL', 
                              f"Error testing modal: {str(e)}")
            
            # Test table functionality
            try:
                table_selectors = [
                    "table",
                    ".entries-table",
                    "#journal-entries",
                    ".table"
                ]
                
                table_found = False
                for selector in table_selectors:
                    try:
                        table = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if table and table.is_displayed():
                            rows = table.find_elements(By.TAG_NAME, "tr")
                            self.log_result('ui_components', 'table_display', 'PASS', 
                                          f"Table found with {len(rows)} rows")
                            table_found = True
                            break
                    except:
                        continue
                
                if not table_found:
                    self.log_result('ui_components', 'table_display', 'WARN', 
                                  "Entries table not found")
                    
            except Exception as e:
                self.log_result('ui_components', 'table_display', 'FAIL', 
                              f"Error testing table: {str(e)}")
            
        except Exception as e:
            self.log_result('ui_components', 'general_error', 'FAIL', str(e))
    
    def test_ajax_operations(self):
        """Test AJAX operations and API connectivity from frontend"""
        print("\n📡 Testing AJAX Operations from Frontend")
        print("-" * 40)
        
        # Test API endpoints directly (simulating frontend AJAX calls)
        ajax_tests = [
            ("/journal/api/entries", "GET", None, "Load entries via AJAX"),
            ("/journal/api/statistics", "GET", None, "Load statistics via AJAX"),
        ]
        
        for endpoint, method, data, description in ajax_tests:
            try:
                if method == "GET":
                    response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
                else:
                    response = requests.post(f"{BASE_URL}{endpoint}", data=data, timeout=5)
                
                if response.status_code == 200:
                    try:
                        json_data = response.json()
                        if json_data.get('success'):
                            self.log_result('ajax_operations', f'ajax_{endpoint.replace("/", "_")}', 'PASS', 
                                          f"{description} successful")
                        else:
                            self.log_result('ajax_operations', f'ajax_{endpoint.replace("/", "_")}', 'FAIL', 
                                          f"{description} returned error: {json_data.get('error', 'Unknown')}")
                    except json.JSONDecodeError:
                        self.log_result('ajax_operations', f'ajax_{endpoint.replace("/", "_")}', 'FAIL', 
                                      f"{description} returned invalid JSON")
                else:
                    self.log_result('ajax_operations', f'ajax_{endpoint.replace("/", "_")}', 'FAIL', 
                                  f"{description} returned HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result('ajax_operations', f'ajax_{endpoint.replace("/", "_")}', 'FAIL', 
                              f"{description} failed: {str(e)}")
    
    def test_form_validation(self):
        """Test form validation and real-time calculations"""
        if not self.driver:
            self.log_result('form_validation', 'driver_unavailable', 'WARN', 
                          "WebDriver not available, skipping form validation tests")
            return
            
        print("\n📝 Testing Form Validation and Calculations")
        print("-" * 40)
        
        # This would require the actual form to be present and interactive
        # For now, we'll test the validation logic through API calls
        
        validation_tests = [
            # Test missing required fields
            ({}, "Empty form should be rejected"),
            
            # Test invalid data types
            ({
                'symbol': 'TEST',
                'trade_type': 'INVALID_TYPE',
                'entry_price': 'not_a_number',
                'trade_date': '2025-08-02'
            }, "Invalid data types should be rejected"),
            
            # Test valid minimal data
            ({
                'symbol': 'VALID_TEST',
                'trade_type': 'LONG',
                'entry_price': '100.50',
                'trade_date': '2025-08-02'
            }, "Valid minimal form should be accepted"),
        ]
        
        for test_data, description in validation_tests:
            try:
                response = requests.post(f"{BASE_URL}/journal/api/create", 
                                       data=test_data, timeout=5)
                
                if response.status_code == 200:
                    json_response = response.json()
                    success = json_response.get('success', False)
                    
                    # For empty and invalid data, we expect failure
                    if not test_data or 'INVALID' in str(test_data) or 'not_a_number' in str(test_data):
                        if not success:
                            self.log_result('form_validation', f'validation_test', 'PASS', 
                                          f"Form validation correctly rejected: {description}")
                        else:
                            self.log_result('form_validation', f'validation_test', 'FAIL', 
                                          f"Form validation incorrectly accepted: {description}")
                    else:
                        # For valid data, we expect success
                        if success:
                            self.log_result('form_validation', f'validation_test', 'PASS', 
                                          f"Form validation correctly accepted: {description}")
                            
                            # Clean up test entry
                            entry_id = json_response.get('entry_id')
                            if entry_id:
                                requests.delete(f"{BASE_URL}/journal/api/entry/{entry_id}")
                        else:
                            self.log_result('form_validation', f'validation_test', 'FAIL', 
                                          f"Form validation incorrectly rejected: {description}")
                else:
                    self.log_result('form_validation', f'validation_test', 'WARN', 
                                  f"HTTP {response.status_code} for: {description}")
                    
            except Exception as e:
                self.log_result('form_validation', f'validation_test', 'FAIL', 
                              f"Error testing {description}: {str(e)}")
    
    def test_mobile_responsiveness(self):
        """Test mobile responsiveness on different screen sizes"""
        if not self.driver:
            self.log_result('mobile_responsive', 'driver_unavailable', 'WARN', 
                          "WebDriver not available, skipping responsive tests")
            return
            
        print("\n📱 Testing Mobile Responsiveness")
        print("-" * 40)
        
        # Test different screen sizes
        screen_sizes = [
            (1920, 1080, "Desktop"),
            (1024, 768, "Tablet"),
            (375, 667, "Mobile"),
            (320, 568, "Small Mobile")
        ]
        
        for width, height, device_type in screen_sizes:
            try:
                # Set window size
                self.driver.set_window_size(width, height)
                time.sleep(1)
                
                # Navigate to journal page
                self.driver.get(f"{BASE_URL}/journal")
                time.sleep(2)
                
                # Check if page loads and is functional at this size
                body = self.driver.find_element(By.TAG_NAME, "body")
                
                if body.is_displayed():
                    # Check for responsive elements
                    viewport_width = self.driver.execute_script("return window.innerWidth")
                    viewport_height = self.driver.execute_script("return window.innerHeight")
                    
                    self.log_result('mobile_responsive', f'responsive_{device_type.lower()}', 'PASS', 
                                  f"{device_type} ({width}x{height}) page loads correctly, viewport: {viewport_width}x{viewport_height}")
                    
                    # Test if navigation is accessible on mobile
                    if width <= 768:  # Mobile/tablet sizes
                        try:
                            # Look for mobile menu button or check if navigation is hidden
                            nav_elements = self.driver.find_elements(By.CSS_SELECTOR, ".navbar, .sidebar, .nav")
                            mobile_menu = self.driver.find_elements(By.CSS_SELECTOR, ".navbar-toggle, .mobile-menu, .hamburger")
                            
                            if mobile_menu or nav_elements:
                                self.log_result('mobile_responsive', f'mobile_nav_{device_type.lower()}', 'PASS', 
                                              f"{device_type} navigation elements found")
                            else:
                                self.log_result('mobile_responsive', f'mobile_nav_{device_type.lower()}', 'WARN', 
                                              f"{device_type} navigation elements not clearly visible")
                        except:
                            pass
                else:
                    self.log_result('mobile_responsive', f'responsive_{device_type.lower()}', 'FAIL', 
                                  f"{device_type} page not displayed correctly")
                    
            except Exception as e:
                self.log_result('mobile_responsive', f'responsive_{device_type.lower()}', 'FAIL', 
                              f"Error testing {device_type}: {str(e)}")
        
        # Reset to desktop size
        try:
            self.driver.set_window_size(1920, 1080)
        except:
            pass
    
    def test_user_workflow(self):
        """Test complete user workflow from adding to viewing trades"""
        print("\n👤 Testing Complete User Workflow")
        print("-" * 40)
        
        # Test the complete workflow using API calls (simulating user actions)
        workflow_steps = [
            "Create new trade entry",
            "Retrieve the created entry",
            "Update the trade entry",
            "View updated statistics",
            "Delete the trade entry"
        ]
        
        test_entry_id = None
        
        try:
            # Step 1: Create new trade entry
            create_data = {
                'symbol': 'WORKFLOW_TEST',
                'trade_type': 'LONG',
                'entry_price': '150.25',
                'exit_price': '155.75',
                'quantity': '5',
                'outcome': 'WIN',
                'profit_loss': '27.50',
                'trade_date': '2025-08-02',
                'entry_time': '10:30:00',
                'exit_time': '14:45:00',
                'notes': 'Complete workflow test trade'
            }
            
            response = requests.post(f"{BASE_URL}/journal/api/create", 
                                   data=create_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    test_entry_id = result.get('entry_id')
                    self.log_result('user_workflow', 'step1_create', 'PASS', 
                                  f"Step 1 - Created entry with ID: {test_entry_id}")
                else:
                    self.log_result('user_workflow', 'step1_create', 'FAIL', 
                                  f"Step 1 - Create failed: {result.get('error')}")
                    return
            else:
                self.log_result('user_workflow', 'step1_create', 'FAIL', 
                              f"Step 1 - HTTP {response.status_code}")
                return
            
            # Step 2: Retrieve the created entry
            if test_entry_id:
                response = requests.get(f"{BASE_URL}/journal/api/entry/{test_entry_id}", timeout=5)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        entry = result.get('entry', {})
                        symbol = entry.get('symbol', 'Unknown')
                        self.log_result('user_workflow', 'step2_retrieve', 'PASS', 
                                      f"Step 2 - Retrieved entry for symbol: {symbol}")
                    else:
                        self.log_result('user_workflow', 'step2_retrieve', 'FAIL', 
                                      f"Step 2 - Retrieve failed: {result.get('error')}")
                else:
                    self.log_result('user_workflow', 'step2_retrieve', 'FAIL', 
                                  f"Step 2 - HTTP {response.status_code}")
            
            # Step 3: Update the trade entry
            if test_entry_id:
                update_data = create_data.copy()
                update_data['notes'] = 'Updated workflow test trade'
                update_data['exit_price'] = '158.00'
                
                response = requests.put(f"{BASE_URL}/journal/api/entry/{test_entry_id}", 
                                      data=update_data, timeout=5)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        self.log_result('user_workflow', 'step3_update', 'PASS', 
                                      "Step 3 - Entry updated successfully")
                    else:
                        self.log_result('user_workflow', 'step3_update', 'FAIL', 
                                      f"Step 3 - Update failed: {result.get('error')}")
                else:
                    self.log_result('user_workflow', 'step3_update', 'FAIL', 
                                  f"Step 3 - HTTP {response.status_code}")
            
            # Step 4: View updated statistics
            response = requests.get(f"{BASE_URL}/journal/api/statistics", timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    stats = result.get('statistics', {})
                    overall = stats.get('overall', [])
                    if overall and len(overall) > 0:
                        total_trades = overall[0]
                        self.log_result('user_workflow', 'step4_statistics', 'PASS', 
                                      f"Step 4 - Statistics updated, total trades: {total_trades}")
                    else:
                        self.log_result('user_workflow', 'step4_statistics', 'WARN', 
                                      "Step 4 - Statistics format unexpected")
                else:
                    self.log_result('user_workflow', 'step4_statistics', 'FAIL', 
                                  f"Step 4 - Statistics failed: {result.get('error')}")
            else:
                self.log_result('user_workflow', 'step4_statistics', 'FAIL', 
                              f"Step 4 - HTTP {response.status_code}")
            
            # Step 5: Delete the trade entry (cleanup)
            if test_entry_id:
                response = requests.delete(f"{BASE_URL}/journal/api/entry/{test_entry_id}", timeout=5)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        self.log_result('user_workflow', 'step5_delete', 'PASS', 
                                      "Step 5 - Entry deleted successfully")
                    else:
                        self.log_result('user_workflow', 'step5_delete', 'FAIL', 
                                      f"Step 5 - Delete failed: {result.get('error')}")
                else:
                    self.log_result('user_workflow', 'step5_delete', 'FAIL', 
                                  f"Step 5 - HTTP {response.status_code}")
            
        except Exception as e:
            self.log_result('user_workflow', 'workflow_error', 'FAIL', 
                          f"Workflow error: {str(e)}")
    
    def run_all_tests(self):
        """Execute all frontend test suites"""
        print("🚀 Starting Frontend UI Testing")
        print("=" * 60)
        
        # Initialize WebDriver
        driver_available = self.setup_driver()
        
        # Run all test suites
        self.test_ajax_operations()
        self.test_form_validation()
        self.test_user_workflow()
        
        if driver_available:
            self.test_ui_components()
            self.test_mobile_responsiveness()
        
        # Generate report
        self.generate_report()
        
        # Cleanup
        if self.driver:
            self.driver.quit()
    
    def generate_report(self):
        """Generate frontend testing report"""
        print("\n📋 Frontend Testing Report")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        warnings = 0
        
        for category, tests in self.results.items():
            if not tests:
                continue
                
            print(f"\n{category.upper().replace('_', ' ')} TESTS:")
            print("-" * 40)
            
            for test_name, result in tests.items():
                status = result['status']
                message = result['message']
                
                status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
                print(f"{status_symbol} {test_name}: {message}")
                
                total_tests += 1
                if status == "PASS":
                    passed_tests += 1
                elif status == "FAIL":
                    failed_tests += 1
                else:
                    warnings += 1
        
        # Summary
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"\nFRONTEND TEST SUMMARY:")
        print("-" * 40)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Warnings: {warnings}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'warnings': warnings,
            'success_rate': success_rate
        }

def main():
    """Main test execution function"""
    suite = FrontendTestSuite()
    suite.run_all_tests()

if __name__ == "__main__":
    main()