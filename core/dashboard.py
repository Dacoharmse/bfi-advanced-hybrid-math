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

from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, flash, session
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
import schedule
import threading
import time
import pytz
from manual_journal import journal_manager
from werkzeug.utils import secure_filename
from auth_manager import auth_manager, login_required, admin_required
from email_config import email_service
from agent_manager import agent_manager

def get_todays_signals():
    """Get signals for today only"""
    try:
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        # Get today's date in YYYY-MM-DD format
        today = datetime.now().strftime('%Y-%m-%d')
        
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
                WHERE DATE(timestamp) = ?
                ORDER BY timestamp DESC
            ''', (today,))
        else:
            cursor.execute('''
                SELECT id, symbol, signal_type, predicted_probability, risk_level, 
                       timestamp, actual_outcome, profit_loss, NULL as risky_play_outcome
                FROM signal_performance 
                WHERE DATE(timestamp) = ?
                ORDER BY timestamp DESC
            ''', (today,))
        
        signals_data = cursor.fetchall()
        conn.close()
        
        return format_signal_data(signals_data)
        
    except Exception as e:
        print(f"❌ Error getting today's signals: {str(e)}")
        return []

def get_week_signals():
    """Get signals for the current week"""
    try:
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        # Get start of current week (Monday)
        today = datetime.now()
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        week_start = monday.strftime('%Y-%m-%d')
        
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
                WHERE DATE(timestamp) >= ?
                ORDER BY timestamp DESC
            ''', (week_start,))
        else:
            cursor.execute('''
                SELECT id, symbol, signal_type, predicted_probability, risk_level, 
                       timestamp, actual_outcome, profit_loss, NULL as risky_play_outcome
                FROM signal_performance 
                WHERE DATE(timestamp) >= ?
                ORDER BY timestamp DESC
            ''', (week_start,))
        
        signals_data = cursor.fetchall()
        conn.close()
        
        return format_signal_data(signals_data)
        
    except Exception as e:
        print(f"❌ Error getting week signals: {str(e)}")
        return []

def format_signal_data(signals_data):
    """Format signal data for consistent frontend display"""
    formatted_signals = []
    
    for signal in signals_data:
        try:
            formatted_signal = {
                'id': signal[0],
                'symbol': signal[1] or 'N/A',
                'signal_type': signal[2] or 'N/A',
                'predicted_probability': float(signal[3]) if signal[3] is not None else 0.0,
                'risk_level': signal[4] or 'N/A',
                'timestamp': signal[5],
                'actual_outcome': signal[6] if signal[6] is not None else None,
                'profit_loss': float(signal[7]) if signal[7] is not None else 0.0,
                'risky_play_outcome': signal[8] if signal[8] is not None else None,
                'formatted_timestamp': None,
                'outcome_text': 'Pending',
                'outcome_class': 'text-warning'
            }
            
            # Format timestamp for display
            if formatted_signal['timestamp']:
                try:
                    dt = datetime.fromisoformat(formatted_signal['timestamp'].replace('Z', '+00:00'))
                    formatted_signal['formatted_timestamp'] = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                except:
                    formatted_signal['formatted_timestamp'] = formatted_signal['timestamp']
            
            # Format outcome display
            if formatted_signal['actual_outcome'] is not None:
                if formatted_signal['actual_outcome'] == 1:
                    formatted_signal['outcome_text'] = 'Win'
                    formatted_signal['outcome_class'] = 'text-success'
                else:
                    formatted_signal['outcome_text'] = 'Loss'
                    formatted_signal['outcome_class'] = 'text-danger'
            
            formatted_signals.append(formatted_signal)
            
        except Exception as e:
            print(f"❌ Error formatting signal: {str(e)}")
            continue
    
    return formatted_signals

def calculate_signal_stats():
    """Calculate comprehensive signal performance statistics"""
    try:
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        # Get basic statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_signals,
                COUNT(CASE WHEN actual_outcome = 1 THEN 1 END) as wins,
                COUNT(CASE WHEN actual_outcome = 0 THEN 1 END) as losses,
                COUNT(CASE WHEN actual_outcome IS NULL THEN 1 END) as pending,
                COALESCE(SUM(profit_loss), 0) as total_pnl,
                COALESCE(AVG(profit_loss), 0) as avg_pnl,
                COALESCE(AVG(predicted_probability), 0) as avg_confidence
            FROM signal_performance
        ''')
        
        basic_stats = cursor.fetchone()
        
        # Calculate win rate
        total_completed = basic_stats[1] + basic_stats[2]  # wins + losses
        win_rate = (basic_stats[1] / total_completed * 100) if total_completed > 0 else 0
        
        # Get today's statistics
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT 
                COUNT(*) as today_signals,
                COUNT(CASE WHEN actual_outcome = 1 THEN 1 END) as today_wins,
                COUNT(CASE WHEN actual_outcome = 0 THEN 1 END) as today_losses,
                COALESCE(SUM(profit_loss), 0) as today_pnl
            FROM signal_performance
            WHERE DATE(timestamp) = ?
        ''', (today,))
        
        today_stats = cursor.fetchone()
        
        # Get this week's statistics
        today_dt = datetime.now()
        days_since_monday = today_dt.weekday()
        monday = today_dt - timedelta(days=days_since_monday)
        week_start = monday.strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT 
                COUNT(*) as week_signals,
                COUNT(CASE WHEN actual_outcome = 1 THEN 1 END) as week_wins,
                COUNT(CASE WHEN actual_outcome = 0 THEN 1 END) as week_losses,
                COALESCE(SUM(profit_loss), 0) as week_pnl
            FROM signal_performance
            WHERE DATE(timestamp) >= ?
        ''', (week_start,))
        
        week_stats = cursor.fetchone()
        
        # Get symbol performance
        cursor.execute('''
            SELECT 
                symbol,
                COUNT(*) as count,
                COUNT(CASE WHEN actual_outcome = 1 THEN 1 END) as wins,
                COUNT(CASE WHEN actual_outcome = 0 THEN 1 END) as losses,
                COALESCE(SUM(profit_loss), 0) as pnl
            FROM signal_performance
            WHERE symbol IS NOT NULL
            GROUP BY symbol
            ORDER BY count DESC
            LIMIT 10
        ''')
        
        symbol_stats = cursor.fetchall()
        
        conn.close()
        
        # Format symbol statistics
        formatted_symbols = []
        for symbol_stat in symbol_stats:
            symbol_completed = symbol_stat[2] + symbol_stat[3]  # wins + losses
            symbol_win_rate = (symbol_stat[2] / symbol_completed * 100) if symbol_completed > 0 else 0
            
            formatted_symbols.append({
                'symbol': symbol_stat[0],
                'total': symbol_stat[1],
                'wins': symbol_stat[2],
                'losses': symbol_stat[3],
                'win_rate': round(symbol_win_rate, 1),
                'pnl': round(symbol_stat[4], 2)
            })
        
        return {
            'total_signals': basic_stats[0],
            'wins': basic_stats[1],
            'losses': basic_stats[2],
            'pending': basic_stats[3],
            'win_rate': round(win_rate, 1),
            'total_pnl': round(basic_stats[4], 2),
            'avg_pnl': round(basic_stats[5], 2),
            'avg_confidence': round(basic_stats[6], 1),
            'today': {
                'signals': today_stats[0],
                'wins': today_stats[1],
                'losses': today_stats[2],
                'pnl': round(today_stats[3], 2)
            },
            'week': {
                'signals': week_stats[0],
                'wins': week_stats[1],
                'losses': week_stats[2],
                'pnl': round(week_stats[3], 2)
            },
            'by_symbol': formatted_symbols
        }
        
    except Exception as e:
        print(f"❌ Error calculating signal stats: {str(e)}")
        return {
            'total_signals': 0,
            'wins': 0,
            'losses': 0,
            'pending': 0,
            'win_rate': 0,
            'total_pnl': 0.0,
            'avg_pnl': 0.0,
            'avg_confidence': 0.0,
            'today': {'signals': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0},
            'week': {'signals': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0},
            'by_symbol': []
        }

def create_signal_notification(signal_data, signal_id=None):
    """Create notifications for all regular users when a new signal is generated"""
    try:
        # Get all regular users (non-admin)
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE role != "admin" AND is_active = 1')
        regular_users = cursor.fetchall()
        
        if not regular_users:
            print("📡 No regular users to notify")
            return
        
        # Create notification for each regular user
        for (user_id,) in regular_users:
            title = f"🎯 New {signal_data.get('instrument', 'Trading')} Signal"
            message = f"{signal_data.get('direction', 'N/A')} signal generated at {signal_data.get('entry_price', 'N/A')} with {signal_data.get('confidence', 'N/A')}% confidence"
            
            auth_manager.create_notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type='signal',
                signal_id=signal_id
            )
        
        print(f"📡 Created signal notifications for {len(regular_users)} users")
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating signal notifications: {str(e)}")

# Load environment variables
load_dotenv('../.env')

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = 'bfi_signals_dashboard_2025'

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'uploads/charts'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

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

def sync_json_signals_to_db():
    """Load signals from JSON files and sync them to SQLite database"""
    try:
        conn = sqlite3.connect("ai_learning.db")
        cursor = conn.cursor()
        
        # Add missing columns to existing table if needed
        columns_to_add = [
            ('entry_price', 'REAL'),
            ('take_profit', 'REAL'),
            ('stop_loss', 'REAL'),
            ('bias', 'TEXT'),
            ('net_change', 'REAL')
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                cursor.execute(f'ALTER TABLE signal_performance ADD COLUMN {column_name} {column_type}')
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    # Column already exists
                    pass
                else:
                    raise
        
        # Get existing signal timestamps to avoid duplicates
        cursor.execute('SELECT timestamp FROM signal_performance')
        existing_timestamps = set(row[0] for row in cursor.fetchall())
        
        # Load signals from daily JSON files
        data_dir = '../data/daily'
        if not os.path.exists(data_dir):
            data_dir = 'data/daily'
            
        if os.path.exists(data_dir):
            for filename in os.listdir(data_dir):
                if filename.endswith('.json') and 'signals_' in filename:
                    filepath = os.path.join(data_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                            
                        if 'signals' in data:
                            for signal_entry in data['signals']:
                                signal = signal_entry.get('signal', {})
                                created_at = signal_entry.get('created_at', signal.get('generated_at', ''))
                                
                                # Skip if already exists
                                if created_at in existing_timestamps:
                                    continue
                                
                                # Extract signal data
                                symbol = signal.get('symbol', 'UNKNOWN')
                                probability = signal.get('probability_percentage', 75) / 100.0
                                entry_price = signal.get('entry1', signal.get('current_value', 0))
                                take_profit = signal.get('take_profit', 0)
                                stop_loss = signal.get('sl_tight', 0)
                                bias = signal.get('bias', 'UNKNOWN')
                                net_change = signal.get('net_change', 0)
                                
                                # Insert into database
                                cursor.execute('''
                                    INSERT INTO signal_performance 
                                    (symbol, signal_type, predicted_probability, risk_level, timestamp, 
                                     entry_price, take_profit, stop_loss, bias, net_change)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (
                                    symbol, 'Hybrid Math', probability, 'Medium', created_at,
                                    entry_price, take_profit, stop_loss, bias, net_change
                                ))
                                
                    except Exception as e:
                        print(f"Error processing {filename}: {e}")
        
        conn.commit()
        conn.close()
        print("✅ Signal sync completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error syncing signals: {e}")
        return False

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
        """Update market data for a symbol (current data only)"""
        current_data = {
            'price': data.get('price', '--'),
            'change': data.get('change', '--'),
            'changePercent': data.get('changePercent', '--'),
            'rawChange': data.get('rawChange', 0),
            'previousClose': data.get('previousClose', '--'),
            'high': data.get('high', '--'),
            'low': data.get('low', '--'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Update current data only
        self.data[symbol] = current_data
        self.data['last_update'] = datetime.now().isoformat()
        self.save_data()
    
    def save_market_close_data(self):
        """Save current data as market close data with date tracking"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Initialize market close data structure
        if 'market_close_history' not in self.data:
            self.data['market_close_history'] = {}
        
        # Save today's close data for each symbol
        symbols = ['nasdaq', 'gold', 'dow']
        for symbol in symbols:
            if symbol in self.data and self.data[symbol]:
                if symbol not in self.data['market_close_history']:
                    self.data['market_close_history'][symbol] = {}
                
                # Save with date as key
                self.data['market_close_history'][symbol][today] = self.data[symbol].copy()
        
        self.save_data()
    
    def get_market_data(self, symbol):
        """Get stored market data for a symbol"""
        return self.data.get(symbol, {})
    
    def get_market_close_data(self):
        """Get market close data"""
        return self.data.get('market_close_history', {})
    
    def get_latest_market_close_data(self):
        """Get the most recent market close data for each symbol (previous day's data)"""
        close_data = self.get_market_close_data()
        latest_data = {}
        
        for symbol in ['nasdaq', 'dow', 'gold']:
            if symbol in close_data and close_data[symbol]:
                # Get the most recent date's data for this symbol
                sorted_dates = sorted(close_data[symbol].keys(), reverse=True)
                if sorted_dates:
                    latest_date = sorted_dates[0]
                    latest_data[symbol] = close_data[symbol][latest_date]
                    latest_data[symbol]['date'] = latest_date
                else:
                    # Fallback to current data if no close data exists
                    latest_data[symbol] = self.get_market_data(symbol)
            else:
                # Fallback to current data if no close data exists
                latest_data[symbol] = self.get_market_data(symbol)
        
        return latest_data
    
    def set_auto_generation_enabled(self, enabled):
        """Enable or disable auto signal generation"""
        if 'settings' not in self.data:
            self.data['settings'] = {}
        self.data['settings']['auto_generation_enabled'] = enabled
        self.save_data()
    
    def is_auto_generation_enabled(self):
        """Check if auto signal generation is enabled"""
        return self.data.get('settings', {}).get('auto_generation_enabled', False)

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

# Authentication Routes
@app.route('/login')
def login():
    """Login page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register')
def register():
    """Registration page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    """Handle login requests"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password are required'})
        
        # Authenticate user
        auth_result = auth_manager.authenticate_user(username, password)
        
        if auth_result['success']:
            user = auth_result['user']
            
            # Create session
            session_token = auth_manager.create_session(
                user['id'],
                request.remote_addr,
                request.headers.get('User-Agent')
            )
            
            if session_token:
                # Set session data
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['user_role'] = user['role']
                session['session_token'] = session_token
                
                # Determine redirect URL based on role
                redirect_url = '/generate_signals' if user['role'] == 'admin' else '/dashboard'
                
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'redirect': redirect_url,
                    'user': {
                        'username': user['username'],
                        'role': user['role']
                    }
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to create session'})
        else:
            return jsonify({'success': False, 'error': auth_result['error']})
            
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'success': False, 'error': 'Login failed'})

@app.route('/api/register', methods=['POST'])
def api_register():
    """Handle registration requests"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not username or not email or not password:
            return jsonify({'success': False, 'error': 'All fields are required'})
        
        # Register user
        register_result = auth_manager.register_user(username, email, password)
        
        if register_result['success']:
            return jsonify({
                'success': True,
                'message': 'Account created successfully! Please log in.'
            })
        else:
            return jsonify({'success': False, 'error': register_result['error']})
            
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'success': False, 'error': 'Registration failed'})

@app.route('/logout')
def logout():
    """Handle user logout"""
    session_token = session.get('session_token')
    if session_token:
        auth_manager.logout_user(session_token)
    
    session.clear()
    return redirect(url_for('login'))

@app.route('/forgot-password')
def forgot_password():
    """Show forgot password form"""
    return render_template('forgot_password.html')

@app.route('/reset-password')
def reset_password():
    """Show password reset form"""
    token = request.args.get('token')
    if not token:
        return redirect(url_for('login'))
    
    # Validate token
    token_data = email_service.validate_password_reset_token(token)
    
    if not token_data['valid']:
        return render_template('reset_password.html', error='Invalid or expired reset token')
    
    return render_template('reset_password.html', token=token, username=token_data['username'])

@app.route('/api/forgot-password', methods=['POST'])
def api_forgot_password():
    """Handle forgot password requests"""
    try:
        data = request.get_json()
        email_or_username = data.get('email', '').strip()
        
        if not email_or_username:
            return jsonify({'success': False, 'error': 'Email or username is required'})
        
        result = auth_manager.initiate_password_reset(email_or_username)
        return jsonify(result)
        
    except Exception as e:
        print(f"Forgot password error: {e}")
        return jsonify({'success': False, 'error': 'An error occurred while processing your request'})

@app.route('/api/reset-password', methods=['POST'])
def api_reset_password():
    """Handle password reset with token"""
    try:
        data = request.get_json()
        token = data.get('token', '').strip()
        new_password = data.get('password', '')
        
        if not token or not new_password:
            return jsonify({'success': False, 'error': 'Token and password are required'})
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters long'})
        
        result = auth_manager.reset_password_with_token(token, new_password)
        return jsonify(result)
        
    except Exception as e:
        print(f"Password reset error: {e}")
        return jsonify({'success': False, 'error': 'An error occurred while resetting your password'})

@app.route('/api/notifications')
@login_required
def api_get_notifications():
    """Get user notifications"""
    try:
        user_id = session.get('user_id')
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        notifications = auth_manager.get_user_notifications(user_id, unread_only)
        
        return jsonify({
            'success': True,
            'notifications': notifications
        })
        
    except Exception as e:
        print(f"Error getting notifications: {e}")
        return jsonify({'success': False, 'error': 'Failed to get notifications'})

@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def api_mark_notification_read(notification_id):
    """Mark notification as read"""
    try:
        user_id = session.get('user_id')
        success = auth_manager.mark_notification_read(notification_id, user_id)
        
        return jsonify({'success': success})
        
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        return jsonify({'success': False, 'error': 'Failed to mark notification as read'})

@app.route('/')
@login_required
def dashboard():
    """Main dashboard page"""
    return dashboard_view()

@app.route('/dashboard')
@login_required
def dashboard_redirect():
    """Redirect /dashboard to root for compatibility"""
    return dashboard_view()

def dashboard_view():
    """Main dashboard page"""
    try:
        # Sync JSON signals to database first
        sync_json_signals_to_db()
        
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
        
        # Get latest market close data (previous day's data)
        market_close_data = market_data_storage.get_latest_market_close_data()
        
        return render_template('dashboard_modern.html', 
                             stats=stats,
                             recent_signals=recent_signals,
                             today_signals=today_signals,
                             model_stats=model_stats,
                             win_rate_stats=win_rate_stats,
                             market_close_data=market_close_data)
    except Exception as e:
        # Get market close data even in error case
        try:
            market_close_data = market_data_storage.get_latest_market_close_data()
        except:
            market_close_data = {'nasdaq': {}, 'dow': {}, 'gold': {}}
            
        return render_template('dashboard_modern.html', 
                             error=f"Error loading dashboard: {e}",
                             stats={'total_signals': 0, 'success_rate': 0},
                             market_close_data=market_close_data,
                             recent_signals=[],
                             today_signals=0,
                             model_stats=[],
                             win_rate_stats=(0, 0, 0, 0, 0.0))


@app.route('/performance')
@login_required
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
@login_required
def signals():
    """Enhanced signals history page with modern UI"""
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
        
        # Format signals data using helper function
        formatted_signals = format_signal_data(signals_data)
        
        # Calculate pagination info
        total_pages = (total_signals + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        # Get signal statistics for dashboard display
        signal_stats = calculate_signal_stats()
        
        return render_template('signals_modern.html',
                             signals=formatted_signals,
                             page=page,
                             total_pages=total_pages,
                             has_prev=has_prev,
                             has_next=has_next,
                             stats=signal_stats,
                             total_signals=total_signals)
        
    except Exception as e:
        print(f"❌ Error loading signals page: {str(e)}")
        return render_template('signals_modern.html', 
                             error=f"Error loading signals: {e}",
                             signals=[],
                             page=1,
                             total_pages=1,
                             has_prev=False,
                             has_next=False,
                             stats=calculate_signal_stats(),
                             total_signals=0)

@app.route('/generate_signals')
@admin_required
def generate_signals():
    """Generate signals page"""
    # Get current real-time market data for signal generation display
    current_market_data = {
        'nasdaq': market_data_storage.get_market_data('nasdaq'),
        'dow': market_data_storage.get_market_data('dow'),
        'gold': market_data_storage.get_market_data('gold')
    }
    
    print("📊 Using current real-time data for generate_signals page")
    print(f"   NASDAQ: {current_market_data['nasdaq'].get('price', 'N/A')} (Change: {current_market_data['nasdaq'].get('change', 'N/A')})")
    
    return render_template('generate_signals_modern.html', 
                         market_close_data=current_market_data)

@app.route('/journal')
@login_required
def journal():
    """Manual Trade Journal Page - Track Manual Trading Performance"""
    try:
        print("📊 Loading manual journal data...")
        
        # Get manual journal statistics filtered by user
        user_id = session.get('user_id')
        stats, stats_message = journal_manager.get_journal_statistics(user_id)
        
        # Get recent manual journal entries filtered by user
        entries, entries_message = journal_manager.get_journal_entries(limit=20, user_id=user_id)
        
        # Calculate display statistics
        if stats and stats['overall']:
            overall = stats['overall']
            total_trades = int(overall[0] or 0)
            wins = int(overall[1] or 0)
            losses = int(overall[2] or 0)
            breakevens = int(overall[3] or 0)
            pending = int(overall[4] or 0)
            total_pnl = float(overall[5] or 0.0)
            avg_pnl = float(overall[6] or 0.0)
            best_trade = float(overall[7] or 0.0)
            worst_trade = float(overall[8] or 0.0)
            
            # Calculate win rate
            completed_trades = wins + losses + breakevens
            win_rate = float(wins / completed_trades * 100) if completed_trades > 0 else 0.0
            
        else:
            # Default values when no data
            total_trades = wins = losses = breakevens = pending = 0
            total_pnl = avg_pnl = best_trade = worst_trade = win_rate = 0.0
        
        # Format data for template compatibility
        overall_stats = (total_trades, wins, losses, breakevens, pending, 0, 0, 0)
        symbol_performance = stats['by_symbol'] if stats else []
        signal_type_performance = stats['by_type'] if stats else []
        
        # Format entries for display
        recent_signals = []
        for entry in entries:
            recent_signals.append((
                entry['symbol'],
                entry['trade_type'],
                entry['entry_price'],
                entry['exit_price'] or 0,
                0,  # stop_loss placeholder
                100,  # predicted_probability placeholder
                'MEDIUM',  # risk_level placeholder
                1 if entry['outcome'] == 'WIN' else 0 if entry['outcome'] == 'LOSS' else 2 if entry['outcome'] == 'BREAKEVEN' else None,
                entry['profit_loss'],
                entry['trade_date']
            ))
        
        print(f"✅ Loaded {len(entries)} manual journal entries")
        print(f"✅ Total trades: {total_trades}, Win rate: {win_rate:.2f}%")
        
        # Create stats object for template
        stats_obj = {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_trade_pnl': avg_pnl,
            'total_pnl': total_pnl,
            'best_trade': best_trade,
            'worst_trade': worst_trade
        }

        return render_template('journal_modern.html',
                             # Manual journal specific data
                             manual_mode=True,
                             entries=entries,
                             stats=stats_obj,
                             # Compatibility with existing template
                             overall_stats=overall_stats,
                             overall_win_rate=round(win_rate, 2),
                             total_signals=total_trades,
                             win_rate=win_rate,
                             avg_rr=2.0,  # Default risk/reward ratio
                             total_pnl=total_pnl,
                             wins=wins,
                             losses=losses,
                             breakevens=breakevens,
                             pending=pending,
                             symbol_performance=symbol_performance,
                             signal_type_performance=signal_type_performance,
                             probability_performance=[],
                             signals=recent_signals,
                             recent_signals=recent_signals,
                             monthly_performance=[],
                             debug_info={'manual_journal': True})
        
    except Exception as e:
        print(f"❌ Error in journal route: {e}")
        import traceback
        traceback.print_exc()
        return render_template('journal_modern.html', 
                             error=f"Error loading journal data: {e}",
                             overall_stats=(0, 0, 0, 0, 0, 0, 0, 0),
                             overall_win_rate=0.0,
                             # Individual stats for display (ensure all numeric types)
                             total_signals=0,
                             win_rate=0.0,
                             avg_rr=0.0,
                             total_pnl=0.0,
                             wins=0,
                             losses=0,
                             breakevens=0,
                             pending=0,
                             # Other data
                             symbol_performance=[],
                             signal_type_performance=[],
                             probability_performance=[],
                             signals=[],
                             recent_signals=[],
                             monthly_performance=[],
                             debug_info={'error_occurred': True})

# ====================================
# MANUAL TRADE JOURNAL ROUTES
# ====================================

@app.route('/journal/new')
def journal_new():
    """Manual trade journal entry form"""
    return render_template('journal_new.html')

@app.route('/journal/api/create', methods=['POST'])
def api_create_journal_entry():
    """Create a new manual journal entry"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            # Get JSON data (new format from frontend)
            json_data = request.get_json()
            
            entry_data = {
                'symbol': str(json_data.get('symbol', '')).strip().upper(),
                'trade_type': str(json_data.get('trade_type', '')).strip().upper(),
                'entry_price': str(json_data.get('entry_price', 0)),
                'exit_price': str(json_data.get('exit_price', '')) if json_data.get('exit_price') else None,
                'quantity': str(json_data.get('quantity', 1)),
                'outcome': str(json_data.get('outcome', 'PENDING')).strip().upper(),
                'profit_loss': str(json_data.get('profit_loss', 0)),
                'trade_date': str(json_data.get('trade_date', '')),
                'entry_time': str(json_data.get('entry_time', '')),
                'exit_time': str(json_data.get('exit_time', '')),
                'notes': str(json_data.get('notes', '')).strip(),
                'chart_link': str(json_data.get('chart_link', '')).strip(),
                'entry_prices': json_data.get('entry_prices', []),
                'position_sizes': json_data.get('position_sizes', [])
            }
        else:
            # Get form data (legacy format)
            entry_data = {
                'symbol': request.form.get('symbol', '').strip().upper(),
                'trade_type': request.form.get('trade_type', '').strip().upper(),
                'entry_price': request.form.get('entry_price', '0'),
                'exit_price': request.form.get('exit_price', '') or None,
                'quantity': request.form.get('quantity', '1'),
                'outcome': request.form.get('outcome', 'PENDING').strip().upper(),
                'profit_loss': request.form.get('profit_loss', '0'),
                'trade_date': request.form.get('trade_date', ''),
                'entry_time': request.form.get('entry_time', ''),
                'exit_time': request.form.get('exit_time', ''),
                'notes': request.form.get('notes', '').strip(),
                'chart_link': '',
                'entry_prices': [],
                'position_sizes': []
            }
        
        # Validate required fields
        if (not entry_data['symbol'] or 
            not entry_data['trade_type'] or 
            not entry_data['entry_price'] or 
            entry_data['entry_price'] == '0' or 
            float(entry_data['entry_price']) <= 0):
            return jsonify({
                'success': False,
                'error': 'Symbol, trade type, and entry price are required'
            }), 400
        
        # Handle chart image upload (for form data only)
        chart_image_path = None
        if not request.is_json and 'chart_image' in request.files:
            file = request.files['chart_image']
            if file and file.filename != '':
                image_path, message = journal_manager.save_chart_image(file)
                if image_path:
                    chart_image_path = image_path
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Image upload failed: {message}'
                    }), 400
        
        entry_data['chart_image_path'] = chart_image_path
        entry_data['user_id'] = session.get('user_id')
        
        # Create journal entry
        entry_id, message = journal_manager.create_journal_entry(entry_data)
        
        if entry_id:
            return jsonify({
                'success': True,
                'message': message,
                'entry_id': entry_id
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/journal/api/entries')
def api_get_journal_entries():
    """Get manual journal entries with optional filtering"""
    try:
        # Get query parameters
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        symbol = request.args.get('symbol', '').strip().upper() or None
        outcome = request.args.get('outcome', '').strip().upper() or None
        
        # Get entries for current user only
        user_id = session.get('user_id')
        entries, message = journal_manager.get_journal_entries(
            limit=limit, offset=offset, symbol=symbol, outcome=outcome, user_id=user_id
        )
        
        return jsonify({
            'success': True,
            'entries': entries,
            'message': message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/journal/api/entry/<int:entry_id>')
def api_get_journal_entry(entry_id):
    """Get a single journal entry"""
    try:
        user_id = session.get('user_id')
        entry, message = journal_manager.get_journal_entry(entry_id, user_id)
        
        if entry:
            return jsonify({
                'success': True,
                'data': entry,  # Frontend expects 'data' not 'entry'
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/journal/api/entry/<int:entry_id>', methods=['PUT'])
def api_update_journal_entry(entry_id):
    """Update a journal entry"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            # Get JSON data (new format from frontend)
            json_data = request.get_json()
            entry_data = {
                'symbol': json_data.get('symbol', '').strip().upper(),
                'trade_type': json_data.get('trade_type', '').strip().upper(),
                'entry_price': str(json_data.get('entry_price', 0)),
                'exit_price': str(json_data.get('exit_price', '')) if json_data.get('exit_price') else None,
                'quantity': str(json_data.get('quantity', 1)),
                'outcome': json_data.get('outcome', 'PENDING').strip().upper(),
                'profit_loss': str(json_data.get('profit_loss', 0)),
                'trade_date': json_data.get('trade_date', ''),
                'entry_time': json_data.get('entry_time', ''),
                'exit_time': json_data.get('exit_time', ''),
                'notes': json_data.get('notes', '').strip(),
                'chart_link': json_data.get('chart_link', '').strip(),
                'entry_prices': json_data.get('entry_prices', []),
                'position_sizes': json_data.get('position_sizes', [])
            }
        else:
            # Get form data (legacy format)
            entry_data = {
                'symbol': request.form.get('symbol', '').strip().upper(),
                'trade_type': request.form.get('trade_type', '').strip().upper(),
                'entry_price': request.form.get('entry_price', '0'),
                'exit_price': request.form.get('exit_price', '') or None,
                'quantity': request.form.get('quantity', '1'),
                'outcome': request.form.get('outcome', 'PENDING').strip().upper(),
                'profit_loss': request.form.get('profit_loss', '0'),
                'trade_date': request.form.get('trade_date', ''),
                'entry_time': request.form.get('entry_time', ''),
                'exit_time': request.form.get('exit_time', ''),
                'notes': request.form.get('notes', '').strip(),
                'chart_link': '',
                'entry_prices': [],
                'position_sizes': []
            }
        
        # Get current entry to preserve existing image if no new one uploaded
        current_entry, _ = journal_manager.get_journal_entry(entry_id)
        if current_entry:
            import json
            entry_data['chart_image_path'] = current_entry.get('chart_image_path')
            # Preserve existing fields if not provided
            if not entry_data.get('chart_link'):
                entry_data['chart_link'] = current_entry.get('chart_link', '')
            if not entry_data.get('entry_prices'):
                entry_data['entry_prices'] = json.loads(current_entry.get('entry_prices', '[]') or '[]')
            if not entry_data.get('position_sizes'):
                entry_data['position_sizes'] = json.loads(current_entry.get('position_sizes', '[]') or '[]')
        
        # Handle new chart image upload (for form data only)
        if not request.is_json and 'chart_image' in request.files:
            file = request.files['chart_image']
            if file and file.filename != '':
                # Delete old image if exists
                if current_entry and current_entry.get('chart_image_path'):
                    old_path = current_entry['chart_image_path']
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except OSError:
                            pass  # File might be in use
                
                # Upload new image
                image_path, message = journal_manager.save_chart_image(file)
                if image_path:
                    entry_data['chart_image_path'] = image_path
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Image upload failed: {message}'
                    }), 400
        
        # Update entry with user_id for security
        user_id = session.get('user_id')
        success, message = journal_manager.update_journal_entry(entry_id, entry_data, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/journal/api/entry/<int:entry_id>', methods=['DELETE'])
def api_delete_journal_entry(entry_id):
    """Delete a journal entry"""
    try:
        user_id = session.get('user_id')
        success, message = journal_manager.delete_journal_entry(entry_id, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 404 if 'not found' in message.lower() else 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/journal/api/statistics')
def api_get_journal_statistics():
    """Get comprehensive journal statistics"""
    try:
        user_id = session.get('user_id')
        stats, message = journal_manager.get_journal_statistics(user_id)
        
        if stats:
            return jsonify({
                'success': True,
                'statistics': stats,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/uploads/charts/<filename>')
def serve_chart_image(filename):
    """Serve uploaded chart images"""
    try:
        # Security: ensure filename is safe
        safe_filename = secure_filename(filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        
        # Check if file exists and is in the upload folder
        if os.path.exists(file_path) and os.path.commonpath([file_path, app.config['UPLOAD_FOLDER']]) == app.config['UPLOAD_FOLDER']:
            return send_file(file_path)
        else:
            return jsonify({'error': 'File not found'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

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

@app.route('/test/journal-js')
def test_journal_js():
    """Serve JavaScript test page for journal functionality"""
    try:
        with open('journal_js_test.html', 'r') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/html'}
    except FileNotFoundError:
        return "Test file not found", 404

@app.route('/api/status')
def api_status():
    """Simple API status endpoint for connectivity testing"""
    try:
        return jsonify({
            'success': True,
            'status': 'online',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

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

@app.route('/api/dashboard_data')
def api_dashboard_data():
    """Get dashboard data including market status and basic info"""
    try:
        # Get market close data
        market_close_data = market_data_storage.get_latest_market_close_data()
        
        # Get market status
        from datetime import datetime
        now = datetime.now()
        
        return jsonify({
            'success': True,
            'data': {
                'market_data': market_close_data,
                'timestamp': now.isoformat(),
                'status': 'active'
            }
        })
        
    except Exception as e:
        print(f"❌ Dashboard data error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Dashboard data error: {str(e)}'
        })

@app.route('/api/live_market_data')
def api_live_market_data():
    """Get live market data - alias for market_close_data"""
    try:
        from datetime import datetime
        market_close_data = market_data_storage.get_latest_market_close_data()
        
        return jsonify({
            'success': True,
            'data': market_close_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Live market data error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Live market data error: {str(e)}'
        })

@app.route('/api/market_data')
def api_market_data():
    """Get market data - alias for market_close_data"""
    try:
        from datetime import datetime
        market_close_data = market_data_storage.get_latest_market_close_data()
        
        return jsonify({
            'success': True,
            'data': market_close_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Market data error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Market data error: {str(e)}'
        })

@app.route('/api/send_discord_signal', methods=['POST'])
def api_send_discord_signal():
    """Send generated signal to Discord"""
    try:
        data = request.get_json()
        if not data or 'signal' not in data:
            return jsonify({
                'success': False,
                'error': 'Invalid request - missing signal data'
            })
        
        signal = data['signal']
        
        # Validate required signal fields
        required_fields = ['instrument', 'direction', 'entry_price', 'take_profit', 'stop_loss', 'confidence']
        for field in required_fields:
            if field not in signal:
                return jsonify({
                    'success': False,
                    'error': f'Invalid signal data - missing {field}'
                })
        
        # Use existing post_signal function
        discord_success = post_signal(signal)
        
        if discord_success:
            # Create notifications for regular users
            create_signal_notification(signal)
            
            return jsonify({
                'success': True,
                'message': 'Signal posted to Discord successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to post signal to Discord - check webhook configuration'
            })
            
    except Exception as e:
        print(f"❌ Discord signal posting error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
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
        
        return render_template('track_signals_modern.html', 
                             daily_signals=daily_signals,
                             manual_signals=manual_signals)
    except Exception as e:
        print(f"❌ Error loading track signals page: {str(e)}")
        return render_template('track_signals_modern.html', 
                             daily_signals=[],
                             manual_signals=[])

@app.route('/api/auto_generate_signal', methods=['POST'])
@admin_required
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
        
        # Create notifications for regular users
        create_signal_notification(signal)
        
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
@admin_required
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
        
        # Create notifications for regular users if posted to Discord
        if discord_success:
            create_signal_notification(signal)
        
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
@admin_required
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
        
        # Create notifications for regular users
        create_signal_notification(signal)
        
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
@admin_required
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
@admin_required
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
    """Get live market prices using enhanced data feed with multiple sources"""
    try:
        from datetime import datetime
        import time
        from data_feed import enhanced_data_feed
        
        live_data = {}
        
        # Get data for each symbol using enhanced data feed with spacing
        symbols = ['nasdaq', 'gold', 'dow']
        for i, symbol_key in enumerate(symbols):
            try:
                # Add spacing between requests to avoid rate limits
                if i > 0:
                    time.sleep(2)  # 2 second delay between symbol requests
                
                # Special handling for Gold - use web scraper for maximum accuracy
                if symbol_key == 'gold':
                    gold_data_found = False
                    try:
                        from yahoo_finance_gold_scraper import get_gold_data
                        print(f"🔄 Attempting to scrape Gold data...")
                        gold_data = get_gold_data()
                        if gold_data:
                            print(f"✅ Got Gold data from web scraper: ${gold_data['price']}")
                            live_data[symbol_key] = gold_data
                            # Save to storage
                            market_data_storage.update_market_data(symbol_key, gold_data)
                            gold_data_found = True
                        else:
                            print(f"❌ Web scraper returned None for Gold")
                    except Exception as scraper_error:
                        print(f"❌ Gold scraper error: {scraper_error}")
                        import traceback
                        traceback.print_exc()
                    
                    # Fallback to enhanced data feed if scraper failed
                    if not gold_data_found:
                        print(f"🔄 Using enhanced data feed fallback for Gold...")
                        try:
                            raw_data = enhanced_data_feed.get_market_data(symbol_key)
                            if raw_data:
                                formatted_data = enhanced_data_feed.format_market_data(raw_data, symbol_key)
                                live_data[symbol_key] = formatted_data
                                market_data_storage.update_market_data(symbol_key, formatted_data)
                                print(f"✅ Got Gold data from enhanced data feed fallback")
                            else:
                                print(f"❌ Enhanced data feed also failed for Gold")
                        except Exception as fallback_error:
                            print(f"❌ Enhanced data feed fallback error: {fallback_error}")
                else:
                    # Use enhanced data feed for other symbols (NASDAQ, DOW)
                    raw_data = enhanced_data_feed.get_market_data(symbol_key)
                    
                    if raw_data:
                        # Format the data for display
                        formatted_data = enhanced_data_feed.format_market_data(raw_data, symbol_key)
                        
                        # Save to storage
                        market_data_storage.update_market_data(symbol_key, formatted_data)
                        
                        live_data[symbol_key] = formatted_data
                    else:
                        # Use stored data if available
                        stored_data = market_data_storage.get_market_data(symbol_key)
                        if stored_data:
                            live_data[symbol_key] = stored_data
                            print(f"📦 Using stored data for {symbol_key}")
                        else:
                            live_data[symbol_key] = {
                                'price': '--',
                                'change': '--',
                                'changePercent': '--',
                                'rawChange': 0,
                                'previousClose': '--',
                                'high': '--',
                                'low': '--'
                            }
                            print(f"❌ No data available for {symbol_key}")
                        
            except Exception as e:
                print(f"❌ Error fetching {symbol_key} data: {str(e)}")
                # Use stored data if available
                stored_data = market_data_storage.get_market_data(symbol_key)
                if stored_data:
                    live_data[symbol_key] = stored_data
                    print(f"📦 Using stored data for {symbol_key}")
                else:
                    live_data[symbol_key] = {
                        'price': '--',
                        'change': '--',
                        'changePercent': '--',
                        'rawChange': 0,
                        'previousClose': '--',
                        'high': '--',
                        'low': '--'
                    }
                    print(f"❌ No data available for {symbol_key}")
        
        # Get connection status and last successful fetch times
        connection_status = enhanced_data_feed.get_connection_status()
        last_successful_fetch = enhanced_data_feed.get_last_successful_fetch()
        
        return jsonify({
            'success': True,
            'nasdaq': live_data['nasdaq'],
            'gold': live_data['gold'],
            'dow': live_data['dow'],
            'timestamp': datetime.now().isoformat(),
            'last_update': market_data_storage.data.get('last_update'),
            'connection_status': connection_status,
            'last_successful_fetch': {k: v.isoformat() if v else None for k, v in last_successful_fetch.items()}
        })
        
    except Exception as e:
        print(f"❌ Error in live prices API: {str(e)}")
        # Return stored data as fallback
        return jsonify({
            'success': False,
            'error': str(e),
            'nasdaq': market_data_storage.get_market_data('nasdaq'),
            'gold': market_data_storage.get_market_data('gold'),
            'dow': market_data_storage.get_market_data('dow'),
            'timestamp': datetime.now().isoformat(),
            'connection_status': enhanced_data_feed.get_connection_status() if 'enhanced_data_feed' in locals() else {},
            'last_successful_fetch': enhanced_data_feed.get_last_successful_fetch() if 'enhanced_data_feed' in locals() else {}
        })

@app.route('/api/market_close_data')
def api_market_close_data():
    """Get current market data for signal generation display"""
    try:
        # Get current real-time market data
        market_close_data = {
            'nasdaq': market_data_storage.get_market_data('nasdaq'),
            'dow': market_data_storage.get_market_data('dow'),
            'gold': market_data_storage.get_market_data('gold')
        }
        print("📊 Using current real-time data for market close data API")
        
        return jsonify({
            'success': True,
            'data': {
                'nasdaq': {
                    'current_value': float(market_close_data.get('nasdaq', {}).get('price', '0').replace(',', '')),
                    'net_change': market_close_data.get('nasdaq', {}).get('rawChange', 0),
                    'previous_close': float(market_close_data.get('nasdaq', {}).get('previousClose', '0').replace(',', '')),
                    'high': float(market_close_data.get('nasdaq', {}).get('high', '0').replace(',', '')),
                    'low': float(market_close_data.get('nasdaq', {}).get('low', '0').replace(',', '')),
                    'change_percent': float(market_close_data.get('nasdaq', {}).get('changePercent', '0%').replace('%', '').replace('+', '')),
                    'date': market_close_data.get('nasdaq', {}).get('date', '')
                },
                'dow': {
                    'current_value': float(market_close_data.get('dow', {}).get('price', '0').replace(',', '')),
                    'net_change': market_close_data.get('dow', {}).get('rawChange', 0),
                    'previous_close': float(market_close_data.get('dow', {}).get('previousClose', '0').replace(',', '')),
                    'high': float(market_close_data.get('dow', {}).get('high', '0').replace(',', '')),
                    'low': float(market_close_data.get('dow', {}).get('low', '0').replace(',', '')),
                    'change_percent': float(market_close_data.get('dow', {}).get('changePercent', '0%').replace('%', '').replace('+', '')),
                    'date': market_close_data.get('dow', {}).get('date', '')
                }
            },
            'timestamp': datetime.now().isoformat(),
            'message': 'Using yesterday\'s market close data for Hybrid Math Strategy (correct trading logic)'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Error fetching market close data'
        })

@app.route('/api/auto_generation_status')
def api_auto_generation_status():
    """Get auto signal generation status"""
    try:
        enabled = market_data_storage.is_auto_generation_enabled()
        return jsonify({
            'success': True,
            'enabled': enabled,
            'message': f'Auto generation is {"enabled" if enabled else "disabled"}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/toggle_auto_generation', methods=['POST'])
def api_toggle_auto_generation():
    """Toggle auto signal generation on/off"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)
        
        market_data_storage.set_auto_generation_enabled(enabled)
        
        return jsonify({
            'success': True,
            'enabled': enabled,
            'message': f'Auto generation {"enabled" if enabled else "disabled"} successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
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
                
                # Convert to UTC+2 (Windhoek timezone)
                market_open_utc2 = market_open.astimezone(windhoek_tz)
                
                return jsonify({
                    'status': 'closed',
                    'total_seconds': total_seconds,
                    'time_until_open': {
                        'hours': hours,
                        'minutes': minutes,
                        'seconds': seconds
                    },
                    'formatted_time': f"{hours:02d}:{minutes:02d}:{seconds:02d}",
                    'message': f"US Markets Closed - Opens {market_open_utc2.strftime('%Y-%m-%d %H:%M UTC+2')}",
                    'next_open': market_open.strftime('%Y-%m-%d %H:%M ET'),
                    'next_open_utc2': market_open_utc2.strftime('%Y-%m-%d %H:%M UTC+2'),
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
                
                # Convert to UTC+2 (Windhoek timezone)
                next_open_utc2 = next_open.astimezone(windhoek_tz)
                
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
                    'message': f"US Markets Closed - Opens {next_open_utc2.strftime('%Y-%m-%d %H:%M UTC+2')}",
                    'next_open': next_open.strftime('%Y-%m-%d %H:%M ET'),
                    'next_open_utc2': next_open_utc2.strftime('%Y-%m-%d %H:%M UTC+2'),
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
            
            # Convert to UTC+2 (Windhoek timezone)
            next_open_utc2 = next_open.astimezone(windhoek_tz)
            
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
                'message': f"US Markets Closed (Weekend) - Opens {next_open_utc2.strftime('%Y-%m-%d %H:%M UTC+2')}",
                'next_open': next_open.strftime('%Y-%m-%d %H:%M ET'),
                'next_open_utc2': next_open_utc2.strftime('%Y-%m-%d %H:%M UTC+2'),
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

@app.route('/data_feed_history')
def data_feed_history():
    """Data Feed History page showing historical market data"""
    try:
        # Get date filter from query parameters
        date_filter = request.args.get('date', '')
        
        # Get historical data from storage
        symbol_data = {
            'nasdaq': [],
            'gold': [],
            'dow': []
        }
        
        # Load market data storage
        if os.path.exists('market_data.pkl'):
            try:
                with open('market_data.pkl', 'rb') as f:
                    stored_data = pickle.load(f)
                
                # Process market close history data
                if 'market_close_history' in stored_data:
                    for symbol in stored_data['market_close_history']:
                        for date, data in stored_data['market_close_history'][symbol].items():
                            # Apply date filter if specified
                            if date_filter and date != date_filter:
                                continue
                            
                            symbol_data[symbol].append({
                                'date': date,
                                'current_value': data.get('price', '--'),
                                'net_change': data.get('change', '--'),
                                'previous_close': data.get('previousClose', '--'),
                                'today_high': data.get('high', '--'),
                                'today_low': data.get('low', '--'),
                                'timestamp': data.get('timestamp', ''),
                                'raw_change': data.get('rawChange', 0)
                            })
                
                # Sort by date (newest first) for each symbol
                for symbol in symbol_data:
                    symbol_data[symbol].sort(key=lambda x: x['date'], reverse=True)
                
            except Exception as e:
                print(f"Error loading historical data: {e}")
        
        # Create pagination info for the template
        pagination_info = {
            'nasdaq': {
                'total_items': len(symbol_data['nasdaq']),
                'total_pages': 1,
                'current_page': 1,
                'has_prev': False,
                'has_next': False,
                'prev_page': None,
                'next_page': None,
                'start_item': 1 if len(symbol_data['nasdaq']) > 0 else 0,
                'end_item': len(symbol_data['nasdaq'])
            },
            'dow': {
                'total_items': len(symbol_data['dow']),
                'total_pages': 1,
                'current_page': 1,
                'has_prev': False,
                'has_next': False,
                'prev_page': None,
                'next_page': None,
                'start_item': 1 if len(symbol_data['dow']) > 0 else 0,
                'end_item': len(symbol_data['dow'])
            },
            'gold': {
                'total_items': len(symbol_data['gold']),
                'total_pages': 1,
                'current_page': 1,
                'has_prev': False,
                'has_next': False,
                'prev_page': None,
                'next_page': None,
                'start_item': 1 if len(symbol_data['gold']) > 0 else 0,
                'end_item': len(symbol_data['gold'])
            }
        }
        
        # Get latest market close data (previous day's data) for widgets
        market_close_data = market_data_storage.get_latest_market_close_data()
        
        return render_template('data_feed_history_modern.html', 
                             symbol_data=symbol_data,
                             date_filter=date_filter,
                             pagination_info=pagination_info,
                             market_close_data=market_close_data)
                             
    except Exception as e:
        # Create empty pagination info for error case
        pagination_info = {
            'nasdaq': {
                'total_items': 0,
                'total_pages': 1,
                'current_page': 1,
                'has_prev': False,
                'has_next': False,
                'prev_page': None,
                'next_page': None,
                'start_item': 0,
                'end_item': 0
            },
            'dow': {
                'total_items': 0,
                'total_pages': 1,
                'current_page': 1,
                'has_prev': False,
                'has_next': False,
                'prev_page': None,
                'next_page': None,
                'start_item': 0,
                'end_item': 0
            },
            'gold': {
                'total_items': 0,
                'total_pages': 1,
                'current_page': 1,
                'has_prev': False,
                'has_next': False,
                'prev_page': None,
                'next_page': None,
                'start_item': 0,
                'end_item': 0
            }
        }
        
        # Get market close data even in error case
        try:
            market_close_data = market_data_storage.get_latest_market_close_data()
        except:
            market_close_data = {'nasdaq': {}, 'dow': {}, 'gold': {}}
        
        return render_template('data_feed_history_modern.html', 
                             symbol_data={'nasdaq': [], 'gold': [], 'dow': []},
                             date_filter='',
                             pagination_info=pagination_info,
                             market_close_data=market_close_data,
                             error=f"Error loading data feed history: {e}")

def generate_auto_signal_for_next_day():
    """Generate signal automatically for the next trading day using market close data"""
    try:
        from datetime import datetime, timedelta
        import random
        
        # Check if auto generation is enabled
        if not market_data_storage.is_auto_generation_enabled():
            print("⏸️ Auto signal generation is disabled")
            return
        
        print("🤖 Starting auto signal generation for next trading day...")
        
        # Get yesterday's market close data (correct for trading logic)
        market_close_data = market_data_storage.get_latest_market_close_data()
        
        print(f"📊 Using yesterday's market close data for today's signals:")
        for symbol in ['nasdaq', 'dow', 'gold']:
            if symbol in market_close_data and market_close_data[symbol]:
                data = market_close_data[symbol]
                print(f"   {symbol.upper()}: {data.get('price', 'N/A')} (Change: {data.get('change', 'N/A')}) Date: {data.get('date', 'N/A')}")
        
        # Use current trading day instead of next day
        current_date = datetime.now()
        if current_date.weekday() >= 5:  # If weekend, get next Monday
            days_until_monday = 7 - current_date.weekday()
            current_date += timedelta(days=days_until_monday)
        
        next_trading_day = current_date.strftime('%Y-%m-%d')
        print(f"📅 Generating signals for: {next_trading_day}")
        
        # Generate signals for available instruments
        signals_generated = []
        instruments = ['NASDAQ', 'DOW', 'GOLD']
        
        for instrument in instruments:
            symbol_key = instrument.lower()
            if symbol_key in market_close_data and market_close_data[symbol_key]:
                signal = create_hybrid_math_auto_signal(instrument, market_close_data[symbol_key], next_trading_day)
                if signal:
                    signals_generated.append(signal)
                    print(f"✅ Generated {instrument} signal for {next_trading_day}")
        
        if signals_generated:
            print(f"🎯 Successfully generated {len(signals_generated)} signals for {next_trading_day}")
            
            # Send signals to Discord
            for signal in signals_generated:
                try:
                    print(f"📤 Posting {signal['instrument']} signal to Discord...")
                    discord_success = post_signal(signal)
                    if discord_success:
                        print(f"✅ {signal['instrument']} signal posted to Discord successfully")
                        # Create notifications for regular users
                        create_signal_notification(signal)
                    else:
                        print(f"❌ Failed to post {signal['instrument']} signal to Discord")
                except Exception as e:
                    print(f"❌ Error posting {signal['instrument']} signal to Discord: {e}")
        else:
            print("❌ No signals generated - insufficient market data")
            
        return signals_generated
        
    except Exception as e:
        print(f"❌ Error in auto signal generation: {e}")
        return []

def create_hybrid_math_auto_signal(instrument, market_data, signal_date):
    """Create a hybrid math signal using market close data for specified date"""
    try:
        # Extract market data
        current_value = float(str(market_data.get('price', '0')).replace(',', ''))
        raw_change = market_data.get('rawChange', 0)
        previous_close = float(str(market_data.get('previousClose', '0')).replace(',', ''))
        high = float(str(market_data.get('high', '0')).replace(',', ''))
        low = float(str(market_data.get('low', '0')).replace(',', ''))
        change_percent = float(str(market_data.get('changePercent', '0%')).replace('%', '').replace('+', ''))
        
        if current_value == 0 or previous_close == 0:
            return None
        
        # Hybrid Math Strategy Logic
        # Determine bias based on net change and price position
        bias = 'LONG' if raw_change > 0 else 'SHORT'
        direction = 'BUY' if bias == 'LONG' else 'SELL'
        
        # Calculate position within daily range
        if high != low:
            cv_position = (current_value - low) / (high - low)
        else:
            cv_position = 0.5
        
        # Calculate probability based on change magnitude and position
        change_magnitude = abs(change_percent)
        base_probability = 0.65  # Base probability
        
        # Adjust probability based on factors
        if change_magnitude > 1.0:
            base_probability += 0.15  # Strong move
        if cv_position > 0.7 or cv_position < 0.3:
            base_probability += 0.10  # At extremes
        
        probability = min(base_probability, 0.95)  # Cap at 95%
        
        # Determine risk level
        if change_magnitude > 2.0:
            risk_level = 'HIGH'
        elif change_magnitude > 1.0:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        # Calculate entry points and targets using Hybrid Math Strategy
        entry_price = current_value
        
        # Calculate take profit (CV + Net Change for LONG, CV - Net Change for SHORT)
        if bias == 'LONG':
            take_profit = current_value + abs(raw_change)
            stop_loss = current_value - (75 if instrument == 'NASDAQ' else 100 if instrument == 'DOW' else 10)
        else:
            take_profit = current_value - abs(raw_change)
            stop_loss = current_value + (75 if instrument == 'NASDAQ' else 100 if instrument == 'DOW' else 10)
        
        # Map instrument to display symbol
        symbol_map = {
            'NASDAQ': 'NAS100',
            'DOW': 'US30',
            'GOLD': 'XAUUSD'
        }
        
        # Create signal object compatible with post_signal function
        signal = {
            # Required fields for post_signal
            'symbol': symbol_map.get(instrument, instrument),
            'display_name': symbol_map.get(instrument, instrument),
            'instrument': instrument,
            'direction': direction,
            'bias': bias,
            'entry_price': entry_price,
            'entry1': entry_price,
            'take_profit': take_profit,
            'tp1': take_profit,
            'stop_loss': stop_loss,
            'sl_tight': stop_loss,
            'confidence': int(probability * 100),
            'probability_percentage': probability * 100,
            'probability_label': 'High' if probability > 0.8 else 'Medium' if probability > 0.65 else 'Low',
            
            # Market data fields
            'current_value': current_value,
            'net_change': raw_change,
            'change_percent': change_percent,
            'previous_close': previous_close,
            'high': high,
            'low': low,
            'today_high': high,
            'today_low': low,
            'cv_position': cv_position,
            
            # Metadata
            'timestamp': datetime.now().isoformat(),
            'strategy': 'Hybrid Math Strategy',
            'auto_generated': True,
            'signal_date': signal_date,
            'market_data_date': market_data.get('date', ''),
            'risk_level': risk_level,
            'sentiment': 'Neutral',
            'sentiment_score': 0.5,
            'news_count': 0
        }
        
        return signal
        
    except Exception as e:
        print(f"❌ Error creating signal for {instrument}: {e}")
        return None

@app.route('/api/generate_auto_signal', methods=['POST'])
@admin_required
def api_generate_auto_signal():
    """API endpoint to manually trigger auto signal generation"""
    try:
        signals = generate_auto_signal_for_next_day()
        return jsonify({
            'success': True,
            'signals_generated': len(signals),
            'signals': signals,
            'message': f'Generated {len(signals)} signals for next trading day'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/settings')
def settings():
    """Settings configuration page"""
    try:
        # Get current settings status
        auto_generation_enabled = market_data_storage.is_auto_generation_enabled()
        
        # Get Discord status
        discord_config = check_discord_config()
        
        return render_template('settings_modern.html',
                             auto_generation_enabled=auto_generation_enabled,
                             discord_config=discord_config)
    except Exception as e:
        return render_template('settings_modern.html', 
                             error=f"Error loading settings: {e}",
                             auto_generation_enabled=False,
                             discord_config={'webhook_configured': False})

@app.route('/api/test_journal_data')
def api_test_journal_data():
    """Test endpoint to verify journal data is working"""
    try:
        conn = sqlite3.connect("ai_learning.db")
        cursor = conn.cursor()
        
        # Test the same query as journal route
        cursor.execute('''
            SELECT 
                COUNT(*) as total_signals,
                SUM(CASE WHEN actual_outcome = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN actual_outcome = 0 THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN actual_outcome = 2 THEN 1 ELSE 0 END) as breakevens,
                SUM(CASE WHEN actual_outcome IS NULL THEN 1 ELSE 0 END) as pending
            FROM signal_performance
        ''')
        overall_stats = cursor.fetchone()
        
        cursor.execute('''
            SELECT COUNT(*) FROM signal_performance 
            ORDER BY timestamp DESC 
            LIMIT 20
        ''')
        signals_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'total_signals': overall_stats[0],
            'wins': overall_stats[1],
            'losses': overall_stats[2],
            'breakevens': overall_stats[3],
            'pending': overall_stats[4],
            'signals_count': signals_count,
            'message': 'Journal data test successful'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# =============================================================================
# AGENT MANAGEMENT ROUTES
# =============================================================================

@app.route('/api/agents/status')
@login_required
def get_agents_status():
    """Get status of all agents"""
    try:
        agents_status = agent_manager.get_all_agents_status()
        return jsonify({
            'success': True,
            'agents': agents_status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/agents/create_task', methods=['POST'])
@login_required
def create_agent_task():
    """Create a new task for agents"""
    try:
        data = request.json
        task_type = data.get('task_type')
        agent_type = data.get('agent_type', 'signal_analyzer')
        parameters = data.get('parameters', {})
        priority = data.get('priority', 5)
        
        task_id = agent_manager.create_task(
            agent_type=agent_type,
            task_type=task_type,
            parameters=parameters,
            priority=priority
        )
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Task created successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/agents/task_history')
@login_required
def get_task_history():
    """Get agent task execution history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        history = agent_manager.get_task_history(limit=limit)
        
        return jsonify({
            'success': True,
            'tasks': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/agents/analyze_signal', methods=['POST'])
@login_required
def analyze_signal_with_agent():
    """Use signal analyzer agent to analyze a trading signal"""
    try:
        data = request.json
        symbol = data.get('symbol')
        signal_data = data.get('signal_data', {})
        
        if not symbol:
            return jsonify({
                'success': False,
                'error': 'Symbol is required'
            })
        
        # Create task for signal analysis
        task_id = agent_manager.create_task(
            agent_type='signal_analyzer',
            task_type='analyze_signal',
            parameters={
                'symbol': symbol,
                'signal_data': signal_data
            },
            priority=7
        )
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': f'Signal analysis initiated for {symbol}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/agents/monitor_market', methods=['POST'])
@login_required
def monitor_market_with_agent():
    """Use market monitor agent to analyze market conditions"""
    try:
        data = request.json
        symbols = data.get('symbols', ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD'])
        timeframe = data.get('timeframe', '1h')
        
        # Create task for market monitoring
        task_id = agent_manager.create_task(
            agent_type='market_monitor',
            task_type='monitor_market',
            parameters={
                'symbols': symbols,
                'timeframe': timeframe
            },
            priority=6
        )
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Market monitoring initiated'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/agents/assess_risk', methods=['POST'])
@login_required
def assess_risk_with_agent():
    """Use risk assessor agent to analyze portfolio risk"""
    try:
        data = request.json
        portfolio = data.get('portfolio', {})
        new_position = data.get('new_position', {})
        
        # Create task for risk assessment
        task_id = agent_manager.create_task(
            agent_type='risk_assessor',
            task_type='assess_risk',
            parameters={
                'portfolio': portfolio,
                'new_position': new_position
            },
            priority=8  # High priority for risk assessment
        )
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Risk assessment initiated'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    print("🚀 Starting BFI Signals Platform...")
    print("📊 Dashboard will be available at: http://localhost:5000")
    print("🤖 Intelligent agents ready for interaction!")
    print("📈 Monitor your trading performance in real-time!")
    
    # Create templates directory if it doesn't exist
    import os
    if not os.path.exists('templates'):
        os.makedirs('templates')
    if not os.path.exists('static'):
        os.makedirs('static')
    
    # Favicon files are handled by the ensure_favicons() function
    
    # Setup scheduler for automatic signal generation
    def setup_scheduler():
        """Setup scheduler for auto signal generation at market close"""
        gmt_plus_2 = pytz.timezone('Africa/Cairo')  # GMT+2 timezone
        
        def scheduled_auto_generation():
            """Wrapper function for scheduled market data collection and auto signal generation"""
            try:
                print("⏰ Market close routine triggered at 23:05 GMT+2")
                
                # Step 1: Save market close data
                print("💾 Collecting and saving market close data...")
                market_data_storage.save_market_close_data()
                print("✅ Market close data saved successfully")
                
                # Step 2: Generate signals for next day if auto generation is enabled
                print("🤖 Checking auto signal generation...")
                generate_auto_signal_for_next_day()
                
            except Exception as e:
                print(f"❌ Error in scheduled market close routine: {e}")
                import traceback
                traceback.print_exc()
        
        # Schedule auto signal generation at 23:05 GMT+2 (market close)
        schedule.every().day.at("23:05").do(scheduled_auto_generation)
        
        def run_scheduler():
            """Run the scheduler in a separate thread"""
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        print("📅 Auto signal generation scheduler started (23:05 GMT+2)")
    
@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Handle logout via API"""
    try:
        session_token = session.get('session_token')
        if session_token:
            auth_manager.logout_user(session_token)
        
        session.clear()
        return jsonify({'success': True, 'message': 'Logged out successfully'})
        
    except Exception as e:
        print(f"❌ Error during logout: {str(e)}")
        return jsonify({'success': False, 'error': 'Logout failed'})

# Profile Management Routes
@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    try:
        user_id = session.get('user_id')
        user_profile = auth_manager.get_user_profile(user_id)
        
        if not user_profile:
            # If no profile found, create basic user data from session
            from datetime import datetime
            user_profile = {
                'id': user_id,
                'username': session.get('user_username', 'User'),
                'email': session.get('user_email', ''),
                'full_name': session.get('user_username', 'User'),
                'profile_picture': None,
                'timezone': 'UTC',
                'role': session.get('user_role', 'user'),
                'created_at': datetime.now(),
                'last_login': datetime.now(),
                'notification_preferences': {
                    'email_notifications': True,
                    'push_notifications': True,
                    'signal_alerts': True,
                    'trading_updates': True
                }
            }
        
        return render_template('profile_modern.html', user=user_profile)
        
    except Exception as e:
        print(f"❌ Error loading profile page: {str(e)}")
        import traceback
        traceback.print_exc()
        from datetime import datetime
        return render_template('profile_modern.html', user={
            'id': user_id,
            'username': session.get('user_username', 'User'),
            'email': session.get('user_email', ''),
            'full_name': session.get('user_username', 'User'),
            'profile_picture': None,
            'timezone': 'UTC',
            'role': session.get('user_role', 'user'),
            'created_at': datetime.now(),
            'last_login': datetime.now(),
            'notification_preferences': {
                'email_notifications': True,
                'push_notifications': True,
                'signal_alerts': True,
                'trading_updates': True
            }
        })

@app.route('/api/user/profile', methods=['GET'])
@login_required
def api_get_user_profile():
    """Get current user's profile"""
    try:
        user_id = session.get('user_id')
        profile = auth_manager.get_user_profile(user_id)
        
        if profile:
            return jsonify({
                'success': True,
                'profile': profile
            })
        else:
            return jsonify({'success': False, 'error': 'Profile not found'}), 404
            
    except Exception as e:
        print(f"❌ Error getting user profile: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get profile'}), 500

@app.route('/api/user/profile', methods=['POST'])
@login_required
def api_update_user_profile():
    """Update current user's profile"""
    try:
        user_id = session.get('user_id')
        profile_data = request.get_json()
        
        success = auth_manager.update_user_profile(user_id, profile_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update profile'}), 400
            
    except Exception as e:
        print(f"❌ Error updating user profile: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to update profile'}), 500

@app.route('/api/user/profile/picture', methods=['POST'])
@login_required
def api_upload_profile_picture():
    """Upload profile picture"""
    try:
        user_id = session.get('user_id')
        
        if 'profile_picture' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
            
        file = request.files['profile_picture']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
        
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(app.root_path, 'uploads', 'profiles')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Generate unique filename
        import uuid
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"profile_{user_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
        file_path = os.path.join(uploads_dir, filename)
        
        # Save file
        file.save(file_path)
        
        # Update user profile with picture path
        relative_path = f"uploads/profiles/{filename}"
        profile_data = {'profile_picture': relative_path}
        success = auth_manager.update_user_profile(user_id, profile_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Profile picture uploaded successfully',
                'profile_picture': relative_path
            })
        else:
            # Clean up file if database update failed
            os.remove(file_path)
            return jsonify({'success': False, 'error': 'Failed to update profile'}), 500
            
    except Exception as e:
        print(f"❌ Error uploading profile picture: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to upload picture'}), 500

@app.route('/api/user/profile/picture/<int:user_id>')
def api_get_profile_picture(user_id):
    """Serve profile picture"""
    try:
        profile = auth_manager.get_user_profile(user_id)
        
        if profile and profile.get('profile_picture'):
            file_path = os.path.join(app.root_path, profile['profile_picture'])
            if os.path.exists(file_path):
                return send_file(file_path)
        
        # Return default avatar if no profile picture
        default_avatar = os.path.join(app.root_path, 'static', 'images', 'default-avatar.svg')
        if os.path.exists(default_avatar):
            return send_file(default_avatar, mimetype='image/svg+xml')
        
        return '', 404
        
    except Exception as e:
        print(f"❌ Error serving profile picture: {str(e)}")
        return '', 404

@app.route('/api/user/change-password', methods=['POST'])
@login_required
def api_change_password():
    """Change user password"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'success': False, 'error': 'Both current and new passwords are required'}), 400
            
        success = auth_manager.change_user_password(user_id, current_password, new_password)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Password changed successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400
            
    except Exception as e:
        print(f"❌ Error changing password: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to change password'}), 500

@app.route('/admin')
@admin_required
def admin_panel():
    """Admin panel for user management"""
    return render_template('admin_panel.html')

@app.route('/api/admin/users')
@admin_required
def api_admin_get_users():
    """Get all users for admin management"""
    try:
        users = auth_manager.get_all_users(include_admins=True)
        return jsonify({
            'success': True,
            'users': users
        })
    except Exception as e:
        print(f"❌ Error getting users: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get users'})

@app.route('/api/admin/pending-users')
@admin_required
def api_admin_get_pending_users():
    """Get pending users for admin approval"""
    try:
        pending_users = auth_manager.get_pending_users()
        return jsonify({
            'success': True,
            'users': pending_users
        })
    except Exception as e:
        print(f"❌ Error getting pending users: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get pending users'})

@app.route('/api/admin/users/<int:user_id>/approve', methods=['POST'])
@admin_required
def api_admin_approve_user(user_id):
    """Approve a user registration"""
    try:
        admin_id = session.get('user_id')
        success = auth_manager.approve_user(user_id, admin_id)
        
        if success:
            return jsonify({'success': True, 'message': 'User approved successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to approve user'})
    except Exception as e:
        print(f"❌ Error approving user: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to approve user'})

@app.route('/api/admin/users/<int:user_id>/reject', methods=['DELETE'])
@admin_required
def api_admin_reject_user(user_id):
    """Reject a user registration"""
    try:
        success = auth_manager.reject_user(user_id)
        
        if success:
            return jsonify({'success': True, 'message': 'User rejected and deleted'})
        else:
            return jsonify({'success': False, 'error': 'Failed to reject user'})
    except Exception as e:
        print(f"❌ Error rejecting user: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to reject user'})

@app.route('/api/admin/users/<int:user_id>/deactivate', methods=['POST'])
@admin_required
def api_admin_deactivate_user(user_id):
    """Deactivate a user account"""
    try:
        admin_id = session.get('user_id')
        success = auth_manager.deactivate_user(user_id, admin_id)
        
        if success:
            return jsonify({'success': True, 'message': 'User deactivated successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to deactivate user'})
    except Exception as e:
        print(f"❌ Error deactivating user: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to deactivate user'})

@app.route('/api/admin/users/<int:user_id>/reactivate', methods=['POST'])
@admin_required
def api_admin_reactivate_user(user_id):
    """Reactivate a user account"""
    try:
        success = auth_manager.reactivate_user(user_id)
        
        if success:
            return jsonify({'success': True, 'message': 'User reactivated successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to reactivate user'})
    except Exception as e:
        print(f"❌ Error reactivating user: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to reactivate user'})

@app.route('/api/admin/users/<int:user_id>/role', methods=['PUT'])
@admin_required
def api_admin_update_user_role(user_id):
    """Update a user's role"""
    try:
        data = request.get_json()
        new_role = data.get('role')
        
        if new_role not in ['user', 'admin']:
            return jsonify({'success': False, 'error': 'Invalid role'})
        
        admin_id = session.get('user_id')
        success = auth_manager.update_user_role(user_id, new_role, admin_id)
        
        if success:
            return jsonify({'success': True, 'message': f'User role updated to {new_role}'})
        else:
            return jsonify({'success': False, 'error': 'Failed to update user role'})
    except Exception as e:
        print(f"❌ Error updating user role: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to update user role'})

@app.route('/api/admin/create-user', methods=['POST'])
@admin_required
def api_admin_create_user():
    """Create a new user as admin"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        role = data.get('role', 'user')
        
        if not username or not email or not password:
            return jsonify({'success': False, 'error': 'All fields are required'})
        
        if role not in ['user', 'admin']:
            return jsonify({'success': False, 'error': 'Invalid role'})
        
        admin_id = session.get('user_id')
        result = auth_manager.admin_create_user(username, email, password, role, admin_id)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error creating user: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to create user'})

@app.route('/api/admin/users/<int:user_id>/change-password', methods=['PUT'])
@admin_required
def api_admin_change_password(user_id):
    """Admin changes user password"""
    try:
        data = request.get_json()
        new_password = data.get('new_password', '').strip()
        
        if not new_password:
            return jsonify({'success': False, 'error': 'New password is required'})
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters long'})
        
        admin_id = session.get('user_id')
        result = auth_manager.admin_change_user_password(user_id, new_password, admin_id)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error changing user password: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to change password'})

@app.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def api_mark_all_notifications_read():
    """Mark all notifications as read for the current user"""
    try:
        user_id = session.get('user_id')
        
        # Get all unread notifications for the user
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_notifications 
            SET is_read = 1 
            WHERE user_id = ? AND is_read = 0
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'All notifications marked as read'})
        
    except Exception as e:
        print(f"❌ Error marking all notifications as read: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to mark notifications as read'})

@app.route('/api/sync_signals', methods=['POST'])
@admin_required
def api_sync_signals():
    """API endpoint to manually sync signals from JSON to database"""
    try:
        success = sync_json_signals_to_db()
        if success:
            return jsonify({
                'success': True,
                'message': 'Signals synced successfully from JSON files to database!'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Signal sync failed. Check server logs for details.'
            })
    except Exception as e:
        print(f"❌ Error in sync API: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error syncing signals: {str(e)}'
        })

# Enhanced Signals API Endpoints
@app.route('/api/signals/today')
@login_required
def api_signals_today():
    """Get today's signals only"""
    try:
        signals = get_todays_signals()
        
        return jsonify({
            'success': True,
            'data': signals,
            'count': len(signals),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'message': f'Retrieved {len(signals)} signals for today'
        })
        
    except Exception as e:
        print(f"❌ Error getting today's signals: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error retrieving today\'s signals: {str(e)}',
            'data': [],
            'count': 0
        }), 500

@app.route('/api/signals/week')
@login_required
def api_signals_week():
    """Get this week's signals"""
    try:
        signals = get_week_signals()
        
        # Calculate week range for response
        today = datetime.now()
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        week_start = monday.strftime('%Y-%m-%d')
        week_end = (monday + timedelta(days=6)).strftime('%Y-%m-%d')
        
        return jsonify({
            'success': True,
            'data': signals,
            'count': len(signals),
            'week_start': week_start,
            'week_end': week_end,
            'message': f'Retrieved {len(signals)} signals for this week ({week_start} to {week_end})'
        })
        
    except Exception as e:
        print(f"❌ Error getting week signals: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error retrieving week signals: {str(e)}',
            'data': [],
            'count': 0
        }), 500

@app.route('/api/signals/search')
@login_required
def api_signals_search():
    """Search signals by symbol or type"""
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query parameter "q" is required',
                'data': [],
                'count': 0
            }), 400
        
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
        # Ensure risky_play_outcome column exists
        try:
            cursor.execute('ALTER TABLE signal_performance ADD COLUMN risky_play_outcome INTEGER')
            conn.commit()
        except sqlite3.OperationalError:
            pass
        
        # Check if risky_play_outcome column exists
        cursor.execute('PRAGMA table_info(signal_performance)')
        columns = [col[1] for col in cursor.fetchall()]
        
        # Search in symbol and signal_type fields
        search_term = f'%{query}%'
        
        if 'risky_play_outcome' in columns:
            cursor.execute('''
                SELECT id, symbol, signal_type, predicted_probability, risk_level, 
                       timestamp, actual_outcome, profit_loss, risky_play_outcome
                FROM signal_performance 
                WHERE (symbol LIKE ? OR signal_type LIKE ?)
                ORDER BY timestamp DESC 
                LIMIT ? OFFSET ?
            ''', (search_term, search_term, limit, offset))
        else:
            cursor.execute('''
                SELECT id, symbol, signal_type, predicted_probability, risk_level, 
                       timestamp, actual_outcome, profit_loss, NULL as risky_play_outcome
                FROM signal_performance 
                WHERE (symbol LIKE ? OR signal_type LIKE ?)
                ORDER BY timestamp DESC 
                LIMIT ? OFFSET ?
            ''', (search_term, search_term, limit, offset))
        
        signals_data = cursor.fetchall()
        
        # Get total count for pagination
        cursor.execute('''
            SELECT COUNT(*) FROM signal_performance 
            WHERE (symbol LIKE ? OR signal_type LIKE ?)
        ''', (search_term, search_term))
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        # Format signals data
        formatted_signals = format_signal_data(signals_data)
        
        return jsonify({
            'success': True,
            'data': formatted_signals,
            'count': len(formatted_signals),
            'total_count': total_count,
            'query': query,
            'limit': limit,
            'offset': offset,
            'message': f'Found {total_count} signals matching "{query}"'
        })
        
    except Exception as e:
        print(f"❌ Error searching signals: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error searching signals: {str(e)}',
            'data': [],
            'count': 0
        }), 500

@app.route('/api/signals/<int:signal_id>')
@login_required
def api_signal_detail(signal_id):
    """Get single signal details"""
    try:
        conn = sqlite3.connect('ai_learning.db')
        cursor = conn.cursor()
        
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
                WHERE id = ?
            ''', (signal_id,))
        else:
            cursor.execute('''
                SELECT id, symbol, signal_type, predicted_probability, risk_level, 
                       timestamp, actual_outcome, profit_loss, NULL as risky_play_outcome
                FROM signal_performance 
                WHERE id = ?
            ''', (signal_id,))
        
        signal_data = cursor.fetchone()
        conn.close()
        
        if not signal_data:
            return jsonify({
                'success': False,
                'error': f'Signal with ID {signal_id} not found',
                'data': None
            }), 404
        
        # Format signal data
        formatted_signals = format_signal_data([signal_data])
        signal = formatted_signals[0] if formatted_signals else None
        
        return jsonify({
            'success': True,
            'data': signal,
            'message': f'Retrieved signal {signal_id}'
        })
        
    except Exception as e:
        print(f"❌ Error getting signal {signal_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error retrieving signal: {str(e)}',
            'data': None
        }), 500

@app.route('/api/signals/stats')
@login_required
def api_signals_stats():
    """Get comprehensive signal performance statistics"""
    try:
        stats = calculate_signal_stats()
        
        return jsonify({
            'success': True,
            'data': stats,
            'message': 'Signal statistics retrieved successfully'
        })
        
    except Exception as e:
        print(f"❌ Error getting signal stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error retrieving signal statistics: {str(e)}',
            'data': None
        }), 500

if __name__ == '__main__':
    # Initialize scheduler
    setup_scheduler()
    
    # Use debug=False for production-like experience, True for development
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000) 