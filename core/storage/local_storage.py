#!/usr/bin/env python3
"""
Local Storage Backup for BFI Signals
Handles local file storage as backup to Supabase
"""

import os
import json
import pickle
import shutil
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalStorage:
    """Local file storage for BFI Signals data backup"""
    
    def __init__(self, base_dir: str = None):
        """Initialize local storage with base directory"""
        if base_dir is None:
            # Default to project data directory
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            base_dir = os.path.join(project_root, 'data')
        
        self.base_dir = base_dir
        self.backups_dir = os.path.join(base_dir, 'backups')
        self.daily_dir = os.path.join(base_dir, 'daily')
        self.current_dir = os.path.join(base_dir, 'current')
        
        # Create directories
        self._ensure_directories()
        logger.info(f"✅ Local storage initialized: {base_dir}")
    
    def _ensure_directories(self):
        """Create storage directories if they don't exist"""
        for directory in [self.backups_dir, self.daily_dir, self.current_dir]:
            os.makedirs(directory, exist_ok=True)
    
    def save_market_close_data(self, capture_date: date, market_data: Dict[str, Dict]) -> bool:
        """
        Save market closing data to local files
        
        Args:
            capture_date: Date of market close
            market_data: Dictionary with symbol data
            
        Returns:
            bool: Success status
        """
        try:
            # Prepare data for storage
            storage_data = {
                'capture_date': capture_date.isoformat(),
                'captured_at': datetime.now().isoformat(),
                'symbols': {},
                'metadata': {
                    'source': 'bfi_signals_local',
                    'symbols_count': len([k for k, v in market_data.items() if v])
                }
            }
            
            # Process each symbol
            for symbol, data in market_data.items():
                if not data:
                    continue
                
                storage_data['symbols'][symbol] = {
                    'price': str(data.get('price', '0')),
                    'change': str(data.get('change', '0')),
                    'changePercent': str(data.get('changePercent', '0%')),
                    'rawChange': float(data.get('rawChange', 0)),
                    'previousClose': str(data.get('previousClose', '0')),
                    'high': str(data.get('high', '0')),
                    'low': str(data.get('low', '0')),
                    'timestamp': data.get('timestamp', datetime.now().isoformat())
                }
            
            # Save to daily file
            daily_file = os.path.join(self.daily_dir, f"{capture_date.isoformat()}.json")
            with open(daily_file, 'w') as f:
                json.dump(storage_data, f, indent=2, default=str)
            
            # Save to current file (latest data)
            current_file = os.path.join(self.current_dir, "market_data.json")
            with open(current_file, 'w') as f:
                json.dump(storage_data, f, indent=2, default=str)
            
            # Create backup
            backup_file = os.path.join(self.backups_dir, f"market_data_{capture_date.isoformat()}.json")
            shutil.copy2(daily_file, backup_file)
            
            logger.info(f"✅ Saved market data locally for {capture_date} ({len(storage_data['symbols'])} symbols)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save market data locally: {e}")
            return False
    
    def get_market_close_data(self, target_date: date, symbol: Optional[str] = None) -> Dict:
        """
        Get market closing data from local files
        
        Args:
            target_date: Date to retrieve data for
            symbol: Optional specific symbol to retrieve
            
        Returns:
            Dict: Market data organized by symbol
        """
        try:
            daily_file = os.path.join(self.daily_dir, f"{target_date.isoformat()}.json")
            
            if not os.path.exists(daily_file):
                logger.warning(f"⚠️ No local data found for {target_date}")
                return {}
            
            with open(daily_file, 'r') as f:
                storage_data = json.load(f)
            
            symbols_data = storage_data.get('symbols', {})
            
            # Filter by symbol if requested
            if symbol:
                symbol_key = symbol.lower()
                if symbol_key in symbols_data:
                    return {symbol_key: symbols_data[symbol_key]}
                else:
                    return {}
            
            # Convert to lowercase keys for consistency
            result = {}
            for symbol_key, data in symbols_data.items():
                result[symbol_key.lower()] = data
            
            logger.info(f"✅ Retrieved {len(result)} symbols locally for {target_date}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to get market data locally: {e}")
            return {}
    
    def get_latest_market_close_data(self) -> Dict:
        """
        Get the most recent market close data from local files
        
        Returns:
            Dict: Latest market data organized by symbol
        """
        try:
            current_file = os.path.join(self.current_dir, "market_data.json")
            
            if not os.path.exists(current_file):
                # Try to find the latest daily file
                daily_files = [f for f in os.listdir(self.daily_dir) if f.endswith('.json')]
                if not daily_files:
                    logger.warning("⚠️ No local market data found")
                    return {}
                
                # Get the latest file
                latest_file = max(daily_files)
                latest_date = datetime.fromisoformat(latest_file.replace('.json', '')).date()
                return self.get_market_close_data(latest_date)
            
            with open(current_file, 'r') as f:
                storage_data = json.load(f)
            
            symbols_data = storage_data.get('symbols', {})
            
            # Convert to lowercase keys for consistency and add date info
            result = {}
            for symbol_key, data in symbols_data.items():
                result[symbol_key.lower()] = {
                    **data,
                    'date': storage_data.get('capture_date', '')
                }
            
            logger.info(f"✅ Retrieved latest market data locally ({len(result)} symbols)")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to get latest market data locally: {e}")
            return {}
    
    def save_signal(self, signal_data: Dict[str, Any]) -> bool:
        """
        Save generated signal to local files
        
        Args:
            signal_data: Complete signal dictionary
            
        Returns:
            bool: Success status
        """
        try:
            signal_date = datetime.now().date()
            
            # Prepare signal for storage
            storage_signal = {
                'signal_date': signal_date.isoformat(),
                'created_at': datetime.now().isoformat(),
                'signal': signal_data
            }
            
            # Save to daily signals file
            signals_file = os.path.join(self.daily_dir, f"signals_{signal_date.isoformat()}.json")
            
            # Load existing signals or create new list
            signals_list = []
            if os.path.exists(signals_file):
                with open(signals_file, 'r') as f:
                    existing_data = json.load(f)
                    signals_list = existing_data.get('signals', [])
            
            signals_list.append(storage_signal)
            
            # Save updated signals
            signals_data = {
                'date': signal_date.isoformat(),
                'signals': signals_list,
                'count': len(signals_list)
            }
            
            with open(signals_file, 'w') as f:
                json.dump(signals_data, f, indent=2, default=str)
            
            # Create backup
            backup_file = os.path.join(self.backups_dir, f"signals_{signal_date.isoformat()}.json")
            shutil.copy2(signals_file, backup_file)
            
            logger.info(f"✅ Saved signal locally for {signal_data.get('symbol', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save signal locally: {e}")
            return False
    
    def create_full_backup(self) -> bool:
        """
        Create a comprehensive backup of all data
        
        Returns:
            bool: Success status
        """
        try:
            backup_date = datetime.now()
            backup_filename = f"full_backup_{backup_date.strftime('%Y-%m-%d_%H-%M-%S')}.json"
            backup_path = os.path.join(self.backups_dir, backup_filename)
            
            # Collect all data
            backup_data = {
                'backup_created': backup_date.isoformat(),
                'daily_data': {},
                'signals': {},
                'metadata': {
                    'total_daily_files': 0,
                    'total_signal_files': 0
                }
            }
            
            # Backup daily market data
            daily_files = [f for f in os.listdir(self.daily_dir) if f.endswith('.json') and not f.startswith('signals_')]
            for daily_file in daily_files:
                date_key = daily_file.replace('.json', '')
                with open(os.path.join(self.daily_dir, daily_file), 'r') as f:
                    backup_data['daily_data'][date_key] = json.load(f)
            
            backup_data['metadata']['total_daily_files'] = len(daily_files)
            
            # Backup signals
            signal_files = [f for f in os.listdir(self.daily_dir) if f.startswith('signals_')]
            for signal_file in signal_files:
                date_key = signal_file.replace('signals_', '').replace('.json', '')
                with open(os.path.join(self.daily_dir, signal_file), 'r') as f:
                    backup_data['signals'][date_key] = json.load(f)
            
            backup_data['metadata']['total_signal_files'] = len(signal_files)
            
            # Save backup
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            logger.info(f"✅ Created full backup: {backup_filename}")
            logger.info(f"   📁 Daily files: {backup_data['metadata']['total_daily_files']}")
            logger.info(f"   📊 Signal files: {backup_data['metadata']['total_signal_files']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create full backup: {e}")
            return False
    
    def cleanup_old_backups(self, keep_days: int = 30) -> bool:
        """
        Clean up old backup files
        
        Args:
            keep_days: Number of days of backups to keep
            
        Returns:
            bool: Success status
        """
        try:
            cutoff_date = datetime.now().date() - datetime.timedelta(days=keep_days)
            removed_count = 0
            
            for filename in os.listdir(self.backups_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.backups_dir, filename)
                    file_date = datetime.fromtimestamp(os.path.getctime(file_path)).date()
                    
                    if file_date < cutoff_date:
                        os.remove(file_path)
                        removed_count += 1
            
            logger.info(f"✅ Cleaned up {removed_count} old backup files (older than {keep_days} days)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old backups: {e}")
            return False


# Global instance
local_storage = LocalStorage()

# Convenience functions
def save_market_data_locally(capture_date: date, market_data: Dict) -> bool:
    """Save market data to local storage"""
    return local_storage.save_market_close_data(capture_date, market_data)

def get_local_market_data(target_date: date, symbol: str = None) -> Dict:
    """Get market data from local storage"""
    return local_storage.get_market_close_data(target_date, symbol)

def get_latest_local_market_data() -> Dict:
    """Get latest market data from local storage"""
    return local_storage.get_latest_market_close_data()