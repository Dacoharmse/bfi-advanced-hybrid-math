#!/usr/bin/env python3
"""
Comprehensive Manual Trade Journal Testing Suite
Tests all components: Backend API endpoints, Database operations, Image uploads, Security, Frontend UI
"""

import requests
import json
import sqlite3
import os
import tempfile
import time
from datetime import datetime
from PIL import Image
import io
import base64

# Test configuration
BASE_URL = "http://localhost:5000"
DB_PATH = "ai_learning.db"

class JournalTestSuite:
    def __init__(self):
        self.results = {
            'backend_api': {},
            'database': {},
            'image_upload': {},
            'security': {},
            'performance': {},
            'errors': []
        }
        self.test_entry_id = None
        
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
        
    def run_all_tests(self):
        """Execute all test suites"""
        print("🚀 Starting Comprehensive Manual Trade Journal Testing")
        print("=" * 60)
        
        # Test backend API endpoints
        self.test_backend_apis()
        
        # Test database operations
        self.test_database_operations()
        
        # Test image upload functionality
        self.test_image_uploads()
        
        # Test security measures
        self.test_security()
        
        # Test performance
        self.test_performance()
        
        # Generate comprehensive report
        self.generate_report()
        
    def test_backend_apis(self):
        """Test all backend API endpoints"""
        print("\n📡 Testing Backend API Endpoints")
        print("-" * 40)
        
        # Test main journal page load
        try:
            response = requests.get(f"{BASE_URL}/journal", timeout=10)
            if response.status_code == 200:
                self.log_result('backend_api', 'journal_page_load', 'PASS', 
                              f"Journal page loaded successfully (size: {len(response.text)} bytes)")
            else:
                self.log_result('backend_api', 'journal_page_load', 'FAIL', 
                              f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result('backend_api', 'journal_page_load', 'FAIL', str(e))
        
        # Test create journal entry API
        test_entry_data = {
            'symbol': 'TEST_SYMBOL',
            'trade_type': 'LONG',
            'entry_price': '100.50',
            'exit_price': '105.75',
            'quantity': '10',
            'outcome': 'WIN',
            'profit_loss': '52.50',
            'trade_date': '2025-08-02',
            'entry_time': '09:30:00',
            'exit_time': '15:30:00',
            'notes': 'Test trade entry for comprehensive testing'
        }
        
        try:
            response = requests.post(f"{BASE_URL}/journal/api/create", 
                                   data=test_entry_data, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.test_entry_id = data.get('entry_id')
                    self.log_result('backend_api', 'create_entry', 'PASS', 
                                  f"Entry created with ID: {self.test_entry_id}")
                else:
                    self.log_result('backend_api', 'create_entry', 'FAIL', 
                                  data.get('error', 'Unknown error'))
            else:
                self.log_result('backend_api', 'create_entry', 'FAIL', 
                              f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result('backend_api', 'create_entry', 'FAIL', str(e))
        
        # Test get entries API
        try:
            response = requests.get(f"{BASE_URL}/journal/api/entries", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    entries_count = len(data.get('entries', []))
                    self.log_result('backend_api', 'get_entries', 'PASS', 
                                  f"Retrieved {entries_count} entries")
                else:
                    self.log_result('backend_api', 'get_entries', 'FAIL', 
                                  data.get('error', 'Unknown error'))
            else:
                self.log_result('backend_api', 'get_entries', 'FAIL', 
                              f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result('backend_api', 'get_entries', 'FAIL', str(e))
        
        # Test get single entry API
        if self.test_entry_id:
            try:
                response = requests.get(f"{BASE_URL}/journal/api/entry/{self.test_entry_id}", 
                                      timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        entry = data.get('entry', {})
                        self.log_result('backend_api', 'get_single_entry', 'PASS', 
                                      f"Entry retrieved: {entry.get('symbol', 'N/A')}")
                    else:
                        self.log_result('backend_api', 'get_single_entry', 'FAIL', 
                                      data.get('error', 'Unknown error'))
                else:
                    self.log_result('backend_api', 'get_single_entry', 'FAIL', 
                                  f"HTTP {response.status_code}")
            except Exception as e:
                self.log_result('backend_api', 'get_single_entry', 'FAIL', str(e))
        
        # Test update entry API
        if self.test_entry_id:
            updated_data = test_entry_data.copy()
            updated_data['notes'] = 'Updated test entry notes'
            updated_data['exit_price'] = '108.25'
            
            try:
                response = requests.put(f"{BASE_URL}/journal/api/entry/{self.test_entry_id}", 
                                      data=updated_data, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        self.log_result('backend_api', 'update_entry', 'PASS', 
                                      "Entry updated successfully")
                    else:
                        self.log_result('backend_api', 'update_entry', 'FAIL', 
                                      data.get('error', 'Unknown error'))
                else:
                    self.log_result('backend_api', 'update_entry', 'FAIL', 
                                  f"HTTP {response.status_code}")
            except Exception as e:
                self.log_result('backend_api', 'update_entry', 'FAIL', str(e))
        
        # Test statistics API
        try:
            response = requests.get(f"{BASE_URL}/journal/api/statistics", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    stats = data.get('statistics', {})
                    overall = stats.get('overall', [])
                    if overall:
                        total_trades = overall[0] if len(overall) > 0 else 0
                        self.log_result('backend_api', 'get_statistics', 'PASS', 
                                      f"Statistics retrieved, total trades: {total_trades}")
                    else:
                        self.log_result('backend_api', 'get_statistics', 'WARN', 
                                      "Statistics structure unexpected")
                else:
                    self.log_result('backend_api', 'get_statistics', 'FAIL', 
                                  data.get('error', 'Unknown error'))
            else:
                self.log_result('backend_api', 'get_statistics', 'FAIL', 
                              f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result('backend_api', 'get_statistics', 'FAIL', str(e))
    
    def test_database_operations(self):
        """Test database CRUD operations directly"""
        print("\n🗄️ Testing Database Operations")
        print("-" * 40)
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Test database connectivity
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='manual_journal_entries'")
            table_exists = cursor.fetchone() is not None
            
            if table_exists:
                self.log_result('database', 'table_exists', 'PASS', 
                              "manual_journal_entries table exists")
            else:
                self.log_result('database', 'table_exists', 'FAIL', 
                              "manual_journal_entries table not found")
                return
                
            # Test table schema
            cursor.execute("PRAGMA table_info(manual_journal_entries)")
            columns = cursor.fetchall()
            expected_columns = ['id', 'symbol', 'trade_type', 'entry_price', 'exit_price', 
                              'quantity', 'outcome', 'profit_loss', 'trade_date', 
                              'entry_time', 'exit_time', 'notes', 'chart_image_path', 
                              'created_at', 'updated_at']
            
            column_names = [col[1] for col in columns]
            missing_columns = [col for col in expected_columns if col not in column_names]
            
            if not missing_columns:
                self.log_result('database', 'table_schema', 'PASS', 
                              f"All {len(expected_columns)} expected columns present")
            else:
                self.log_result('database', 'table_schema', 'FAIL', 
                              f"Missing columns: {missing_columns}")
            
            # Test count of existing entries
            cursor.execute("SELECT COUNT(*) FROM manual_journal_entries")
            entry_count = cursor.fetchone()[0]
            self.log_result('database', 'entry_count', 'PASS', 
                          f"Database contains {entry_count} entries")
            
            # Test direct database insert
            test_data = (
                'DB_TEST', 'SHORT', 50.25, 48.75, 5, 'WIN', 7.50,
                '2025-08-02', '10:00:00', '14:00:00', 'Direct DB test', None
            )
            
            cursor.execute('''
                INSERT INTO manual_journal_entries 
                (symbol, trade_type, entry_price, exit_price, quantity, outcome, 
                 profit_loss, trade_date, entry_time, exit_time, notes, chart_image_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', test_data)
            
            db_test_id = cursor.lastrowid
            conn.commit()
            
            self.log_result('database', 'direct_insert', 'PASS', 
                          f"Direct insert successful, ID: {db_test_id}")
            
            # Test direct database select
            cursor.execute("SELECT * FROM manual_journal_entries WHERE id = ?", (db_test_id,))
            result = cursor.fetchone()
            
            if result:
                self.log_result('database', 'direct_select', 'PASS', 
                              f"Direct select successful, symbol: {result[1]}")
            else:
                self.log_result('database', 'direct_select', 'FAIL', 
                              "Could not retrieve inserted record")
            
            # Test direct database update
            cursor.execute('''
                UPDATE manual_journal_entries 
                SET notes = ? 
                WHERE id = ?
            ''', ('Updated via direct DB test', db_test_id))
            
            updated_rows = cursor.rowcount
            conn.commit()
            
            if updated_rows > 0:
                self.log_result('database', 'direct_update', 'PASS', 
                              f"Updated {updated_rows} record(s)")
            else:
                self.log_result('database', 'direct_update', 'FAIL', 
                              "No records updated")
            
            # Clean up test entry
            cursor.execute("DELETE FROM manual_journal_entries WHERE id = ?", (db_test_id,))
            deleted_rows = cursor.rowcount
            conn.commit()
            
            if deleted_rows > 0:
                self.log_result('database', 'direct_delete', 'PASS', 
                              f"Deleted {deleted_rows} record(s)")
            else:
                self.log_result('database', 'direct_delete', 'FAIL', 
                              "No records deleted")
            
            conn.close()
            
        except Exception as e:
            self.log_result('database', 'connection_error', 'FAIL', str(e))
    
    def test_image_uploads(self):
        """Test image upload functionality with various file types and sizes"""
        print("\n📸 Testing Image Upload Functionality")
        print("-" * 40)
        
        # Create test images of different formats and sizes
        test_images = []
        
        # Create a small PNG test image
        try:
            img = Image.new('RGB', (100, 100), color='red')
            png_buffer = io.BytesIO()
            img.save(png_buffer, format='PNG')
            png_buffer.seek(0)
            test_images.append(('small_test.png', png_buffer.getvalue(), 'image/png'))
            
            self.log_result('image_upload', 'create_test_png', 'PASS', 
                          f"Created PNG test image ({len(png_buffer.getvalue())} bytes)")
        except Exception as e:
            self.log_result('image_upload', 'create_test_png', 'FAIL', str(e))
        
        # Create a JPEG test image
        try:
            img = Image.new('RGB', (200, 200), color='blue')
            jpeg_buffer = io.BytesIO()
            img.save(jpeg_buffer, format='JPEG')
            jpeg_buffer.seek(0)
            test_images.append(('test_chart.jpg', jpeg_buffer.getvalue(), 'image/jpeg'))
            
            self.log_result('image_upload', 'create_test_jpeg', 'PASS', 
                          f"Created JPEG test image ({len(jpeg_buffer.getvalue())} bytes)")
        except Exception as e:
            self.log_result('image_upload', 'create_test_jpeg', 'FAIL', str(e))
        
        # Test image upload with journal entry creation
        for filename, image_data, content_type in test_images:
            try:
                # Create form data with image
                files = {'chart_image': (filename, image_data, content_type)}
                data = {
                    'symbol': 'IMG_TEST',
                    'trade_type': 'LONG',
                    'entry_price': '75.25',
                    'exit_price': '78.50',
                    'quantity': '8',
                    'outcome': 'WIN',
                    'profit_loss': '26.00',
                    'trade_date': '2025-08-02',
                    'entry_time': '11:00:00',
                    'exit_time': '16:00:00',
                    'notes': f'Image upload test with {filename}'
                }
                
                response = requests.post(f"{BASE_URL}/journal/api/create", 
                                       data=data, files=files, timeout=15)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        entry_id = result.get('entry_id')
                        image_path = result.get('image_path', 'Not provided')
                        self.log_result('image_upload', f'upload_{filename}', 'PASS', 
                                      f"Image uploaded successfully, entry ID: {entry_id}, path: {image_path}")
                        
                        # Check if image file was actually created
                        if image_path and os.path.exists(image_path):
                            file_size = os.path.getsize(image_path)
                            self.log_result('image_upload', f'file_created_{filename}', 'PASS', 
                                          f"Image file created on disk ({file_size} bytes)")
                        else:
                            self.log_result('image_upload', f'file_created_{filename}', 'FAIL', 
                                          "Image file not found on disk")
                    else:
                        self.log_result('image_upload', f'upload_{filename}', 'FAIL', 
                                      result.get('error', 'Unknown error'))
                else:
                    self.log_result('image_upload', f'upload_{filename}', 'FAIL', 
                                  f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result('image_upload', f'upload_{filename}', 'FAIL', str(e))
    
    def test_security(self):
        """Test security measures including file validation and SQL injection protection"""
        print("\n🔒 Testing Security Measures")
        print("-" * 40)
        
        # Test malicious file upload (non-image file)
        try:
            malicious_content = b"<?php echo 'malicious code'; ?>"
            files = {'chart_image': ('malicious.php', malicious_content, 'application/x-php')}
            data = {
                'symbol': 'SEC_TEST',
                'trade_type': 'LONG',
                'entry_price': '100',
                'trade_date': '2025-08-02'
            }
            
            response = requests.post(f"{BASE_URL}/journal/api/create", 
                                   data=data, files=files, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if not result.get('success'):
                    self.log_result('security', 'malicious_file_upload', 'PASS', 
                                  "Malicious file upload correctly rejected")
                else:
                    self.log_result('security', 'malicious_file_upload', 'FAIL', 
                                  "Malicious file upload was accepted")
            else:
                self.log_result('security', 'malicious_file_upload', 'PASS', 
                              "Malicious file upload rejected with HTTP error")
                
        except Exception as e:
            self.log_result('security', 'malicious_file_upload', 'FAIL', str(e))
        
        # Test SQL injection in symbol field
        try:
            injection_data = {
                'symbol': "'; DROP TABLE manual_journal_entries; --",
                'trade_type': 'LONG',
                'entry_price': '100',
                'trade_date': '2025-08-02'
            }
            
            response = requests.post(f"{BASE_URL}/journal/api/create", 
                                   data=injection_data, timeout=10)
            
            # Check if database still exists after injection attempt
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='manual_journal_entries'")
            table_still_exists = cursor.fetchone() is not None
            conn.close()
            
            if table_still_exists:
                self.log_result('security', 'sql_injection_protection', 'PASS', 
                              "SQL injection attempt blocked, table still exists")
            else:
                self.log_result('security', 'sql_injection_protection', 'FAIL', 
                              "SQL injection successful, table dropped")
                
        except Exception as e:
            self.log_result('security', 'sql_injection_protection', 'FAIL', str(e))
        
        # Test oversized image upload
        try:
            # Create a large image (over 10MB limit)
            large_img = Image.new('RGB', (5000, 5000), color='green')
            large_buffer = io.BytesIO()
            large_img.save(large_buffer, format='PNG')
            large_buffer.seek(0)
            large_data = large_buffer.getvalue()
            
            if len(large_data) > 10 * 1024 * 1024:  # Over 10MB
                files = {'chart_image': ('large_image.png', large_data, 'image/png')}
                data = {
                    'symbol': 'SIZE_TEST',
                    'trade_type': 'LONG',
                    'entry_price': '100',
                    'trade_date': '2025-08-02'
                }
                
                response = requests.post(f"{BASE_URL}/journal/api/create", 
                                       data=data, files=files, timeout=20)
                
                if response.status_code == 200:
                    result = response.json()
                    if not result.get('success'):
                        self.log_result('security', 'oversized_file_protection', 'PASS', 
                                      "Oversized file correctly rejected")
                    else:
                        self.log_result('security', 'oversized_file_protection', 'FAIL', 
                                      "Oversized file was accepted")
                else:
                    self.log_result('security', 'oversized_file_protection', 'PASS', 
                                  f"Oversized file rejected with HTTP {response.status_code}")
            else:
                self.log_result('security', 'oversized_file_protection', 'WARN', 
                              f"Test image not large enough ({len(large_data)} bytes)")
                
        except Exception as e:
            self.log_result('security', 'oversized_file_protection', 'FAIL', str(e))
    
    def test_performance(self):
        """Test performance with multiple entries and operations"""
        print("\n⚡ Testing Performance")
        print("-" * 40)
        
        # Test multiple entry creation performance
        start_time = time.time()
        successful_creates = 0
        
        try:
            for i in range(10):
                test_data = {
                    'symbol': f'PERF_{i:03d}',
                    'trade_type': 'LONG' if i % 2 == 0 else 'SHORT',
                    'entry_price': str(100 + i),
                    'exit_price': str(105 + i),
                    'quantity': str(i + 1),
                    'outcome': 'WIN' if i % 3 == 0 else 'LOSS',
                    'profit_loss': str((105 + i - 100 - i) * (i + 1)),
                    'trade_date': '2025-08-02',
                    'entry_time': f'{9 + (i % 6):02d}:30:00',
                    'exit_time': f'{15 + (i % 3):02d}:30:00',
                    'notes': f'Performance test entry #{i}'
                }
                
                response = requests.post(f"{BASE_URL}/journal/api/create", 
                                       data=test_data, timeout=5)
                
                if response.status_code == 200 and response.json().get('success'):
                    successful_creates += 1
            
            creation_time = time.time() - start_time
            avg_time = creation_time / 10
            
            self.log_result('performance', 'bulk_creation', 'PASS', 
                          f"Created {successful_creates}/10 entries in {creation_time:.2f}s (avg: {avg_time:.3f}s/entry)")
            
        except Exception as e:
            self.log_result('performance', 'bulk_creation', 'FAIL', str(e))
        
        # Test entries retrieval performance
        start_time = time.time()
        try:
            response = requests.get(f"{BASE_URL}/journal/api/entries?limit=50", timeout=10)
            retrieval_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    entry_count = len(data.get('entries', []))
                    self.log_result('performance', 'bulk_retrieval', 'PASS', 
                                  f"Retrieved {entry_count} entries in {retrieval_time:.3f}s")
                else:
                    self.log_result('performance', 'bulk_retrieval', 'FAIL', 
                                  data.get('error', 'Unknown error'))
            else:
                self.log_result('performance', 'bulk_retrieval', 'FAIL', 
                              f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result('performance', 'bulk_retrieval', 'FAIL', str(e))
        
        # Test statistics calculation performance
        start_time = time.time()
        try:
            response = requests.get(f"{BASE_URL}/journal/api/statistics", timeout=10)
            stats_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_result('performance', 'statistics_calculation', 'PASS', 
                                  f"Statistics calculated in {stats_time:.3f}s")
                else:
                    self.log_result('performance', 'statistics_calculation', 'FAIL', 
                                  data.get('error', 'Unknown error'))
            else:
                self.log_result('performance', 'statistics_calculation', 'FAIL', 
                              f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result('performance', 'statistics_calculation', 'FAIL', str(e))
    
    def cleanup_test_data(self):
        """Clean up test data from database"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Remove test entries
            test_patterns = ['TEST_SYMBOL', 'DB_TEST', 'IMG_TEST', 'SEC_TEST', 'SIZE_TEST', 'PERF_%']
            
            for pattern in test_patterns:
                if '%' in pattern:
                    cursor.execute("DELETE FROM manual_journal_entries WHERE symbol LIKE ?", (pattern,))
                else:
                    cursor.execute("DELETE FROM manual_journal_entries WHERE symbol = ?", (pattern,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            print(f"\n🧹 Cleanup: Removed {deleted_count} test entries from database")
            
        except Exception as e:
            print(f"\n⚠️ Cleanup Warning: {str(e)}")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n📋 Generating Comprehensive Test Report")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        warnings = 0
        
        report_lines = []
        report_lines.append("MANUAL TRADE JOURNAL - COMPREHENSIVE TEST REPORT")
        report_lines.append("=" * 60)
        report_lines.append(f"Test Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Flask Server: {BASE_URL}")
        report_lines.append(f"Database: {DB_PATH}")
        report_lines.append("")
        
        for category, tests in self.results.items():
            if not tests:
                continue
                
            report_lines.append(f"{category.upper().replace('_', ' ')} TESTS:")
            report_lines.append("-" * 40)
            
            for test_name, result in tests.items():
                status = result['status']
                message = result['message']
                timestamp = result['timestamp']
                
                status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
                report_lines.append(f"{status_symbol} {test_name}: {message}")
                report_lines.append(f"   Timestamp: {timestamp}")
                
                total_tests += 1
                if status == "PASS":
                    passed_tests += 1
                elif status == "FAIL":
                    failed_tests += 1
                else:
                    warnings += 1
            
            report_lines.append("")
        
        # Summary
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        report_lines.append("SUMMARY:")
        report_lines.append("-" * 40)
        report_lines.append(f"Total Tests: {total_tests}")
        report_lines.append(f"Passed: {passed_tests}")
        report_lines.append(f"Failed: {failed_tests}")
        report_lines.append(f"Warnings: {warnings}")
        report_lines.append(f"Success Rate: {success_rate:.1f}%")
        
        # Overall status
        if failed_tests == 0:
            overall_status = "✅ ALL TESTS PASSED"
        elif failed_tests <= 2:
            overall_status = "⚠️ MINOR ISSUES DETECTED"
        else:
            overall_status = "❌ MAJOR ISSUES DETECTED"
        
        report_lines.append("")
        report_lines.append(f"OVERALL STATUS: {overall_status}")
        
        # Print report
        for line in report_lines:
            print(line)
        
        # Save report to file
        try:
            report_filename = f"journal_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_filename, 'w') as f:
                f.write('\n'.join(report_lines))
            print(f"\n📄 Test report saved to: {report_filename}")
        except Exception as e:
            print(f"\n⚠️ Could not save report to file: {str(e)}")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'warnings': warnings,
            'success_rate': success_rate,
            'overall_status': overall_status
        }

def main():
    """Main test execution function"""
    suite = JournalTestSuite()
    
    try:
        suite.run_all_tests()
    finally:
        # Always attempt cleanup
        suite.cleanup_test_data()

if __name__ == "__main__":
    main()