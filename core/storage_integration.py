#!/usr/bin/env python3
"""
Storage Integration Layer for BFI Signals
Connects new storage system with existing dashboard
"""

import os
import sys
from datetime import datetime, date
from typing import Dict, Any, Optional
import logging

# Add storage module to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'storage'))

try:
    from storage.data_manager import data_manager
    STORAGE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"New storage system not available: {e}")
    STORAGE_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StorageIntegration:
    """Integration layer between new storage system and existing dashboard"""
    
    def __init__(self):
        """Initialize storage integration"""
        self.storage_available = STORAGE_AVAILABLE
        if self.storage_available:
            self.data_manager = data_manager
            logger.info("✅ New storage system integrated")
        else:
            self.data_manager = None
            logger.warning("⚠️ New storage system not available, using fallback")
    
    def get_latest_market_close_data(self) -> Dict:
        """
        Get latest market close data for signals
        Returns YESTERDAY's closing data for today's signals (correct trading logic)
        Compatible with existing dashboard interface
        
        Returns:
            Dict: Market data in dashboard format
        """
        if not self.storage_available:
            return {}
        
        try:
            # Get YESTERDAY's data for today's signals (correct trading logic)
            from datetime import date, timedelta
            yesterday = date.today() - timedelta(days=1)
            
            raw_data = self.data_manager.get_market_close_data(yesterday)
            
            if not raw_data:
                logger.warning("⚠️ No data available from new storage system")
                return {}
            
            # Convert to dashboard format
            dashboard_data = {}
            for symbol, data in raw_data.items():
                dashboard_data[symbol] = {
                    'price': data.get('price', '0'),
                    'change': data.get('change', '0'),
                    'changePercent': data.get('changePercent', '0%'),
                    'rawChange': float(data.get('rawChange', 0)),
                    'previousClose': data.get('previousClose', '0'),
                    'high': data.get('high', '0'),
                    'low': data.get('low', '0'),
                    'timestamp': data.get('timestamp', datetime.now().isoformat()),
                    'date': data.get('date', datetime.now().date().isoformat())
                }
            
            logger.info(f"✅ Retrieved market data from new storage ({len(dashboard_data)} symbols)")
            return dashboard_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get market data from new storage: {e}")
            return {}
    
    def get_market_close_data_for_date(self, target_date: date) -> Dict:
        """
        Get market close data for specific date
        
        Args:
            target_date: Date to retrieve data for
            
        Returns:
            Dict: Market data in dashboard format
        """
        if not self.storage_available:
            return {}
        
        try:
            raw_data = self.data_manager.get_market_close_data(target_date)
            
            if not raw_data:
                logger.warning(f"⚠️ No data available for {target_date}")
                return {}
            
            # Convert to dashboard format
            dashboard_data = {}
            for symbol, data in raw_data.items():
                dashboard_data[symbol] = {
                    'price': data.get('price', '0'),
                    'change': data.get('change', '0'),
                    'changePercent': data.get('changePercent', '0%'),
                    'rawChange': float(data.get('rawChange', 0)),
                    'previousClose': data.get('previousClose', '0'),
                    'high': data.get('high', '0'),
                    'low': data.get('low', '0'),
                    'timestamp': data.get('timestamp', datetime.now().isoformat()),
                    'date': target_date.isoformat()
                }
            
            logger.info(f"✅ Retrieved market data for {target_date} ({len(dashboard_data)} symbols)")
            return dashboard_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get market data for {target_date}: {e}")
            return {}
    
    def save_signal_to_storage(self, signal_data) -> bool:
        """
        Save signal to storage system
        
        Args:
            signal_data: Signal data dictionary
            
        Returns:
            bool: Success status
        """
        if not self.storage_available:
            logger.warning("⚠️ New storage system not available for signal saving")
            return False
        
        try:
            # Save signal using data manager
            result = self.data_manager.save_signal(signal_data)
            logger.info(f"✅ Signal saved to storage")
            return result.get('supabase', False) or result.get('local', False)
            
        except Exception as e:
            logger.error(f"❌ Failed to save signal to storage: {e}")
            return False
    
    def save_current_market_data_as_close(self, market_data_storage) -> bool:
        """
        Save current market data as closing data (called at 23:05 GMT+2)
        
        Args:
            market_data_storage: Existing MarketDataStorage instance
            
        Returns:
            bool: Success status
        """
        if not self.storage_available:
            return False
        
        try:
            current_date = datetime.now().date()
            
            # Get current market data from existing system
            current_data = market_data_storage.data
            
            # Extract main symbols
            market_data = {}
            for symbol in ['nasdaq', 'dow', 'gold']:
                if symbol in current_data and current_data[symbol]:
                    market_data[symbol] = current_data[symbol]
            
            if not market_data:
                logger.warning("⚠️ No current market data to save as closing data")
                return False
            
            # Save to new storage system
            results = self.data_manager.save_market_close_data(current_date, market_data)
            
            success = results.get('supabase', False) or results.get('local', False)
            if success:
                logger.info(f"✅ Saved current data as closing data for {current_date}")
                logger.info(f"   📊 Symbols: {len(market_data)}")
                logger.info(f"   📡 Supabase: {'✅' if results.get('supabase') else '❌'}")
                logger.info(f"   💾 Local: {'✅' if results.get('local') else '❌'}")
            else:
                logger.error("❌ Failed to save closing data to any storage system")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to save current data as closing data: {e}")
            return False
    
    def save_generated_signal(self, signal_data: Dict[str, Any]) -> bool:
        """
        Save generated signal to new storage system
        
        Args:
            signal_data: Complete signal dictionary
            
        Returns:
            bool: Success status
        """
        if not self.storage_available:
            return False
        
        try:
            results = self.data_manager.save_signal(signal_data)
            
            success = results.get('supabase', False) or results.get('local', False)
            if success:
                symbol = signal_data.get('symbol', 'unknown')
                logger.info(f"✅ Saved signal for {symbol} to new storage system")
            else:
                logger.error("❌ Failed to save signal to any storage system")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to save signal: {e}")
            return False
    
    def get_storage_status(self) -> Dict[str, Any]:
        """
        Get status of storage systems
        
        Returns:
            Dict: Storage system status
        """
        if not self.storage_available:
            return {
                'available': False,
                'supabase': False,
                'local': False,
                'error': 'Storage system not initialized'
            }
        
        try:
            connections = self.data_manager.test_connections()
            
            return {
                'available': True,
                'supabase': connections.get('supabase', False),
                'local': connections.get('local', False),
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'available': False,
                'supabase': False,
                'local': False,
                'error': str(e)
            }


# Global instance
storage_integration = StorageIntegration()

# Convenience functions for dashboard use
def get_latest_market_close_data() -> Dict:
    """Get latest market close data (compatible with existing dashboard)"""
    return storage_integration.get_latest_market_close_data()

def save_current_as_closing_data(market_data_storage) -> bool:
    """Save current market data as closing data"""
    return storage_integration.save_current_market_data_as_close(market_data_storage)

def save_signal_to_storage(signal_data: Dict[str, Any]) -> bool:
    """Save generated signal to storage"""
    return storage_integration.save_generated_signal(signal_data)

def get_storage_system_status() -> Dict[str, Any]:
    """Get storage system status"""
    return storage_integration.get_storage_status()

def is_new_storage_available() -> bool:
    """Check if new storage system is available"""
    return storage_integration.storage_available


# Initialize global storage integration instance
storage_integration = StorageIntegration()

# Convenience functions for easy import
def get_latest_market_close_data():
    """Get latest market close data - convenience function for dashboard"""
    return storage_integration.get_latest_market_close_data()

def save_signal_to_storage(signal_data):
    """Save signal to storage - convenience function for dashboard"""
    return storage_integration.save_signal_to_storage(signal_data)

def get_storage_system_status():
    """Get storage system status"""
    return {
        'supabase': storage_integration.storage_available and storage_integration.data_manager,
        'local': True  # Local storage is always available
    }

if __name__ == "__main__":
    # Test the integration
    print("🧪 Testing Storage Integration...")
    
    integration = StorageIntegration()
    
    # Test status
    status = integration.get_storage_status()
    print(f"Storage Status: {status}")
    
    # Test data retrieval
    if integration.storage_available:
        data = integration.get_latest_market_close_data()
        print(f"Latest Data: {len(data)} symbols retrieved")
        
        for symbol, info in data.items():
            print(f"  {symbol.upper()}: {info.get('price', 'N/A')} ({info.get('change', 'N/A')})")
    
    print("✅ Integration test complete")