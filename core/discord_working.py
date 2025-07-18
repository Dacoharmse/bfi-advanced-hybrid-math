#!/usr/bin/env python3
"""
Working Discord Module for BFI Signals
All functions properly handle environment variables
"""

import os
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../.env')

def get_webhook_url():
    """Get webhook URL from environment"""
    return os.getenv("DISCORD_WEBHOOK_URL")

def test_discord_connection() -> bool:
    """
    Test the Discord webhook connection
    
    Returns:
        bool: True if connection is working, False otherwise
    """
    
    webhook_url = get_webhook_url()
    if not webhook_url:
        print("ERROR: Discord webhook URL not configured!")
        return False
    
    # Test connection by sending a minimal request and checking response
    test_payload = {
        "content": "",  # Empty content to avoid posting visible message
        "embeds": []
    }
    
    try:
        response = requests.post(
            webhook_url, 
            json=test_payload,
            timeout=10
        )
        
        # Check if webhook URL is valid (should return 400 for empty content, not 404)
        if response.status_code in [200, 204, 400]:  # 400 is expected for empty content
            print("SUCCESS: Discord connection test successful!")
            return True
        else:
            print(f"ERROR: Discord connection test failed: HTTP {response.status_code}")
            return False
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Discord connection test failed: {str(e)}")
        return False

def post_signal(signal: Dict[str, Any], include_risky_play: bool = True) -> bool:
    """
    Post a trading signal to Discord using the professional Bonang Finance format
    
    Args:
        signal (Dict[str, Any]): Signal dictionary containing all signal parameters
        include_risky_play (bool): Whether to include risky play section (default: True)
    
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    
    webhook_url = get_webhook_url()
    if not webhook_url:
        print("ERROR: Discord webhook URL not configured! Please set DISCORD_WEBHOOK_URL in .env file")
        return False
    
    # Import here to avoid circular imports
    from strategy import format_signal_for_discord
    
    # Format the signal using the professional format
    formatted_signal = format_signal_for_discord(signal, include_risky_play=include_risky_play)
    
    try:
        # Send the message to Discord
        response = requests.post(
            webhook_url, 
            json={"content": formatted_signal},
            timeout=30
        )
        response.raise_for_status()
        
        print(f"SUCCESS: Signal posted to Discord successfully for {signal['symbol']}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to post signal to Discord: {str(e)}")
        return False

def post_simple_message(message: str) -> bool:
    """
    Post a simple message to Discord
    
    Args:
        message (str): Message to send
    
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    
    webhook_url = get_webhook_url()
    if not webhook_url:
        print("ERROR: Discord webhook URL not configured!")
        return False
    
    try:
        response = requests.post(
            webhook_url, 
            json={"content": message},
            timeout=30
        )
        response.raise_for_status()
        
        print("SUCCESS: Message posted to Discord successfully")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to post message to Discord: {str(e)}")
        return False

if __name__ == "__main__":
    # Test the Discord functionality
    print("🧪 Testing Discord connection...")
    
    if test_discord_connection():
        print("✅ Discord connection test successful!")
        
        # Test posting a simple message
        test_result = post_simple_message("🎉 BFI Signals Discord integration is working!")
        if test_result:
            print("✅ Test message posted successfully!")
        
    else:
        print("❌ Discord connection failed. Please check your webhook URL.")
    
    print("\n🏁 Discord tests complete!") 