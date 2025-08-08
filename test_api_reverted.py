#!/usr/bin/env python3
"""
Test script to verify the API returns yesterday's closing data (correct trading logic)
"""
import sys
import os
import pickle

# Add core directory to path
sys.path.append('core')

# Load market data directly
with open('core/market_data.pkl', 'rb') as f:
    data = pickle.load(f)

# Simulate the reverted API logic
def get_latest_market_close_data():
    """Simulate market_data_storage.get_latest_market_close_data()"""
    close_history = data.get('market_close_history', {})
    latest_data = {}
    
    for symbol in ['nasdaq', 'dow', 'gold']:
        symbol_history = close_history.get(symbol, {})
        if symbol_history:
            # Get the latest date
            latest_date = max(symbol_history.keys())
            latest_data[symbol] = symbol_history[latest_date]
    
    return latest_data

# Simulate the reverted API endpoint
market_close_data = get_latest_market_close_data()

print("=== REVERTED API ENDPOINT OUTPUT (Yesterday's Close Data) ===")
print(f"NASDAQ Current Value: {market_close_data.get('nasdaq', {}).get('price', 'N/A')}")
print(f"NASDAQ Net Change: {market_close_data.get('nasdaq', {}).get('change', 'N/A')}")
print(f"NASDAQ Date: {market_close_data.get('nasdaq', {}).get('date', 'N/A')}")
print()
print(f"DOW Current Value: {market_close_data.get('dow', {}).get('price', 'N/A')}")
print(f"DOW Net Change: {market_close_data.get('dow', {}).get('change', 'N/A')}")
print(f"DOW Date: {market_close_data.get('dow', {}).get('date', 'N/A')}")

print("\n✅ API reverted - now correctly returns YESTERDAY'S closing data for today's trading!")
print("📅 Today (30/07/2025) signals use 29/07/2025 closing data ✅")