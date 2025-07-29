#!/usr/bin/env python3
"""
Test script for Gemini-enhanced news sentiment analysis
"""

import os
import sys
from news_sentiment import analyze_symbol_news

def test_gemini_news_analysis():
    """Test the Gemini-enhanced news sentiment analysis"""
    
    print("🧪 Testing Gemini News Sentiment Analysis...")
    print("=" * 50)
    
    # Check if Gemini API key is configured
    gemini_key = os.getenv('GEMINI_API_KEY')
    if not gemini_key or gemini_key == 'your_gemini_key_here':
        print("⚠️ GEMINI_API_KEY not configured!")
        print("Please set your Gemini API key in the environment variables.")
        print("You can get a free API key at: https://ai.google.dev/")
        return False
    
    print(f"✅ Gemini API key configured: {gemini_key[:10]}...")
    
    # Test signal data
    test_signal = {
        'symbol': 'US30',
        'bias': 'LONG',
        'cv_position': 0.8,
        'change_pct': 0.5,
        'current_value': 44346.15,
        'previous_close': 44371.51,
        'net_change': -25.36,
        'today_high': 44441.26,
        'today_low': 44237.28
    }
    
    print(f"\n📊 Testing with {test_signal['symbol']}...")
    print(f"Current setup: {test_signal['bias']} bias, CV position: {test_signal['cv_position']:.1%}")
    
    try:
        # Run the analysis
        result = analyze_symbol_news('US30', test_signal)
        
        print(f"\n📈 Results:")
        print(f"📰 Headlines analyzed: {result['sentiment']['total_articles']}")
        print(f"🤖 AI Model used: {result['sentiment'].get('model_used', 'unknown')}")
        print(f"📊 Sentiment: {result['sentiment']['sentiment_label']}")
        print(f"📈 Sentiment Score: {result['sentiment']['sentiment_score']}")
        print(f"🎯 Confidence: {result['sentiment']['confidence']}%")
        print(f"📊 Probability: {result['probability']['probability_percentage']}%")
        
        # Show sample headlines
        if result.get('raw_headlines'):
            print(f"\n📰 Sample Headlines:")
            for i, headline in enumerate(result['raw_headlines'][:3], 1):
                print(f"  {i}. {headline}")
        
        # Verify Gemini was used
        model_used = result['sentiment'].get('model_used', 'unknown')
        if 'gemini' in model_used.lower():
            print(f"\n✅ SUCCESS: Gemini AI analysis working! Model: {model_used}")
            return True
        else:
            print(f"\n⚠️ WARNING: Gemini not used, fallback model: {model_used}")
            return False
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_gemini_news_analysis()
    
    if success:
        print(f"\n🎉 Gemini News Analysis Test PASSED!")
        print(f"The system is ready to generate signals with Gemini-enhanced sentiment analysis.")
    else:
        print(f"\n⚠️ Gemini News Analysis Test FAILED!")
        print(f"Please check your API key and internet connection.")
    
    print(f"\nTo use this feature, ensure GEMINI_API_KEY is set in your environment.")
    print(f"Then run the dashboard and click 'Auto Generate & Post to Discord'.") 