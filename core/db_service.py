#!/usr/bin/env python3
"""
Database Service Layer for BFI Signals
Provides unified interface for database operations using Supabase
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import logging
from storage.supabase_client import supabase_client

logger = logging.getLogger(__name__)

class DatabaseService:
    """Unified database service using Supabase backend"""
    
    def __init__(self):
        self.client = supabase_client
    
    def is_available(self) -> bool:
        """Check if database is available"""
        return self.client.available
    
    def test_connection(self) -> bool:
        """Test database connection"""
        return self.client.test_connection()
    
    # User Management
    def create_user(self, username: str, email: str, password_hash: str, role: str = 'user', **kwargs) -> Optional[Dict]:
        """Create a new user"""
        user_data = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'role': role
        }
        # Add optional fields
        for key, value in kwargs.items():
            if value is not None:
                user_data[key] = value
                
        return self.client.create_user(username, email, password_hash, role)
    
    def get_user(self, username: str = None, email: str = None, user_id: int = None) -> Optional[Dict]:
        """Get user by username, email, or ID"""
        if user_id:
            return self.client.get_user_by_id(user_id)
        elif username:
            return self.client.get_user_by_username(username)
        elif email:
            return self.client.get_user_by_email(email)
        return None
    
    def update_user_login(self, user_id: int) -> bool:
        """Update user's last login timestamp"""
        return self.client.update_user_login(user_id)
    
    # Session Management
    def create_session(self, user_id: int, session_token: str, expires_at: datetime, **kwargs) -> bool:
        """Create user session"""
        return self.client.create_session(
            user_id, session_token, expires_at, 
            kwargs.get('ip_address'), kwargs.get('user_agent')
        )
    
    def get_session(self, session_token: str) -> Optional[Dict]:
        """Get session by token"""
        return self.client.get_session(session_token)
    
    def delete_session(self, session_token: str) -> bool:
        """Delete session"""
        return self.client.delete_session(session_token)
    
    # Signal Performance Management
    def save_signal_performance(self, **kwargs) -> bool:
        """Save signal performance data"""
        # Map common SQLite column names to Supabase format
        signal_data = {}
        
        # Required fields
        signal_data['symbol'] = kwargs.get('symbol', '')
        signal_data['timestamp'] = kwargs.get('timestamp', datetime.now().isoformat())
        
        # Optional fields with defaults
        signal_data['signal_type'] = kwargs.get('signal_type')
        signal_data['predicted_probability'] = kwargs.get('predicted_probability')
        signal_data['risk_level'] = kwargs.get('risk_level')
        signal_data['actual_outcome'] = kwargs.get('actual_outcome')
        signal_data['profit_loss'] = kwargs.get('profit_loss')
        signal_data['risky_play_outcome'] = kwargs.get('risky_play_outcome')
        signal_data['user_id'] = kwargs.get('user_id')
        signal_data['bias'] = kwargs.get('bias')
        signal_data['current_value'] = kwargs.get('current_value')
        signal_data['take_profit'] = kwargs.get('take_profit')
        signal_data['entry1'] = kwargs.get('entry1')
        signal_data['entry2'] = kwargs.get('entry2')
        signal_data['sl_tight'] = kwargs.get('sl_tight')
        signal_data['sl_wide'] = kwargs.get('sl_wide')
        signal_data['probability_percentage'] = kwargs.get('probability_percentage')
        signal_data['cv_position'] = kwargs.get('cv_position')
        signal_data['posted_to_discord'] = kwargs.get('posted_to_discord', False)
        
        # Store full signal data as JSONB
        signal_data['signal_data'] = kwargs.get('signal_data', {})
        
        # Remove None values
        signal_data = {k: v for k, v in signal_data.items() if v is not None}
        
        return self.client.save_signal_performance(signal_data)
    
    def get_signals(self, limit: int = 100, date_filter: str = None) -> List[Dict]:
        """Get signal performance data"""
        if date_filter:
            return self.client.get_signals_by_date(date_filter)
        return self.client.get_signal_performance(limit)
    
    def get_todays_signals(self) -> List[Dict]:
        """Get signals for today"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.client.get_signals_by_date(today)
    
    def get_week_signals(self) -> List[Dict]:
        """Get signals for current week"""
        # Get start of current week (Monday)
        today = datetime.now()
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        week_start = monday.strftime('%Y-%m-%d')
        
        # For now, get all signals since Monday
        # TODO: Implement proper week range query
        return self.client.get_signal_performance(limit=1000)
    
    def update_signal_outcome(self, signal_id: int, outcome: int, profit_loss: float = None) -> bool:
        """Update signal outcome"""
        return self.client.update_signal_outcome(signal_id, outcome, profit_loss)
    
    def count_signals(self) -> int:
        """Count total signals"""
        try:
            signals = self.client.get_signal_performance(limit=10000)  # Get all to count
            return len(signals)
        except Exception as e:
            logger.error(f"❌ Failed to count signals: {e}")
            return 0
    
    # Password Reset Management
    def create_password_reset_token(self, user_id: int, token: str, expires_at: datetime) -> bool:
        """Create password reset token"""
        return self.client.create_password_reset_token(user_id, token, expires_at)
    
    def get_password_reset_token(self, token: str) -> Optional[Dict]:
        """Get password reset token"""
        return self.client.get_password_reset_token(token)
    
    def mark_token_used(self, token: str) -> bool:
        """Mark password reset token as used"""
        return self.client.mark_token_used(token)
    
    # Journal Management
    def save_journal_entry(self, user_id: int, symbol: str, entry_type: str, entry_date: date, content: str) -> bool:
        """Save journal entry"""
        return self.client.save_journal_entry(user_id, symbol, entry_type, entry_date, content)
    
    def get_journal_entries(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get journal entries for user"""
        return self.client.get_journal_entries(user_id, limit)
    
    # Notification Management
    def create_notification(self, user_id: int, title: str, message: str, notification_type: str = 'signal', signal_id: int = None) -> bool:
        """Create user notification"""
        return self.client.create_notification(user_id, title, message, notification_type, signal_id)
    
    def get_user_notifications(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get user notifications"""
        return self.client.get_user_notifications(user_id, limit)
    
    def mark_notification_read(self, notification_id: int) -> bool:
        """Mark notification as read"""
        return self.client.mark_notification_read(notification_id)
    
    # Market Data Management (existing functionality)
    def save_market_data(self, capture_date: date, market_data: Dict) -> bool:
        """Save market data"""
        return self.client.save_market_close_data(capture_date, market_data)
    
    def get_market_data(self, target_date: date, symbol: str = None) -> Dict:
        """Get market data"""
        return self.client.get_market_close_data(target_date, symbol)
    
    def get_latest_market_data(self) -> Dict:
        """Get latest market data"""
        return self.client.get_latest_market_close_data()
    
    # Legacy SQLite compatibility methods
    def execute_raw_query(self, query: str, params: tuple = None):
        """Execute raw SQL query - NOT SUPPORTED in Supabase"""
        logger.warning("⚠️ Raw SQL queries not supported with Supabase. Use specific methods instead.")
        raise NotImplementedError("Raw SQL queries not supported with Supabase backend")
    
    def get_connection(self):
        """Get database connection - NOT SUPPORTED in Supabase"""
        logger.warning("⚠️ Direct database connections not supported with Supabase. Use specific methods instead.")
        raise NotImplementedError("Direct database connections not supported with Supabase backend")

# Global database service instance
db_service = DatabaseService()

# Convenience functions for backward compatibility
def get_db():
    """Get database service instance"""
    return db_service

def test_database_connection():
    """Test database connection"""
    return db_service.test_connection()

def is_database_available():
    """Check if database is available"""
    return db_service.is_available()