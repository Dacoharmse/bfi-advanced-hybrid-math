#!/usr/bin/env python3
"""
Discord Signals Module
Handles sending trading/investment signals to Discord channels
"""

import os
import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any

class DiscordSignals:
    """
    A class to handle sending signals to Discord using webhooks or bot
    """
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Discord Signals
        
        Args:
            webhook_url: Discord webhook URL (if using webhooks)
        """
        self.webhook_url = webhook_url or os.getenv('DISCORD_WEBHOOK_URL')
        
    def send_webhook_message(self, message: str, username: str = "BFI Signals", 
                           embed: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a message to Discord using webhook
        
        Args:
            message: Text message to send
            username: Display name for the bot
            embed: Optional embed object for rich formatting
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.webhook_url:
            print("❌ Discord webhook URL not configured!")
            return False
            
        payload = {
            "content": message,
            "username": username
        }
        
        if embed:
            payload["embeds"] = [embed]
            
        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            print("✅ Message sent to Discord successfully!")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to send Discord message: {e}")
            return False
    
    def send_signal(self, signal_type: str, symbol: str, price: float, 
                   action: str, confidence: str = "Medium", 
                   additional_info: str = "") -> bool:
        """
        Send a formatted trading signal to Discord
        
        Args:
            signal_type: Type of signal (e.g., "BUY", "SELL", "HOLD")
            symbol: Stock/crypto symbol (e.g., "AAPL", "BTC")
            price: Current price
            action: Recommended action
            confidence: Confidence level (Low, Medium, High)
            additional_info: Any additional information
            
        Returns:
            bool: True if successful, False otherwise
        """
        
        # Create rich embed for better formatting
        embed = {
            "title": f"🚨 {signal_type} Signal: {symbol}",
            "color": self._get_signal_color(signal_type),
            "timestamp": datetime.utcnow().isoformat(),
            "fields": [
                {
                    "name": "💰 Price",
                    "value": f"${price:.2f}",
                    "inline": True
                },
                {
                    "name": "📊 Action",
                    "value": action,
                    "inline": True
                },
                {
                    "name": "🎯 Confidence",
                    "value": confidence,
                    "inline": True
                }
            ],
            "footer": {
                "text": "BFI Signals • Trade at your own risk"
            }
        }
        
        if additional_info:
            embed["fields"].append({
                "name": "📝 Additional Info",
                "value": additional_info,
                "inline": False
            })
        
        # Simple text message as backup
        message = f"🚨 **{signal_type} Signal** for **{symbol}** at ${price:.2f} | Action: {action} | Confidence: {confidence}"
        
        return self.send_webhook_message(message, embed=embed)
    
    def send_market_update(self, title: str, updates: Dict[str, Any]) -> bool:
        """
        Send a market update with multiple data points
        
        Args:
            title: Title for the update
            updates: Dictionary of market data
            
        Returns:
            bool: True if successful, False otherwise
        """
        
        embed = {
            "title": f"📈 {title}",
            "color": 0x3498db,  # Blue color
            "timestamp": datetime.utcnow().isoformat(),
            "fields": []
        }
        
        for key, value in updates.items():
            embed["fields"].append({
                "name": key,
                "value": str(value),
                "inline": True
            })
        
        embed["footer"] = {
            "text": "BFI Signals • Market Update"
        }
        
        return self.send_webhook_message("", embed=embed)
    
    def _get_signal_color(self, signal_type: str) -> int:
        """Get color code for signal type"""
        colors = {
            "BUY": 0x2ecc71,     # Green
            "SELL": 0xe74c3c,    # Red
            "HOLD": 0xf39c12,    # Orange
            "ALERT": 0x9b59b6    # Purple
        }
        return colors.get(signal_type.upper(), 0x95a5a6)  # Default gray

# Example usage functions
def example_buy_signal():
    """Example of sending a BUY signal"""
    discord = DiscordSignals()
    return discord.send_signal(
        signal_type="BUY",
        symbol="AAPL",
        price=150.25,
        action="Strong Buy - Technical breakout detected",
        confidence="High",
        additional_info="RSI oversold, breaking resistance at $150"
    )

def example_market_update():
    """Example of sending a market update"""
    discord = DiscordSignals()
    return discord.send_market_update(
        title="Daily Market Summary",
        updates={
            "📊 S&P 500": "+0.85%",
            "🏦 NASDAQ": "+1.20%",
            "💼 DOW": "+0.45%",
            "🛢️ Oil": "$85.20 (+2.1%)",
            "🥇 Gold": "$2,050 (-0.3%)"
        }
    )

if __name__ == "__main__":
    # Test the Discord functionality
    print("🧪 Testing Discord Signals...")
    
    # Test simple message
    discord = DiscordSignals()
    discord.send_webhook_message("🚀 BFI Signals is now connected to Discord!")
    
    # Test signal
    example_buy_signal()
    
    # Test market update
    example_market_update() 