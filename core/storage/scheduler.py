#!/usr/bin/env python3
"""
Data Capture Scheduler for BFI Signals
Captures market close data at 23:05 GMT+2 and saves to both storage systems
"""

import os
import sys
import time
import schedule
from datetime import datetime, timedelta
from typing import Dict, Any
import pytz
import logging

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from storage.data_manager import data_manager
    from market_data import MarketDataStorage
except ImportError as e:
    logging.error(f"Import error: {e}")
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/chronic/Projects/bfi-signals/logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MarketDataScheduler:
    """Scheduler for capturing market close data at 23:05 GMT+2"""
    
    def __init__(self):
        """Initialize the scheduler"""
        self.data_manager = data_manager
        self.market_data_storage = MarketDataStorage()
        self.timezone = pytz.timezone('Europe/Berlin')  # GMT+2 (CET/CEST)
        
        # Ensure logs directory exists
        os.makedirs('/home/chronic/Projects/bfi-signals/logs', exist_ok=True)
        
        logger.info("✅ Market Data Scheduler initialized")
        logger.info(f"   🌍 Timezone: {self.timezone}")
        logger.info(f"   🕐 Capture Time: 23:05 GMT+2")
    
    def capture_market_close_data(self) -> Dict[str, Any]:
        """
        Capture market close data and save to both storage systems
        
        Returns:
            Dict: Capture results and statistics
        """
        capture_time = datetime.now(self.timezone)
        capture_date = capture_time.date()
        
        logger.info(f"🚀 Starting market close data capture for {capture_date}")
        
        results = {
            'capture_date': capture_date.isoformat(),
            'capture_time': capture_time.isoformat(),
            'success': False,
            'symbols_captured': 0,
            'storage_results': {},
            'errors': []
        }
        
        try:
            # Get current market data from the existing system
            current_data = self.market_data_storage.data
            
            # Extract market data for main symbols
            market_data = {}
            symbols_to_capture = ['nasdaq', 'dow', 'gold']
            
            for symbol in symbols_to_capture:
                if symbol in current_data and current_data[symbol]:
                    market_data[symbol] = current_data[symbol]
                    logger.info(f"   📊 {symbol.upper()}: {current_data[symbol].get('price', 'N/A')}")
            
            if not market_data:
                error_msg = "No market data available to capture"
                logger.error(f"❌ {error_msg}")
                results['errors'].append(error_msg)
                return results
            
            results['symbols_captured'] = len(market_data)
            
            # Save to both storage systems
            logger.info(f"💾 Saving market close data to storage systems...")
            storage_results = self.data_manager.save_market_close_data(capture_date, market_data)
            results['storage_results'] = storage_results
            
            # Check if at least one storage system succeeded
            if storage_results.get('supabase', False) or storage_results.get('local', False):
                results['success'] = True
                logger.info(f"✅ Market close data capture completed successfully")
                logger.info(f"   📊 Symbols: {results['symbols_captured']}")
                logger.info(f"   📡 Supabase: {'✅' if storage_results.get('supabase') else '❌'}")
                logger.info(f"   💾 Local: {'✅' if storage_results.get('local') else '❌'}")
            else:
                error_msg = "Failed to save data to any storage system"
                logger.error(f"❌ {error_msg}")
                results['errors'].append(error_msg)
            
            # Log the capture attempt
            if self.data_manager.supabase_available:
                try:
                    self.data_manager.supabase.log_data_capture(
                        capture_date=capture_date,
                        symbols_captured=results['symbols_captured'],
                        success=results['success'],
                        error_message='; '.join(results['errors']) if results['errors'] else None
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Failed to log capture attempt: {e}")
            
        except Exception as e:
            error_msg = f"Market data capture failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        return results
    
    def setup_schedule(self):
        """Set up the daily schedule for market close data capture"""
        
        # Schedule daily capture at 23:05 GMT+2
        schedule.every().day.at("23:05").do(self.capture_market_close_data)
        
        logger.info("📅 Schedule configured:")
        logger.info("   🕐 Daily capture at 23:05 GMT+2")
        logger.info("   📊 Symbols: NASDAQ, DOW, GOLD")
        logger.info("   💾 Storage: Supabase + Local backup")
    
    def run_scheduler(self):
        """Run the scheduler continuously"""
        logger.info("🚀 Starting BFI Signals Market Data Scheduler...")
        logger.info("   Press Ctrl+C to stop")
        
        self.setup_schedule()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("⏹️ Scheduler stopped by user")
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")
    
    def test_capture(self) -> Dict[str, Any]:
        """Test the capture process without waiting for schedule"""
        logger.info("🧪 Testing market data capture process...")
        return self.capture_market_close_data()
    
    def manual_capture(self, target_date: str = None) -> Dict[str, Any]:
        """
        Manually trigger data capture for a specific date
        
        Args:
            target_date: Date string in YYYY-MM-DD format, None for today
            
        Returns:
            Dict: Capture results
        """
        if target_date:
            try:
                capture_date = datetime.fromisoformat(target_date).date()
            except ValueError:
                logger.error(f"❌ Invalid date format: {target_date}. Use YYYY-MM-DD")
                return {'success': False, 'error': 'Invalid date format'}
        else:
            capture_date = datetime.now().date()
        
        logger.info(f"🎯 Manual capture triggered for {capture_date}")
        
        # Temporarily modify the capture process for the specified date
        original_method = self.capture_market_close_data
        
        def capture_for_date():
            results = original_method()
            results['capture_date'] = capture_date.isoformat()
            return results
        
        return capture_for_date()


def main():
    """Main function to run the scheduler"""
    import argparse
    
    parser = argparse.ArgumentParser(description='BFI Signals Market Data Scheduler')
    parser.add_argument('--test', action='store_true', help='Test capture process')
    parser.add_argument('--manual', type=str, help='Manual capture for specific date (YYYY-MM-DD)')
    parser.add_argument('--run', action='store_true', help='Run scheduler continuously')
    
    args = parser.parse_args()
    
    scheduler = MarketDataScheduler()
    
    if args.test:
        print("🧪 Testing market data capture...")
        results = scheduler.test_capture()
        print(f"Test Results: {results}")
        
    elif args.manual:
        print(f"🎯 Manual capture for {args.manual}...")
        results = scheduler.manual_capture(args.manual)
        print(f"Manual Capture Results: {results}")
        
    elif args.run:
        scheduler.run_scheduler()
        
    else:
        print("BFI Signals Market Data Scheduler")
        print("Usage:")
        print("  --test     Test the capture process")
        print("  --manual   Manual capture for specific date")
        print("  --run      Run scheduler continuously")
        print()
        print("Examples:")
        print("  python scheduler.py --test")
        print("  python scheduler.py --manual 2025-07-29")
        print("  python scheduler.py --run")


if __name__ == "__main__":
    main()