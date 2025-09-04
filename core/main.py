#!/usr/bin/env python3
"""
BFI Signals - Main Application
Hybrid Math 1-hour signal strategy for NASDAQ-100 and other symbols
Run manually each morning to generate and send signals to Discord
"""

import os
import hashlib
from datetime import datetime
from dotenv import load_dotenv

# Import our custom modules (now in the same core directory)
from data_fetch import fetch_last_two_1h_bars
from strategy import calculate_signal
from discord_post import post_signal, post_simple_signal, post_market_status, test_discord_connection
from ai_engine import AIEngine
from whatsapp_signals import NotificationManager

# Load environment variables from parent directory
load_dotenv('../.env')


def generate_signals():
    """
    Main function that generates signals and posts them to Discord
    """
    now = datetime.now()
    print(f"Running BFI Signals at {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize AI Engine
    ai_engine = AIEngine()
    print("AI Engine initialized")
    
    # Initialize Notification Manager
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
    
    notification_manager = NotificationManager(
        whatsapp_config=whatsapp_config,
        discord_webhook=os.getenv('DISCORD_WEBHOOK_URL')
    )
    
    whatsapp_group_id = os.getenv('WHATSAPP_GROUP_ID')
    if whatsapp_config and whatsapp_group_id:
        print(f"WhatsApp notifications enabled for group: {whatsapp_group_id}")
    else:
        print("WhatsApp notifications disabled")
    
    print("Notification manager initialized")
    
    # Check if it's weekend and show appropriate message
    if now.weekday() == 5:  # Saturday
        print("Weekend detected: Signal will be for Monday's trading session")
    elif now.weekday() == 6:  # Sunday
        print("Weekend detected: Signal will be for Monday's trading session")
    
    # Get symbols from environment or use defaults
    symbols_env = os.getenv('TRADING_SYMBOLS', '^NDX')
    symbols = [s.strip() for s in symbols_env.split(',') if s.strip()]
    
    # Check if news analysis should be included
    include_news = os.getenv('INCLUDE_NEWS_ANALYSIS', 'true').lower() == 'true'
    
    print(f"Processing {len(symbols)} symbols: {', '.join(symbols)}")
    print(f"News analysis: {'Enabled' if include_news else 'Disabled'}")
    
    if not include_news:
        print("News analysis disabled - signals will use technical analysis only")
    else:
        print("News analysis enabled - may take longer but provides better probability estimates")
    
    successful_signals = []
    failed_signals = []
    
    for symbol in symbols:
        try:
            print(f"\n--- Processing {symbol} ---")
            
            # Fetch the last two 1-hour bars
            df = fetch_last_two_1h_bars(symbol)
            
            # Calculate the signal using the new format with news analysis
            signal = calculate_signal(df, symbol, include_news=include_news)
            
            # AI Enhancement: Improve sentiment analysis and probability calculation
            if include_news and signal.get('raw_news_headlines'):
                print("AI: Analyzing news sentiment...")
                ai_sentiment = ai_engine.analyze_sentiment_ai(signal['raw_news_headlines'], symbol)
                
                # Enhance probability using AI
                enhanced_probability = ai_engine.get_ai_enhanced_probability(
                    signal['probability_percentage'], 
                    signal, 
                    ai_sentiment
                )
                
                # Assess risk level
                risk_level = ai_engine.assess_risk_level(signal, ai_sentiment)
                
                # Update signal with AI enhancements
                signal['probability_percentage'] = enhanced_probability
                signal['ai_sentiment'] = ai_sentiment
                signal['risk_level'] = risk_level
                
                print(f"AI: Enhanced probability: {enhanced_probability:.1f}%")
                print(f"AI: Risk level: {risk_level}")
                print(f"AI: Sentiment model: {ai_sentiment.get('model_used', 'unknown')}")
            
            print(f"SUCCESS: {symbol} signal calculated:")
            print(f"   Bias: {signal['bias']}")
            print(f"   Current Value: {signal['current_value']:.2f}")
            print(f"   Net Change: {signal['net_change']:+.2f}")
            print(f"   Change %: {signal['change_pct']:+.2f}%")
            print(f"   Probability: {signal['probability_percentage']}% ({signal['probability_label']})")
            print(f"   Sentiment: {signal['sentiment']}")
            if signal.get('risk_level'):
                print(f"   Risk Level: {signal['risk_level']}")
            
            # Send to both Discord and WhatsApp using unified notification manager
            use_simple = os.getenv('USE_SIMPLE_DISCORD', 'false').lower() == 'true'
            
            # Prepare signal data for unified notifications
            signal_data = {
                'signal_type': signal['bias'],
                'symbol': signal['symbol'],
                'price': signal['current_value'],
                'action': f"{signal['bias']} - {signal['probability_label']}",
                'confidence': signal.get('risk_level', 'Medium'),
                'additional_info': f"Change: {signal['change_pct']:+.2f}% | Probability: {signal['probability_percentage']}%"
            }
            
            # Send to platforms
            notification_results = {}
            
            # Discord
            if use_simple:
                discord_success = post_simple_signal(signal)
            else:
                discord_success = post_signal(signal)
            notification_results['discord'] = discord_success
            
            # WhatsApp (if configured)
            if whatsapp_config and whatsapp_group_id:
                whatsapp_results = notification_manager.send_signal_to_all(
                    signal_data=signal_data,
                    whatsapp_group_id=whatsapp_group_id
                )
                notification_results.update(whatsapp_results)
            
            # Consider successful if at least one platform succeeded
            success = any(notification_results.values())
            
            if success:
                successful_signals.append(signal)
                platforms_sent = [platform for platform, result in notification_results.items() if result]
                print(f"SUCCESS: {symbol} signal sent to: {', '.join(platforms_sent)}")
                
                # Store signal for AI learning
                try:
                    import sqlite3
                    conn = sqlite3.connect("ai_learning.db")
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO signal_performance 
                        (symbol, signal_type, predicted_probability, risk_level, timestamp, news_hash)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        signal['symbol'],
                        signal['bias'],
                        signal['probability_percentage'],
                        signal.get('risk_level', 'medium'),
                        datetime.now(),
                        hashlib.md5(str(signal.get('raw_news_headlines', [])).encode()).hexdigest()
                    ))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f"INFO: Could not store signal for learning: {e}")
                    # Don't fail the main process if learning storage fails
            else:
                failed_signals.append(signal)
                platforms_failed = [platform for platform, result in notification_results.items() if not result]
                print(f"ERROR: Failed to send {symbol} signal to: {', '.join(platforms_failed) if platforms_failed else 'all platforms'}")
                
        except Exception as e:
            print(f"ERROR: Error processing {symbol}: {str(e)}")
            failed_signals.append({"symbol": symbol, "error": str(e)})
    
    # Summary to console only (no Discord posting)
    total_processed = len(successful_signals) + len(failed_signals)
    print(f"\nSignal generation completed!")
    print(f"Successfully processed: {len(successful_signals)} signals")
    if failed_signals:
        print(f"Failed: {len(failed_signals)} signals")
    
    # Show average probability for successful signals
    if successful_signals:
        avg_probability = sum(s.get('probability_percentage', 0) for s in successful_signals) / len(successful_signals)
        print(f"Average probability: {avg_probability:.1f}%")
    
    return len(successful_signals) > 0


def main():
    """
    Main function - handles command line arguments
    """
    import sys
    
    print("BFI Signals - Bonang Finance Hybrid Math Strategy")
    print("=" * 60)
    
    # Load and validate environment
    load_dotenv()
    
    # Check if Discord webhook is configured
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("ERROR: Discord webhook URL not configured!")
        print("Please add DISCORD_WEBHOOK_URL to your .env file")
        print("See DISCORD_SETUP.md for instructions")
        return 1
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print_help()
            return 0
        elif sys.argv[1] == "--test-connection":
            print("Testing Discord connection...")
            if test_discord_connection():
                print("SUCCESS: Discord connection successful!")
                return 0
            else:
                print("ERROR: Discord connection failed!")
                return 1
        else:
            print(f"ERROR: Unknown argument: {sys.argv[1]}")
            print_help()
            return 1
    
    # Default mode: generate signals
    print("Generating trading signals...")
    
    # Test Discord connection first
    if not test_discord_connection():
        print("ERROR: Discord connection failed! Please check your webhook URL.")
        print("Add DISCORD_WEBHOOK_URL to your .env file")
        return 1
    
    # Generate and send signals
    success = generate_signals()
    
    if success:
        print("\nAll done! Check your Discord channel for the signals.")
        return 0
    else:
        print("\nNo signals were generated successfully.")
        return 1


def print_help():
    """Print help information"""
    print("""
Usage: python main.py [OPTIONS]

Options:
  --test-connection    Test Discord webhook connection
  --help              Show this help message

Default behavior:
  Generates trading signals and posts them to Discord immediately

Environment Variables:
  DISCORD_WEBHOOK_URL       Discord webhook URL (required)
  TRADING_SYMBOLS          Comma-separated list of symbols (default: ^NDX)
  USE_SIMPLE_DISCORD       Use simple Discord formatting (default: false)
  INCLUDE_NEWS_ANALYSIS    Include news sentiment analysis (default: true)

Examples:
  python main.py                  # Generate and send signals now
  python main.py --test-connection # Test Discord connection
  python main.py --help          # Show this help

How to use:
  1. Set up your Discord webhook in the .env file
  2. Run 'python main.py' each morning when you want signals
  3. Check your Discord channel for the professional trading signals

Signal Format:
  - Professional Bonang Finance Hybrid Math Strategy format
  - Includes Current Value, Previous Close, Net Change
  - Buy/Sell entry points with Value Area and Breakout entries
  - Take Profit levels (Hybrid Math Target + Today's High/Low)
  - Stop Loss levels (Tight + Wide)
  - Probability percentage based on technical + fundamental analysis
  - Market sentiment analysis from financial news
  - Complete risk warning and disclaimer

News Analysis Features:
  - Scrapes financial news from multiple sources
  - Analyzes sentiment using bullish/bearish keywords
  - Calculates probability based on technical + fundamental alignment
  - Provides probability percentages (25-85% range)
  - Includes sentiment indicators (Bullish/Bearish/Neutral)
  - Fallback to technical-only analysis if news fails
""")


if __name__ == "__main__":
    exit(main()) 