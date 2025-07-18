"""
Enhanced Data Feed Service for BFI Signals
Uses multiple data sources with fallback mechanisms for reliable market data
"""

import requests
import yfinance as yf
from datetime import datetime, timedelta
import time
import logging

class EnhancedDataFeed:
    def __init__(self):
        try:
            from config import config
            self.config = config
            self.sources = config.data_sources
            self.symbols = config.symbols
        except ImportError:
            # Fallback configurations if config module is not available
            self.config = None
            self.sources = {
                'alpha_vantage': {
                    'enabled': True,
                    'api_key': 'demo',
                    'base_url': 'https://www.alphavantage.co/query',
                    'rate_limit': 5
                },
                'yahoo_finance': {
                    'enabled': True,
                    'rate_limit': 100
                }
            }
            self.symbols = {
                'nasdaq': {
                    'alpha_vantage': 'NDX',
                    'yahoo_finance': '^NDX'
                },
                'gold': {
                    'alpha_vantage': 'XAUUSD',
                    'yahoo_finance': 'GC=F'
                },
                'dow': {
                    'alpha_vantage': 'DJI',
                    'yahoo_finance': '^DJI'
                }
            }
        
        self.last_request_time = {}
        self.request_count = {}
        
    def _rate_limit_check(self, source):
        """Check if we can make a request to the given source"""
        if source not in self.last_request_time:
            return True
            
        now = time.time()
        time_since_last = now - self.last_request_time[source]
        rate_limit = self.sources[source]['rate_limit']
        
        # Convert rate limit to seconds between requests
        min_interval = 60 / rate_limit
        
        return time_since_last >= min_interval
    
    def _update_request_time(self, source):
        """Update the last request time for a source"""
        self.last_request_time[source] = time.time()
    
    def get_alpha_vantage_data(self, symbol_key):
        """Get data from Alpha Vantage API"""
        if not self.sources['alpha_vantage']['enabled']:
            return None
            
        if not self._rate_limit_check('alpha_vantage'):
            return None
            
        try:
            symbol = self.symbols[symbol_key]['alpha_vantage']
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.sources['alpha_vantage']['api_key']
            }
            
            response = requests.get(
                self.sources['alpha_vantage']['base_url'],
                params=params,
                timeout=10
            )
            
            self._update_request_time('alpha_vantage')
            
            if response.status_code == 200:
                data = response.json()
                
                if 'Global Quote' in data and data['Global Quote']:
                    quote = data['Global Quote']
                    
                    current_price = float(quote.get('05. price', 0))
                    previous_close = float(quote.get('08. previous close', 0))
                    change = float(quote.get('09. change', 0))
                    change_percent_str = quote.get('10. change percent', '0%')
                    
                    # Clean up percentage string
                    change_percent = float(change_percent_str.replace('%', ''))
                    
                    # Get high/low from intraday data
                    high, low = self._get_alpha_vantage_intraday(symbol)
                    
                    return {
                        'price': current_price,
                        'previous_close': previous_close,
                        'change': change,
                        'change_percent': change_percent,
                        'high': high or current_price,
                        'low': low or current_price,
                        'source': 'Alpha Vantage'
                    }
                    
        except Exception as e:
            print(f"❌ Alpha Vantage error for {symbol_key}: {str(e)}")
            
        return None
    
    def _get_alpha_vantage_intraday(self, symbol):
        """Get intraday high/low from Alpha Vantage"""
        try:
            params = {
                'function': 'TIME_SERIES_INTRADAY',
                'symbol': symbol,
                'interval': '1min',
                'apikey': self.sources['alpha_vantage']['api_key']
            }
            
            response = requests.get(
                self.sources['alpha_vantage']['base_url'],
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'Time Series (1min)' in data:
                    time_series = data['Time Series (1min)']
                    today = datetime.now().strftime('%Y-%m-%d')
                    
                    highs = []
                    lows = []
                    
                    for timestamp, values in time_series.items():
                        if timestamp.startswith(today):
                            high = float(values.get('2. high', 0))
                            low = float(values.get('3. low', 0))
                            if high > 0:
                                highs.append(high)
                            if low > 0:
                                lows.append(low)
                    
                    if highs and lows:
                        return max(highs), min(lows)
                        
        except Exception as e:
            print(f"❌ Alpha Vantage intraday error: {str(e)}")
            
        return None, None
    
    def get_yahoo_finance_data(self, symbol_key):
        """Get data from Yahoo Finance"""
        if not self.sources['yahoo_finance']['enabled']:
            return None
            
        if not self._rate_limit_check('yahoo_finance'):
            return None
            
        try:
            symbol = self.symbols[symbol_key]['yahoo_finance']
            ticker = yf.Ticker(symbol)
            current_data = ticker.history(period='2d')
            
            self._update_request_time('yahoo_finance')
            
            if len(current_data) >= 2:
                current_price = current_data['Close'].iloc[-1]
                previous_price = current_data['Close'].iloc[-2]
                today_data = current_data.iloc[-1]
                
                change = current_price - previous_price
                change_percent = (change / previous_price) * 100
                
                return {
                    'price': current_price,
                    'previous_close': previous_price,
                    'change': change,
                    'change_percent': change_percent,
                    'high': today_data['High'],
                    'low': today_data['Low'],
                    'source': 'Yahoo Finance'
                }
                
        except Exception as e:
            print(f"❌ Yahoo Finance error for {symbol_key}: {str(e)}")
            
        return None
    
    def get_market_data(self, symbol_key):
        """Get market data with fallback to multiple sources"""
        print(f"📊 Fetching {symbol_key.upper()} data...")
        
        # Try Alpha Vantage first
        data = self.get_alpha_vantage_data(symbol_key)
        if data:
            print(f"✅ {symbol_key.upper()} data from Alpha Vantage")
            return data
        
        # Fallback to Yahoo Finance
        data = self.get_yahoo_finance_data(symbol_key)
        if data:
            print(f"✅ {symbol_key.upper()} data from Yahoo Finance (fallback)")
            return data
        
        # If all sources fail
        print(f"❌ All data sources failed for {symbol_key}")
        return None
    
    def format_market_data(self, data, symbol_key):
        """Format market data for display"""
        if not data:
            return {
                'price': '--',
                'change': '--',
                'changePercent': '--',
                'rawChange': 0,
                'previousClose': '--',
                'high': '--',
                'low': '--',
                'source': 'No Data'
            }
        
        # Format based on symbol type
        if symbol_key == 'gold':
            price_str = f"${data['price']:.2f}"
            change_str = f"{data['change']:+.2f}"
            change_percent_str = f"{data['change_percent']:+.2f}%"
            prev_close_str = f"${data['previous_close']:.2f}"
            high_str = f"${data['high']:.2f}"
            low_str = f"${data['low']:.2f}"
        else:
            price_str = f"{data['price']:,.2f}"
            change_str = f"{data['change']:+.2f}"
            change_percent_str = f"{data['change_percent']:+.2f}%"
            prev_close_str = f"{data['previous_close']:,.2f}"
            high_str = f"{data['high']:,.2f}"
            low_str = f"{data['low']:,.2f}"
        
        return {
            'price': price_str,
            'change': change_str,
            'changePercent': change_percent_str,
            'rawChange': data['change'],
            'previousClose': prev_close_str,
            'high': high_str,
            'low': low_str,
            'source': data['source']
        }

# Global instance
enhanced_data_feed = EnhancedDataFeed() 