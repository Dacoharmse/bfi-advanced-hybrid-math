#!/usr/bin/env python3
"""
BFI Signals AI Dashboard
Web interface for AI interaction, performance monitoring, and learning management
"""

# Configure logging to reduce verbose output
import logging
import warnings
logging.getLogger('werkzeug').setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning, module="transformers")

from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import json
from datetime import datetime, timedelta
import pickle
from ai_engine import AIEngine
from ai_manager import AIManager
import os
from dotenv import load_dotenv
import pandas as pd
from strategy import calculate_signal, get_display_name, get_trading_date, format_signal_for_discord
from data_fetch import fetch_last_two_1h_bars, get_current_price
from discord_working import post_signal, test_discord_connection
from discord_signals import DiscordSignals
import traceback

# Load environment variables
load_dotenv('../.env')

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = 'bfi_signals_dashboard_2025'

# Ensure favicon files are available in static folder
def ensure_favicons():
    """Copy favicon files from assets to static folder if needed"""
    assets_favicon_path = '../assets/Favicon'
    static_path = app.static_folder or 'static'
    
    if os.path.exists(assets_favicon_path) and static_path:
        import shutil
        favicon_files = ['favicon.ico', 'favicon-16x16.png', 'favicon-32x32.png']
        for favicon_file in favicon_files:
            src_path = os.path.join(assets_favicon_path, favicon_file)
            dst_path = os.path.join(static_path, favicon_file)
            if os.path.exists(src_path) and not os.path.exists(dst_path):
                try:
                    shutil.copy2(src_path, dst_path)
                except:
                    pass  # Silently ignore copy errors

ensure_favicons()

# Initialize AI components
ai_engine = AIEngine()
ai_manager = AIManager()

# Market Data Storage System
class MarketDataStorage:
    def __init__(self, file_path='market_data.pkl'):
        self.file_path = file_path
        self.data = self.load_data()
    
    def load_data(self):
        """Load market data from file"""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'rb') as f:
                    return pickle.load(f)
            else:
                return {
                    'nasdaq': {},
                    'gold': {},
                    'dow': {},
                    'last_update': None,
                    'market_close_data': {}
                }
        except Exception as e:
            print(f"Error loading market data: {e}")
            return {
                'nasdaq': {},
                'gold': {},
                'dow': {},
                'last_update': None,
                'market_close_data': {}
            }
    
    def save_data(self):
        """Save market data to file"""
        try:
            with open(self.file_path, 'wb') as f:
                pickle.dump(self.data, f)
        except Exception as e:
            print(f"Error saving market data: {e}")
    
    def update_market_data(self, symbol, data):
        """Update market data for a symbol"""
        self.data[symbol] = {
            'price': data.get('price', '--'),
            'change': data.get('change', '--'),
            'changePercent': data.get('changePercent', '--'),
            'rawChange': data.get('rawChange', 0),
            'previousClose': data.get('previousClose', '--'),
            'high': data.get('high', '--'),
            'low': data.get('low', '--'),
            'timestamp': datetime.now().isoformat()
        }
        self.data['last_update'] = datetime.now().isoformat()
        self.save_data()
    
    def get_market_data(self, symbol):
        """Get stored market data for a symbol"""
        return self.data.get(symbol, {})
    
    def save_market_close_data(self):
        """Save current data as market close data"""
        self.data['market_close_data'] = {
            'nasdaq': self.data.get('nasdaq', {}),
            'gold': self.data.get('gold', {}),
            'dow': self.data.get('dow', {}),
            'close_timestamp': datetime.now().isoformat()
        }
        self.save_data()
    
    def get_market_close_data(self):
        """Get market close data"""
        return self.data.get('market_close_data', {})

# Initialize market data storage
market_data_storage = MarketDataStorage()

# Debug Discord configuration
def check_discord_config():
    """Check Discord configuration and return detailed status"""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    # Check multiple possible .env file locations
    possible_env_paths = [
        '../.env',  # Parent directory
        '.env',     # Current directory
        os.path.join(os.path.dirname(__file__), '..', '.env'),  # Absolute path to parent
    ]
    
    env_file_exists = False
    env_file_path = '../.env'
    
    for path in possible_env_paths:
        if os.path.exists(path):
            env_file_exists = True
            env_file_path = path
            break
    
    return {
        'webhook_configured': bool(webhook_url),
        'webhook_url': webhook_url[:50] + "..." if webhook_url else None,
        'env_file_path': env_file_path,
        'env_file_exists': env_file_exists
    }

@app.route('/')
def dashboard():
    """Main dashboard page"""
    try:
        # Get AI statistics
        stats = ai_engine.get_learning_stats()
        
        # Get recent signals
        conn = sqlite3.connect("ai_learning.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, signal_type, predicted_probability, risk_level, timestamp, actual_outcome, profit_loss
            FROM signal_performance 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        recent_signals = cursor.fetchall()
        
        # Calculate daily stats
        cursor.execute('''
            SELECT COUNT(*) as total_today
            FROM signal_performance 
            WHERE date(timestamp) = date('now')
        ''')
        today_signals = cursor.fetchone()[0]
        
        # Calculate win rate statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_signals,
                SUM(CASE WHEN actual_outcome = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN actual_outcome = 0 THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN actual_outcome = 2 THEN 1 ELSE 0 END) as breakevens,
                CASE 
                    WHEN COUNT(*) > 0 THEN 
                        ROUND((SUM(CASE WHEN actual_outcome = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 1)
                    ELSE 0 
                END as win_rate
            FROM signal_performance 
            WHERE actual_outcome IS NOT NULL
        ''')
        win_rate_stats = cursor.fetchone()
        
        # If no data, set defaults
        if not win_rate_stats or win_rate_stats[0] == 0:
            win_rate_stats = (0, 0, 0, 0, 0.0)
        
        # Get model performance
        cursor.execute('''
            SELECT model_used, COUNT(*) as count, AVG(confidence) as avg_confidence
            FROM news_sentiment 
            GROUP BY model_used
        ''')
        model_stats = cursor.fetchall()
        
        conn.close()
        
        return render_template('dashboard.html', 
                             stats=stats,
                             recent_signals=recent_signals,
                             today_signals=today_signals,
                             model_stats=model_stats,
                             win_rate_stats=win_rate_stats)
    except Exception as e:
        return render_template('dashboard.html', 
                             error=f"Error loading dashboard: {e}",
                             stats={'total_signals': 0, 'success_rate': 0},
                             recent_signals=[],
                             today_signals=0,
                             model_stats=[],
                             win_rate_stats=(0, 0, 0, 0, 0.0))


@app.route('/performance')
def performance():
    """Performance monitoring page"""
    try:
        conn = sqlite3.connect("ai_learning.db")
        cursor = conn.cursor()
        
        # Get performance by symbol
        cursor.execute('''
            SELECT symbol, 
                   COUNT(*) as total_signals,
                   AVG(CASE WHEN actual_outcome = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                   SUM(profit_loss) as total_pl,
                   AVG(predicted_probability) as avg_probability
            FROM signal_performance 
            WHERE actual_outcome IS NOT NULL
            GROUP BY symbol
            ORDER BY total_signals DESC
        ''')
        symbol_performance = cursor.fetchall()
        
        # Get performance by signal type
        cursor.execute('''
            SELECT signal_type,
                   COUNT(*) as total_signals,
                   AVG(CASE WHEN actual_outcome = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                   SUM(profit_loss) as total_pl
            FROM signal_performance 
            WHERE actual_outcome IS NOT NULL
            GROUP BY signal_type
        ''')
        signal_type_performance = cursor.fetchall()
        
        # Get performance by risk level
        cursor.execute('''
            SELECT risk_level,
                   COUNT(*) as total_signals,
                   AVG(CASE WHEN actual_outcome = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                   SUM(profit_loss) as total_pl
            FROM signal_performance 
            WHERE actual_outcome IS NOT NULL
            GROUP BY risk_level
        ''')
        risk_performance = cursor.fetchall()
        
        # Get daily performance for chart
        cursor.execute('''
            SELECT date(timestamp) as trade_date,
                   COUNT(*) as signals,
                   SUM(CASE WHEN actual_outcome = 1 THEN 1 ELSE 0 END) as wins,
                   SUM(profit_loss) as daily_pl
            FROM signal_performance 
            WHERE actual_outcome IS NOT NULL
            AND timestamp > datetime('now', '-30 days')
            GROUP BY date(timestamp)
            ORDER BY trade_date DESC
        ''')
        daily_performance = cursor.fetchall()
        
        conn.close()
        
        return render_template('performance.html',
                             symbol_performance=symbol_performance,
                             signal_type_performance=signal_type_performance,
                             risk_performance=risk_performance,
                             daily_performance=daily_performance)
        
    except Exception as e:
        return render_template('performance.html', 
                             error=f"Error loading performance data: {e}",
                             symbol_performance=[],
                             signal_type_performance=[],
                             risk_performance=[],
                             daily_performance=[])

@app.route('/add_outcome')
def add_outcome_form():
    """Form to add trading outcomes"""
    try:
        conn = sqlite3.connect("ai_learning.db")
        cursor = conn.cursor()
        
        # Get pending signals
        cursor.execute('''
            SELECT id, symbol, signal_type, predicted_probability, timestamp
            FROM signal_performance 
            WHERE actual_outcome IS NULL
            ORDER BY timestamp DESC
            LIMIT 20
        ''')
        pending_signals = cursor.fetchall()
        
        conn.close()
        
        return render_template('add_outcome.html', pending_signals=pending_signals)
        
    except Exception as e:
        return render_template('add_outcome.html', 
                             error=f"Error loading pending signals: {e}",
                             pending_signals=[])

@app.route('/api/add_outcome', methods=['POST'])
def api_add_outcome():
    """API endpoint to add trading outcome"""
    try:
        signal_id = request.form.get('signal_id')
        outcome = request.form.get('outcome') == 'true'
        profit_loss = float(request.form.get('profit_loss', 0))
        
        if not signal_id:
            return jsonify({'error': 'Signal ID required'})
        
        # Add outcome using AI manager
        ai_engine.learn_from_outcome(signal_id, outcome, profit_loss)
        
        return jsonify({'success': True, 'message': 'Trading outcome added successfully!'})
        
    except Exception as e:
        return jsonify({'error': f'Error adding outcome: {str(e)}'})

@app.route('/api/manual_outcome', methods=['POST'])
def api_manual_outcome():
    """API endpoint to manually add trading outcome"""
    try:
        symbol = request.form.get('symbol')
        signal_type = request.form.get('signal_type')
        outcome = request.form.get('outcome') == 'true'
        profit_loss = float(request.form.get('profit_loss', 0))
        
        if not symbol or not signal_type:
            return jsonify({'error': 'Symbol and signal type required'})
        
        # Add manual outcome - ensure symbol and signal_type are not None
        ai_manager.add_manual_outcome(symbol, signal_type, outcome, profit_loss)
        
        return jsonify({'success': True, 'message': 'Manual trading outcome added successfully!'})
        
    except Exception as e:
        return jsonify({'error': f'Error adding manual outcome: {str(e)}'})

@app.route('/signals')
def signals():
    """Signals history page"""
    try:
        conn = sqlite3.connect("ai_learning.db")
        cursor = conn.cursor()
        
        # Get all signals with pagination
        page = request.args.get('page', 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page
        
        # Ensure risky_play_outcome column exists
        try:
            cursor.execute('ALTER TABLE signal_performance ADD COLUMN risky_play_outcome INTEGER')
            conn.commit()
        except sqlite3.OperationalError:
            pass
        
        # Check if risky_play_outcome column exists
        cursor.execute('PRAGMA table_info(signal_performance)')
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'risky_play_outcome' in columns:
            cursor.execute('''
                SELECT id, symbol, signal_type, predicted_probability, risk_level, 
                       timestamp, actual_outcome, profit_loss, risky_play_outcome
                FROM signal_performance 
                ORDER BY timestamp DESC 
                LIMIT ? OFFSET ?
            ''', (per_page, offset))
        else:
            cursor.execute('''
                SELECT id, symbol, signal_type, predicted_probability, risk_level, 
                       timestamp, actual_outcome, profit_loss, NULL as risky_play_outcome
                FROM signal_performance 
                ORDER BY timestamp DESC 
                LIMIT ? OFFSET ?
            ''', (per_page, offset))
        signals_data = cursor.fetchall()
        
        # Get total count for pagination
        cursor.execute('SELECT COUNT(*) FROM signal_performance')
        total_signals = cursor.fetchone()[0]
        
        conn.close()
        
        # Calculate pagination info
        total_pages = (total_signals + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        return render_template('signals.html',
                             signals=signals_data,
                             page=page,
                             total_pages=total_pages,
                             has_prev=has_prev,
                             has_next=has_next)
        
    except Exception as e:
        return render_template('signals.html', 
                             error=f"Error loading signals: {e}",
                             signals=[],
                             page=1,
                             total_pages=1,
                             has_prev=False,
                             has_next=False)

@app.route('/generate_signals')
def generate_signals():
    """Generate signals page"""
    return render_template('generate_signals.html')

@app.route('/journal')
def journal():
    """Journal Signal Page - Track Win Rate and Performance"""
    try:
        conn = sqlite3.connect("ai_learning.db")
        cursor = conn.cursor()
        
        # Get comprehensive performance statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_signals,
                SUM(CASE WHEN actual_outcome = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN actual_outcome = 0 THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN actual_outcome = 2 THEN 1 ELSE 0 END) as breakevens,
                SUM(CASE WHEN actual_outcome IS NULL THEN 1 ELSE 0 END) as pending,
                AVG(CASE WHEN actual_outcome IS NOT NULL THEN predicted_probability * 100 ELSE NULL END) as avg_probability,
                AVG(CASE WHEN actual_outcome = 1 THEN predicted_probability * 100 ELSE NULL END) as avg_win_probability,
                AVG(CASE WHEN actual_outcome = 0 THEN predicted_probability * 100 ELSE NULL END) as avg_loss_probability
            FROM signal_performance
        ''')
        overall_stats = cursor.fetchone()
        
        # Get performance by symbol
        cursor.execute('''
            SELECT 
                symbol,
                COUNT(*) as total_signals,
                SUM(CASE WHEN actual_outcome = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN actual_outcome = 0 THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN actual_outcome = 2 THEN 1 ELSE 0 END) as breakevens,
                SUM(CASE WHEN actual_outcome IS NULL THEN 1 ELSE 0 END) as pending,
                AVG(predicted_probability * 100) as avg_probability,
                ROUND(
                    CAST(SUM(CASE WHEN actual_outcome = 1 THEN 1 ELSE 0 END) AS FLOAT) / 
                    CAST(SUM(CASE WHEN actual_outcome IS NOT NULL THEN 1 ELSE 0 END) AS FLOAT) * 100, 2
                ) as win_rate
            FROM signal_performance 
            GROUP BY symbol
            ORDER BY total_signals DESC
        ''')
        symbol_performance = cursor.fetchall()
        
        # Get performance by signal type (LONG/SHORT)
        cursor.execute('''
            SELECT 
                signal_type,
                COUNT(*) as total_signals,
                SUM(CASE WHEN actual_outcome = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN actual_outcome = 0 THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN actual_outcome = 2 THEN 1 ELSE 0 END) as breakevens,
                SUM(CASE WHEN actual_outcome IS NULL THEN 1 ELSE 0 END) as pending,
                AVG(predicted_probability * 100) as avg_probability,
                ROUND(
                    CAST(SUM(CASE WHEN actual_outcome = 1 THEN 1 ELSE 0 END) AS FLOAT) / 
                    CAST(SUM(CASE WHEN actual_outcome IS NOT NULL THEN 1 ELSE 0 END) AS FLOAT) * 100, 2
                ) as win_rate
            FROM signal_performance 
            GROUP BY signal_type
            ORDER BY total_signals DESC
        ''')
        signal_type_performance = cursor.fetchall()
        
        # Get performance by probability range
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN predicted_probability >= 0.8 THEN 'High (80%+)'
                    WHEN predicted_probability >= 0.65 THEN 'Medium (65-79%)'
                    WHEN predicted_probability >= 0.5 THEN 'Low (50-64%)'
                    ELSE 'Very Low (<50%)'
                END as probability_range,
                COUNT(*) as total_signals,
                SUM(CASE WHEN actual_outcome = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN actual_outcome = 0 THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN actual_outcome = 2 THEN 1 ELSE 0 END) as breakevens,
                SUM(CASE WHEN actual_outcome IS NULL THEN 1 ELSE 0 END) as pending,
                AVG(predicted_probability * 100) as avg_probability,
                ROUND(
                    CAST(SUM(CASE WHEN actual_outcome = 1 THEN 1 ELSE 0 END) AS FLOAT) / 
                    CAST(SUM(CASE WHEN actual_outcome IS NOT NULL THEN 1 ELSE 0 END) AS FLOAT) * 100, 2
                ) as win_rate
            FROM signal_performance 
            GROUP BY probability_range
            ORDER BY avg_probability DESC
        ''')
        probability_performance = cursor.fetchall()
        
        # Get recent signals with outcomes
        cursor.execute('''
            SELECT 
                id, symbol, signal_type, predicted_probability, risk_level, 
                timestamp, actual_outcome, profit_loss
            FROM signal_performance 
            ORDER BY timestamp DESC 
            LIMIT 20
        ''')
        recent_signals = cursor.fetchall()
        
        # Get monthly performance for chart
        cursor.execute('''
            SELECT 
                strftime('%Y-%m', timestamp) as month,
                COUNT(*) as total_signals,
                SUM(CASE WHEN actual_outcome = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN actual_outcome = 0 THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN actual_outcome = 2 THEN 1 ELSE 0 END) as breakevens,
                ROUND(
                    CAST(SUM(CASE WHEN actual_outcome = 1 THEN 1 ELSE 0 END) AS FLOAT) / 
                    CAST(SUM(CASE WHEN actual_outcome IS NOT NULL THEN 1 ELSE 0 END) AS FLOAT) * 100, 2
                ) as win_rate
            FROM signal_performance 
            WHERE timestamp >= datetime('now', '-6 months')
            GROUP BY strftime('%Y-%m', timestamp)
            ORDER BY month DESC
        ''')
        monthly_performance = cursor.fetchall()
        
        conn.close()
        
        # Calculate overall win rate
        total_completed = overall_stats[1] + overall_stats[2] + overall_stats[3]  # wins + losses + breakevens
        overall_win_rate = (overall_stats[1] / total_completed * 100) if total_completed > 0 else 0
        
        return render_template('journal.html',
                             overall_stats=overall_stats,
                             overall_win_rate=round(overall_win_rate, 2),
                             symbol_performance=symbol_performance,
                             signal_type_performance=signal_type_performance,
                             probability_performance=probability_performance,
                             recent_signals=recent_signals,
                             monthly_performance=monthly_performance)
        
    except Exception as e:
        return render_template('journal.html', 
                             error=f"Error loading journal data: {e}",
                             overall_stats=(0, 0, 0, 0, 0, 0, 0, 0),
                             overall_win_rate=0,
                             symbol_performance=[],
                             signal_type_performance=[],
                             probability_performance=[],
                             recent_signals=[],
                             monthly_performance=[])

@app.route('/api/discord_debug', methods=['GET'])
def api_discord_debug():
    """Debug Discord configuration"""
    try:
        config = check_discord_config()
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Debug error: {str(e)}'
        })

@app.route('/api/test_discord_connection', methods=['POST'])
def api_test_discord_connection():
    """Test Discord webhook connection with detailed debugging"""
    try:
        # First check configuration
        config = check_discord_config()
        
        if not config['env_file_exists']:
            return jsonify({
                'success': False,
                'error': '❌ .env file not found. Please create .env file in project root.',
                'debug': config
            })
        
        if not config['webhook_configured']:
            return jsonify({
                'success': False,
                'error': '❌ DISCORD_WEBHOOK_URL not configured in .env file.',
                'debug': config
            })
        
        # Test the actual connection
        success = test_discord_connection()
        if success:
            return jsonify({
                'success': True,
                'message': '✅ Discord connection test successful!',
                'debug': config
            })
        else:
            return jsonify({
                'success': False,
                'error': '❌ Discord webhook test failed. Check webhook URL validity.',
                'debug': config
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'❌ Discord connection error: {str(e)}',
            'debug': check_discord_config()
        })

@app.route('/track_signals')
def track_signals():
    """Track Signals Page - Mark signals as Win/Loss/Breakeven"""
    try:
        conn = sqlite3.connect("ai_learning.db")
        cursor = conn.cursor()
        
        # Ensure risky_play_outcome and manual columns exist
        try:
            cursor.execute('ALTER TABLE signal_performance ADD COLUMN risky_play_outcome INTEGER')
            conn.commit()
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE signal_performance ADD COLUMN manual INTEGER DEFAULT 0')
            conn.commit()
        except sqlite3.OperationalError:
            pass
        
        # Check if risky_play_outcome column exists
        cursor.execute('PRAGMA table_info(signal_performance)')
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'risky_play_outcome' in columns:
            cursor.execute('''
                SELECT 
                    id, symbol, signal_type, predicted_probability, risk_level, 
                    timestamp, actual_outcome, risky_play_outcome, COALESCE(manual, 0) as manual
                FROM signal_performance 
                ORDER BY timestamp DESC
                LIMIT 100
            ''')
        else:
            cursor.execute('''
                SELECT 
                    id, symbol, signal_type, predicted_probability, risk_level, 
                    timestamp, actual_outcome, NULL as risky_play_outcome, COALESCE(manual, 0) as manual
                FROM signal_performance 
                ORDER BY timestamp DESC
                LIMIT 100
            ''')
        all_signals = cursor.fetchall()
        
        # Split signals into daily (auto-generated) and manual based on manual flag
        daily_signals = []
        manual_signals = []
        
        for signal in all_signals:
            # Use the manual flag to properly categorize signals
            is_manual = signal[8] if len(signal) > 8 else 0  # manual flag is at index 8
            
            if is_manual:
                manual_signals.append(signal)
            else:
                daily_signals.append(signal)
        
        conn.close()
        
        return render_template('track_signals.html', 
                             daily_signals=daily_signals,
                             manual_signals=manual_signals)
    except Exception as e:
        print(f"❌ Error loading track signals page: {str(e)}")
        return render_template('track_signals.html', 
                             daily_signals=[],
                             manual_signals=[])

@app.route('/api/auto_generate_signal', methods=['POST'])
def api_auto_generate_signal():
    """Auto-generate signal using hybrid math strategy and post to Discord"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'US30')
        
        # Validate symbol (only US30 and NAS100 allowed)
        if symbol not in ['US30', 'NAS100']:
            return jsonify({'error': 'Only US30 and NAS100 symbols are supported'})
        
        # Convert to technical symbol for data fetching
        tech_symbol = '^DJI' if symbol == 'US30' else '^NDX'
        
        # Fetch market data
        print(f"🔄 Fetching market data for {symbol}...")
        df = fetch_last_two_1h_bars(tech_symbol)
        
        if len(df) < 2:
            return jsonify({'error': f'Insufficient market data for {symbol}. Need at least 2 bars.'})
        
        # Get real-time current price and update dataframe
        current_value = get_current_price(tech_symbol)
        if current_value is None:
            # Fallback to last close if real-time price unavailable
            current_value = float(df.iloc[-1]['Close'])
            print(f"⚠️ Using last close as current price: ${current_value:,.2f}")
        else:
            print(f"✅ Got real-time current price: ${current_value:,.2f}")
            # Update the last bar's close price to current real-time price
            df.iloc[-1, df.columns.get_loc('Close')] = current_value
        
        # Generate signal using hybrid math strategy
        print(f"📊 Calculating signal for {symbol}...")
        signal = calculate_signal(df, symbol, include_news=True)
        

        
        # Post signal to Discord using the signals bot
        print(f"🚀 Posting signal to Discord for {symbol}...")
        discord_success = post_signal(signal)
        
        if not discord_success:
            return jsonify({
                'error': 'Failed to post signal to Discord. Check webhook configuration.',
                'signal': signal
            })
        
        # Store signal in database as backup/logging
        trading_date = get_trading_date()
        conn = sqlite3.connect("ai_learning.db")
        cursor = conn.cursor()
        
        # Ensure manual column exists
        try:
            cursor.execute('ALTER TABLE signal_performance ADD COLUMN manual INTEGER DEFAULT 0')
            conn.commit()
        except sqlite3.OperationalError:
            pass
        
        cursor.execute('''
            INSERT INTO signal_performance 
            (symbol, signal_type, predicted_probability, risk_level, timestamp, manual)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            symbol,
            signal['bias'],
            signal['probability_percentage'] / 100.0,
            signal.get('probability_label', 'Medium').lower(),
            trading_date.isoformat(),
            0  # Mark as auto-generated signal
        ))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'signal': signal,
            'discord_posted': True,
            'message': f'🚀 Signal generated and posted to Discord successfully for {symbol}!'
        })
        
    except Exception as e:
        print(f"❌ Error in auto signal generation: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Error generating signal: {str(e)}'})

@app.route('/api/fetch_market_data', methods=['POST'])
def api_fetch_market_data():
    """Fetch market data for semi-auto signal generation"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'US30')
        
        # Validate symbol
        if symbol not in ['US30', 'NAS100']:
            return jsonify({'error': 'Only US30 and NAS100 symbols are supported'})
        
        # Convert to technical symbol
        tech_symbol = '^DJI' if symbol == 'US30' else '^NDX'
        
        # Fetch market data
        print(f"🔄 Fetching market data for {symbol}...")
        df = fetch_last_two_1h_bars(tech_symbol)
        
        if len(df) < 2:
            return jsonify({'error': f'Insufficient market data for {symbol}. Need at least 2 bars.'})
        
        # Get real-time current price
        current_value = get_current_price(tech_symbol)
        if current_value is None:
            # Fallback to last close if real-time price unavailable
            current_value = float(df.iloc[-1]['Close'])
            print(f"⚠️ Using last close as current price: ${current_value:,.2f}")
        else:
            print(f"✅ Got real-time current price: ${current_value:,.2f}")
        
        # Use previous day's close (which is the close of the most recent completed bar)
        previous_close = float(df.iloc[-2]['Close'])
        today_high = float(df.iloc[-1]['High'])
        today_low = float(df.iloc[-1]['Low'])
        
        # Calculate net change and bias
        net_change = current_value - previous_close
        bias = 'LONG' if net_change > 0 else 'SHORT'
        
        # Calculate TP: CV + net change (if bullish) or CV - net change (if bearish)
        if bias == 'LONG':
            tp_value = current_value + abs(net_change)
        else:
            tp_value = current_value - abs(net_change)
        
        print(f"📊 Market Data Summary:")
        print(f"   Current: ${current_value:,.2f}")
        print(f"   Previous Close: ${previous_close:,.2f}")
        print(f"   Net Change: ${net_change:+,.2f}")
        print(f"   Bias: {bias}")
        print(f"   TP Value: ${tp_value:,.2f}")
        
        market_data = {
            'current_value': current_value,
            'previous_close': previous_close,
            'today_high': today_high,
            'today_low': today_low,
            'net_change': net_change,
            'bias': bias,
            'tp_value': tp_value
        }
        
        return jsonify({
            'success': True,
            'market_data': market_data,
            'message': f'Market data fetched for {symbol}'
        })
        
    except Exception as e:
        print(f"❌ Error fetching market data: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Error fetching market data: {str(e)}'})

@app.route('/api/semi_auto_generate_signal', methods=['POST'])
def api_semi_auto_generate_signal():
    """Generate signal from datafeed but allow manual TP/SL setting"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'US30')
        tp1 = data.get('tp1')
        tp2 = data.get('tp2')
        sl1 = data.get('sl1')
        sl2 = data.get('sl2')
        include_risky_play = data.get('include_risky_play', False)
        additional_comments = data.get('additional_comments', False)
        custom_comments = data.get('custom_comments', '')
        risky_play_values = data.get('risky_play_values', None)
        
        # Validate symbol
        if symbol not in ['US30', 'NAS100']:
            return jsonify({'error': 'Only US30 and NAS100 symbols are supported'})
        
        # Convert to technical symbol
        tech_symbol = '^DJI' if symbol == 'US30' else '^NDX'
        
        # Fetch market data
        print(f"🔄 Fetching market data for {symbol}...")
        df = fetch_last_two_1h_bars(tech_symbol)
        
        if len(df) < 2:
            return jsonify({'error': f'Insufficient market data for {symbol}. Need at least 2 bars.'})
        
        # Get real-time current price for accurate signal generation
        current_value = get_current_price(tech_symbol)
        if current_value is None:
            # Fallback to last close if real-time price unavailable
            current_value = float(df.iloc[-1]['Close'])
            print(f"⚠️ Using last close as current price: ${current_value:,.2f}")
        else:
            print(f"✅ Got real-time current price: ${current_value:,.2f}")
        
        # Update the dataframe with real-time current price
        df.iloc[-1, df.columns.get_loc('Close')] = current_value
        
        # Generate base signal with updated real-time data
        signal = calculate_signal(df, symbol, include_news=True)
        
        # Override TP/SL with manual values
        if tp1 is not None:
            signal['tp1'] = float(tp1)
        if tp2 is not None:
            signal['tp2'] = float(tp2)
        if sl1 is not None:
            signal['sl_tight'] = float(sl1)
        if sl2 is not None:
            signal['sl_wide'] = float(sl2)
        
        # Add custom comments if provided
        if additional_comments and custom_comments:
            signal['custom_comments'] = custom_comments
        
        # Add manual risky play values if provided
        if include_risky_play and risky_play_values:
            if risky_play_values.get('risky_entry'):
                signal['manual_risky_entry'] = float(risky_play_values['risky_entry'])
            if risky_play_values.get('risky_tp1'):
                signal['manual_risky_tp1'] = float(risky_play_values['risky_tp1'])
            if risky_play_values.get('risky_tp2'):
                signal['manual_risky_tp2'] = float(risky_play_values['risky_tp2'])
            if risky_play_values.get('risky_sl'):
                signal['manual_risky_sl'] = float(risky_play_values['risky_sl'])
            if risky_play_values.get('risky_strategy'):
                signal['manual_risky_strategy'] = risky_play_values['risky_strategy']
        

        
        # Post to Discord with user-selected risky play option
        discord_success = post_signal(signal, include_risky_play=include_risky_play)
        
        # Store signal in database
        trading_date = get_trading_date()
        conn = sqlite3.connect("ai_learning.db")
        cursor = conn.cursor()
        
        # Ensure manual column exists
        try:
            cursor.execute('ALTER TABLE signal_performance ADD COLUMN manual INTEGER DEFAULT 0')
            conn.commit()
        except sqlite3.OperationalError:
            pass
        
        cursor.execute('''
            INSERT INTO signal_performance 
            (symbol, signal_type, predicted_probability, risk_level, timestamp, manual)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            symbol,
            signal['bias'],
            signal['probability_percentage'] / 100.0,
            signal.get('probability_label', 'Medium').lower(),
            trading_date.isoformat(),
            0  # Mark as auto-generated signal
        ))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'signal': signal,
            'discord_posted': discord_success,
            'message': f'Semi-auto signal for {symbol} generated with manual TP/SL!'
        })
        
    except Exception as e:
        print(f"❌ Error in semi-auto signal generation: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Error generating signal: {str(e)}'})

@app.route('/api/manual_generate_signal', methods=['POST'])
def api_manual_generate_signal():
    """Manually generate signal with all custom parameters"""
    try:
        data = request.get_json()
        
        # Extract manual signal parameters
        symbol = data.get('symbol', 'US30')
        bias = data.get('bias', 'LONG')
        entry_price = float(data.get('entry_price', 0))
        take_profit = float(data.get('take_profit', 0))
        take_profit_2 = data.get('take_profit_2')
        take_profit_3 = data.get('take_profit_3')
        stop_loss = float(data.get('stop_loss', 0))
        confidence = int(data.get('confidence', 50))
        risk_level = data.get('risk_level', 'medium')
        
        # Validate symbol
        if symbol not in ['US30', 'NAS100']:
            return jsonify({'error': 'Only US30 and NAS100 symbols are supported'})
        
        # Validate required fields
        if entry_price <= 0 or take_profit <= 0 or stop_loss <= 0:
            return jsonify({'error': 'Entry price, take profit, and stop loss must be greater than 0'})
        
        # For manual signals, use the provided values instead of fetching market data
        # Use entry price as current value and calculate reasonable defaults
        current_price = entry_price
        previous_close = entry_price * 0.995  # Slight difference for net change calculation
        today_high = max(entry_price, take_profit) * 1.01  # Slightly above the higher of entry or TP
        today_low = min(entry_price, stop_loss) * 0.99   # Slightly below the lower of entry or SL
        
        # Calculate net change based on manual entry
        net_change = entry_price - previous_close
        change_pct = (net_change / previous_close * 100) if previous_close > 0 else 0
        
        # Create manual signal structure with all required fields
        from datetime import datetime
        current_time = datetime.now()
        trading_date = get_trading_date()
        is_weekend_signal = current_time.weekday() >= 5  # Saturday or Sunday
        
        signal = {
            'symbol': symbol,
            'display_name': get_display_name(symbol),
            'bias': bias,
            'bias_text': f"Manual {bias} Signal",
            'current_value': round(entry_price, 2),  # Use manual entry price
            'previous_close': round(previous_close, 2),
            'net_change': round(net_change, 2),
            'change_pct': round(change_pct, 2),
            'today_high': round(today_high, 2),
            'today_low': round(today_low, 2),
            'take_profit': round(take_profit, 2),
            'entry1': round(entry_price, 2),
            'entry2': round(entry_price, 2),
            'tp1': round(take_profit, 2),
            'tp2': round(float(take_profit_2) if take_profit_2 else take_profit, 2),
            'tp3': round(float(take_profit_3), 2) if take_profit_3 else None,
            'sl_tight': round(stop_loss, 2),
            'sl_wide': round(stop_loss * 0.98, 2),  # Extended SL is 2% wider for more room
            'confidence': confidence,
            'risk_quality': risk_level.upper(),
            'timestamp': trading_date.strftime("%d %B %Y"),
            'generated_at': current_time.isoformat(),
            'is_weekend_signal': is_weekend_signal,
            'trading_date': trading_date.strftime('%Y-%m-%d'),
            'probability_percentage': confidence,
            'has_risky_play': False,
            'manual': True  # Mark as manual signal to use simplified format
        }
        
        # Post signal to Discord
        print(f"🚀 Posting manual signal to Discord for {symbol}...")
        discord_success = post_signal(signal)
        
        if not discord_success:
            return jsonify({
                'error': 'Failed to post signal to Discord. Check webhook configuration.',
                'signal': signal
            })
        
        # Store signal in database
        trading_date = get_trading_date()
        conn = sqlite3.connect("ai_learning.db")
        cursor = conn.cursor()
        
        # Ensure manual column exists
        try:
            cursor.execute('ALTER TABLE signal_performance ADD COLUMN manual INTEGER DEFAULT 0')
            conn.commit()
        except sqlite3.OperationalError:
            pass
        
        cursor.execute('''
            INSERT INTO signal_performance 
            (symbol, signal_type, predicted_probability, risk_level, timestamp, manual)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            symbol,
            bias,
            confidence / 100.0,
            risk_level.lower(),
            trading_date.isoformat(),
            1  # Mark as manual signal
        ))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'signal': signal,
            'discord_posted': True,
            'message': f'Manual signal for {symbol} created and posted to Discord successfully!'
        })
        
    except Exception as e:
        print(f"❌ Error in manual signal generation: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Error creating manual signal: {str(e)}'})

@app.route('/api/delete_signal/<int:signal_id>', methods=['DELETE'])
def api_delete_signal(signal_id):
    """API endpoint to delete individual signal"""
    try:
        conn = sqlite3.connect("ai_learning.db")
        cursor = conn.cursor()
        
        # Check if signal exists
        cursor.execute('SELECT id FROM signal_performance WHERE id = ?', (signal_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Signal not found'}), 404
        
        # Delete the signal
        cursor.execute('DELETE FROM signal_performance WHERE id = ?', (signal_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Signal deleted successfully!'})
    except Exception as e:
        print(f"❌ Error deleting signal: {str(e)}")
        return jsonify({'error': f'Error deleting signal: {str(e)}'})

@app.route('/api/update_outcome', methods=['POST'])
def api_update_outcome():
    """API endpoint to update signal outcome"""
    try:
        data = request.get_json()
        signal_id = data.get('signal_id')
        outcome = data.get('outcome')
        outcome_type = data.get('type', 'main')  # 'main' or 'risky'
        
        if not signal_id or outcome is None:
            return jsonify({'error': 'Signal ID and outcome are required'})
        
        conn = sqlite3.connect("ai_learning.db")
        cursor = conn.cursor()
        
        # Check if signal exists
        cursor.execute('SELECT id FROM signal_performance WHERE id = ?', (signal_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Signal not found'}), 404
        
        # Convert outcome to appropriate values
        # 1 = Win, 0 = Loss, 2 = Breakeven
        outcome_value = int(outcome)
        
        # First, ensure the risky_play_outcome column exists
        try:
            cursor.execute('ALTER TABLE signal_performance ADD COLUMN risky_play_outcome INTEGER')
            conn.commit()
        except sqlite3.OperationalError:
            # Column already exists, that's fine
            pass
        
        # Update based on type
        if outcome_type == 'main':
            # Update main signal outcome
            cursor.execute('''
                UPDATE signal_performance 
                SET actual_outcome = ?
                WHERE id = ?
            ''', (outcome_value, signal_id))
        else:
            # Update risky play outcome
            cursor.execute('''
                UPDATE signal_performance 
                SET risky_play_outcome = ?
                WHERE id = ?
            ''', (outcome_value, signal_id))
        
        conn.commit()
        conn.close()
        
        outcome_text = {1: 'Win', 0: 'Loss', 2: 'Breakeven'}
        message = f'Signal outcome updated to {outcome_text.get(outcome_value, "Unknown")}'
        
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        print(f"❌ Error updating outcome: {str(e)}")
        return jsonify({'error': f'Error updating outcome: {str(e)}'})

@app.route('/api/clear_data', methods=['POST'])
def api_clear_data():
    """API endpoint to clear learning data"""
    try:
        ai_manager.clear_learning_data()
        return jsonify({'success': True, 'message': 'All learning data cleared successfully!'})
    except Exception as e:
        return jsonify({'error': f'Error clearing data: {str(e)}'})

@app.route('/api/live_prices')
def api_live_prices():
    """Get live market prices for NASDAQ, Gold, and DOW with data persistence"""
    try:
        import yfinance as yf
        from datetime import datetime
        
        # Define symbols
        symbols = {
            'nasdaq': '^NDX',   # NASDAQ-100
            'gold': 'GC=F',     # Gold Futures
            'dow': '^DJI'       # Dow Jones Industrial Average
        }
        
        live_data = {}
        
        for key, symbol in symbols.items():
            try:
                # Get current data
                ticker = yf.Ticker(symbol)
                current_data = ticker.history(period='2d')
                
                if len(current_data) >= 2:
                    current_price = current_data['Close'].iloc[-1]
                    previous_price = current_data['Close'].iloc[-2]
                    
                    # Get today's high and low
                    today_data = current_data.iloc[-1]
                    today_high = today_data['High']
                    today_low = today_data['Low']
                    
                    # Calculate change
                    change = current_price - previous_price
                    change_percent = (change / previous_price) * 100
                    
                    # Format prices
                    if key == 'gold':
                        price_str = f"${current_price:.2f}"
                        change_str = f"{change:+.2f}"
                        change_percent_str = f"{change_percent:+.2f}%"
                        prev_close_str = f"${previous_price:.2f}"
                        high_str = f"${today_high:.2f}"
                        low_str = f"${today_low:.2f}"
                    else:
                        price_str = f"{current_price:,.2f}"
                        change_str = f"{change:+.2f}"
                        change_percent_str = f"{change_percent:+.2f}%"
                        prev_close_str = f"{previous_price:,.2f}"
                        high_str = f"{today_high:,.2f}"
                        low_str = f"{today_low:,.2f}"
                    
                    live_data[key] = {
                        'price': price_str,
                        'change': change_str,
                        'changePercent': change_percent_str,
                        'rawChange': change,
                        'previousClose': prev_close_str,
                        'high': high_str,
                        'low': low_str
                    }
                    
                    # Save to storage
                    market_data_storage.update_market_data(key, live_data[key])
                else:
                    # Use stored data if available, otherwise show defaults
                    stored_data = market_data_storage.get_market_data(key)
                    if stored_data:
                        live_data[key] = stored_data
                    else:
                        live_data[key] = {
                            'price': '--',
                            'change': '--',
                            'changePercent': '--',
                            'rawChange': 0,
                            'previousClose': '--',
                            'high': '--',
                            'low': '--'
                        }
                    
            except Exception as e:
                print(f"Error fetching {key} data: {str(e)}")
                # Use stored data if available
                stored_data = market_data_storage.get_market_data(key)
                if stored_data:
                    live_data[key] = stored_data
                else:
                    live_data[key] = {
                        'price': '--',
                        'change': '--',
                        'changePercent': '--',
                        'rawChange': 0,
                        'previousClose': '--',
                        'high': '--',
                        'low': '--'
                    }
        
        return jsonify({
            'success': True,
            'nasdaq': live_data['nasdaq'],
            'gold': live_data['gold'],
            'dow': live_data['dow'],
            'timestamp': datetime.now().isoformat(),
            'last_update': market_data_storage.data.get('last_update')
        })
        
    except Exception as e:
        print(f"Error in live prices API: {str(e)}")
        # Return stored data as fallback
        return jsonify({
            'success': False,
            'error': str(e),
            'nasdaq': market_data_storage.get_market_data('nasdaq'),
            'gold': market_data_storage.get_market_data('gold'),
            'dow': market_data_storage.get_market_data('dow'),
            'timestamp': datetime.now().isoformat()
        })

@app.route('/api/market_timer')
def api_market_timer():
    """Get US market status and timer information"""
    try:
        from datetime import datetime, timedelta
        import pytz
        
        # Define timezones
        ny_tz = pytz.timezone('America/New_York')
        windhoek_tz = pytz.timezone('Africa/Windhoek')
        
        # Get current time in both timezones
        now_ny = datetime.now(ny_tz)
        now_windhoek = datetime.now(windhoek_tz)
        
        # US Market hours: 9:30 AM - 4:00 PM ET (Monday-Friday)
        market_open = now_ny.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now_ny.replace(hour=16, minute=0, second=0, microsecond=0)
        
        # Check if it's a weekday
        is_weekday = now_ny.weekday() < 5  # Monday = 0, Friday = 4
        
        if is_weekday:
            if market_open <= now_ny <= market_close:
                # Market is open
                time_remaining = market_close - now_ny
                total_seconds = int(time_remaining.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                
                return jsonify({
                    'status': 'open',
                    'total_seconds': total_seconds,
                    'time_remaining': {
                        'hours': hours,
                        'minutes': minutes,
                        'seconds': seconds
                    },
                    'formatted_time': f"{hours:02d}:{minutes:02d}:{seconds:02d}",
                    'message': f"US Markets Open - {hours:02d}:{minutes:02d}:{seconds:02d} remaining",
                    'next_open': None,
                    'market_close_time': market_close.isoformat()
                })
            elif now_ny < market_open:
                # Market opens today
                time_until_open = market_open - now_ny
                total_seconds = int(time_until_open.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                
                return jsonify({
                    'status': 'closed',
                    'total_seconds': total_seconds,
                    'time_until_open': {
                        'hours': hours,
                        'minutes': minutes,
                        'seconds': seconds
                    },
                    'formatted_time': f"{hours:02d}:{minutes:02d}:{seconds:02d}",
                    'message': f"US Markets Closed - Opens in {hours:02d}:{minutes:02d}:{seconds:02d}",
                    'next_open': market_open.strftime('%Y-%m-%d %H:%M ET'),
                    'market_open_time': market_open.isoformat()
                })
            else:
                # Market closed for today, calculate next open
                next_open = now_ny + timedelta(days=1)
                while next_open.weekday() >= 5:  # Skip weekends
                    next_open += timedelta(days=1)
                next_open = next_open.replace(hour=9, minute=30, second=0, microsecond=0)
                
                time_until_next = next_open - now_ny
                total_seconds = int(time_until_next.total_seconds())
                days = time_until_next.days
                hours = (total_seconds % (24 * 3600)) // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                
                return jsonify({
                    'status': 'closed',
                    'total_seconds': total_seconds,
                    'time_until_open': {
                        'days': days,
                        'hours': hours,
                        'minutes': minutes,
                        'seconds': seconds
                    },
                    'formatted_time': f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}",
                    'message': f"US Markets Closed - Opens {next_open.strftime('%A, %B %d at %H:%M ET')}",
                    'next_open': next_open.strftime('%Y-%m-%d %H:%M ET'),
                    'market_open_time': next_open.isoformat()
                })
        else:
            # Weekend - calculate next Monday
            next_open = now_ny + timedelta(days=(7 - now_ny.weekday()))
            next_open = next_open.replace(hour=9, minute=30, second=0, microsecond=0)
            
            time_until_next = next_open - now_ny
            total_seconds = int(time_until_next.total_seconds())
            days = time_until_next.days
            hours = (total_seconds % (24 * 3600)) // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            return jsonify({
                'status': 'closed',
                'total_seconds': total_seconds,
                'time_until_open': {
                    'days': days,
                    'hours': hours,
                    'minutes': minutes,
                    'seconds': seconds
                },
                'formatted_time': f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}",
                'message': f"US Markets Closed (Weekend) - Opens {next_open.strftime('%A, %B %d at %H:%M ET')}",
                'next_open': next_open.strftime('%Y-%m-%d %H:%M ET'),
                'market_open_time': next_open.isoformat()
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'Error getting market timer: {e}',
            'message': 'Unable to get market status'
        })

@app.route('/api/save_market_close', methods=['POST'])
def api_save_market_close():
    """Save current market data as market close data"""
    try:
        market_data_storage.save_market_close_data()
        return jsonify({
            'success': True,
            'message': 'Market close data saved successfully',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/get_market_close_data')
def api_get_market_close_data():
    """Get saved market close data"""
    try:
        close_data = market_data_storage.get_market_close_data()
        return jsonify({
            'success': True,
            'data': close_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/export_data')
def api_export_data():
    """API endpoint to export learning data"""
    try:
        filename = f"ai_learning_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        ai_manager.export_learning_data(filename)
        return jsonify({'success': True, 'message': f'Data exported to {filename}'})
    except Exception as e:
        return jsonify({'error': f'Error exporting data: {str(e)}'})

if __name__ == '__main__':
    print("🚀 Starting BFI Signals AI Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:5000")
    print("🤖 AI features ready for interaction!")
    print("📈 Monitor your trading performance in real-time!")
    
    # Create templates directory if it doesn't exist
    import os
    if not os.path.exists('templates'):
        os.makedirs('templates')
    if not os.path.exists('static'):
        os.makedirs('static')
    
    # Favicon files are handled by the ensure_favicons() function
    
    # Use debug=False for production-like experience, True for development
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000) 