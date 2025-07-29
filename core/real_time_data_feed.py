#!/usr/bin/env python3
"""
Real-time Yahoo Finance Data Feed for BFI Signals
Provides accurate, live market data for NASDAQ, DOW, and GOLD
"""

import yfinance as yf
import requests
import json
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, Optional, Any

class RealTimeDataFeed:
    def __init__(self):
        """Initialize with correct Yahoo Finance symbols"""
        self.symbols = {
            'nasdaq': '^NDX',   # NASDAQ 100 Index - NAS100
            'dow': '^DJI',      # Dow Jones Industrial Average - US30
            'gold': 'GC=F'      # Gold Futures (COMEX) - GOLD
        }
        
        # Alternative symbols as fallback
        self.fallback_symbols = {
            'nasdaq': '^IXIC',  # NASDAQ Composite (fallback)
            'dow': 'DIA',       # SPDR Dow Jones ETF
            'gold': 'XAUUSD=X'  # Gold Spot Price
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('RealTimeDataFeed')
        
        # Cache to avoid excessive API calls - aligned with dashboard refresh rate
        self.cache = {}
        self.cache_duration = 300  # 5 minutes cache (300 seconds)
        self.last_request_time = {}
        
        print("Real-time Yahoo Finance data feed initialized")
    
    def get_live_market_data(self) -> Dict[str, Any]:
        """Get real-time market data from Yahoo Finance"""
        market_data = {}
        
        for name, symbol in self.symbols.items():
            try:
                self.logger.info(f"Fetching real-time data for {name.upper()} ({symbol})")
                
                # Check cache first
                cached_data = self.get_cached_data(name)
                if cached_data:
                    market_data[name] = cached_data
                    continue
                
                # Rate limiting
                self.respect_rate_limit(name)
                
                # Primary method: yfinance
                data = self.get_yfinance_data(symbol, name)
                
                if not data:
                    # Fallback method: Direct Yahoo API
                    data = self.get_yahoo_api_data(symbol, name)
                
                if not data and name in self.fallback_symbols:
                    # Try fallback symbol
                    fallback_symbol = self.fallback_symbols[name]
                    self.logger.info(f"Trying fallback symbol {fallback_symbol} for {name}")
                    data = self.get_yfinance_data(fallback_symbol, name)
                
                if data:
                    # Cache successful data
                    self.cache_data(name, data)
                    market_data[name] = data
                    self.logger.info(f"Successfully fetched {name.upper()}: ${data['current_value']:.2f}")
                else:
                    # Use default data as last resort
                    market_data[name] = self.get_default_data(name)
                    self.logger.warning(f"Using default data for {name.upper()}")
                    
            except Exception as e:
                self.logger.error(f"Error fetching {name} data: {str(e)}")
                market_data[name] = self.get_default_data(name)
        
        return market_data
    
    def get_yfinance_data(self, symbol: str, name: str) -> Optional[Dict[str, Any]]:
        """Get data using yfinance library"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get current info
            info = ticker.info
            
            # Get recent history for more accurate data
            hist = ticker.history(period="2d", interval="1m")
            
            if hist.empty:
                return None
            
            # Get the most recent data
            current_price = float(hist['Close'].iloc[-1])
            
            # Get previous close (yesterday's close, not previous minute)
            daily_hist = ticker.history(period="5d", interval="1d")
            if len(daily_hist) >= 2:
                previous_close = float(daily_hist['Close'].iloc[-2])
            else:
                previous_close = float(hist['Close'].iloc[0])
            
            # Get today's high and low
            today_data = hist.tail(1440)  # Last 1440 minutes (1 day)
            daily_high = float(today_data['High'].max())
            daily_low = float(today_data['Low'].min())
            
            # Calculate changes
            net_change = current_price - previous_close
            percentage_change = (net_change / previous_close) * 100 if previous_close != 0 else 0
            
            return {
                'current_value': current_price,
                'previous_close': previous_close,
                'net_change': net_change,
                'change_percent': percentage_change,
                'high': daily_high,
                'low': daily_low,
                'display_name': self.get_display_name(name),
                'source': 'yfinance',
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'last_updated': datetime.now().strftime('%H:%M:%S GMT+2')
            }
            
        except Exception as e:
            self.logger.error(f"yfinance error for {symbol}: {str(e)}")
            return None
    
    def get_yahoo_api_data(self, symbol: str, name: str) -> Optional[Dict[str, Any]]:
        """Fallback: Direct Yahoo Finance API"""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                'interval': '1m',
                'range': '1d',
                'includePrePost': 'false'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'chart' in data and data['chart']['result']:
                    result = data['chart']['result'][0]
                    meta = result['meta']
                    
                    current_price = float(meta.get('regularMarketPrice', 0))
                    previous_close = float(meta.get('previousClose', 0))
                    daily_high = float(meta.get('regularMarketDayHigh', current_price))
                    daily_low = float(meta.get('regularMarketDayLow', current_price))
                    
                    net_change = current_price - previous_close
                    percentage_change = (net_change / previous_close) * 100 if previous_close != 0 else 0
                    
                    return {
                        'current_value': current_price,
                        'previous_close': previous_close,
                        'net_change': net_change,
                        'change_percent': percentage_change,
                        'high': daily_high,
                        'low': daily_low,
                        'display_name': self.get_display_name(name),
                        'source': 'yahoo_api',
                        'symbol': symbol,
                        'timestamp': datetime.now().isoformat(),
                        'last_updated': datetime.now().strftime('%H:%M:%S GMT+2')
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Yahoo API error for {symbol}: {str(e)}")
            return None
    
    def get_display_name(self, name: str) -> str:
        """Get proper display name for instruments"""
        display_names = {
            'nasdaq': 'NASDAQ (NAS100)',
            'dow': 'DOW JONES (US30)',
            'gold': 'GOLD (XAUUSD)'
        }
        return display_names.get(name, name.upper())
    
    def get_cached_data(self, name: str) -> Optional[Dict[str, Any]]:
        """Get cached data if still valid"""
        if name in self.cache:
            cached_data, timestamp = self.cache[name]
            if time.time() - timestamp < self.cache_duration:
                self.logger.info(f"Using cached data for {name}")
                return cached_data
        return None
    
    def cache_data(self, name: str, data: Dict[str, Any]):
        """Cache data with timestamp"""
        self.cache[name] = (data, time.time())
    
    def respect_rate_limit(self, name: str):
        """Respect rate limits"""
        if name in self.last_request_time:
            elapsed = time.time() - self.last_request_time[name]
            if elapsed < 2:  # 2 seconds between requests
                sleep_time = 2 - elapsed
                time.sleep(sleep_time)
        self.last_request_time[name] = time.time()
    
    def get_default_data(self, name: str) -> Dict[str, Any]:
        """Default data when all sources fail"""
        # Use realistic base prices as fallback
        default_prices = {
            'nasdaq': {'price': 23180.00, 'previous': 23065.00},
            'dow': {'price': 44320.00, 'previous': 44340.00},
            'gold': {'price': 3410.00, 'previous': 3358.00}
        }
        
        base_data = default_prices.get(name, {'price': 1000.00, 'previous': 1000.00})
        current = base_data['price']
        previous = base_data['previous']
        net_change = current - previous
        
        return {
            'current_value': current,
            'previous_close': previous,
            'net_change': net_change,
            'change_percent': (net_change / previous) * 100,
            'high': current + 50,
            'low': current - 50,
            'display_name': self.get_display_name(name),
            'source': 'fallback',
            'symbol': 'FALLBACK',
            'timestamp': datetime.now().isoformat(),
            'last_updated': datetime.now().strftime('%H:%M:%S GMT+2'),
            'error': 'Live data temporarily unavailable'
        }
    
    def test_connection(self) -> bool:
        """Test connection to Yahoo Finance"""
        try:
            test_data = self.get_yfinance_data('^IXIC', 'nasdaq')
            if test_data and test_data.get('current_value', 0) > 0:
                self.logger.info("Yahoo Finance connection test successful")
                return True
            else:
                self.logger.error("Yahoo Finance connection test failed")
                return False
        except Exception as e:
            self.logger.error(f"Connection test error: {str(e)}")
            return False

# Global instance for Flask app
real_time_data_feed = RealTimeDataFeed()

def get_real_time_market_data() -> Dict[str, Any]:
    """Main function to get real-time market data - used by Flask app"""
    try:
        data = real_time_data_feed.get_live_market_data()
        
        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': data,
            'message': 'Real-time market data fetched from Yahoo Finance',
            'source': 'yahoo_finance'
        }
    except Exception as e:
        real_time_data_feed.logger.error(f"Error in get_real_time_market_data: {str(e)}")
        return {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'data': {},
            'message': f'Failed to fetch real-time market data: {str(e)}',
            'source': 'error'
        }

if __name__ == "__main__":
    # Test the real-time data feed
    print("Testing Real-time Yahoo Finance Data Feed...")
    
    feed = RealTimeDataFeed()
    
    # Test connection
    if feed.test_connection():
        print("Connection test passed")
        
        # Fetch all data
        market_data = feed.get_live_market_data()
        
        print("\nReal-time Market Data:")
        print("=" * 50)
        
        for instrument, data in market_data.items():
            if data:
                print(f"\n{data.get('display_name', instrument)}:")
                print(f"  Current: ${data['current_value']:,.2f}")
                print(f"  Previous Close: ${data['previous_close']:,.2f}")
                print(f"  Net Change: {data['net_change']:+.2f}")
                print(f"  Change %: {data['change_percent']:+.2f}%")
                print(f"  High: ${data['high']:,.2f}")
                print(f"  Low: ${data['low']:,.2f}")
                print(f"  Source: {data['source']}")
                print(f"  Updated: {data['last_updated']}")
        
        print("\nReal-time data feed test completed successfully!")
    else:
        print("Connection test failed")