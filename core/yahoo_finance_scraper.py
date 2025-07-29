#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
import time
import json
import pickle
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import threading
import schedule

class YahooFinanceScraper:
    """Advanced Yahoo Finance Web Scraper for real-time market data"""
    
    def __init__(self, cache_file: str = "market_data_cache.pkl"):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://finance.yahoo.com/'
        })
        
        # Symbol configuration
        self.symbols = {
            '^NDX': {
                'name': 'NASDAQ',
                'url': 'https://finance.yahoo.com/quote/%5ENDX/',
                'price_range': (15000, 30000)
            },
            '^DJI': {
                'name': 'DOW JONES',
                'url': 'https://finance.yahoo.com/quote/%5EDJI/',
                'price_range': (30000, 60000)
            },
            'GC=F': {
                'name': 'GOLD',
                'url': 'https://finance.yahoo.com/quote/GC%3DF/',
                'price_range': (1500, 5000)
            }
        }
        
        self.cache_file = cache_file
        self.data_cache = {}
        self.last_update = None
        self.auto_refresh_active = False
        self._load_cache()
    
    def _load_cache(self):
        """Load cached data from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    self.data_cache = cache_data.get('data', {})
                    self.last_update = cache_data.get('last_update')
                print(f"[OK] Loaded cached data from {self.cache_file}")
        except Exception as e:
            print(f"[WARN] Could not load cache: {e}")
            self.data_cache = {}
    
    def _save_cache(self):
        """Save current data to cache file"""
        try:
            cache_data = {
                'data': self.data_cache,
                'last_update': self.last_update
            }
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            print(f"[OK] Saved data to cache: {self.cache_file}")
        except Exception as e:
            print(f"[WARN] Could not save cache: {e}")
    
    def scrape_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Scrape comprehensive data for a specific symbol"""
        if symbol not in self.symbols:
            print(f"[ERROR] Unknown symbol: {symbol}")
            return None
        
        symbol_info = self.symbols[symbol]
        url = symbol_info['url']
        name = symbol_info['name']
        price_range = symbol_info['price_range']
        
        try:
            print(f"[SCRAPING] {name} ({symbol}) from Yahoo Finance...")
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract all required data
            current_price = self._extract_current_price(soup, symbol, price_range)
            previous_close = self._extract_previous_close(soup, symbol, price_range)
            day_high = self._extract_day_high(soup, symbol, price_range)
            day_low = self._extract_day_low(soup, symbol, price_range)
            
            # Calculate net change
            net_change = None
            net_change_percent = None
            if current_price and previous_close:
                net_change = current_price - previous_close
                net_change_percent = (net_change / previous_close) * 100
            
            # Validate we have minimum required data
            if not current_price:
                print(f"[ERROR] Could not extract current price for {symbol}")
                return None
            
            result = {
                'symbol': symbol,
                'name': name,
                'current_price': current_price,
                'previous_close': previous_close,
                'net_change': net_change,
                'net_change_percent': net_change_percent,
                'day_high': day_high,
                'day_low': day_low,
                'timestamp': datetime.now().isoformat(),
                'source': 'yahoo_finance_scraper',
                'url': url
            }
            
            print(f"[SUCCESS] {name} data extracted successfully:")
            print(f"   Current: ${current_price:,.2f}")
            if previous_close:
                print(f"   Previous Close: ${previous_close:,.2f}")
            if net_change:
                print(f"   Net Change: ${net_change:+,.2f} ({net_change_percent:+.2f}%)")
            if day_high and day_low:
                print(f"   Day Range: ${day_low:,.2f} - ${day_high:,.2f}")
            
            return result
            
        except Exception as e:
            print(f"[ERROR] Error scraping {symbol}: {e}")
            return None
    
    def _extract_current_price(self, soup: BeautifulSoup, symbol: str, price_range: tuple) -> Optional[float]:
        """Extract current price using multiple methods"""
        try:
            # Method 1: Direct selectors for current price
            price_selectors = [
                'fin-streamer[data-field="regularMarketPrice"]',
                '[data-testid="qsp-price"]',
                '.Fw\\(b\\).Fz\\(36px\\).Mb\\(-4px\\).D\\(ib\\)',
                '.livePrice span',
                '[data-symbol] [data-field="regularMarketPrice"]'
            ]
            
            for selector in price_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        price_text = element.get_text().strip().replace(',', '').replace('$', '')
                        price = float(price_text)
                        if price_range[0] <= price <= price_range[1]:
                            return price
                except:
                    continue
            
            # Method 2: JSON data extraction
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'regularMarketPrice' in script.string:
                    try:
                        # Look for JSON patterns
                        json_patterns = [
                            r'"regularMarketPrice":\s*(\d+\.?\d*)',
                            r'"currentPrice":\s*(\d+\.?\d*)',
                            r'regularMarketPrice.*?(\d+\.?\d*)'
                        ]
                        
                        for pattern in json_patterns:
                            matches = re.findall(pattern, script.string)
                            for match in matches:
                                try:
                                    price = float(match)
                                    if price_range[0] <= price <= price_range[1]:
                                        return price
                                except:
                                    continue
                    except:
                        continue
            
            # Method 3: Text pattern matching
            page_text = soup.get_text()
            price_patterns = [
                rf'Current Price.*?(\d{{1,3}}(?:,\d{{3}})*\.?\d*)',
                rf'({price_range[0]//1000}\d{{3}}(?:,\d{{3}})*\.?\d*)',
                rf'(\d{{2,3}},\d{{3}}\.?\d*)'
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    try:
                        price = float(match.replace(',', ''))
                        if price_range[0] <= price <= price_range[1]:
                            return price
                    except:
                        continue
            
            return None
            
        except Exception as e:
            print(f"  [ERROR] Error extracting current price: {e}")
            return None
    
    def _extract_previous_close(self, soup: BeautifulSoup, symbol: str, price_range: tuple) -> Optional[float]:
        """Extract previous close price"""
        try:
            # Method 1: Direct selectors
            close_selectors = [
                'fin-streamer[data-field="regularMarketPreviousClose"]',
                '[data-testid="PREV_CLOSE-value"]',
                'td[data-test="PREV_CLOSE-value"]'
            ]
            
            for selector in close_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        price_text = element.get_text().strip().replace(',', '').replace('$', '')
                        price = float(price_text)
                        if price_range[0] <= price <= price_range[1]:
                            return price
                except:
                    continue
            
            # Method 2: Text pattern matching
            page_text = soup.get_text()
            patterns = [
                r'Previous Close.*?(\d{1,3}(?:,\d{3})*\.?\d*)',
                r'Prev\. Close.*?(\d{1,3}(?:,\d{3})*\.?\d*)',
                r'regularMarketPreviousClose.*?(\d+\.?\d*)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    try:
                        price = float(match.replace(',', ''))
                        if price_range[0] <= price <= price_range[1]:
                            return price
                    except:
                        continue
            
            return None
            
        except Exception as e:
            print(f"  [ERROR] Error extracting previous close: {e}")
            return None
    
    def _extract_day_high(self, soup: BeautifulSoup, symbol: str, price_range: tuple) -> Optional[float]:
        """Extract day's high price"""
        try:
            # Method 1: Direct selectors
            high_selectors = [
                'fin-streamer[data-field="regularMarketDayHigh"]',
                '[data-testid="DAYS_RANGE-value"]',
                'td[data-test="DAYS_RANGE-value"]'
            ]
            
            for selector in high_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        text = element.get_text().strip()
                        # Handle range format like "2,100.50 - 2,150.75"
                        range_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d*)\s*-\s*(\d{1,3}(?:,\d{3})*\.?\d*)', text)
                        if range_match:
                            low_val = float(range_match.group(1).replace(',', ''))
                            high_val = float(range_match.group(2).replace(',', ''))
                            high_price = max(low_val, high_val)
                            if price_range[0] <= high_price <= price_range[1]:
                                return high_price
                        else:
                            # Single value
                            price = float(text.replace(',', '').replace('$', ''))
                            if price_range[0] <= price <= price_range[1]:
                                return price
                except:
                    continue
            
            # Method 2: Text pattern matching
            page_text = soup.get_text()
            patterns = [
                r"Day's Range.*?(\d{1,3}(?:,\d{3})*\.?\d*)\s*-\s*(\d{1,3}(?:,\d{3})*\.?\d*)",
                r"High.*?(\d{1,3}(?:,\d{3})*\.?\d*)",
                r"regularMarketDayHigh.*?(\d+\.?\d*)"
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    try:
                        if isinstance(match, tuple):
                            # Range format
                            val1 = float(match[0].replace(',', ''))
                            val2 = float(match[1].replace(',', ''))
                            high_price = max(val1, val2)
                        else:
                            # Single value
                            high_price = float(match.replace(',', ''))
                        
                        if price_range[0] <= high_price <= price_range[1]:
                            return high_price
                    except:
                        continue
            
            return None
            
        except Exception as e:
            print(f"  [ERROR] Error extracting day high: {e}")
            return None
    
    def _extract_day_low(self, soup: BeautifulSoup, symbol: str, price_range: tuple) -> Optional[float]:
        """Extract day's low price"""
        try:
            # Method 1: From day's range
            range_selectors = [
                'fin-streamer[data-field="regularMarketDayLow"]',
                '[data-testid="DAYS_RANGE-value"]',
                'td[data-test="DAYS_RANGE-value"]'
            ]
            
            for selector in range_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        text = element.get_text().strip()
                        # Handle range format like "2,100.50 - 2,150.75"
                        range_match = re.search(r'(\d{1,3}(?:,\d{3})*\.?\d*)\s*-\s*(\d{1,3}(?:,\d{3})*\.?\d*)', text)
                        if range_match:
                            val1 = float(range_match.group(1).replace(',', ''))
                            val2 = float(range_match.group(2).replace(',', ''))
                            low_price = min(val1, val2)
                            if price_range[0] <= low_price <= price_range[1]:
                                return low_price
                except:
                    continue
            
            # Method 2: Text pattern matching
            page_text = soup.get_text()
            patterns = [
                r"Day's Range.*?(\d{1,3}(?:,\d{3})*\.?\d*)\s*-\s*(\d{1,3}(?:,\d{3})*\.?\d*)",
                r"Low.*?(\d{1,3}(?:,\d{3})*\.?\d*)",
                r"regularMarketDayLow.*?(\d+\.?\d*)"
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    try:
                        if isinstance(match, tuple):
                            # Range format
                            val1 = float(match[0].replace(',', ''))
                            val2 = float(match[1].replace(',', ''))
                            low_price = min(val1, val2)
                        else:
                            # Single value
                            low_price = float(match.replace(',', ''))
                        
                        if price_range[0] <= low_price <= price_range[1]:
                            return low_price
                    except:
                        continue
            
            return None
            
        except Exception as e:
            print(f"  [ERROR] Error extracting day low: {e}")
            return None
    
    def scrape_all(self) -> Dict[str, Any]:
        """Scrape data for all configured symbols"""
        print("[SCRAPER] STARTING YAHOO FINANCE SCRAPING SESSION")
        print("=" * 60)
        
        results = {}
        start_time = datetime.now()
        
        for symbol in self.symbols.keys():
            data = self.scrape_symbol(symbol)
            if data:
                results[symbol] = data
                self.data_cache[symbol] = data
            else:
                print(f"[FAILED] Failed to scrape {symbol}")
            
            # Brief delay between requests
            time.sleep(1)
        
        self.last_update = datetime.now()
        self._save_cache()
        
        duration = (datetime.now() - start_time).total_seconds()
        
        print("\n" + "=" * 60)
        print(f"[COMPLETE] SCRAPING COMPLETE - Duration: {duration:.1f}s")
        print("=" * 60)
        
        for symbol, data in results.items():
            name = data['name']
            current = data['current_price']
            net_change = data.get('net_change', 0) or 0
            print(f"{name} ({symbol}): ${current:,.2f} ({net_change:+.2f})")
        
        return results
    
    def get_cached_data(self, symbol: str = None) -> Dict[str, Any]:
        """Get cached data for symbol(s)"""
        if symbol:
            return self.data_cache.get(symbol, {})
        return self.data_cache
    
    def start_auto_refresh(self, interval_minutes: int = 5):
        """Start automatic data refresh every N minutes"""
        if self.auto_refresh_active:
            print("[WARN] Auto-refresh already active")
            return
        
        print(f"[AUTO-REFRESH] Starting auto-refresh every {interval_minutes} minutes...")
        
        def refresh_job():
            try:
                print(f"\n[AUTO-REFRESH] Auto-refresh triggered at {datetime.now().strftime('%H:%M:%S')}")
                self.scrape_all()
            except Exception as e:
                print(f"[ERROR] Auto-refresh error: {e}")
        
        # Schedule the refresh
        schedule.every(interval_minutes).minutes.do(refresh_job)
        
        def run_scheduler():
            while self.auto_refresh_active:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
        
        self.auto_refresh_active = True
        
        # Run initial scrape
        refresh_job()
        
        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        print(f"[OK] Auto-refresh started - next update in {interval_minutes} minutes")
    
    def stop_auto_refresh(self):
        """Stop automatic refresh"""
        self.auto_refresh_active = False
        schedule.clear()
        print("[STOP] Auto-refresh stopped")

if __name__ == "__main__":
    # Test the scraper
    scraper = YahooFinanceScraper()
    
    # Test individual symbol
    print("Testing individual symbol scraping:")
    nasdaq_data = scraper.scrape_symbol('^NDX')
    
    # Test all symbols
    print("\nTesting all symbols:")
    all_data = scraper.scrape_all()
    
    # Test auto-refresh (uncomment to test)
    # print("\nStarting auto-refresh for 2 minutes...")
    # scraper.start_auto_refresh(interval_minutes=1)
    # time.sleep(120)
    # scraper.stop_auto_refresh()