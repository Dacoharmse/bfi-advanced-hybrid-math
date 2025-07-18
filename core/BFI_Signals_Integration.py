#!/usr/bin/env python3
"""
BFI Signals TradingView Integration
Exports signal data for TradingView indicator integration
"""

import json
import os
from datetime import datetime
from typing import Dict, Any
import pandas as pd

class TradingViewIntegration:
    """
    Class to handle integration between BFI Signals bot and TradingView indicator
    """
    
    def __init__(self, output_dir: str = "data/tradingview"):
        """
        Initialize TradingView integration
        
        Args:
            output_dir (str): Directory to save TradingView data files
        """
        self.output_dir = output_dir
        self.ensure_output_directory()
    
    def ensure_output_directory(self):
        """Create output directory if it doesn't exist"""
        os.makedirs(self.output_dir, exist_ok=True)
    
    def export_signal_data(self, signal: Dict[str, Any], symbol: str) -> None:
        """
        Export signal data to JSON format for TradingView consumption
        
        Args:
            signal (Dict[str, Any]): Signal data from BFI strategy
            symbol (str): Trading symbol
        """
        
        # Create TradingView compatible data structure
        tv_data = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "display_name": signal.get("display_name", symbol),
            "levels": {
                "cv": signal["current_value"],           # Current Value
                "prv": signal["previous_close"],         # Previous Close  
                "keylevel_high": signal["today_high"],   # Daily High
                "keylevel_low": signal["today_low"],     # Daily Low
                "tp": signal["take_profit"],             # Take Profit
                "entry1": signal["entry1"],             # Primary Entry
                "entry2": signal["entry2"],             # Secondary Entry
                "sl_tight": signal["sl_tight"],         # Tight Stop Loss
                "sl_wide": signal["sl_wide"]             # Wide Stop Loss
            },
            "bias": {
                "direction": signal["bias"],             # LONG or SHORT
                "net_change": signal["net_change"],      # Net Change
                "change_pct": signal["change_pct"],      # Percentage Change
                "bias_text": signal["bias_text"]         # Bias description
            },
            "meta": {
                "trading_date": signal["timestamp"],
                "generated_at": signal["generated_at"],
                "is_weekend_signal": signal.get("is_weekend_signal", False),
                "cv_position": signal.get("cv_position", 0.5)
            }
        }
        
        # Save to JSON file for TradingView indicator
        filename = f"{symbol}_signals_{datetime.now().strftime('%Y%m%d')}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(tv_data, f, indent=2)
        
        print(f"📊 TradingView data exported: {filepath}")
        
        # Also save latest signal for real-time updates
        latest_filepath = os.path.join(self.output_dir, f"{symbol}_latest.json")
        with open(latest_filepath, 'w') as f:
            json.dump(tv_data, f, indent=2)
            
    def generate_pine_script_data(self, signal: Dict[str, Any]) -> str:
        """
        Generate Pine Script variable assignments for direct integration
        
        Args:
            signal (Dict[str, Any]): Signal data from BFI strategy
            
        Returns:
            str: Pine Script variable assignments
        """
        
        pine_script = f"""
// BFI Signals Data - Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
// Symbol: {signal.get('display_name', 'Unknown')}
// Bias: {signal['bias']} ({signal['change_pct']:.2f}%)

bfi_cv = {signal['current_value']:.2f}              // Current Value
bfi_prv = {signal['previous_close']:.2f}            // Previous Close
bfi_keylevel_high = {signal['today_high']:.2f}      // Daily High
bfi_keylevel_low = {signal['today_low']:.2f}        // Daily Low  
bfi_tp = {signal['take_profit']:.2f}                // Take Profit
bfi_entry1 = {signal['entry1']:.2f}                 // Primary Entry
bfi_entry2 = {signal['entry2']:.2f}                 // Secondary Entry
bfi_sl_tight = {signal['sl_tight']:.2f}             // Tight Stop Loss
bfi_sl_wide = {signal['sl_wide']:.2f}               // Wide Stop Loss

bfi_bias_long = {str(signal['bias'] == 'LONG').lower()}
bfi_net_change = {signal['net_change']:.2f}
bfi_change_pct = {signal['change_pct']:.2f}
        """
        
        return pine_script.strip()
    
    def create_webhook_payload(self, signal: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        Create webhook payload for real-time TradingView updates
        
        Args:
            signal (Dict[str, Any]): Signal data from BFI strategy
            symbol (str): Trading symbol
            
        Returns:
            Dict[str, Any]: Webhook payload
        """
        
        return {
            "action": "update_bfi_levels",
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "cv": signal["current_value"],
                "prv": signal["previous_close"], 
                "high": signal["today_high"],
                "low": signal["today_low"],
                "tp": signal["take_profit"],
                "bias": signal["bias"],
                "net_change": signal["net_change"],
                "change_pct": signal["change_pct"]
            }
        }
    
    def save_historical_signals(self, signals_list: list, symbol: str) -> None:
        """
        Save historical signals for backtesting and analysis
        
        Args:
            signals_list (list): List of historical signals
            symbol (str): Trading symbol
        """
        
        filename = f"{symbol}_historical_signals.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(signals_list, f, indent=2)
            
        print(f"📈 Historical signals saved: {filepath}")


def integrate_with_strategy(signal_data: Dict[str, Any], symbol: str) -> bool:
    """
    Main integration function to be called from strategy.py
    
    Args:
        signal_data (Dict[str, Any]): Signal data from calculate_signal()
        symbol (str): Trading symbol
    """
    
    try:
        # Initialize TradingView integration
        tv_integration = TradingViewIntegration()
        
        # Export signal data for TradingView
        tv_integration.export_signal_data(signal_data, symbol)
        
        # Generate Pine Script data
        pine_script = tv_integration.generate_pine_script_data(signal_data)
        
        # Save Pine Script data
        pine_filepath = os.path.join(tv_integration.output_dir, f"{symbol}_pine_data.txt")
        with open(pine_filepath, 'w') as f:
            f.write(pine_script)
            
        print(f"🌲 Pine Script data saved: {pine_filepath}")
        
        # Create webhook payload (for future real-time integration)
        webhook_payload = tv_integration.create_webhook_payload(signal_data, symbol)
        
        # Save webhook payload
        webhook_filepath = os.path.join(tv_integration.output_dir, f"{symbol}_webhook.json")
        with open(webhook_filepath, 'w') as f:
            json.dump(webhook_payload, f, indent=2)
            
        return True
        
    except Exception as e:
        print(f"❌ TradingView integration error: {str(e)}")
        return False


# Example usage
if __name__ == "__main__":
    # Example signal data (this would come from your strategy.py)
    example_signal = {
        "symbol": "US30",
        "display_name": "US30",
        "bias": "LONG",
        "bias_text": "Bullish (Net Change > 0)",
        "current_value": 44500.25,
        "previous_close": 44450.75,
        "net_change": 49.50,
        "change_pct": 0.11,
        "today_high": 44580.00,
        "today_low": 44420.30,
        "take_profit": 44549.75,
        "entry1": 44420.30,
        "entry2": 44500.25,
        "tp1": 44500.25,
        "tp2": 44549.75,
        "sl_tight": 44475.50,
        "sl_wide": 44420.30,
        "cv_position": 0.65,
        "timestamp": "15 July 2025",
        "generated_at": "2025-07-15T13:26:00",
        "is_weekend_signal": False
    }
    
    # Test integration
    integrate_with_strategy(example_signal, "US30") 