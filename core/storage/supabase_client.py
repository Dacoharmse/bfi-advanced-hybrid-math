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
        # Try different URL formats
        self.url = "https://mlcunoaiebghhxjycogb.supabase.co"  
        # Use the correct anon public key
        self.key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1sY3Vub2FpZWJnaGh4anljb2diIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc0MTA3NDEsImV4cCI6MjA3Mjk4Njc0MX0.PXBjFUXPbpl2E5_McuGbWwbtFIORluyltbHhD0a4Zhc"
        self.password = "fiw5Y1uxmLBEcJj3"
        
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

    def init_tables(self) -> bool:
        """Initialize all required tables in Supabase"""
        if not self.available:
            return False
        
        try:
            # Note: In Supabase, we'll create tables via the web interface first
            # This method can be used to verify tables exist
            test_queries = [
                self.supabase.table('users').select('id').limit(1),
                self.supabase.table('signal_performance').select('id').limit(1),
                self.supabase.table('user_sessions').select('id').limit(1),
                self.supabase.table('user_notifications').select('id').limit(1),
                self.supabase.table('password_reset_tokens').select('id').limit(1),
                self.supabase.table('journal_entries').select('id').limit(1)
            ]
            
            for query in test_queries:
                query.execute()
            
            logger.info("✅ All Supabase tables verified successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to verify Supabase tables: {e}")
            return False

    # User Management Methods
    def create_user(self, username: str, email: str, password_hash: str, role: str = 'user') -> Optional[Dict]:
        """Create a new user"""
        if not self.available:
            return None
        
        try:
            response = self.supabase.table('users').insert({
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'role': role
            }).execute()
            
            if response.data:
                logger.info(f"✅ User created: {username}")
                return response.data[0]
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to create user: {e}")
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        if not self.available:
            return None
        
        try:
            response = self.supabase.table('users').select('*').eq('username', username).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"❌ Failed to get user by username: {e}")
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        if not self.available:
            return None
        
        try:
            response = self.supabase.table('users').select('*').eq('email', email).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"❌ Failed to get user by email: {e}")
            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        if not self.available:
            return None
        
        try:
            response = self.supabase.table('users').select('*').eq('id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"❌ Failed to get user by ID: {e}")
            return None

    def update_user_login(self, user_id: int) -> bool:
        """Update user's last login timestamp"""
        if not self.available:
            return False
        
        try:
            self.supabase.table('users').update({
                'last_login': datetime.now().isoformat()
            }).eq('id', user_id).execute()
            return True
        except Exception as e:
            logger.error(f"❌ Failed to update user login: {e}")
            return False

    # Session Management Methods
    def create_session(self, user_id: int, session_token: str, expires_at: datetime, ip_address: str = None, user_agent: str = None) -> bool:
        """Create a new user session"""
        if not self.available:
            return False
        
        try:
            self.supabase.table('user_sessions').insert({
                'user_id': user_id,
                'session_token': session_token,
                'expires_at': expires_at.isoformat(),
                'ip_address': ip_address,
                'user_agent': user_agent
            }).execute()
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create session: {e}")
            return False

    def get_session(self, session_token: str) -> Optional[Dict]:
        """Get session by token"""
        if not self.available:
            return None
        
        try:
            response = self.supabase.table('user_sessions').select('*').eq('session_token', session_token).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"❌ Failed to get session: {e}")
            return None

    def delete_session(self, session_token: str) -> bool:
        """Delete a user session"""
        if not self.available:
            return False
        
        try:
            self.supabase.table('user_sessions').delete().eq('session_token', session_token).execute()
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete session: {e}")
            return False

    # Signal Performance Methods
    def save_signal_performance(self, signal_data: Dict[str, Any]) -> bool:
        """Save signal performance data"""
        if not self.available:
            return False
        
        try:
            self.supabase.table('signal_performance').insert(signal_data).execute()
            logger.info(f"✅ Saved signal performance data")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save signal performance: {e}")
            return False

    def get_signal_performance(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get signal performance data"""
        if not self.available:
            return []
        
        try:
            response = self.supabase.table('signal_performance').select('*').order('timestamp', desc=True).limit(limit).offset(offset).execute()
            return response.data
        except Exception as e:
            logger.error(f"❌ Failed to get signal performance: {e}")
            return []

    def get_signals_by_date(self, date_str: str) -> List[Dict]:
        """Get signals for a specific date"""
        if not self.available:
            return []
        
        try:
            response = self.supabase.table('signal_performance').select('*').gte('timestamp', f"{date_str} 00:00:00").lt('timestamp', f"{date_str} 23:59:59").order('timestamp', desc=True).execute()
            return response.data
        except Exception as e:
            logger.error(f"❌ Failed to get signals by date: {e}")
            return []

    def update_signal_outcome(self, signal_id: int, outcome: int, profit_loss: float = None) -> bool:
        """Update signal outcome"""
        if not self.available:
            return False
        
        try:
            update_data = {'actual_outcome': outcome}
            if profit_loss is not None:
                update_data['profit_loss'] = profit_loss
                
            self.supabase.table('signal_performance').update(update_data).eq('id', signal_id).execute()
            return True
        except Exception as e:
            logger.error(f"❌ Failed to update signal outcome: {e}")
            return False

    # Password Reset Methods
    def create_password_reset_token(self, user_id: int, token: str, expires_at: datetime) -> bool:
        """Create password reset token"""
        if not self.available:
            return False
        
        try:
            self.supabase.table('password_reset_tokens').insert({
                'user_id': user_id,
                'token': token,
                'expires_at': expires_at.isoformat()
            }).execute()
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create password reset token: {e}")
            return False

    def get_password_reset_token(self, token: str) -> Optional[Dict]:
        """Get password reset token"""
        if not self.available:
            return None
        
        try:
            response = self.supabase.table('password_reset_tokens').select('*').eq('token', token).eq('used', False).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"❌ Failed to get password reset token: {e}")
            return None

    def mark_token_used(self, token: str) -> bool:
        """Mark password reset token as used"""
        if not self.available:
            return False
        
        try:
            self.supabase.table('password_reset_tokens').update({'used': True}).eq('token', token).execute()
            return True
        except Exception as e:
            logger.error(f"❌ Failed to mark token as used: {e}")
            return False

    # Journal Management Methods
    def save_journal_entry(self, user_id: int, symbol: str, entry_type: str, entry_date: date, content: str) -> bool:
        """Save journal entry"""
        if not self.available:
            return False
        
        try:
            self.supabase.table('journal_entries').insert({
                'user_id': user_id,
                'symbol': symbol,
                'entry_type': entry_type,
                'entry_date': entry_date.isoformat(),
                'content': content
            }).execute()
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save journal entry: {e}")
            return False

    def get_journal_entries(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get journal entries for user"""
        if not self.available:
            return []
        
        try:
            response = self.supabase.table('journal_entries').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            return response.data
        except Exception as e:
            logger.error(f"❌ Failed to get journal entries: {e}")
            return []

    # Notification Methods
    def create_notification(self, user_id: int, title: str, message: str, notification_type: str = 'signal', signal_id: int = None) -> bool:
        """Create user notification"""
        if not self.available:
            return False
        
        try:
            self.supabase.table('user_notifications').insert({
                'user_id': user_id,
                'title': title,
                'message': message,
                'notification_type': notification_type,
                'signal_id': signal_id
            }).execute()
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create notification: {e}")
            return False

    def get_user_notifications(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get user notifications"""
        if not self.available:
            return []
        
        try:
            response = self.supabase.table('user_notifications').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            return response.data
        except Exception as e:
            logger.error(f"❌ Failed to get user notifications: {e}")
            return []

    def mark_notification_read(self, notification_id: int) -> bool:
        """Mark notification as read"""
        if not self.available:
            return False
        
        try:
            self.supabase.table('user_notifications').update({'is_read': True}).eq('id', notification_id).execute()
            return True
        except Exception as e:
            logger.error(f"❌ Failed to mark notification as read: {e}")
            return False


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