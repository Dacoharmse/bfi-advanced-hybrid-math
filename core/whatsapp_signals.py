#!/usr/bin/env python3
"""
WhatsApp Signals Module
Handles sending trading/investment signals to WhatsApp groups using third-party APIs
"""

import os
import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

class WhatsAppSignals:
    """
    A class to handle sending signals to WhatsApp groups using various third-party APIs
    Supports: GREEN API, Wassenger, Whapi.Cloud
    """
    
    def __init__(self, api_provider: str = "green", **kwargs):
        """
        Initialize WhatsApp Signals
        
        Args:
            api_provider: Which API to use ('green', 'wassenger', 'whapi')
            **kwargs: API-specific configuration
        """
        self.api_provider = api_provider.lower()
        self.config = self._load_config(**kwargs)
        
    def _load_config(self, **kwargs) -> Dict[str, str]:
        """Load configuration based on API provider"""
        config = {}
        
        if self.api_provider == "green":
            config = {
                "instance_id": kwargs.get('instance_id') or os.getenv('GREEN_API_INSTANCE_ID'),
                "access_token": kwargs.get('access_token') or os.getenv('GREEN_API_ACCESS_TOKEN'),
                "base_url": f"https://api.green-api.com"
            }
        elif self.api_provider == "wassenger":
            config = {
                "api_key": kwargs.get('api_key') or os.getenv('WASSENGER_API_KEY'),
                "device_id": kwargs.get('device_id') or os.getenv('WASSENGER_DEVICE_ID'),
                "base_url": "https://api.wassenger.com"
            }
        elif self.api_provider == "whapi":
            config = {
                "access_token": kwargs.get('access_token') or os.getenv('WHAPI_ACCESS_TOKEN'),
                "base_url": "https://gate.whapi.cloud"
            }
            
        return config
    
    def send_message_to_group(self, group_id: str, message: str) -> bool:
        """
        Send a message to a WhatsApp group
        
        Args:
            group_id: WhatsApp group ID
            message: Text message to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.api_provider == "green":
                return self._send_green_api_message(group_id, message)
            elif self.api_provider == "wassenger":
                return self._send_wassenger_message(group_id, message)
            elif self.api_provider == "whapi":
                return self._send_whapi_message(group_id, message)
            else:
                print(f"❌ Unsupported API provider: {self.api_provider}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to send WhatsApp message: {e}")
            return False
    
    def _send_green_api_message(self, group_id: str, message: str) -> bool:
        """Send message using GREEN API"""
        if not self.config.get('instance_id') or not self.config.get('access_token'):
            print("❌ GREEN API credentials not configured!")
            return False
            
        url = f"{self.config['base_url']}/waInstance{self.config['instance_id']}/sendMessage/{self.config['access_token']}"
        
        payload = {
            "chatId": group_id,
            "message": message
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("✅ Message sent to WhatsApp group via GREEN API!")
        return True
    
    def _send_wassenger_message(self, group_id: str, message: str) -> bool:
        """Send message using Wassenger API"""
        if not self.config.get('api_key') or not self.config.get('device_id'):
            print("❌ Wassenger API credentials not configured!")
            return False
            
        url = f"{self.config['base_url']}/v1/messages"
        
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}"
        }
        
        payload = {
            "device": self.config['device_id'],
            "recipient": group_id,
            "type": "text",
            "message": message
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print("✅ Message sent to WhatsApp group via Wassenger!")
        return True
    
    def _send_whapi_message(self, group_id: str, message: str) -> bool:
        """Send message using Whapi.Cloud"""
        if not self.config.get('access_token'):
            print("❌ Whapi access token not configured!")
            return False
            
        url = f"{self.config['base_url']}/messages/text"
        
        headers = {
            "Authorization": f"Bearer {self.config['access_token']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "to": group_id,
            "body": message
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print("✅ Message sent to WhatsApp group via Whapi!")
        return True
    
    def send_signal(self, group_id: str, signal_type: str, symbol: str, 
                   price: float, action: str, confidence: str = "Medium", 
                   additional_info: str = "") -> bool:
        """
        Send a formatted trading signal to WhatsApp group
        
        Args:
            group_id: WhatsApp group ID
            signal_type: Type of signal (e.g., "BUY", "SELL", "HOLD")
            symbol: Stock/crypto symbol (e.g., "AAPL", "BTC")
            price: Current price
            action: Recommended action
            confidence: Confidence level (Low, Medium, High)
            additional_info: Any additional information
            
        Returns:
            bool: True if successful, False otherwise
        """
        
        # Create formatted message for WhatsApp
        message = f"""🚨 *{signal_type} SIGNAL* 🚨

📊 *Symbol:* {symbol}
💰 *Price:* ${price:.2f}
📈 *Action:* {action}
🎯 *Confidence:* {confidence}
⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        if additional_info:
            message += f"\n📝 *Info:* {additional_info}"
            
        message += "\n\n⚠️ *BFI Signals • Trade at your own risk*"
        
        return self.send_message_to_group(group_id, message)
    
    def send_market_update(self, group_id: str, title: str, updates: Dict[str, Any]) -> bool:
        """
        Send a market update to WhatsApp group
        
        Args:
            group_id: WhatsApp group ID
            title: Title for the update
            updates: Dictionary of market data
            
        Returns:
            bool: True if successful, False otherwise
        """
        
        message = f"📈 *{title}*\n\n"
        
        for key, value in updates.items():
            message += f"{key}: {value}\n"
            
        message += f"\n⏰ *Updated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        message += "\n\n📊 *BFI Signals • Market Update*"
        
        return self.send_message_to_group(group_id, message)
    
    def create_group(self, group_name: str, participants: List[str]) -> Optional[str]:
        """
        Create a new WhatsApp group (GREEN API only)
        
        Args:
            group_name: Name for the new group
            participants: List of phone numbers (with country code)
            
        Returns:
            str: Group ID if successful, None otherwise
        """
        if self.api_provider != "green":
            print("❌ Group creation only supported with GREEN API")
            return None
            
        if not self.config.get('instance_id') or not self.config.get('access_token'):
            print("❌ GREEN API credentials not configured!")
            return None
            
        url = f"{self.config['base_url']}/waInstance{self.config['instance_id']}/createGroup/{self.config['access_token']}"
        
        # Format participants for GREEN API
        formatted_participants = [f"{num}@c.us" for num in participants]
        
        payload = {
            "groupName": group_name,
            "chatIds": formatted_participants
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data.get('created'):
                group_id = data.get('chatId')
                print(f"✅ WhatsApp group '{group_name}' created! ID: {group_id}")
                return group_id
            else:
                print(f"❌ Failed to create group: {data}")
                return None
                
        except Exception as e:
            print(f"❌ Failed to create WhatsApp group: {e}")
            return None

# Notification manager that combines WhatsApp and Discord
class NotificationManager:
    """
    Unified notification manager for both WhatsApp and Discord
    """
    
    def __init__(self, whatsapp_config: Optional[Dict] = None, discord_webhook: Optional[str] = None):
        """
        Initialize notification manager
        
        Args:
            whatsapp_config: Configuration for WhatsApp (api_provider, credentials)
            discord_webhook: Discord webhook URL
        """
        self.whatsapp = None
        self.discord = None
        
        # Initialize WhatsApp if configured
        if whatsapp_config:
            self.whatsapp = WhatsAppSignals(**whatsapp_config)
            
        # Initialize Discord if configured
        if discord_webhook:
            try:
                from discord_signals import DiscordSignals
            except ImportError:
                from .discord_signals import DiscordSignals
            self.discord = DiscordSignals(discord_webhook)
    
    def send_signal_to_all(self, signal_data: Dict[str, Any], 
                          whatsapp_group_id: Optional[str] = None) -> Dict[str, bool]:
        """
        Send signal to both WhatsApp and Discord
        
        Args:
            signal_data: Dictionary containing signal information
            whatsapp_group_id: WhatsApp group ID (required if WhatsApp is configured)
            
        Returns:
            dict: Results for each platform
        """
        results = {}
        
        # Send to WhatsApp
        if self.whatsapp and whatsapp_group_id:
            results['whatsapp'] = self.whatsapp.send_signal(
                group_id=whatsapp_group_id,
                signal_type=signal_data['signal_type'],
                symbol=signal_data['symbol'],
                price=signal_data['price'],
                action=signal_data['action'],
                confidence=signal_data.get('confidence', 'Medium'),
                additional_info=signal_data.get('additional_info', '')
            )
        
        # Send to Discord
        if self.discord:
            results['discord'] = self.discord.send_signal(
                signal_type=signal_data['signal_type'],
                symbol=signal_data['symbol'],
                price=signal_data['price'],
                action=signal_data['action'],
                confidence=signal_data.get('confidence', 'Medium'),
                additional_info=signal_data.get('additional_info', '')
            )
            
        return results

# Example usage functions
def example_whatsapp_signal():
    """Example of sending a signal to WhatsApp"""
    whatsapp = WhatsAppSignals(api_provider="green")
    return whatsapp.send_signal(
        group_id="120363025343298765@g.us",  # Example group ID
        signal_type="BUY",
        symbol="AAPL",
        price=150.25,
        action="Strong Buy - Technical breakout detected",
        confidence="High",
        additional_info="RSI oversold, breaking resistance at $150"
    )

def example_unified_notifications():
    """Example of sending to both WhatsApp and Discord"""
    manager = NotificationManager(
        whatsapp_config={
            'api_provider': 'green',
            'instance_id': 'your_instance_id',
            'access_token': 'your_access_token'
        },
        discord_webhook=os.getenv('DISCORD_WEBHOOK_URL')
    )
    
    signal_data = {
        'signal_type': 'BUY',
        'symbol': 'AAPL',
        'price': 150.25,
        'action': 'Strong Buy - Technical breakout',
        'confidence': 'High',
        'additional_info': 'RSI oversold, breaking resistance'
    }
    
    results = manager.send_signal_to_all(
        signal_data=signal_data,
        whatsapp_group_id="120363025343298765@g.us"
    )
    
    return results

if __name__ == "__main__":
    # Test WhatsApp functionality
    print("🧪 Testing WhatsApp Signals...")
    
    # Test simple message
    whatsapp = WhatsAppSignals(api_provider="green")
    # whatsapp.send_message_to_group("GROUP_ID_HERE", "🚀 BFI Signals is now connected to WhatsApp!")
    
    # Test signal (uncomment to use)
    # example_whatsapp_signal()
    
    # Test unified notifications (uncomment to use)
    # example_unified_notifications()