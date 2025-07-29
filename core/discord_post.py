#!/usr/bin/env python3
"""
Discord Posting Module for BFI Signals
Handles posting trading signals to Discord channels via webhooks
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


def post_signal(signal: Dict[str, Any]) -> bool:
    """
    Post a trading signal to Discord using the professional Bonang Finance format
    
    Args:
        signal (Dict[str, Any]): Signal dictionary containing all signal parameters
    
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
    formatted_signal = format_signal_for_discord(signal)
    
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


def post_simple_signal(signal: Dict[str, Any]) -> bool:
    """
    Post a simple trading signal to Discord (backup format)
    
    Args:
        signal (Dict[str, Any]): Signal dictionary containing all signal parameters
    
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    
    webhook_url = get_webhook_url()
    if not webhook_url:
        print("ERROR: Discord webhook URL not configured! Please set DISCORD_WEBHOOK_URL in .env file")
        return False
    
    # Choose indicator based on bias
    bias_indicator = "[LONG]" if signal["bias"] == "LONG" else "[SHORT]"
    
    # Use display name instead of technical symbol
    display_name = signal.get("display_name", signal["symbol"])
    
    # Format Take Profits line with TP3 if available
    if signal.get('tp3') is not None:
        take_profits_line = f"**Take Profits:** {signal['tp1']:,.2f} | {signal['tp2']:,.2f} | {signal['tp3']:,.2f}\n"
    else:
        take_profits_line = f"**Take Profits:** {signal['tp1']:,.2f} | {signal['tp2']:,.2f}\n"
    
    # Build the message
    message = (
        f"{bias_indicator} **{display_name} – {signal['bias']} Signal**\n"
        f"**Current Value:** {signal['current_value']:,.2f}\n"
        f"**Previous Close:** {signal['previous_close']:,.2f}\n"
        f"**Net Change:** {signal['net_change']:+.2f} / {signal['change_pct']:+.2f}%\n"
        f"**Today's High:** {signal['today_high']:,.2f}\n"
        f"**Today's Low:** {signal['today_low']:,.2f}\n"
        f"**Entry Points:** {signal['entry1']:,.2f} | {signal['entry2']:,.2f}\n"
        f"{take_profits_line}"
        f"**Stop Loss:** {signal['sl_tight']:,.2f} | {signal['sl_wide']:,.2f}\n"
        f"*Generated: {signal['timestamp']}*"
    )
    
    try:
        # Send the message to Discord
        response = requests.post(
            webhook_url, 
            json={"content": message},
            timeout=30
        )
        response.raise_for_status()
        
        print(f"SUCCESS: Simple signal posted to Discord successfully for {signal['symbol']}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to post simple signal to Discord: {str(e)}")
        return False


def post_market_status(message: str, status_type: str = "info") -> bool:
    """
    Post a market status update to Discord
    
    Args:
        message (str): Status message to post
        status_type (str): Type of status (info, warning, error, success)
    
    Returns:
        bool: True if message was posted successfully, False otherwise
    """
    
    webhook_url = get_webhook_url()
    if not webhook_url:
        print("ERROR: Discord webhook URL not configured!")
        return False
    
    # Choose prefix based on status type
    status_prefixes = {
        "info": "[INFO]",
        "warning": "[WARNING]",
        "error": "[ERROR]",
        "success": "[SUCCESS]"
    }
    
    prefix = status_prefixes.get(status_type, "[INFO]")
    formatted_message = f"{prefix} **BFI Signals Status**\n{message}"
    
    try:
        response = requests.post(
            webhook_url, 
            json={"content": formatted_message},
            timeout=30
        )
        response.raise_for_status()
        
        print(f"SUCCESS: Market status posted to Discord successfully")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to post market status to Discord: {str(e)}")
        return False


def test_discord_connection() -> bool:
    """
    Test the Discord webhook connection silently (without posting a message)
    
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


if __name__ == "__main__":
    # Test the Discord posting functionality
    print("Testing Discord posting functionality...")
    
    # Test connection silently
    if test_discord_connection():
        print("SUCCESS: Discord connection is working!")
        print("Test completed without posting messages to Discord")
        
        # NOTE: Actual signal posting tests are commented out to avoid spam
        # Uncomment these lines if you want to test posting to Discord:
        
        # sample_signal = {
        #     "symbol": "US30",
        #     "bias": "LONG",
        #     "bias_text": "Bullish (Change is Positive)",
        #     "current_value": 44650.63,
        #     "previous_close": 44458.29,
        #     "net_change": 192.34,
        #     "change_pct": 0.43,
        #     "today_high": 44775.47,
        #     "today_low": 44372.92,
        #     "entry1": 44458.29,
        #     "entry2": 44650.63,
        #     "tp1": 44842.97,
        #     "tp2": 44775.47,
        #     "sl_tight": 44554.46,
        #     "sl_wide": 44372.92,
        #     "timestamp": "11 July 2025",
        #     "generated_at": datetime.now().isoformat()
        # }
        
        # print("\nTesting professional signal posting...")
        # post_signal(sample_signal)
        
        # print("\nTesting simple signal posting...")
        # post_simple_signal(sample_signal)
        
        # print("\nTesting market status posting...")
        # post_market_status("Test status message", "info")
        
    else:
        print("ERROR: Discord connection failed. Please check your webhook URL.")
    
    print("\nDiscord posting tests complete!") 