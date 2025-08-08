#!/usr/bin/env python3
"""
Unified Data Manager for BFI Signals
Manages both Supabase and local storage with automatic fallback
"""

import os
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import logging

try:
    from .supabase_client import supabase_client
    from .local_storage import local_storage
except ImportError:
    # Handle relative imports when run directly
    import sys
    sys.path.append(os.path.dirname(__file__))
    from supabase_client import supabase_client
    from local_storage import local_storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataManager:
    """
    Unified data manager that handles both Supabase and local storage
    Primary: Supabase (cloud, reliable)
    Backup: Local storage (fast, offline access)
    """
    
    def __init__(self):
        """Initialize data manager with both storage systems"""
        self.supabase = supabase_client
        self.local = local_storage
        self.supabase_available = self.supabase.available
        
        logger.info(f"✅ Data Manager initialized")
        logger.info(f"   📡 Supabase: {'Available' if self.supabase_available else 'Unavailable'}")
        logger.info(f"   💾 Local Storage: Available")
    
    def test_connections(self) -> Dict[str, bool]:
        """Test both storage connections"""
        results = {
            'supabase': False,
            'local': True  # Local storage is always available
        }
        
        if self.supabase_available:
            results['supabase'] = self.supabase.test_connection()
        
        logger.info(f"Connection Status - Supabase: {results['supabase']}, Local: {results['local']}")
        return results
    
    def save_market_close_data(self, capture_date: date, market_data: Dict[str, Dict]) -> Dict[str, bool]:
        """
        Save market closing data to both storage systems
        
        Args:
            capture_date: Date of market close
            market_data: Dictionary with symbol data
            
        Returns:
            Dict[str, bool]: Success status for each storage system
        """
        results = {
            'supabase': False,
            'local': False,
            'total_symbols': len([k for k, v in market_data.items() if v])
        }
        
        # Save to Supabase (primary)
        if self.supabase_available:
            try:
                results['supabase'] = self.supabase.save_market_close_data(capture_date, market_data)
            except Exception as e:
                logger.error(f"❌ Supabase save failed: {e}")
                results['supabase'] = False
        
        # Save to local storage (backup)
        try:
            results['local'] = self.local.save_market_close_data(capture_date, market_data)
        except Exception as e:
            logger.error(f"❌ Local save failed: {e}")
            results['local'] = False
        
        # Log results
        success_count = sum([results['supabase'], results['local']])
        if success_count > 0:
            logger.info(f"✅ Market data saved for {capture_date} ({results['total_symbols']} symbols)")
            logger.info(f"   📡 Supabase: {'✅' if results['supabase'] else '❌'}")
            logger.info(f"   💾 Local: {'✅' if results['local'] else '❌'}")
        else:
            logger.error(f"❌ Failed to save market data to both storage systems!")
        
        return results
    
    def get_market_close_data(self, target_date: date, symbol: Optional[str] = None) -> Dict:
        """
        Get market closing data with automatic fallback
        Try Supabase first, fallback to local storage
        
        Args:
            target_date: Date to retrieve data for
            symbol: Optional specific symbol to retrieve
            
        Returns:
            Dict: Market data organized by symbol
        """
        
        # Try Supabase first (primary)
        if self.supabase_available:
            try:
                data = self.supabase.get_market_close_data(target_date, symbol)
                if data:
                    logger.info(f"✅ Retrieved data from Supabase for {target_date}")
                    return data
            except Exception as e:
                logger.warning(f"⚠️ Supabase retrieval failed: {e}")
        
        # Fallback to local storage
        try:
            data = self.local.get_market_close_data(target_date, symbol)
            if data:
                logger.info(f"✅ Retrieved data from local storage for {target_date}")
                return data
        except Exception as e:
            logger.error(f"❌ Local retrieval failed: {e}")
        
        logger.warning(f"⚠️ No data found for {target_date} in either storage system")
        return {}
    
    def get_latest_market_close_data(self) -> Dict:
        """
        Get the most recent market close data with automatic fallback
        
        Returns:
            Dict: Latest market data organized by symbol
        """
        
        # Try Supabase first (primary)
        if self.supabase_available:
            try:
                data = self.supabase.get_latest_market_close_data()
                if data:
                    logger.info("✅ Retrieved latest data from Supabase")
                    return data
            except Exception as e:
                logger.warning(f"⚠️ Supabase latest data retrieval failed: {e}")
        
        # Fallback to local storage
        try:
            data = self.local.get_latest_market_close_data()
            if data:
                logger.info("✅ Retrieved latest data from local storage")
                return data
        except Exception as e:
            logger.error(f"❌ Local latest data retrieval failed: {e}")
        
        logger.warning("⚠️ No latest data found in either storage system")
        return {}
    
    def save_signal(self, signal_data: Dict[str, Any]) -> Dict[str, bool]:
        """
        Save generated signal to both storage systems
        
        Args:
            signal_data: Complete signal dictionary
            
        Returns:
            Dict[str, bool]: Success status for each storage system
        """
        results = {
            'supabase': False,
            'local': False
        }
        
        # Save to Supabase (primary)
        if self.supabase_available:
            try:
                results['supabase'] = self.supabase.save_signal(signal_data)
            except Exception as e:
                logger.error(f"❌ Supabase signal save failed: {e}")
                results['supabase'] = False
        
        # Save to local storage (backup)
        try:
            results['local'] = self.local.save_signal(signal_data)
        except Exception as e:
            logger.error(f"❌ Local signal save failed: {e}")
            results['local'] = False
        
        # Log results
        symbol = signal_data.get('symbol', 'unknown')
        success_count = sum([results['supabase'], results['local']])
        if success_count > 0:
            logger.info(f"✅ Signal saved for {symbol}")
            logger.info(f"   📡 Supabase: {'✅' if results['supabase'] else '❌'}")
            logger.info(f"   💾 Local: {'✅' if results['local'] else '❌'}")
        else:
            logger.error(f"❌ Failed to save signal for {symbol} to both storage systems!")
        
        return results
    
    def sync_data(self, sync_date: date = None) -> Dict[str, Any]:
        """
        Sync data between Supabase and local storage
        
        Args:
            sync_date: Specific date to sync, None for latest
            
        Returns:
            Dict: Sync results and statistics
        """
        results = {
            'sync_date': sync_date.isoformat() if sync_date else 'latest',
            'supabase_to_local': False,
            'local_to_supabase': False,
            'conflicts': 0,
            'synced_symbols': 0
        }
        
        if not self.supabase_available:
            logger.warning("⚠️ Cannot sync - Supabase not available")
            return results
        
        try:
            # Get data from both sources
            if sync_date:
                supabase_data = self.supabase.get_market_close_data(sync_date)
                local_data = self.local.get_market_close_data(sync_date)
            else:
                supabase_data = self.supabase.get_latest_market_close_data()
                local_data = self.local.get_latest_market_close_data()
            
            # Sync missing data
            supabase_symbols = set(supabase_data.keys())
            local_symbols = set(local_data.keys())
            
            # Sync from Supabase to Local (missing symbols)
            missing_in_local = supabase_symbols - local_symbols
            if missing_in_local:
                missing_data = {symbol: supabase_data[symbol] for symbol in missing_in_local}
                if sync_date:
                    results['supabase_to_local'] = self.local.save_market_close_data(sync_date, missing_data)
                else:
                    # For latest data, we need to determine the date
                    capture_date = datetime.now().date()
                    results['supabase_to_local'] = self.local.save_market_close_data(capture_date, missing_data)
            
            # Sync from Local to Supabase (missing symbols)
            missing_in_supabase = local_symbols - supabase_symbols
            if missing_in_supabase:
                missing_data = {symbol: local_data[symbol] for symbol in missing_in_supabase}
                if sync_date:
                    results['local_to_supabase'] = self.supabase.save_market_close_data(sync_date, missing_data)
                else:
                    # For latest data, we need to determine the date
                    capture_date = datetime.now().date()
                    results['local_to_supabase'] = self.supabase.save_market_close_data(capture_date, missing_data)
            
            results['synced_symbols'] = len(missing_in_local) + len(missing_in_supabase)
            
            logger.info(f"✅ Data sync completed for {results['sync_date']}")
            logger.info(f"   📊 Synced symbols: {results['synced_symbols']}")
            
        except Exception as e:
            logger.error(f"❌ Data sync failed: {e}")
        
        return results
    
    def create_comprehensive_backup(self) -> bool:
        """
        Create a comprehensive backup including local files and Supabase export
        
        Returns:
            bool: Success status
        """
        try:
            # Create local backup
            local_backup_success = self.local.create_full_backup()
            
            # TODO: Add Supabase export functionality
            # For now, the local backup serves as the comprehensive backup
            
            logger.info(f"✅ Comprehensive backup created")
            return local_backup_success
            
        except Exception as e:
            logger.error(f"❌ Comprehensive backup failed: {e}")
            return False


# Global instance
data_manager = DataManager()

# Convenience functions for external use
def save_market_data(capture_date: date, market_data: Dict) -> Dict[str, bool]:
    """Save market data to both storage systems"""
    return data_manager.save_market_close_data(capture_date, market_data)

def get_market_data(target_date: date, symbol: str = None) -> Dict:
    """Get market data with automatic fallback"""
    return data_manager.get_market_close_data(target_date, symbol)

def get_latest_market_data() -> Dict:
    """Get latest market data with automatic fallback"""
    return data_manager.get_latest_market_close_data()

def save_signal_data(signal_data: Dict[str, Any]) -> Dict[str, bool]:
    """Save signal to both storage systems"""
    return data_manager.save_signal(signal_data)

def test_storage_connections() -> Dict[str, bool]:
    """Test both storage connections"""
    return data_manager.test_connections()


if __name__ == "__main__":
    # Test the data manager
    print("🧪 Testing BFI Signals Data Manager...")
    
    # Test connections
    connections = test_storage_connections()
    print(f"Connection Test Results: {connections}")
    
    # Test data operations
    from datetime import date
    
    test_data = {
        'nasdaq': {
            'price': '23,336.25',
            'change': '-20.02',
            'changePercent': '-0.09%',
            'rawChange': -20.018046875,
            'previousClose': '23,356.27',
            'high': '23,510.92',
            'low': '23,298.91'
        }
    }
    
    test_date = date(2025, 7, 29)
    
    print(f"\n📊 Testing data save for {test_date}...")
    save_results = save_market_data(test_date, test_data)
    print(f"Save Results: {save_results}")
    
    print(f"\n📊 Testing data retrieval for {test_date}...")
    retrieved_data = get_market_data(test_date)
    print(f"Retrieved Data: {retrieved_data}")
    
    print(f"\n✅ Data Manager testing complete!")