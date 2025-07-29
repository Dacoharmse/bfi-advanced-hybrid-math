#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Data Service with Auto-Refresh
Provides real-time market data scraping with automatic refresh functionality
"""

from core.yahoo_finance_scraper import YahooFinanceScraper
import time
import json

class MarketDataService:
    """Service to provide market data with auto-refresh capabilities"""
    
    def __init__(self, cache_file: str = "market_data_cache.pkl"):
        self.scraper = YahooFinanceScraper(cache_file)
        
    def get_all_market_data(self) -> dict:
        """Get current market data for all symbols"""
        return self.scraper.scrape_all()
    
    def get_symbol_data(self, symbol: str) -> dict:
        """Get data for a specific symbol"""
        return self.scraper.scrape_symbol(symbol) or {}
    
    def get_cached_data(self, symbol: str = None) -> dict:
        """Get cached data without making new requests"""
        return self.scraper.get_cached_data(symbol)
    
    def start_auto_refresh(self, interval_minutes: int = 5):
        """Start automatic data refresh every N minutes"""
        print(f"[SERVICE] Starting market data service with {interval_minutes}-minute refresh...")
        self.scraper.start_auto_refresh(interval_minutes)
    
    def stop_auto_refresh(self):
        """Stop automatic refresh"""
        self.scraper.stop_auto_refresh()
    
    def export_data_json(self, filename: str = "market_data_export.json"):
        """Export current data to JSON file"""
        data = self.get_cached_data()
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"[EXPORT] Data exported to {filename}")
    
    def print_summary(self):
        """Print a summary of current market data"""
        data = self.get_cached_data()
        
        if not data:
            print("[INFO] No cached data available. Run scraper first.")
            return
        
        print("\n" + "=" * 60)
        print("MARKET DATA SUMMARY")
        print("=" * 60)
        
        for symbol, info in data.items():
            name = info.get('name', symbol)
            current = info.get('current_price', 0)
            prev_close = info.get('previous_close', 0)
            net_change = info.get('net_change', 0) or 0
            net_change_pct = info.get('net_change_percent', 0) or 0
            
            status = "UP" if net_change >= 0 else "DOWN"
            
            print(f"{name} ({symbol}):")
            print(f"  Current:  ${current:,.2f}")
            if prev_close:
                print(f"  Previous: ${prev_close:,.2f}")
            print(f"  Change:   ${net_change:+,.2f} ({net_change_pct:+.2f}%) [{status}]")
            print()

def main():
    """Demo the market data service"""
    service = MarketDataService()
    
    print("Market Data Service Demo")
    print("========================")
    
    # Get initial data
    print("\n1. Fetching initial market data...")
    data = service.get_all_market_data()
    service.print_summary()
    
    # Export to JSON
    print("\n2. Exporting data to JSON...")
    service.export_data_json()
    
    # Test individual symbol
    print("\n3. Testing individual symbol lookup...")
    nasdaq_data = service.get_symbol_data('^NDX')
    if nasdaq_data:
        print(f"NASDAQ Current Price: ${nasdaq_data['current_price']:,.2f}")
    
    # Demonstrate auto-refresh (uncomment to test)
    # print("\n4. Starting auto-refresh for 2 minutes...")
    # service.start_auto_refresh(interval_minutes=1)
    # time.sleep(120)
    # service.stop_auto_refresh()
    
    print("\n[DEMO] Market Data Service demo complete!")

if __name__ == "__main__":
    main()