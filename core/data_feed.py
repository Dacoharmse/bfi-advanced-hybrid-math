"""
Enhanced Data Feed Service for BFI Signals
Uses multiple data sources with fallback mechanisms for reliable market data
"""

import requests
import yfinance as yf
from datetime import datetime, timedelta
import time
import logging
import json
import pandas as pd

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
                'yahoo_finance': {
                    'enabled': True,
                    'rate_limit': 100
                },
                'alpha_vantage': {
                    'enabled': True,
                    'api_key': 'demo',
                    'base_url': 'https://www.alphavantage.co/query',
                    'rate_limit': 5
                },
                'finnhub': {
                    'enabled': True,
                    'api_key': 'demo',
                    'base_url': 'https://finnhub.io/api/v1',
                    'rate_limit': 60
                }
            }
            # Updated symbols with more reliable options
            self.symbols = {
                'nasdaq': {
                    'yahoo_finance': '^NDX',
                    'yahoo_finance_backup': '^IXIC',
                    'alpha_vantage': 'NDX'
                },
                'gold': {
                    'yahoo_finance': 'GC=F',  # Gold Futures (COMEX values)
                    'yahoo_finance_backup': 'XAUUSD=X',  # Gold spot
                    'yahoo_finance_backup2': 'GLD',  # Gold ETF
                    'alpha_vantage': 'XAUUSD'
                },
                'dow': {
                    'yahoo_finance': '^DJI',  # US30 (as requested)
                    'yahoo_finance_backup': 'DJIA',  # DJIA alternative
                    'yahoo_finance_backup2': 'DIA',  # Dow ETF
                    'alpha_vantage': 'DJI'
                }
            }
        
        self.last_request_time = {}
        self.request_count = {}
        self.connection_status = {}
        self.last_successful_fetch = {}
        
        # Setup logging
        self.setup_logging()
        
        # Test initial connection
        self.test_yahoo_connection()

    def setup_logging(self):
        """Setup detailed logging for debugging"""
        self.logger = logging.getLogger('EnhancedDataFeed')
        self.logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def test_yahoo_connection(self):
        """Test Yahoo Finance API connectivity"""
        try:
            self.logger.info("🔍 Testing Yahoo Finance connection...")
            test_data = yf.download('^IXIC', period='1d', interval='1m', timeout=10)
            if not test_data.empty:
                self.connection_status['yahoo_finance'] = True
                self.logger.info("✅ Yahoo Finance connection successful")
                return True
            else:
                self.connection_status['yahoo_finance'] = False
                self.logger.warning("⚠️ Yahoo Finance connection failed - empty data")
                return False
        except Exception as e:
            self.connection_status['yahoo_finance'] = False
            self.logger.error(f"❌ Yahoo Finance connection failed: {str(e)}")
            return False

    def validate_symbol(self, symbol: str) -> bool:
        """Validate if a symbol is likely to work"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if info and info.get('regularMarketPrice'):
                self.logger.info(f"✅ Symbol {symbol} validated successfully")
                return True
            else:
                self.logger.warning(f"⚠️ Symbol {symbol} validation failed - no market price")
                return False
        except Exception as e:
            self.logger.error(f"❌ Symbol {symbol} validation error: {str(e)}")
            return False

    def _rate_limit_check(self, source):
        """Check if we can make a request to the given source"""
        if source not in self.last_request_time:
            return True
            
        now = time.time()
        time_since_last = now - self.last_request_time[source]
        rate_limit = self.sources[source]['rate_limit']
        
        # Convert rate limit to seconds between requests
        min_interval = 60 / rate_limit
        
        # Add extra spacing to avoid rate limits
        if source == 'yahoo_finance':
            min_interval = max(min_interval, 2)  # At least 2 seconds between Yahoo requests
        
        return time_since_last >= min_interval
    
    def _update_request_time(self, source):
        """Update the last request time for a source"""
        self.last_request_time[source] = time.time()
    
    def fetch_with_fallback(self, symbol_key: str):
        """Try primary symbol, then alternatives if it fails"""
        symbol_config = self.symbols[symbol_key]
        symbols_to_try = []
        
        # Primary symbol
        if 'yahoo_finance' in symbol_config:
            symbols_to_try.append(symbol_config['yahoo_finance'])
        
        # Backup symbols
        for key in symbol_config:
            if key.startswith('yahoo_finance_backup'):
                symbols_to_try.append(symbol_config[key])
        
        self.logger.info(f"🔄 Attempting to fetch {symbol_key} with {len(symbols_to_try)} symbols")
        
        for symbol in symbols_to_try:
            try:
                self.logger.info(f"🔄 Trying Yahoo Finance symbol: {symbol} for {symbol_key}")
                
                # Validate symbol first
                if not self.validate_symbol(symbol):
                    self.logger.warning(f"⚠️ Symbol {symbol} failed validation, trying next...")
                    continue
                
                ticker = yf.Ticker(symbol)
                
                # Add timeout and retry logic with exponential backoff
                max_retries = 3
                retry_count = 0
                base_delay = 2
                
                while retry_count < max_retries:
                    try:
                        self.logger.info(f"📊 Fetching data for {symbol} (attempt {retry_count + 1}/{max_retries})")
                        current_data = ticker.history(period='2d', timeout=15)
                        break
                    except Exception as retry_error:
                        retry_count += 1
                        delay = base_delay * (2 ** (retry_count - 1))  # Exponential backoff
                        self.logger.warning(f"⚠️ Retry {retry_count}/{max_retries} for {symbol}: {str(retry_error)}")
                        if retry_count < max_retries:
                            self.logger.info(f"⏳ Waiting {delay} seconds before retry...")
                            time.sleep(delay)
                        else:
                            raise retry_error
                
                self.logger.info(f"📊 Data length for {symbol}: {len(current_data)} rows")
                
                if len(current_data) >= 2:
                    current_price = current_data['Close'].iloc[-1]
                    previous_price = current_data['Close'].iloc[-2]
                    today_data = current_data.iloc[-1]
                    
                    self.logger.info(f"💰 {symbol} - Current: {current_price}, Previous: {previous_price}")
                    
                    # Enhanced data validation
                    if self.validate_market_data(current_price, previous_price, symbol):
                        change = current_price - previous_price
                        change_percent = (change / previous_price) * 100
                        
                        self._update_request_time('yahoo_finance')
                        self.last_successful_fetch[symbol_key] = datetime.now()
                        
                        result = {
                            'price': current_price,
                            'previous_close': previous_price,
                            'change': change,
                            'change_percent': change_percent,
                            'high': today_data['High'],
                            'low': today_data['Low'],
                            'source': f'Yahoo Finance ({symbol})',
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        self.logger.info(f"✅ Successfully fetched {symbol_key} data from {symbol}")
                        return result
                    else:
                        self.logger.warning(f"⚠️ Data validation failed for {symbol}")
                else:
                    self.logger.warning(f"⚠️ Insufficient data for {symbol}: {len(current_data)} rows")
                    # Try to get info about the ticker
                    try:
                        info = ticker.info
                        self.logger.info(f"ℹ️ Ticker info for {symbol}: {info.get('shortName', 'Unknown')}")
                    except:
                        self.logger.info(f"ℹ️ No ticker info available for {symbol}")
                        
            except Exception as e:
                self.logger.error(f"❌ Yahoo Finance error for {symbol_key} ({symbol}): {str(e)}")
                # Enhanced error categorization
                error_msg = str(e).lower()
                if "symbol may be delisted" in error_msg:
                    self.logger.error(f"🚫 Symbol {symbol} may be delisted or unavailable")
                elif "rate limit" in error_msg:
                    self.logger.error(f"⏰ Rate limit hit for {symbol}")
                elif "timeout" in error_msg:
                    self.logger.error(f"⏱️ Timeout for {symbol}")
                elif "connection" in error_msg:
                    self.logger.error(f"🌐 Connection error for {symbol}")
                elif "not found" in error_msg:
                    self.logger.error(f"🔍 Symbol {symbol} not found")
                continue
        
        self.logger.error(f"❌ All symbols failed for {symbol_key}")
        return None

    def validate_market_data(self, current_price, previous_price, symbol):
        """Validate market data quality"""
        try:
            # Check for valid prices
            if not (isinstance(current_price, (int, float)) and isinstance(previous_price, (int, float))):
                self.logger.warning(f"⚠️ Invalid price types for {symbol}")
                return False
            
            # Check for positive prices
            if current_price <= 0 or previous_price <= 0:
                self.logger.warning(f"⚠️ Non-positive prices for {symbol}: current={current_price}, previous={previous_price}")
                return False
            
            # Check for reasonable price ranges based on symbol
            if symbol.startswith('^DJI') or symbol == 'DJIA':
                # Dow Jones should be in 20,000-50,000 range
                if not (20000 <= current_price <= 50000):
                    self.logger.warning(f"⚠️ Unusual Dow Jones price: {current_price}")
                    return False
            elif symbol.startswith('GC') or 'GOLD' in symbol.upper():
                # Gold should be in 1,000-5,000 range
                if not (1000 <= current_price <= 5000):
                    self.logger.warning(f"⚠️ Unusual Gold price: {current_price}")
                    return False
            elif symbol.startswith('^NDX'):
                # NASDAQ should be in 10,000-30,000 range
                if not (10000 <= current_price <= 30000):
                    self.logger.warning(f"⚠️ Unusual NASDAQ price: {current_price}")
                    return False
            
            # Check for reasonable change percentage (not more than 50% in one day)
            change_percent = abs((current_price - previous_price) / previous_price * 100)
            if change_percent > 50:
                self.logger.warning(f"⚠️ Unusual price change for {symbol}: {change_percent:.2f}%")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Data validation error for {symbol}: {str(e)}")
            return False

    def get_yahoo_finance_data(self, symbol_key):
        """Get data from Yahoo Finance with enhanced error handling"""
        if not self.sources['yahoo_finance']['enabled']:
            self.logger.warning(f"⚠️ Yahoo Finance disabled for {symbol_key}")
            return None
            
        if not self._rate_limit_check('yahoo_finance'):
            self.logger.warning(f"⚠️ Rate limit active for Yahoo Finance")
            return None
        
        return self.fetch_with_fallback(symbol_key)
    
    def get_finnhub_data(self, symbol_key):
        """Get data from Finnhub API"""
        if not self.sources['finnhub']['enabled']:
            return None
            
        if not self._rate_limit_check('finnhub'):
            return None
            
        try:
            # Map symbol keys to Finnhub symbols
            finnhub_symbols = {
                'nasdaq': '^NDX',
                'gold': 'XAUUSD',
                'dow': '^DJI'
            }
            
            symbol = finnhub_symbols.get(symbol_key)
            if not symbol:
                return None
                
            params = {
                'symbol': symbol,
                'token': self.sources['finnhub']['api_key']
            }
            
            response = requests.get(
                f"{self.sources['finnhub']['base_url']}/quote",
                params=params,
                timeout=10
            )
            
            self._update_request_time('finnhub')
            
            if response.status_code == 200:
                data = response.json()
                
                if 'c' in data and data['c'] > 0:
                    current_price = data['c']
                    previous_close = data['pc']
                    change = current_price - previous_close
                    change_percent = (change / previous_close) * 100
                    
                    return {
                        'price': current_price,
                        'previous_close': previous_close,
                        'change': change,
                        'change_percent': change_percent,
                        'high': data.get('h', current_price),
                        'low': data.get('l', current_price),
                        'source': 'Finnhub'
                    }
                    
        except Exception as e:
            self.logger.error(f"❌ Finnhub error for {symbol_key}: {str(e)}")
            
        return None
    
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
                    
                    return {
                        'price': current_price,
                        'previous_close': previous_close,
                        'change': change,
                        'change_percent': change_percent,
                        'high': current_price,  # Simplified for demo API
                        'low': current_price,   # Simplified for demo API
                        'source': 'Alpha Vantage'
                    }
                    
        except Exception as e:
            self.logger.error(f"❌ Alpha Vantage error for {symbol_key}: {str(e)}")
            
        return None
    
    def get_market_data(self, symbol_key):
        """Get market data with enhanced fallback to multiple sources"""
        self.logger.info(f"📊 Fetching {symbol_key.upper()} data...")
        
        # Add delay between requests to avoid rate limits
        if self.last_request_time:
            time_since_last = time.time() - max(self.last_request_time.values())
            if time_since_last < 3:  # At least 3 seconds between any requests
                sleep_time = 3 - time_since_last
                self.logger.info(f"⏳ Waiting {sleep_time:.1f}s to avoid rate limits...")
                time.sleep(sleep_time)
        
        # Try Yahoo Finance first (most reliable)
        data = self.get_yahoo_finance_data(symbol_key)
        if data:
            self.logger.info(f"✅ {symbol_key.upper()} data from Yahoo Finance")
            return data
        
        # Try Finnhub as second option
        data = self.get_finnhub_data(symbol_key)
        if data:
            self.logger.info(f"✅ {symbol_key.upper()} data from Finnhub")
            return data
        
        # Try Alpha Vantage as last resort
        data = self.get_alpha_vantage_data(symbol_key)
        if data:
            self.logger.info(f"✅ {symbol_key.upper()} data from Alpha Vantage")
            return data
        
        # If all sources fail
        self.logger.error(f"❌ All data sources failed for {symbol_key}")
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
            price_str = f"{data['price']:.2f}"
            change_str = f"{data['change']:+.2f}"
            change_percent_str = f"{data['change_percent']:+.2f}%"
            prev_close_str = f"{data['previous_close']:.2f}"
            high_str = f"{data['high']:.2f}"
            low_str = f"{data['low']:.2f}"
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

    def get_connection_status(self):
        """Get current connection status for all sources"""
        return self.connection_status

    def get_last_successful_fetch(self):
        """Get timestamp of last successful fetch for each symbol"""
        return self.last_successful_fetch

# Global instance
enhanced_data_feed = EnhancedDataFeed() 