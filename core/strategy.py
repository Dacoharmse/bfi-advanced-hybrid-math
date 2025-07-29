#!/usr/bin/env python3
"""
Hybrid Math Strategy Module for BFI Signals
Implements the complete Hybrid Math Strategy by Prophet Bonang @ Bonang Financial Institute
Based on the official strategy document: "THE HYBRID MATH STRATEGY - Market Analyzed as 1 + 1"
"""

import pandas as pd
from typing import Dict, Any
from datetime import datetime, timedelta


def get_trading_date() -> datetime:
    """
    Get the appropriate trading date for the signal.
    If it's weekend (Saturday or Sunday), return next Monday.
    Otherwise, return today.
    
    Returns:
        datetime: The trading date to use for the signal
    """
    today = datetime.now()
    
    # Check if it's weekend
    if today.weekday() == 5:  # Saturday (weekday 5)
        # Return next Monday (2 days later)
        return today + timedelta(days=2)
    elif today.weekday() == 6:  # Sunday (weekday 6)
        # Return next Monday (1 day later)
        return today + timedelta(days=1)
    else:
        # Weekday - return today
        return today


def get_display_name(symbol: str) -> str:
    """
    Convert technical symbol to user-friendly display name for Discord messages
    
    Args:
        symbol (str): Technical symbol (e.g., "^NDX", "US30")
    
    Returns:
        str: User-friendly display name
    """
    symbol_display_map = {
        "^NDX": "NAS100",
        "NDX": "NAS100",
        "US30": "US30",
        "^DJI": "US30",
        "DJI": "US30",
        "^GSPC": "SPX500",
        "SPX": "SPX500",
        "^IXIC": "NAS100",
        "IXIC": "NAS100"
    }
    
    return symbol_display_map.get(symbol, symbol)


def calculate_signal(df: pd.DataFrame, symbol: str = "UNKNOWN", include_news: bool = True) -> Dict[str, Any]:
    """
    Calculate trading signal using the complete Hybrid Math Strategy by Bonang Financial Institute
    
    CORE CONCEPTS:
    - Current Value (CV): The market's current price - primary decision zone
    - Net Change: Used to calculate Take Profit (TP) zone
    - Previous Close: Last price from previous trading day
    - High & Low: Session's highest and lowest prices
    
    ADVANCED LOGIC:
    - When CV is near Daily High: Sell from high to low, then buy back toward CV aiming for TP
    - When CV is near Daily Low: Buy from low to high, then sell back toward CV aiming for TP
    - CV is the highest priority entry zone
    - Always expect price to revisit CV before reaching TP
    
    Args:
        df (pd.DataFrame): DataFrame with OHLC data
        symbol (str): Trading symbol (e.g., "US30", "^NDX")
        include_news (bool): Whether to include news sentiment analysis
    
    Returns:
        Dict[str, Any]: Dictionary containing all signal parameters
    """
    
    if len(df) < 2:
        raise ValueError(f"DataFrame must have at least 2 rows, got {len(df)}")
    
    # Get the most recent data
    current_bar = df.iloc[-1]  # Most recent bar
    prev_bar = df.iloc[-2]     # Previous bar
    
    # CORE CONCEPTS from Hybrid Math Strategy
    current_value = float(current_bar["Close"])  # Current Value (CV) - PRIMARY DECISION ZONE
    previous_close = float(prev_bar["Close"])    # Previous Close
    net_change = current_value - previous_close  # Net Change
    
    # Calculate percentage change
    change_pct = (net_change / previous_close) * 100 if previous_close != 0 else 0
    
    # Get today's high and low - key zones for reversals/breakouts
    today_high = float(df["High"].max())
    today_low = float(df["Low"].min())
    
    # Calculate CV position within daily range for advanced logic
    daily_range = today_high - today_low
    if daily_range > 0:
        cv_position = (current_value - today_low) / daily_range
    else:
        cv_position = 0.5  # Default to middle if no range
    
    # TAKE PROFIT CALCULATION (Core Hybrid Math Formula)
    # If net change is positive → TP = CV + Net Change
    # If net change is negative → TP = CV - Net Change
    if net_change > 0:
        take_profit = current_value + abs(net_change)
    else:
        take_profit = current_value - abs(net_change)
    
    # HYBRID MATH STRATEGY v2.0 - Net Change Determines Bias
    
    # Step 1: Determine bias based on Net Change (user's requirement)
    if net_change > 0:
        bias = "LONG"
        bias_text = "Bullish (Net Change > 0)"
    else:
        bias = "SHORT"
        bias_text = "Bearish (Net Change < 0)"
    
    # Step 2: Standard entry/exit calculations (will be refined in formatting)
    # These are basic calculations that will be overridden in the formatting function
    entry1 = today_low if bias == "LONG" else today_high
    entry2 = current_value
    tp1 = current_value
    tp2 = take_profit
    # Stop loss should be 100-200 points from entry, in the correct direction
    if bias == "LONG":
        # For bullish signals, stop loss should be BELOW the entry points
        sl_tight = min(today_low, current_value) - 100  # 100 points below lower entry
        sl_wide = min(today_low, current_value) - 200   # 200 points below lower entry
    else:
        # For bearish signals, stop loss should be ABOVE the entry points  
        sl_tight = max(today_high, current_value) + 100  # 100 points above higher entry
        sl_wide = max(today_high, current_value) + 200   # 200 points above higher entry
    
    # Determine if this is a weekend signal
    current_time = datetime.now()
    trading_date = get_trading_date()
    is_weekend_signal = current_time.weekday() >= 5  # Saturday or Sunday
    
    # Create the signal dictionary
    signal = {
        "symbol": symbol,
        "display_name": get_display_name(symbol),
        "bias": bias,
        "bias_text": bias_text,
        "current_value": round(current_value, 2),
        "previous_close": round(previous_close, 2),
        "net_change": round(net_change, 2),
        "change_pct": round(change_pct, 2),
        "today_high": round(today_high, 2),
        "today_low": round(today_low, 2),
        "take_profit": round(take_profit, 2),  # The official TP calculation
        "entry1": round(entry1, 2),
        "entry2": round(entry2, 2),
        "tp1": round(tp1, 2),
        "tp2": round(tp2, 2),
        "sl_tight": round(sl_tight, 2),
        "sl_wide": round(sl_wide, 2),
        "cv_position": round(cv_position, 2),
        "timestamp": trading_date.strftime("%d %B %Y"),
        "generated_at": current_time.isoformat(),
        "is_weekend_signal": is_weekend_signal
    }
    
    # Simplified strategy - no complex risky plays
    signal["has_risky_play"] = False
    
    # Add news sentiment analysis using Gemini AI
    if include_news:
        try:
            from news_sentiment import analyze_symbol_news
            news_analysis = analyze_symbol_news(symbol, signal)
            
            # Extract sentiment data
            sentiment_data = news_analysis['sentiment']
            sentiment_label = sentiment_data['sentiment_label']
            sentiment_score = sentiment_data['sentiment_score']
            sentiment_confidence = sentiment_data['confidence']
            model_used = sentiment_data.get('model_used', 'unknown')
            
            # Calculate probability based on setup type + news sentiment
            if cv_position <= 0.3:
                # CV Low Range setups have higher base confidence
                base_probability = 80  # High confidence for low range
            elif cv_position >= 0.7:
                # CV High Range setups have higher base confidence
                base_probability = 80  # High confidence for high range
            else:
                # CV Middle Range setups have medium base confidence
                base_probability = 65  # Medium confidence for middle range
            
            # Adjust probability based on news sentiment alignment
            if sentiment_label == 'Bullish' and bias == 'LONG':
                # News supports bullish bias
                probability_percentage = min(85, base_probability + 10)
            elif sentiment_label == 'Bearish' and bias == 'SHORT':
                # News supports bearish bias  
                probability_percentage = min(85, base_probability + 10)
            elif sentiment_label == 'Bullish' and bias == 'SHORT':
                # News contradicts bearish bias
                probability_percentage = max(45, base_probability - 15)
            elif sentiment_label == 'Bearish' and bias == 'LONG':
                # News contradicts bullish bias
                probability_percentage = max(45, base_probability - 15)
            else:
                # Neutral sentiment or no strong alignment
                probability_percentage = base_probability
            
            # Factor in news confidence
            if sentiment_confidence >= 80:
                # High confidence news - stronger adjustment
                if probability_percentage > base_probability:
                    probability_percentage = min(88, probability_percentage + 3)
            
            probability_label = "High" if probability_percentage >= 75 else "Medium"
            
            # Update signal with news-enhanced analysis
            signal.update({
                "bias": bias,
                "bias_text": f"{bias_text} | News: {sentiment_label} ({model_used})",
                "sentiment": sentiment_label,
                "sentiment_score": sentiment_score,
                "probability_percentage": probability_percentage,
                "probability_label": probability_label,
                "news_count": sentiment_data.get('total_articles', 0),
                "model_used": model_used
            })
            
        except Exception as e:
            print(f"⚠️ News analysis failed: {str(e)}")
            # Fallback to technical-only analysis
            probability_percentage = 80 if cv_position <= 0.3 or cv_position >= 0.7 else 65
            probability_label = "High" if probability_percentage >= 75 else "Medium"
            
            signal.update({
                "bias": bias,
                "bias_text": f"{bias_text} | Technical Only",
                "sentiment": "Technical Only",
                "sentiment_score": 0.0,
                "probability_percentage": probability_percentage,
                "probability_label": probability_label,
                "news_count": 0,
                "model_used": "none"
            })
    else:
        # Pure technical analysis without news
        probability_percentage = 80 if cv_position <= 0.3 or cv_position >= 0.7 else 65
        probability_label = "High" if probability_percentage >= 75 else "Medium"
        
        signal.update({
            "bias": bias,
            "bias_text": f"{bias_text} | Technical Only",
            "sentiment": "Technical Only",
            "sentiment_score": 0.0,
            "probability_percentage": probability_percentage,
            "probability_label": probability_label,
            "news_count": 0,
            "model_used": "none"
        })
    
    # Add TradingView integration at the end, before returning signal
    try:
        from BFI_Signals_Integration import integrate_with_strategy
        integrate_with_strategy(signal, symbol)
    except ImportError:
        # Integration module not available, continue without it
        pass
    except Exception as e:
        print(f"⚠️ TradingView integration warning: {str(e)}")
    
    return signal


def format_signal_for_discord(signal: Dict[str, Any], include_risky_play: bool = True) -> str:
    """
    Format a signal for Discord posting using the comprehensive Hybrid Math Strategy format
    
    Args:
        signal (Dict[str, Any]): Signal dictionary from calculate_signal()
        include_risky_play (bool): Whether to include risky play section (default: True)
    
    Returns:
        str: Formatted signal for Discord posting
    """
    
    # Check if this is a manual signal - use simplified format
    if signal.get('manual', False):
        display_name = signal.get("display_name", signal["symbol"])
        date_header = signal['timestamp']
        if signal.get('is_weekend_signal', False):
            date_header += " (Weekend Signal for Monday Trading)"
        
        # Build simplified manual signal format
        bias_emoji = "🟢" if signal['bias'] == "LONG" else "🔴"
        
        # Format Take Profits
        tp_text = f"**TP1:** {signal['tp1']:,.2f}"
        if signal.get('tp2') and signal['tp2'] != signal['tp1']:
            tp_text += f" | **TP2:** {signal['tp2']:,.2f}"
        if signal.get('tp3'):
            tp_text += f" | **TP3:** {signal['tp3']:,.2f}"
        
        # Format Stop Loss
        sl_text = f"**SL Tight:** {signal['sl_tight']:,.2f}"
        if signal.get('sl_wide') and signal['sl_wide'] != signal['sl_tight']:
            sl_text += f" | **SL Extended:** {signal['sl_wide']:,.2f}"
        
        # Risk Level formatting
        risk_level = signal.get('risk_quality', 'MEDIUM')
        risk_emojis = {
            'LOW': '🟢',
            'MEDIUM': '🟡', 
            'HIGH': '🟠',
            'EXTREME': '🔴'
        }
        risk_emoji = risk_emojis.get(risk_level, '🟡')
        
        manual_signal = f"""
{bias_emoji} **{display_name} – {signal['bias']} Signal**
**Date:** {date_header}

📈 **Entry:** {signal['entry1']:,.2f}
{tp_text}
{sl_text}

📊 **Confidence:** {signal.get('confidence', 50)}%
{risk_emoji} **Risk Level:** {risk_level}

⚠️ **Disclaimer:** These signals are developed under the Bonang Finance Hybrid Math Strategy for VIP traders. Markets may behave differently depending on broker feeds. Use strict risk management and only trade what you can afford to lose.

*By Prophet Bonang @ Bonang Financial Institute - Trade at your own risk.*
"""
        return manual_signal.strip()
    
    # Use display name instead of technical symbol
    display_name = signal.get("display_name", signal["symbol"])
    
    # Format timestamp to show readable date format
    from datetime import datetime
    try:
        # Parse ISO timestamp and format as "28 July 2025"
        timestamp_obj = datetime.fromisoformat(signal['timestamp'].replace('Z', '+00:00'))
        date_header = timestamp_obj.strftime('%d %B %Y')
    except (ValueError, KeyError):
        # Fallback to original timestamp if parsing fails
        date_header = signal.get('timestamp', 'Unknown Date')
    
    # Add weekend signal indicator
    if signal.get('is_weekend_signal', False):
        date_header += " (Weekend Signal for Monday Trading)"
    
    # Determine strategy type based on CV position
    cv_position = signal.get('cv_position', 0.5)
    cv_position_pct = cv_position * 100
    
    if cv_position <= 0.3:
        strategy_type = "CV Low Range"
        cv_context = "CV ≈ Daily Low"
    elif cv_position >= 0.7:
        strategy_type = "CV High Range" 
        cv_context = "CV ≈ Daily High"
    else:
        strategy_type = "CV Middle Range"
        cv_context = "CV Middle Range"
    
    # Market bias with CV context - BIAS IS DETERMINED BY NET CHANGE
    main_bias = signal["bias"]  # Get bias from the signal calculation
    
    # Check if CV is within 30% of daily extremes for risky play scenarios
    cv_near_highs = cv_position >= 0.7  # CV within 30% of daily highs
    cv_near_lows = cv_position <= 0.3   # CV within 30% of daily lows
    
    if main_bias == "LONG":
        bias_emoji = "✅"
        if cv_near_lows:
            # Bullish bias + CV near lows → Regular signal: Buy from CV/Low
            bias_text = f"Bullish (Net Change +{signal['net_change']:.2f}) - CV at Lows: Buy Zone Active"
            strategy_type = "CV Low Range - Buy Zone"
        else:
            # Normal bullish bias
            bias_text = f"Bullish (Net Change +{signal['net_change']:.2f}) - Wait for Low Entry"
            strategy_type = "CV Middle/High Range - Wait for Pullback"
    else:
        bias_emoji = "❌"
        if cv_near_highs:
            # Bearish bias + CV near highs → Regular signal: Sell from CV/High
            bias_text = f"Bearish (Net Change {signal['net_change']:.2f}) - CV at Highs: Sell Zone Active"
            strategy_type = "CV High Range - Sell Zone"
        else:
            # Normal bearish bias
            bias_text = f"Bearish (Net Change {signal['net_change']:.2f}) - Wait for High Entry"
            strategy_type = "CV Low/Middle Range - Wait for Bounce"
    
    # Get probability and sentiment data
    prob_pct = signal.get("probability_percentage", 65)
    prob_label = signal.get("probability_label", "Medium")
    sentiment = signal.get("sentiment", "Neutral")
    
    # Probability emoji
    if prob_pct >= 75:
        prob_emoji = "🔥"
    elif prob_pct >= 60:
        prob_emoji = "⚡"
    else:
        prob_emoji = "📊"
    
    # Take Profit calculation (official Hybrid Math formula)
    if signal['net_change'] > 0:
        tp_calculation = f"CV + Net Change = {signal['current_value']:,.2f} + {signal['net_change']:,.2f} = {signal['take_profit']:,.2f}"
    else:
        tp_calculation = f"CV - Net Change = {signal['current_value']:,.2f} - {abs(signal['net_change']):,.2f} = {signal['take_profit']:,.2f}"
    
    # Strategy logic based on bias and CV position
    if main_bias == "LONG":
        if cv_near_lows:
            # Bullish bias + CV near lows → Regular signal: Buy from CV/Low
            strategy_logic = "Conservative: Buy from CV/Low + Risky Play: Advanced targeting"
        else:
            # Normal bullish trend
            strategy_logic = "Conservative: Wait for Low Entry + Risky Play: Buy from CV targeting Highs"
    else:
        if cv_near_highs:
            # Bearish bias + CV near highs → Regular signal: Sell from CV/High
            strategy_logic = "Conservative: Sell from CV/High + Risky Play: Advanced targeting"
        else:
            # Normal bearish trend
            strategy_logic = "Conservative: Wait for High Entry + Risky Play: Sell from CV targeting Lows"
    
    # Entry zones based on main bias and CV position - REGULAR SIGNAL LOGIC
    if main_bias == "LONG":
        if cv_near_lows:
            # Bullish bias + CV at lows → Buy from CV or Low
            entry1 = signal['current_value']
            entry1_desc = "Buy from CV (At Lows)"
            entry2 = signal['today_low']
            entry2_desc = "Buy from Daily Low"
    
            # Check for manual TP values first, then use automatic calculation
            if 'tp1' in signal and signal['tp1'] is not None:
                tp1 = signal['tp1']
                tp1_desc = "Manual TP1 (User Set)"
            else:
                # Target: High or (CV + net change) - whichever is higher
                target_high = signal['today_high']
                target_calculated = signal['current_value'] + abs(signal['net_change'])
                if target_high > target_calculated:
                    tp1 = target_high
                    tp1_desc = "Daily High (Higher Target)"
                else:
                    tp1 = target_calculated
                    tp1_desc = "CV + Net Change (Higher Target)"
            
            if 'tp2' in signal and signal['tp2'] is not None:
                tp2 = signal['tp2']
                tp2_desc = "Manual TP2 (User Set)"
            else:
                # Target: High or (CV + net change) - whichever is higher
                target_high = signal['today_high']
                target_calculated = signal['current_value'] + abs(signal['net_change'])
                if target_high > target_calculated:
                    tp2 = target_calculated
                    tp2_desc = "CV + Net Change (Secondary)"
                else:
                    tp2 = target_high
                    tp2_desc = "Daily High (Secondary)"
        else:
            # Normal bullish - wait for low entry
            entry1 = signal['today_low']
            entry1_desc = "Buy from Daily Low"
            entry2 = signal['previous_close']
            entry2_desc = "Buy from Previous Close"
            
            # Check for manual TP values first, then use automatic calculation
            if 'tp1' in signal and signal['tp1'] is not None:
                tp1 = signal['tp1']
                tp1_desc = "Manual TP1 (User Set)"
            else:
                tp1 = signal['today_high']
            tp1_desc = "Daily High (First Target)"
            
            if 'tp2' in signal and signal['tp2'] is not None:
                tp2 = signal['tp2']
                tp2_desc = "Manual TP2 (User Set)"
            else:
                tp2 = signal['take_profit']
            tp2_desc = "TP Calculation (Extended)"
    else:
        if cv_near_highs:
            # Bearish bias + CV at highs → Sell from CV or High
            entry1 = signal['current_value']
            entry1_desc = "Sell from CV (At Highs)"
            entry2 = signal['today_high']
            entry2_desc = "Sell from Daily High"
            
            # Check for manual TP values first, then use automatic calculation
            if 'tp1' in signal and signal['tp1'] is not None:
                tp1 = signal['tp1']
                tp1_desc = "Manual TP1 (User Set)"
            else:
                # Target: Low or (CV - net change) - whichever is lower
                target_low = signal['today_low']
                target_calculated = signal['current_value'] - abs(signal['net_change'])
                if target_low < target_calculated:
                    tp1 = target_low
                    tp1_desc = "Daily Low (Lower Target)"
                else:
                    tp1 = target_calculated
                    tp1_desc = "CV - Net Change (Lower Target)"
            
            if 'tp2' in signal and signal['tp2'] is not None:
                tp2 = signal['tp2']
                tp2_desc = "Manual TP2 (User Set)"
            else:
                # Target: Low or (CV - net change) - whichever is lower
                target_low = signal['today_low']
                target_calculated = signal['current_value'] - abs(signal['net_change'])
                if target_low < target_calculated:
                    tp2 = target_calculated
                    tp2_desc = "CV - Net Change (Secondary)"
                else:
                    tp2 = target_low
                    tp2_desc = "Daily Low (Secondary)"
        else:
            # Normal bearish - wait for high entry
            entry1 = signal['today_high']
            entry1_desc = "Sell from Daily High"
            entry2 = signal['previous_close']
            entry2_desc = "Sell from Previous Close"
            
            # Check for manual TP values first, then use automatic calculation
            if 'tp1' in signal and signal['tp1'] is not None:
                tp1 = signal['tp1']
                tp1_desc = "Manual TP1 (User Set)"
            else:
                tp1 = signal['today_low']
            tp1_desc = "Daily Low (First Target)"
            
            if 'tp2' in signal and signal['tp2'] is not None:
                tp2 = signal['tp2']
                tp2_desc = "Manual TP2 (User Set)"
            else:
                tp2 = signal['take_profit']
            tp2_desc = "TP Calculation (Extended)"
    
    # Stop Loss calculations - use manual values if provided, otherwise calculate automatically
    if 'sl_tight' in signal and signal['sl_tight'] is not None:
        tight_sl = signal['sl_tight']
        # Use manual tight SL for all entries
        entry1_tight_sl = tight_sl
        entry2_tight_sl = tight_sl
    else:
        # Automatic calculation based on entry points (100 points from each entry)
        if main_bias == "LONG":
            # For buy signals, stop loss should be BELOW the entry points
            entry1_tight_sl = entry1 - 100
            entry2_tight_sl = entry2 - 100
            # Use the higher of the two SLs (more conservative)
            tight_sl = max(entry1_tight_sl, entry2_tight_sl)
        else:
            # For sell signals, stop loss should be ABOVE the entry points
            entry1_tight_sl = entry1 + 100
            entry2_tight_sl = entry2 + 100
            # Use the higher of the two SLs (more conservative for sell signals)
            tight_sl = max(entry1_tight_sl, entry2_tight_sl)
    
    if 'sl_wide' in signal and signal['sl_wide'] is not None:
        wide_sl = signal['sl_wide']
        # Use manual wide SL for all entries
        entry1_wide_sl = wide_sl
        entry2_wide_sl = wide_sl
    else:
        # Automatic calculation based on entry points (200 points from each entry)
        if main_bias == "LONG":
            # For buy signals, stop loss should be BELOW the entry points
            entry1_wide_sl = entry1 - 200
            entry2_wide_sl = entry2 - 200
            # Use the higher of the two SLs (more conservative)
            wide_sl = max(entry1_wide_sl, entry2_wide_sl)
        else:
            # For sell signals, stop loss should be ABOVE the entry points
            entry1_wide_sl = entry1 + 200
            entry2_wide_sl = entry2 + 200
            # Use the higher of the two SLs (more conservative for sell signals)
            wide_sl = max(entry1_wide_sl, entry2_wide_sl)
    
    # Risky Play calculations based on CV position and main bias
    risky_entry = signal['current_value']  # Always from CV
    
    if main_bias == "LONG" and cv_near_highs:
        # Bullish bias but CV near highs → Risky play: sell to lows then buy
        risky_strategy = "Sell from CV targeting Lows, then Buy from Lows targeting Highs/Previous Close."
        # For risky play: sell first, then buy
        risky_target_sell = min(signal['today_low'], signal['previous_close'])  # Lowest value
        risky_target_buy = max(signal['today_high'], signal['previous_close'])  # Highest value
        risky_tp1 = risky_target_sell
        # For the initial sell action, TP2 should be even lower than TP1
        risky_tp2 = risky_target_sell - abs(signal['net_change'])
        # For sell signals, stop loss should be ABOVE entry: CV + 100 for tight, CV + 200 for wide
        risky_sl_tight = signal['current_value'] + 100
        risky_sl_wide = signal['current_value'] + 200
        
    elif main_bias == "SHORT" and cv_near_lows:
        # Bearish bias but CV near lows → Risky play: buy from CV/lows
        risky_strategy = "Buy from CV/Lows targeting Highs/Previous Close based on highest value."
        # For risky play: buy targeting highest value
        risky_target = max(signal['today_high'], signal['previous_close'])  # Highest value
        risky_tp1 = risky_target
        # For this buy scenario, TP2 should be higher than TP1
        risky_tp2 = risky_target + abs(signal['net_change'])
        # For buy signals, stop loss should be below entry: CV - 100 for tight, CV - 200 for wide
        risky_sl_tight = signal['current_value'] - 100
        risky_sl_wide = signal['current_value'] - 200
        
    else:
        # Normal trend following risky play
        if main_bias == "LONG":
            risky_strategy = "Buy from CV targeting Daily High or Previous Close."
            risky_target = max(signal['today_high'], signal['previous_close'])
            risky_tp1 = risky_target
            risky_tp2 = signal['take_profit']
            # For buy signals, stop loss should be below entry: CV - 100 for tight, CV - 200 for wide
            risky_sl_tight = signal['current_value'] - 100
            risky_sl_wide = signal['current_value'] - 200
        else:
            risky_strategy = "Sell from CV targeting Daily Low or Previous Close."
            risky_target = min(signal['today_low'], signal['previous_close'])
            risky_tp1 = risky_target
            # For SHORT signals, TP2 should be even lower than TP1
            risky_tp2 = risky_target - abs(signal['net_change'])
            # For sell signals, stop loss should be above entry: CV + 100 for tight, CV + 200 for wide
            risky_sl_tight = signal['current_value'] + 100
            risky_sl_wide = signal['current_value'] + 200
    
    # Set risky play header and descriptions
    if main_bias == "LONG" and cv_near_highs:
        # Bullish bias + CV near highs → Risky play: sell then buy
        risky_play_header = "🚨 **RISKY PLAY OPTION (Sell from CV, then Buy):**"
        risky_entry_desc = "Sell from CV"
        risky_target_display = f"{risky_target_sell:,.2f} (Sell Target), then {risky_target_buy:,.2f} (Buy Target)"
        risky_tp1_desc = "Sell target (Low/Previous Close)"
        risky_tp2_desc = "Extended sell target"
    elif main_bias == "SHORT" and cv_near_lows:
        # Bearish bias + CV near lows → Risky play: buy from CV/lows
        risky_play_header = "🚨 **RISKY PLAY OPTION (Buy from CV):**"
        risky_entry_desc = "Buy from CV"
        risky_target_display = f"{risky_target:,.2f} (Buy Target - Highest Value)"
        risky_tp1_desc = "Buy target (High/Previous Close)"
        risky_tp2_desc = "Extended target"
    else:
        # Normal trend following risky play
        if main_bias == "LONG":
            risky_play_header = "🚨 **RISKY PLAY OPTION (Buy from CV):**"
            risky_entry_desc = "Buy from CV"
            risky_target_display = f"{risky_target:,.2f} (Trend Target)"
            risky_tp1_desc = "Buy target (High/Previous Close)"
            risky_tp2_desc = "Extended target"
        else:
            risky_play_header = "🚨 **RISKY PLAY OPTION (Sell from CV):**"
            risky_entry_desc = "Sell from CV"
            risky_target_display = f"{risky_target:,.2f} (Trend Target)"
            risky_tp1_desc = "Sell target (Low/Previous Close)"
            risky_tp2_desc = "Extended target"
    
    # Conditionally include risky play section
    if include_risky_play:
        # Use manual risky play values if provided, otherwise use automatic calculations
        final_risky_entry = signal.get('manual_risky_entry', risky_entry)
        final_risky_tp1 = signal.get('manual_risky_tp1', risky_tp1)
        final_risky_tp2 = signal.get('manual_risky_tp2', risky_tp2)
        final_risky_sl = signal.get('manual_risky_sl', risky_sl_tight)
        final_risky_strategy = signal.get('manual_risky_strategy', risky_strategy)
        
        # Update descriptions for manual values
        if 'manual_risky_entry' in signal:
            risky_entry_desc = "Manual Entry (User Set)"
        if 'manual_risky_tp1' in signal:
            risky_tp1_desc = "Manual TP1 (User Set)"
        if 'manual_risky_tp2' in signal:
            risky_tp2_desc = "Manual TP2 (User Set)"
        
        # Format risky target display for manual values
        if 'manual_risky_tp1' in signal and 'manual_risky_tp2' in signal:
            risky_target_display = f"{final_risky_tp1:,.2f} (TP1) | {final_risky_tp2:,.2f} (TP2)"
        elif 'manual_risky_tp1' in signal:
            risky_target_display = f"{final_risky_tp1:,.2f} (Manual TP1)"
        elif 'manual_risky_tp2' in signal:
            risky_target_display = f"{final_risky_tp2:,.2f} (Manual TP2)"
        
        risky_play_section = f"""{risky_play_header}
💰 **Risky Entry:** {final_risky_entry:,.2f} ({risky_entry_desc})
🎯 **Target:** {risky_target_display}
📈 **Risky TP1:** {final_risky_tp1:,.2f} ({risky_tp1_desc})
📉 **Risky TP2:** {final_risky_tp2:,.2f} ({risky_tp2_desc})
🛑 **Risky SL:** {final_risky_sl:,.2f} ({"Manual (User Set)" if 'manual_risky_sl' in signal else "Tight"}) | {risky_sl_wide:,.2f} (Wide)

💡 **Risky Play Strategy:** {final_risky_strategy}

"""
    else:
        risky_play_section = ""

    # Add custom comments section if provided
    custom_comments_section = ""
    if signal.get('custom_comments'):
        custom_comments_section = f"""
📝 **Additional Analysis:**
{signal['custom_comments']}

"""
    

    
    # Format the comprehensive signal
    formatted_signal = f"""📈 **{display_name} Signal – {date_header}**

**Strategy:** The Hybrid Math Strategy by Bonang Financial Institute
**Type:** Dual Strategy: {strategy_type}
**Market Bias:** {bias_emoji} {bias_text}
**Probability:** {prob_emoji} {prob_pct}% ({prob_label}) | Sentiment: {sentiment}

📊 **Core Data (Market Analyzed as 1 + 1):**
Current Value (CV): {signal['current_value']:,.2f} | Previous Close: {signal['previous_close']:,.2f}
Net Change: {signal['net_change']:+.2f} ({signal['change_pct']:+.2f}%) | High: {signal['today_high']:,.2f} | Low: {signal['today_low']:,.2f}
CV Position: {cv_position_pct:.1f}% from daily low

📈 **Take Profit Calculation:**
{tp_calculation}

🎯 **Strategy Logic:**
{strategy_logic}

🔹 **Entry Zones:**
Entry 1: {entry1:,.2f} ({entry1_desc})
Entry 2: {entry2:,.2f} ({entry2_desc})

🎯 **Take Profit Targets:**
TP1: {tp1:,.2f} ({tp1_desc})
TP2: {tp2:,.2f} ({tp2_desc})

🛡️ **Stop Loss:**
Entry 1 - Tight SL: {entry1_tight_sl:,.2f} | Wide SL: {entry1_wide_sl:,.2f}
Entry 2 - Tight SL: {entry2_tight_sl:,.2f} | Wide SL: {entry2_wide_sl:,.2f}

{risky_play_section}{custom_comments_section}📋 **Key Rule:** Wait for optimal entry points. Use partial profit management for better risk-to-reward ratios.

⚠️ **Risk Warning & Disclaimer:** These signals are developed under the Bonang Finance Hybrid Math Strategy for VIP traders. Markets may behave differently depending on broker feeds. Use strict risk management and only trade what you can afford to lose.

*By Prophet Bonang @ Bonang Financial Institute - Trade at your own risk.*"""

    return formatted_signal


if __name__ == "__main__":
    # Test the strategy with sample data
    print("🧪 Testing Hybrid Math Strategy with News Sentiment...")
    
    # Create sample data matching the user's example
    test_data = {
        'Open': [44400.00, 44500.00],
        'High': [44600.00, 44775.47],
        'Low': [44350.00, 44372.92],
        'Close': [44458.29, 44650.63]
    }
    
    df = pd.DataFrame(test_data)
    
    try:
        # Test signal calculation without news
        signal = calculate_signal(df, "US30", include_news=False)
        print(f"✅ Signal calculated successfully!")
        print(f"Symbol: {signal['symbol']}")
        print(f"Bias: {signal['bias']}")
        print(f"Current Value: {signal['current_value']}")
        print(f"Net Change: {signal['net_change']:+.2f}")
        print(f"Probability: {signal['probability_percentage']}% ({signal['probability_label']})")
        print(f"Sentiment: {signal['sentiment']}")
        
        # Test formatting
        formatted = format_signal_for_discord(signal)
        print(f"\n📋 Formatted Signal:\n{formatted}")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
    
    print("\n✅ Strategy testing complete!") 