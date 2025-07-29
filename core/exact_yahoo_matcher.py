#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exact Yahoo Finance Data Matcher
Replicates Yahoo Finance daily high/low ranges with precision
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import time
import requests
import json
import logging
import re
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExactYahooDataMatcher:
    def __init__(self):
        self.symbols = {
            'NASDAQ': '^NDX',   # NASDAQ-100 Index
            'DOW': '^DJI',      # Dow Jones Industrial Average  
            'GOLD': 'GC=F'      # Gold Futures
        }
        
        # US Eastern Time (market timezone)
        self.market_tz = pytz.timezone('America/New_York')
        self.utc_tz = pytz.UTC
        
    def get_exact_yahoo_ranges(self):
        """Get exact daily ranges matching Yahoo Finance display"""
        market_data = {}
        
        for name, symbol in self.symbols.items():
            try:
                print(f"Fetching LIVE {name} data to match Yahoo Finance...")
                
                # Use direct Yahoo Finance API for most accurate data
                live_data = self.get_yahoo_finance_api_data(symbol, name)
                
                if live_data:
                    print(f"SUCCESS - Yahoo API for {name}:")
                    print(f"  High: {live_data['daily_high']:.2f}")
                    print(f"  Low: {live_data['daily_low']:.2f}")
                    print(f"  Current: {live_data['current_value']:.2f}")
                    
                    validated_data = self.validate_yahoo_methodology(live_data, symbol)
                    market_data[name] = validated_data
                else:
                    # Fallback to enhanced data fetching
                    print(f"Yahoo API failed for {name}, using enhanced fallback...")
                    fallback_data = self.get_enhanced_fallback_data(symbol, name)
                    market_data[name] = fallback_data
                
                print(f"FINAL {name} ranges:")
                print(f"   High: {market_data[name]['daily_high']:.2f}")
                print(f"   Low: {market_data[name]['daily_low']:.2f}")
                print(f"   Current: {market_data[name]['current_value']:.2f}")
                print(f"   Source: {market_data[name]['data_source']}")
                
            except Exception as e:
                print(f"ERROR fetching {name} data: {e}")
                # Use enhanced fallback as last resort
                market_data[name] = self.get_enhanced_fallback_data(symbol, name)
        
        return market_data
    
    def get_yahoo_finance_api_data(self, symbol, name):
        """Get data directly from Yahoo Finance API for accurate day's range values"""
        try:
            print(f"Fetching Yahoo Finance API data for {symbol}...")
            
            # Use yfinance to get the most current data
            ticker = yf.Ticker(symbol)
            
            # Try multiple approaches to get the most accurate data
            # Method 1: Get today's intraday data
            today_data = ticker.history(period="1d", interval="1m")
            
            if not today_data.empty:
                # Calculate ranges from intraday data
                current_price = float(today_data['Close'].iloc[-1])
                daily_high = float(today_data['High'].max())
                daily_low = float(today_data['Low'].min())
                daily_open = float(today_data['Open'].iloc[0])
                daily_volume = int(today_data['Volume'].sum())
                
                print(f"Method 1 (1d/1m) for {name}: High {daily_high:.2f}, Low {daily_low:.2f}")
                
                return {
                    'current_value': current_price,
                    'daily_high': daily_high,
                    'daily_low': daily_low,
                    'daily_open': daily_open,
                    'daily_volume': daily_volume,
                    'daily_range': daily_high - daily_low,
                    'data_source': 'yahoo_api_1d_1m',
                    'data_points': len(today_data),
                    'validation_passed': True,
                    'last_updated': datetime.now().isoformat()
                }
            
            # Method 2: Try 2-day period to ensure we get today's data
            two_day_data = ticker.history(period="2d", interval="1m")
            
            if not two_day_data.empty:
                # Filter for today's data
                today = datetime.now(self.market_tz).date()
                two_day_data.index = two_day_data.index.tz_convert(self.market_tz)
                today_filtered = two_day_data[two_day_data.index.date == today]
                
                if not today_filtered.empty:
                    current_price = float(today_filtered['Close'].iloc[-1])
                    daily_high = float(today_filtered['High'].max())
                    daily_low = float(today_filtered['Low'].min())
                    daily_open = float(today_filtered['Open'].iloc[0])
                    daily_volume = int(today_filtered['Volume'].sum())
                    
                    print(f"Method 2 (2d/1m filtered) for {name}: High {daily_high:.2f}, Low {daily_low:.2f}")
                    
                    return {
                        'current_value': current_price,
                        'daily_high': daily_high,
                        'daily_low': daily_low,
                        'daily_open': daily_open,
                        'daily_volume': daily_volume,
                        'daily_range': daily_high - daily_low,
                        'data_source': 'yahoo_api_2d_1m_filtered',
                        'data_points': len(today_filtered),
                        'validation_passed': True,
                        'last_updated': datetime.now().isoformat()
                    }
            
            # Method 3: Use daily data as fallback
            daily_data = ticker.history(period="5d", interval="1d")
            
            if not daily_data.empty:
                latest = daily_data.iloc[-1]
                current_price = float(latest['Close'])
                daily_high = float(latest['High'])
                daily_low = float(latest['Low'])
                daily_open = float(latest['Open'])
                daily_volume = int(latest['Volume'])
                
                print(f"Method 3 (5d/1d latest) for {name}: High {daily_high:.2f}, Low {daily_low:.2f}")
                
                return {
                    'current_value': current_price,
                    'daily_high': daily_high,
                    'daily_low': daily_low,
                    'daily_open': daily_open,
                    'daily_volume': daily_volume,
                    'daily_range': daily_high - daily_low,
                    'data_source': 'yahoo_api_5d_1d',
                    'data_points': len(daily_data),
                    'validation_passed': True,
                    'last_updated': datetime.now().isoformat()
                }
            
            print(f"All methods failed for {name} - no data available")
            return None
            
        except Exception as e:
            print(f"Yahoo Finance API failed for {name}: {e}")
            return None
    
    def scrape_yahoo_finance_web(self, symbol, name):
        """Scrape Yahoo Finance web interface to get exact values that match the web display"""
        try:
            # Clean symbol for URL
            clean_symbol = symbol.replace('^', '%5E')
            url = f"https://finance.yahoo.com/quote/{clean_symbol}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'no-cache'
            }
            
            print(f"Scraping Yahoo Finance web: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract current price
            current_price = None
            price_selectors = [
                'fin-streamer[data-field="regularMarketPrice"]',
                '[data-testid="qsp-price"]',
                '.Fw\\(b\\).Fz\\(36px\\).Mb\\(-4px\\).D\\(ib\\)',
                '.Trsdu\\(0\\.3s\\).Fw\\(b\\).Fz\\(36px\\).Mb\\(-4px\\).D\\(ib\\)'
            ]
            
            for selector in price_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        price_text = element.get_text().strip().replace(',', '')
                        current_price = float(price_text)
                        break
                except:
                    continue
            
            # Extract day's range (High - Low)
            daily_high = None
            daily_low = None
            
            # Look for "Day's Range" section with improved patterns
            range_patterns = [
                r"Day's Range[\s\S]*?(\d{2},\d{3}\.\d{2})\s*-\s*(\d{2},\d{3}\.\d{2})",
                r"Day's Range[\s\S]*?(\d{1,2},\d{3}\.\d{2})\s*-\s*(\d{1,2},\d{3}\.\d{2})",
                r"Day's Range[\s\S]*?(\d+,\d+\.\d+)\s*-\s*(\d+,\d+\.\d+)",
                r"(\d{2},\d{3}\.\d{2})\s*-\s*(\d{2},\d{3}\.\d{2})",
                # Additional patterns for different formats
                r"(\d{2},\d{3}\.\d{2})\s+(\d{2},\d{3}\.\d{2})",
                r"Low\s*(\d{2},\d{3}\.\d{2}).*?High\s*(\d{2},\d{3}\.\d{2})",
                r"High\s*(\d{2},\d{3}\.\d{2}).*?Low\s*(\d{2},\d{3}\.\d{2})"
            ]
            
            page_text = soup.get_text()
            
            for pattern in range_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    try:
                        low_val = float(match[0].replace(',', ''))
                        high_val = float(match[1].replace(',', ''))
                        
                        # Ensure high > low (sometimes they're reversed in the match)
                        if high_val > low_val:
                            daily_high = high_val
                            daily_low = low_val
                        else:
                            daily_high = low_val
                            daily_low = high_val
                        
                        # Validate range makes sense for the symbol
                        if name == 'NASDAQ' and 20000 <= daily_low <= 25000 and 20000 <= daily_high <= 25000:
                            break
                        elif name == 'DOW' and 40000 <= daily_low <= 50000 and 40000 <= daily_high <= 50000:
                            break
                        elif name == 'GOLD' and 3000 <= daily_low <= 4000 and 3000 <= daily_high <= 4000:
                            break
                    except:
                        continue
                
                if daily_high and daily_low:
                    break
            
            # If we found valid data, return it
            if current_price and daily_high and daily_low:
                print(f"Web scraping SUCCESS for {name}:")
                print(f"  Current: {current_price:,.2f}")
                print(f"  High: {daily_high:,.2f}")
                print(f"  Low: {daily_low:,.2f}")
                
                return {
                    'current_value': current_price,
                    'daily_high': daily_high,
                    'daily_low': daily_low,
                    'daily_open': current_price,  # Approximate
                    'daily_volume': 0,
                    'daily_range': daily_high - daily_low,
                    'data_source': 'yahoo_web_scraping',
                    'data_points': 1,
                    'validation_passed': True,
                    'last_updated': datetime.now().isoformat()
                }
            else:
                print(f"Web scraping incomplete for {name}: price={current_price}, high={daily_high}, low={daily_low}")
                return None
                
        except Exception as e:
            print(f"Web scraping failed for {name}: {e}")
            return None
    
    def fetch_exact_intraday_data(self, symbol, name):
        """Fetch exact intraday data using Yahoo Finance methodology"""
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Method 1: Try 1-minute data for current trading day
            print(f"Attempting 1-minute data for {symbol}...")
            minute_data = self.get_1_minute_current_day(ticker, symbol)
            
            if minute_data is not None and len(minute_data) > 10:  # Sufficient data points
                return self.calculate_ranges_from_intraday(minute_data, '1min')
            
            # Method 2: Try 5-minute data  
            print(f"Attempting 5-minute data for {symbol}...")
            five_min_data = self.get_5_minute_current_day(ticker, symbol)
            
            if five_min_data is not None and len(five_min_data) > 5:
                return self.calculate_ranges_from_intraday(five_min_data, '5min')
            
            # Method 3: Try hourly data for current day
            print(f"Attempting hourly data for {symbol}...")
            hourly_data = self.get_hourly_current_day(ticker, symbol)
            
            if hourly_data is not None and len(hourly_data) > 0:
                return self.calculate_ranges_from_intraday(hourly_data, 'hourly')
            
            # Method 4: Direct Yahoo Finance API call
            print(f"Attempting direct Yahoo API for {symbol}...")
            return self.get_direct_yahoo_data(symbol)
            
        except Exception as e:
            raise Exception(f"All intraday methods failed for {symbol}: {e}")
    
    def get_1_minute_current_day(self, ticker, symbol):
        """Get 1-minute data for current trading day"""
        try:
            # Get 1-minute data for last 2 days to ensure we have today's data
            data = ticker.history(period="2d", interval="1m")
            
            if data.empty:
                return None
            
            # Filter for current trading day in market timezone
            now_et = datetime.now(self.market_tz)
            today_et = now_et.date()
            
            # Convert index to market timezone and filter for today
            data.index = data.index.tz_convert(self.market_tz)
            today_data = data[data.index.date == today_et]
            
            print(f"   1-min data points: {len(today_data)}")
            return today_data if len(today_data) > 0 else None
            
        except Exception as e:
            print(f"   1-minute data failed: {e}")
            return None
    
    def get_5_minute_current_day(self, ticker, symbol):
        """Get 5-minute data for current trading day"""
        try:
            data = ticker.history(period="2d", interval="5m")
            
            if data.empty:
                return None
            
            # Filter for current day
            now_et = datetime.now(self.market_tz)
            today_et = now_et.date()
            
            data.index = data.index.tz_convert(self.market_tz)
            today_data = data[data.index.date == today_et]
            
            print(f"   5-min data points: {len(today_data)}")
            return today_data if len(today_data) > 0 else None
            
        except Exception as e:
            print(f"   5-minute data failed: {e}")
            return None
    
    def get_hourly_current_day(self, ticker, symbol):
        """Get hourly data for current trading day"""
        try:
            data = ticker.history(period="3d", interval="1h")
            
            if data.empty:
                return None
            
            # Filter for current day
            now_et = datetime.now(self.market_tz)
            today_et = now_et.date()
            
            data.index = data.index.tz_convert(self.market_tz)
            today_data = data[data.index.date == today_et]
            
            print(f"   Hourly data points: {len(today_data)}")
            return today_data if len(today_data) > 0 else None
            
        except Exception as e:
            print(f"   Hourly data failed: {e}")
            return None
    
    def calculate_ranges_from_intraday(self, data, source_type):
        """Calculate exact ranges from intraday data"""
        if data.empty:
            raise Exception("No intraday data available")
        
        # Calculate exact values
        current_price = float(data['Close'].iloc[-1])
        daily_high = float(data['High'].max())
        daily_low = float(data['Low'].min())
        daily_open = float(data['Open'].iloc[0])
        daily_volume = int(data['Volume'].sum())
        
        # Get precise timestamps
        first_time = data.index[0]
        last_time = data.index[-1]
        
        return {
            'current_value': current_price,
            'daily_high': daily_high,
            'daily_low': daily_low,
            'daily_open': daily_open,
            'daily_volume': daily_volume,
            'daily_range': daily_high - daily_low,
            'data_source': f'{source_type}_intraday',
            'data_points': len(data),
            'first_timestamp': first_time.isoformat(),
            'last_timestamp': last_time.isoformat(),
            'trading_session_complete': len(data) > 300  # Rough indicator
        }
    
    def get_direct_yahoo_data(self, symbol):
        """Direct Yahoo Finance API call as fallback"""
        try:
            # Yahoo Finance API endpoint
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            
            params = {
                'interval': '1m',
                'range': '1d',
                'includePrePost': 'false'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self.parse_yahoo_api_response(data, symbol)
            else:
                raise Exception(f"Yahoo API returned status {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Direct Yahoo API failed: {e}")
    
    def parse_yahoo_api_response(self, data, symbol):
        """Parse Yahoo Finance API response"""
        try:
            result = data['chart']['result'][0]
            meta = result['meta']
            
            # Get current values from meta
            current_price = meta.get('regularMarketPrice', 0)
            daily_high = meta.get('regularMarketDayHigh', 0)
            daily_low = meta.get('regularMarketDayLow', 0)
            daily_open = meta.get('regularMarketOpen', 0)
            daily_volume = meta.get('regularMarketVolume', 0)
            
            # Get historical data for validation
            quotes = result.get('indicators', {}).get('quote', [{}])[0]
            highs = [h for h in quotes.get('high', []) if h is not None]
            lows = [l for l in quotes.get('low', []) if l is not None]
            
            # Use the maximum high and minimum low from intraday data
            if highs and lows:
                intraday_high = max(highs)
                intraday_low = min(lows)
                
                # Use intraday values if they're more extreme
                daily_high = max(daily_high, intraday_high)
                daily_low = min(daily_low, intraday_low)
            
            return {
                'current_value': float(current_price),
                'daily_high': float(daily_high),
                'daily_low': float(daily_low),
                'daily_open': float(daily_open),
                'daily_volume': int(daily_volume),
                'daily_range': float(daily_high - daily_low),
                'data_source': 'yahoo_api_direct',
                'data_points': len(highs),
                'trading_session_complete': True
            }
            
        except Exception as e:
            raise Exception(f"Failed to parse Yahoo API response: {e}")
    
    def validate_yahoo_methodology(self, data, symbol):
        """Validate data matches Yahoo Finance methodology"""
        
        # Yahoo Finance validation rules
        current = data['current_value']
        high = data['daily_high']
        low = data['daily_low']
        
        # Rule 1: Current price should be within daily range
        if current > high:
            print(f"WARNING: Current price ({current}) above daily high ({high}), adjusting...")
            data['daily_high'] = current
        
        if current < low:
            print(f"WARNING: Current price ({current}) below daily low ({low}), adjusting...")
            data['daily_low'] = current
        
        # Rule 2: High must be >= Low
        if high < low:
            print(f"WARNING: High ({high}) less than low ({low}), swapping...")
            data['daily_high'], data['daily_low'] = low, high
        
        # Rule 3: Range validation (should be reasonable)
        range_pct = ((data['daily_high'] - data['daily_low']) / current) * 100
        if range_pct > 10:  # More than 10% range seems unusual
            print(f"WARNING: Unusual daily range: {range_pct:.2f}%")
        
        # Add validation timestamp
        data['validated_at'] = datetime.now().isoformat()
        data['validation_passed'] = True
        
        return data
    
    def get_enhanced_fallback_data(self, symbol, name):
        """Enhanced fallback that attempts to fetch real-time data"""
        
        try:
            print(f"Attempting enhanced fallback for {symbol}...")
            
            # Try direct yfinance call as last resort
            ticker = yf.Ticker(symbol)
            
            # Get today's data with multiple intervals
            today_1d = ticker.history(period="1d", interval="1d")
            today_1h = ticker.history(period="1d", interval="1h")
            
            if not today_1d.empty:
                # Use daily data for high/low if available
                current_price = float(today_1d['Close'].iloc[-1])
                daily_high = float(today_1d['High'].iloc[-1])
                daily_low = float(today_1d['Low'].iloc[-1])
                daily_open = float(today_1d['Open'].iloc[-1])
                daily_volume = float(today_1d['Volume'].iloc[-1])
                
                print(f"Enhanced fallback SUCCESS for {symbol}:")
                print(f"  High: {daily_high:.2f}, Low: {daily_low:.2f}, Current: {current_price:.2f}")
                
                return {
                    'current_value': current_price,
                    'daily_high': daily_high,
                    'daily_low': daily_low,
                    'daily_open': daily_open,
                    'daily_volume': daily_volume,
                    'daily_range': daily_high - daily_low,
                    'data_source': 'enhanced_fallback_1d',
                    'validation_passed': True,
                    'last_updated': datetime.now().isoformat()
                }
            
            elif not today_1h.empty:
                # Use hourly data to calculate ranges
                current_price = float(today_1h['Close'].iloc[-1])
                daily_high = float(today_1h['High'].max())
                daily_low = float(today_1h['Low'].min())
                daily_open = float(today_1h['Open'].iloc[0])
                daily_volume = float(today_1h['Volume'].sum())
                
                print(f"Enhanced fallback SUCCESS (hourly) for {symbol}:")
                print(f"  High: {daily_high:.2f}, Low: {daily_low:.2f}, Current: {current_price:.2f}")
                
                return {
                    'current_value': current_price,
                    'daily_high': daily_high,
                    'daily_low': daily_low,
                    'daily_open': daily_open,
                    'daily_volume': daily_volume,
                    'daily_range': daily_high - daily_low,
                    'data_source': 'enhanced_fallback_1h',
                    'validation_passed': True,
                    'last_updated': datetime.now().isoformat()
                }
            
        except Exception as e:
            print(f"Enhanced fallback failed for {symbol}: {e}")
        
        # Only use static fallback as absolute last resort
        print(f"WARNING: Using static fallback for {symbol} - data may be outdated")
        return self.get_static_fallback_data(symbol, name)
    
    def get_static_fallback_data(self, symbol, name):
        """Static fallback with warning - only used when all else fails"""
        
        # Basic fallback values - these should rarely be used
        if symbol == '^NDX':
            base_value = 23000.0
        elif symbol == '^DJI':
            base_value = 44000.0
        else:  # Gold
            base_value = 3400.0
        
        # Generate reasonable range based on typical volatility
        range_pct = 0.015  # 1.5% typical daily range
        daily_range = base_value * range_pct
        
        return {
            'current_value': base_value,
            'daily_high': base_value + (daily_range * 0.6),
            'daily_low': base_value - (daily_range * 0.4),
            'daily_open': base_value - (daily_range * 0.2),
            'daily_volume': 0,
            'daily_range': daily_range,
            'data_source': 'static_fallback_warning',
            'validation_passed': False,
            'last_updated': datetime.now().isoformat(),
            'warning': 'Static fallback data - may not reflect current market values'
        }
    
    def get_previous_close_data(self, symbol):
        """Get previous trading day close for net change calculation"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get last 5 days to ensure we capture previous trading day
            historical_data = ticker.history(period="5d", interval="1d")
            
            if len(historical_data) < 2:
                raise Exception(f"Insufficient historical data for {symbol}")
            
            # Get previous trading day (second to last)
            previous_close = historical_data['Close'].iloc[-2]
            previous_date = historical_data.index[-2].strftime('%Y-%m-%d')
            
            return {
                'close': float(previous_close),
                'date': previous_date,
                'source': 'daily_historical'
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Previous trading day data failed for {symbol}: {e}")
            # Return fallback based on symbol
            fallback_values = {
                '^NDX': 22831.07,   # NASDAQ-100 previous close estimate
                '^DJI': 44152.44,   # DOW previous close estimate
                'GC=F': 3409.40     # GOLD previous close estimate
            }
            return {
                'close': fallback_values.get(symbol, 0.0),
                'date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                'source': 'fallback'
            }