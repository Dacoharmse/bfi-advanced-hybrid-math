#!/usr/bin/env python3
"""
Test script for WhatsApp and Discord notifications
Run this to verify your notification setup is working
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add core directory to path
sys.path.append('./core')

from whatsapp_signals import WhatsAppSignals, NotificationManager
from discord_signals import DiscordSignals

# Load environment variables
load_dotenv()

def test_discord():
    """Test Discord webhook connection"""
    print("🧪 Testing Discord connection...")
    
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("❌ Discord webhook URL not configured in .env file")
        return False
    
    try:
        discord = DiscordSignals(webhook_url)
        success = discord.send_webhook_message("🚀 Discord test message from BFI Signals!")
        
        if success:
            print("✅ Discord test successful!")
            return True
        else:
            print("❌ Discord test failed!")
            return False
    except Exception as e:
        print(f"❌ Discord test error: {e}")
        return False

def test_whatsapp():
    """Test WhatsApp connection"""
    print("🧪 Testing WhatsApp connection...")
    
    if os.getenv('WHATSAPP_ENABLED', 'false').lower() != 'true':
        print("⚠️ WhatsApp is disabled in .env file")
        return False
    
    api_provider = os.getenv('WHATSAPP_API_PROVIDER', 'green')
    group_id = os.getenv('WHATSAPP_GROUP_ID')
    
    if not group_id or group_id == 'your_group_id_here':
        print("❌ WhatsApp group ID not configured in .env file")
        return False
    
    try:
        # Initialize based on provider
        if api_provider == 'green':
            instance_id = os.getenv('GREEN_API_INSTANCE_ID')
            access_token = os.getenv('GREEN_API_ACCESS_TOKEN')
            if not instance_id or not access_token:
                print("❌ GREEN API credentials not configured")
                return False
            whatsapp = WhatsAppSignals(api_provider='green', instance_id=instance_id, access_token=access_token)
            
        elif api_provider == 'wassenger':
            api_key = os.getenv('WASSENGER_API_KEY')
            device_id = os.getenv('WASSENGER_DEVICE_ID')
            if not api_key or not device_id:
                print("❌ Wassenger credentials not configured")
                return False
            whatsapp = WhatsAppSignals(api_provider='wassenger', api_key=api_key, device_id=device_id)
            
        elif api_provider == 'whapi':
            access_token = os.getenv('WHAPI_ACCESS_TOKEN')
            if not access_token:
                print("❌ Whapi access token not configured")
                return False
            whatsapp = WhatsAppSignals(api_provider='whapi', access_token=access_token)
        else:
            print(f"❌ Unknown WhatsApp API provider: {api_provider}")
            return False
        
        success = whatsapp.send_message_to_group(group_id, "🚀 WhatsApp test message from BFI Signals!")
        
        if success:
            print("✅ WhatsApp test successful!")
            return True
        else:
            print("❌ WhatsApp test failed!")
            return False
            
    except Exception as e:
        print(f"❌ WhatsApp test error: {e}")
        return False

def test_signal_sending():
    """Test sending actual trading signal to both platforms"""
    print("🧪 Testing signal sending to both platforms...")
    
    # Create sample signal data
    signal_data = {
        'signal_type': 'BUY',
        'symbol': 'TEST',
        'price': 100.50,
        'action': 'Test Signal - Integration Check',
        'confidence': 'High',
        'additional_info': 'This is a test signal to verify integration'
    }
    
    whatsapp_group_id = os.getenv('WHATSAPP_GROUP_ID')
    discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
    
    # Setup WhatsApp config if enabled
    whatsapp_config = None
    if os.getenv('WHATSAPP_ENABLED', 'false').lower() == 'true':
        api_provider = os.getenv('WHATSAPP_API_PROVIDER', 'green')
        if api_provider == 'green':
            whatsapp_config = {
                'api_provider': 'green',
                'instance_id': os.getenv('GREEN_API_INSTANCE_ID'),
                'access_token': os.getenv('GREEN_API_ACCESS_TOKEN')
            }
        elif api_provider == 'wassenger':
            whatsapp_config = {
                'api_provider': 'wassenger',
                'api_key': os.getenv('WASSENGER_API_KEY'),
                'device_id': os.getenv('WASSENGER_DEVICE_ID')
            }
        elif api_provider == 'whapi':
            whatsapp_config = {
                'api_provider': 'whapi',
                'access_token': os.getenv('WHAPI_ACCESS_TOKEN')
            }
    
    try:
        # Initialize notification manager
        manager = NotificationManager(
            whatsapp_config=whatsapp_config,
            discord_webhook=discord_webhook
        )
        
        # Send to all platforms
        results = manager.send_signal_to_all(
            signal_data=signal_data,
            whatsapp_group_id=whatsapp_group_id
        )
        
        print(f"📊 Signal sending results: {results}")
        
        successful_platforms = [platform for platform, success in results.items() if success]
        failed_platforms = [platform for platform, success in results.items() if not success]
        
        if successful_platforms:
            print(f"✅ Signal sent successfully to: {', '.join(successful_platforms)}")
        
        if failed_platforms:
            print(f"❌ Signal failed to send to: {', '.join(failed_platforms)}")
        
        return len(successful_platforms) > 0
        
    except Exception as e:
        print(f"❌ Signal sending test error: {e}")
        return False

def test_market_update():
    """Test sending market update"""
    print("🧪 Testing market update sending...")
    
    # Test Discord market update
    discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
    if discord_webhook:
        try:
            discord = DiscordSignals(discord_webhook)
            discord_success = discord.send_market_update(
                title="Test Market Update",
                updates={
                    "📊 S&P 500": "+0.85% (Test)",
                    "🏦 NASDAQ": "+1.20% (Test)",
                    "💼 DOW": "+0.45% (Test)",
                    "🛢️ Oil": "$85.20 (+2.1%) (Test)",
                    "🥇 Gold": "$2,050 (-0.3%) (Test)"
                }
            )
            if discord_success:
                print("✅ Discord market update sent!")
            else:
                print("❌ Discord market update failed!")
        except Exception as e:
            print(f"❌ Discord market update error: {e}")
    
    # Test WhatsApp market update
    if os.getenv('WHATSAPP_ENABLED', 'false').lower() == 'true':
        try:
            api_provider = os.getenv('WHATSAPP_API_PROVIDER', 'green')
            whatsapp = WhatsAppSignals(api_provider=api_provider)
            group_id = os.getenv('WHATSAPP_GROUP_ID')
            
            if group_id:
                whatsapp_success = whatsapp.send_market_update(
                    group_id=group_id,
                    title="Test Market Update",
                    updates={
                        "📊 S&P 500": "+0.85% (Test)",
                        "🏦 NASDAQ": "+1.20% (Test)",
                        "💼 DOW": "+0.45% (Test)"
                    }
                )
                if whatsapp_success:
                    print("✅ WhatsApp market update sent!")
                else:
                    print("❌ WhatsApp market update failed!")
        except Exception as e:
            print(f"❌ WhatsApp market update error: {e}")

def main():
    """Main test function"""
    print("🚀 BFI Signals Notification Test Suite")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check environment file
    if not os.path.exists('.env'):
        print("❌ .env file not found! Please create one based on the setup guides.")
        return 1
    
    # Test individual services
    discord_ok = test_discord()
    print()
    
    whatsapp_ok = test_whatsapp()
    print()
    
    # Test unified signal sending
    if discord_ok or whatsapp_ok:
        signal_ok = test_signal_sending()
        print()
        
        # Test market updates
        test_market_update()
        print()
    else:
        print("⚠️ Skipping signal tests - no platforms are working")
        signal_ok = False
    
    # Summary
    print("📋 Test Summary:")
    print(f"   Discord: {'✅' if discord_ok else '❌'}")
    print(f"   WhatsApp: {'✅' if whatsapp_ok else '❌'}")
    print(f"   Signal Sending: {'✅' if signal_ok else '❌'}")
    print()
    
    if discord_ok or whatsapp_ok:
        print("🎉 At least one notification method is working!")
        print("You can now use python core/main.py to send real signals.")
        return 0
    else:
        print("❌ No notification methods are working!")
        print("Please check your .env configuration and setup guides.")
        return 1

if __name__ == "__main__":
    exit(main())