#!/usr/bin/env python3
"""
Mobile Responsiveness Testing for Manual Trade Journal
Tests CSS responsiveness, viewport handling, and mobile-specific features
"""

import requests
import re
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:5000"

class MobileResponsiveTestSuite:
    def __init__(self):
        self.results = {
            'css_analysis': {},
            'viewport_meta': {},
            'responsive_design': {},
            'mobile_features': {}
        }
        
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
    
    def test_viewport_meta_tags(self):
        """Test for proper viewport meta tags"""
        print("\n📱 Testing Viewport Meta Tags")
        print("-" * 40)
        
        try:
            response = requests.get(f"{BASE_URL}/journal", timeout=10)
            
            if response.status_code == 200:
                html_content = response.text
                
                # Check for viewport meta tag
                viewport_pattern = r'<meta\s+name=["\']viewport["\'][^>]*>'
                viewport_match = re.search(viewport_pattern, html_content, re.IGNORECASE)
                
                if viewport_match:
                    viewport_tag = viewport_match.group(0)
                    self.log_result('viewport_meta', 'viewport_tag_present', 'PASS', 
                                  f"Viewport meta tag found: {viewport_tag}")
                    
                    # Check for proper viewport settings
                    if 'width=device-width' in viewport_tag:
                        self.log_result('viewport_meta', 'device_width', 'PASS', 
                                      "Device width scaling enabled")
                    else:
                        self.log_result('viewport_meta', 'device_width', 'FAIL', 
                                      "Device width scaling not enabled")
                    
                    if 'initial-scale=1' in viewport_tag:
                        self.log_result('viewport_meta', 'initial_scale', 'PASS', 
                                      "Initial scale properly set")
                    else:
                        self.log_result('viewport_meta', 'initial_scale', 'WARN', 
                                      "Initial scale not explicitly set")
                else:
                    self.log_result('viewport_meta', 'viewport_tag_present', 'FAIL', 
                                  "Viewport meta tag not found")
                
                # Check for responsive charset
                charset_pattern = r'<meta\s+charset=["\']utf-8["\']'
                if re.search(charset_pattern, html_content, re.IGNORECASE):
                    self.log_result('viewport_meta', 'charset_utf8', 'PASS', 
                                  "UTF-8 charset properly set")
                else:
                    self.log_result('viewport_meta', 'charset_utf8', 'WARN', 
                                  "UTF-8 charset not explicitly set")
                    
            else:
                self.log_result('viewport_meta', 'page_load_error', 'FAIL', 
                              f"Could not load page: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result('viewport_meta', 'test_error', 'FAIL', str(e))
    
    def test_css_responsiveness(self):
        """Analyze CSS for responsive design patterns"""
        print("\n🎨 Testing CSS Responsiveness")
        print("-" * 40)
        
        try:
            response = requests.get(f"{BASE_URL}/journal", timeout=10)
            
            if response.status_code == 200:
                html_content = response.text
                
                # Extract CSS content (inline styles and external references)
                css_content = ""
                
                # Find inline styles
                style_pattern = r'<style[^>]*>(.*?)</style>'
                style_matches = re.findall(style_pattern, html_content, re.DOTALL | re.IGNORECASE)
                for style in style_matches:
                    css_content += style
                
                # Check for media queries
                media_query_patterns = [
                    r'@media\s*\([^)]*max-width[^)]*\)',
                    r'@media\s*\([^)]*min-width[^)]*\)',
                    r'@media\s*screen\s*and\s*\([^)]*\)',
                ]
                
                media_queries_found = 0
                for pattern in media_query_patterns:
                    matches = re.findall(pattern, css_content, re.IGNORECASE)
                    media_queries_found += len(matches)
                
                if media_queries_found > 0:
                    self.log_result('css_analysis', 'media_queries', 'PASS', 
                                  f"Found {media_queries_found} media queries")
                else:
                    self.log_result('css_analysis', 'media_queries', 'WARN', 
                                  "No media queries found in inline CSS")
                
                # Check for responsive units
                responsive_units = ['vw', 'vh', 'vmin', 'vmax', '%', 'em', 'rem']
                responsive_units_found = []
                
                for unit in responsive_units:
                    pattern = rf'\d+\.?\d*{unit}\b'
                    if re.search(pattern, css_content, re.IGNORECASE):
                        responsive_units_found.append(unit)
                
                if responsive_units_found:
                    self.log_result('css_analysis', 'responsive_units', 'PASS', 
                                  f"Responsive units found: {', '.join(responsive_units_found)}")
                else:
                    self.log_result('css_analysis', 'responsive_units', 'WARN', 
                                  "No obvious responsive units found")
                
                # Check for flexbox usage
                flexbox_patterns = ['display:\s*flex', 'flex-direction', 'flex-wrap', 'justify-content']
                flexbox_found = any(re.search(pattern, css_content, re.IGNORECASE) for pattern in flexbox_patterns)
                
                if flexbox_found:
                    self.log_result('css_analysis', 'flexbox_usage', 'PASS', 
                                  "Flexbox layout detected")
                else:
                    self.log_result('css_analysis', 'flexbox_usage', 'WARN', 
                                  "No flexbox usage detected")
                
                # Check for grid usage
                grid_patterns = ['display:\s*grid', 'grid-template', 'grid-gap']
                grid_found = any(re.search(pattern, css_content, re.IGNORECASE) for pattern in grid_patterns)
                
                if grid_found:
                    self.log_result('css_analysis', 'grid_usage', 'PASS', 
                                  "CSS Grid layout detected")
                else:
                    self.log_result('css_analysis', 'grid_usage', 'WARN', 
                                  "No CSS Grid usage detected")
                    
            else:
                self.log_result('css_analysis', 'page_load_error', 'FAIL', 
                              f"Could not load page: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result('css_analysis', 'test_error', 'FAIL', str(e))
    
    def test_responsive_breakpoints(self):
        """Test for common responsive breakpoints"""
        print("\n📐 Testing Responsive Breakpoints")
        print("-" * 40)
        
        try:
            response = requests.get(f"{BASE_URL}/journal", timeout=10)
            
            if response.status_code == 200:
                html_content = response.text
                
                # Extract CSS content
                css_content = ""
                style_pattern = r'<style[^>]*>(.*?)</style>'
                style_matches = re.findall(style_pattern, html_content, re.DOTALL | re.IGNORECASE)
                for style in style_matches:
                    css_content += style
                
                # Common responsive breakpoints
                breakpoints = {
                    'mobile': [320, 375, 414, 480],
                    'tablet': [768, 834, 1024],
                    'desktop': [1200, 1366, 1440, 1920]
                }
                
                breakpoints_found = {}
                
                for category, widths in breakpoints.items():
                    found_widths = []
                    for width in widths:
                        # Check for max-width and min-width patterns
                        patterns = [
                            rf'max-width:\s*{width}px',
                            rf'min-width:\s*{width}px',
                            rf'\({width}px\)',
                        ]
                        
                        for pattern in patterns:
                            if re.search(pattern, css_content, re.IGNORECASE):
                                found_widths.append(width)
                                break
                    
                    if found_widths:
                        breakpoints_found[category] = found_widths
                        self.log_result('responsive_design', f'breakpoints_{category}', 'PASS', 
                                      f"{category.title()} breakpoints found: {found_widths}")
                    else:
                        self.log_result('responsive_design', f'breakpoints_{category}', 'WARN', 
                                      f"No {category} breakpoints detected")
                
                # Overall breakpoint assessment
                total_breakpoints = sum(len(widths) for widths in breakpoints_found.values())
                if total_breakpoints >= 3:
                    self.log_result('responsive_design', 'breakpoint_coverage', 'PASS', 
                                  f"Good breakpoint coverage ({total_breakpoints} breakpoints)")
                elif total_breakpoints >= 1:
                    self.log_result('responsive_design', 'breakpoint_coverage', 'WARN', 
                                  f"Limited breakpoint coverage ({total_breakpoints} breakpoints)")
                else:
                    self.log_result('responsive_design', 'breakpoint_coverage', 'FAIL', 
                                  "No responsive breakpoints detected")
                    
            else:
                self.log_result('responsive_design', 'page_load_error', 'FAIL', 
                              f"Could not load page: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result('responsive_design', 'test_error', 'FAIL', str(e))
    
    def test_mobile_specific_features(self):
        """Test for mobile-specific features and optimizations"""
        print("\n📲 Testing Mobile-Specific Features")
        print("-" * 40)
        
        try:
            response = requests.get(f"{BASE_URL}/journal", timeout=10)
            
            if response.status_code == 200:
                html_content = response.text
                
                # Check for touch-friendly elements
                touch_patterns = [
                    r'touch-action',
                    r'pointer-events',
                    r'-webkit-tap-highlight-color',
                    r'user-select:\s*none'
                ]
                
                touch_optimizations = []
                for pattern in touch_patterns:
                    if re.search(pattern, html_content, re.IGNORECASE):
                        touch_optimizations.append(pattern.replace(r'\s*', ' ').replace(':', ''))
                
                if touch_optimizations:
                    self.log_result('mobile_features', 'touch_optimizations', 'PASS', 
                                  f"Touch optimizations found: {', '.join(touch_optimizations)}")
                else:
                    self.log_result('mobile_features', 'touch_optimizations', 'WARN', 
                                  "No explicit touch optimizations detected")
                
                # Check for mobile navigation patterns
                mobile_nav_patterns = [
                    r'hamburger',
                    r'mobile-menu',
                    r'navbar-toggle',
                    r'menu-toggle',
                    r'sidebar-toggle'
                ]
                
                mobile_nav_found = []
                for pattern in mobile_nav_patterns:
                    if re.search(pattern, html_content, re.IGNORECASE):
                        mobile_nav_found.append(pattern)
                
                if mobile_nav_found:
                    self.log_result('mobile_features', 'mobile_navigation', 'PASS', 
                                  f"Mobile navigation patterns found: {', '.join(mobile_nav_found)}")
                else:
                    self.log_result('mobile_features', 'mobile_navigation', 'WARN', 
                                  "No obvious mobile navigation patterns detected")
                
                # Check for mobile-optimized input types
                input_patterns = [
                    r'type=["\']tel["\']',
                    r'type=["\']email["\']',
                    r'type=["\']number["\']',
                    r'type=["\']date["\']',
                    r'type=["\']time["\']'
                ]
                
                mobile_inputs = []
                for pattern in input_patterns:
                    matches = re.findall(pattern, html_content, re.IGNORECASE)
                    if matches:
                        input_type = pattern.split('["\']')[1]
                        mobile_inputs.append(input_type)
                
                if mobile_inputs:
                    self.log_result('mobile_features', 'mobile_input_types', 'PASS', 
                                  f"Mobile-optimized inputs found: {', '.join(set(mobile_inputs))}")
                else:
                    self.log_result('mobile_features', 'mobile_input_types', 'WARN', 
                                  "No mobile-optimized input types detected")
                
                # Check for loading optimizations
                loading_patterns = [
                    r'loading=["\']lazy["\']',
                    r'preload',
                    r'prefetch',
                    r'async',
                    r'defer'
                ]
                
                loading_optimizations = []
                for pattern in loading_patterns:
                    if re.search(pattern, html_content, re.IGNORECASE):
                        loading_optimizations.append(pattern.replace(r'["\']', '').replace(r'=', ''))
                
                if loading_optimizations:
                    self.log_result('mobile_features', 'loading_optimizations', 'PASS', 
                                  f"Loading optimizations found: {', '.join(set(loading_optimizations))}")
                else:
                    self.log_result('mobile_features', 'loading_optimizations', 'WARN', 
                                  "No explicit loading optimizations detected")
                    
            else:
                self.log_result('mobile_features', 'page_load_error', 'FAIL', 
                              f"Could not load page: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result('mobile_features', 'test_error', 'FAIL', str(e))
    
    def test_font_and_readability(self):
        """Test font sizes and readability for mobile devices"""
        print("\n📖 Testing Font and Readability")
        print("-" * 40)
        
        try:
            response = requests.get(f"{BASE_URL}/journal", timeout=10)
            
            if response.status_code == 200:
                html_content = response.text
                
                # Extract CSS content
                css_content = ""
                style_pattern = r'<style[^>]*>(.*?)</style>'
                style_matches = re.findall(style_pattern, html_content, re.DOTALL | re.IGNORECASE)
                for style in style_matches:
                    css_content += style
                
                # Check for minimum font sizes
                font_size_pattern = r'font-size:\s*(\d+(?:\.\d+)?)(px|em|rem)'
                font_sizes = re.findall(font_size_pattern, css_content, re.IGNORECASE)
                
                px_sizes = []
                relative_sizes = []
                
                for size, unit in font_sizes:
                    size_val = float(size)
                    if unit.lower() == 'px':
                        px_sizes.append(size_val)
                    else:
                        relative_sizes.append((size_val, unit))
                
                # Check for mobile-friendly font sizes (minimum 16px)
                small_fonts = [size for size in px_sizes if size < 16]
                
                if small_fonts:
                    self.log_result('mobile_features', 'font_size_mobile', 'WARN', 
                                  f"Small font sizes detected: {small_fonts}px (recommend min 16px for mobile)")
                else:
                    self.log_result('mobile_features', 'font_size_mobile', 'PASS', 
                                  "Font sizes appear mobile-friendly")
                
                # Check for relative font units
                if relative_sizes:
                    self.log_result('mobile_features', 'relative_font_units', 'PASS', 
                                  f"Relative font units found: {len(relative_sizes)} instances")
                else:
                    self.log_result('mobile_features', 'relative_font_units', 'WARN', 
                                  "No relative font units (em/rem) detected")
                
                # Check for line height settings
                line_height_pattern = r'line-height:\s*(\d+(?:\.\d+)?)'
                line_heights = re.findall(line_height_pattern, css_content, re.IGNORECASE)
                
                if line_heights:
                    line_height_values = [float(lh) for lh in line_heights]
                    good_line_heights = [lh for lh in line_height_values if 1.4 <= lh <= 2.0]
                    
                    if good_line_heights:
                        self.log_result('mobile_features', 'line_height_mobile', 'PASS', 
                                      f"Good line heights for readability: {good_line_heights}")
                    else:
                        self.log_result('mobile_features', 'line_height_mobile', 'WARN', 
                                      f"Line heights may not be optimal for mobile: {line_height_values}")
                else:
                    self.log_result('mobile_features', 'line_height_mobile', 'WARN', 
                                  "No explicit line height settings found")
                    
            else:
                self.log_result('mobile_features', 'page_load_error', 'FAIL', 
                              f"Could not load page: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result('mobile_features', 'test_error', 'FAIL', str(e))
    
    def run_all_tests(self):
        """Execute all mobile responsiveness tests"""
        print("📱 Starting Mobile Responsiveness Testing")
        print("=" * 60)
        
        self.test_viewport_meta_tags()
        self.test_css_responsiveness()
        self.test_responsive_breakpoints()
        self.test_mobile_specific_features()
        self.test_font_and_readability()
        
        self.generate_report()
    
    def generate_report(self):
        """Generate mobile responsiveness testing report"""
        print("\n📋 Mobile Responsiveness Testing Report")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        warnings = 0
        
        for category, tests in self.results.items():
            if not tests:
                continue
                
            print(f"\n{category.upper().replace('_', ' ')} TESTS:")
            print("-" * 50)
            
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
        
        # Calculate scores
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\nMOBILE RESPONSIVENESS SUMMARY:")
        print("-" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Warnings: {warnings}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Responsiveness assessment
        if failed_tests == 0 and warnings <= 2:
            responsiveness_grade = "A - Excellent Mobile Support"
        elif failed_tests <= 1 and warnings <= 4:
            responsiveness_grade = "B - Good Mobile Support"
        elif failed_tests <= 2 and warnings <= 6:
            responsiveness_grade = "C - Adequate Mobile Support"
        else:
            responsiveness_grade = "D - Poor Mobile Support"
        
        print(f"\nMOBILE RESPONSIVENESS GRADE: {responsiveness_grade}")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'warnings': warnings,
            'success_rate': success_rate,
            'responsiveness_grade': responsiveness_grade
        }

def main():
    """Main test execution function"""
    suite = MobileResponsiveTestSuite()
    suite.run_all_tests()

if __name__ == "__main__":
    main()