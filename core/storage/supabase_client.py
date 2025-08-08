#!/usr/bin/env python3
"""
Supabase Client for BFI Signals
Handles all Supabase database operations
"""

import os
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from decimal import Decimal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseClient:
    """Supabase client for BFI Signals data operations"""
    
    def __init__(self):
        """Initialize Supabase client with credentials"""
        self.url = "https://kiiugsmjybncvtrdshdk.supabase.co"
        self.key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtpaXVnc21qeWJuY3Z0cmRzaGRrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4NzY2ODIsImV4cCI6MjA2OTQ1MjY4Mn0.4GRc469_WzsUERgsqikeGQ2SQZwJpR4HPW1kkqXR3Sw"
        
        try:
            # Try to import supabase
            from supabase import create_client, Client
            self.supabase: Client = create_client(self.url, self.key)
            self.available = True
            logger.info("✅ Supabase client initialized successfully")
        except ImportError:
            logger.warning("⚠️ Supabase library not installed. Install with: pip install supabase")
            self.supabase = None
            self.available = False
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}")
            self.supabase = None
            self.available = False
    
    def test_connection(self) -> bool:
        """Test connection to Supabase"""
        if not self.available:
            return False
        
        try:
            # Try to query the market_close_data table
            response = self.supabase.table('market_close_data').select('*').limit(1).execute()
            logger.info("✅ Supabase connection test successful")
            return True
        except Exception as e:
            logger.error(f"❌ Supabase connection test failed: {e}")
            return False
    
    def save_market_close_data(self, capture_date: date, market_data: Dict[str, Dict]) -> bool:
        """
        Save market closing data to Supabase
        
        Args:
            capture_date: Date of market close
            market_data: Dictionary with symbol data
            
        Returns:
            bool: Success status
        """
        if not self.available:
            return False
        
        try:
            records = []
            for symbol, data in market_data.items():
                if not data:
                    continue
                
                # Convert string prices to float
                price = float(str(data.get('price', '0')).replace(',', ''))
                change_amount = float(str(data.get('change', '0')).replace('+', ''))
                change_percent = float(str(data.get('changePercent', '0%')).replace('%', '').replace('+', ''))
                previous_close = float(str(data.get('previousClose', '0')).replace(',', ''))
                daily_high = float(str(data.get('high', '0')).replace(',', ''))
                daily_low = float(str(data.get('low', '0')).replace(',', ''))
                raw_change = float(data.get('rawChange', 0))
                
                record = {
                    'capture_date': capture_date.isoformat(),
                    'symbol': symbol.upper(),
                    'price': price,
                    'change_amount': change_amount,
                    'change_percent': change_percent,
                    'previous_close': previous_close,
                    'daily_high': daily_high,
                    'daily_low': daily_low,
                    'raw_change': raw_change,
                    'source': 'bfi_signals'
                }
                records.append(record)
            
            if records:
                # Use upsert to handle conflicts
                response = self.supabase.table('market_close_data').upsert(
                    records, 
                    on_conflict='capture_date,symbol'
                ).execute()
                
                logger.info(f"✅ Saved {len(records)} market close records to Supabase for {capture_date}")
                return True
            else:
                logger.warning("⚠️ No valid market data to save")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to save market close data to Supabase: {e}")
            return False
    
    def get_market_close_data(self, target_date: date, symbol: Optional[str] = None) -> Dict:
        """
        Get market closing data from Supabase
        
        Args:
            target_date: Date to retrieve data for
            symbol: Optional specific symbol to retrieve
            
        Returns:
            Dict: Market data organized by symbol
        """
        if not self.available:
            return {}
        
        try:
            query = self.supabase.table('market_close_data').select('*').eq('capture_date', target_date.isoformat())
            
            if symbol:
                query = query.eq('symbol', symbol.upper())
            
            response = query.execute()
            
            # Organize data by symbol
            market_data = {}
            for record in response.data:
                symbol_key = record['symbol'].lower()
                market_data[symbol_key] = {
                    'price': f"{record['price']:,.2f}",
                    'change': f"{record['change_amount']:+.2f}",
                    'changePercent': f"{record['change_percent']:+.2f}%",
                    'rawChange': record['raw_change'],
                    'previousClose': f"{record['previous_close']:,.2f}",
                    'high': f"{record['daily_high']:,.2f}",
                    'low': f"{record['daily_low']:,.2f}",
                    'timestamp': record['captured_at'],
                    'date': record['capture_date']
                }
            
            logger.info(f"✅ Retrieved {len(market_data)} symbols from Supabase for {target_date}")
            return market_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get market close data from Supabase: {e}")
            return {}
    
    def save_signal(self, signal_data: Dict[str, Any]) -> bool:
        """
        Save generated signal to Supabase
        
        Args:
            signal_data: Complete signal dictionary
            
        Returns:
            bool: Success status
        """
        if not self.available:
            return False
        
        try:
            # Extract key fields for structured storage
            record = {
                'signal_date': datetime.now().date().isoformat(),
                'symbol': signal_data.get('symbol', ''),
                'signal_type': 'auto',  # or detect type
                'bias': signal_data.get('bias', ''),
                'current_value': float(signal_data.get('current_value', 0)),
                'take_profit': float(signal_data.get('take_profit', 0)),
                'entry1': float(signal_data.get('entry1', 0)),
                'entry2': float(signal_data.get('entry2', 0)),
                'sl_tight': float(signal_data.get('sl_tight', 0)),
                'sl_wide': float(signal_data.get('sl_wide', 0)),
                'probability_percentage': int(signal_data.get('probability_percentage', 50)),
                'cv_position': float(signal_data.get('cv_position', 0.5)),
                'signal_data': signal_data,  # Store full signal as JSONB
                'posted_to_discord': False
            }
            
            response = self.supabase.table('signals').insert(record).execute()
            logger.info(f"✅ Saved signal for {record['symbol']} to Supabase")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save signal to Supabase: {e}")
            return False
    
    def log_data_capture(self, capture_date: date, symbols_captured: int, success: bool, error_message: str = None) -> bool:
        """
        Log data capture attempt
        
        Args:
            capture_date: Date of capture attempt
            symbols_captured: Number of symbols captured
            success: Whether capture was successful
            error_message: Error message if failed
            
        Returns:
            bool: Success status
        """
        if not self.available:
            return False
        
        try:
            record = {
                'capture_date': capture_date.isoformat(),
                'symbols_captured': symbols_captured,
                'success': success,
                'error_message': error_message
            }
            
            response = self.supabase.table('data_capture_log').insert(record).execute()
            logger.info(f"✅ Logged data capture for {capture_date}: {symbols_captured} symbols, success: {success}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to log data capture: {e}")
            return False
    
    def get_latest_market_close_data(self) -> Dict:
        """
        Get the most recent market close data from Supabase
        
        Returns:
            Dict: Latest market data organized by symbol
        """
        if not self.available:
            return {}
        
        try:
            # Get the most recent capture date
            response = self.supabase.table('market_close_data').select('capture_date').order('capture_date', desc=True).limit(1).execute()
            
            if not response.data:
                logger.warning("⚠️ No market close data found in Supabase")
                return {}
            
            latest_date = datetime.fromisoformat(response.data[0]['capture_date']).date()
            return self.get_market_close_data(latest_date)
            
        except Exception as e:
            logger.error(f"❌ Failed to get latest market close data: {e}")
            return {}


# Global instance
supabase_client = SupabaseClient()

# Convenience functions
def test_supabase_connection() -> bool:
    """Test Supabase connection"""
    return supabase_client.test_connection()

def save_market_data_to_supabase(capture_date: date, market_data: Dict) -> bool:
    """Save market data to Supabase"""
    return supabase_client.save_market_close_data(capture_date, market_data)

def get_supabase_market_data(target_date: date, symbol: str = None) -> Dict:
    """Get market data from Supabase"""
    return supabase_client.get_market_close_data(target_date, symbol)