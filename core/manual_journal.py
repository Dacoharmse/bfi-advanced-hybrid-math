#!/usr/bin/env python3
"""
Manual Trade Journal Utilities
Handles CRUD operations and file uploads for manual trade entries
"""

import os
import sqlite3
import uuid
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
import io

# Configuration
UPLOAD_FOLDER = 'uploads/charts'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGE_DIMENSION = 2048

class ManualJournalManager:
    """Manages manual trade journal operations"""
    
    def __init__(self, db_path="ai_learning.db"):
        self.db_path = db_path
        self.upload_folder = UPLOAD_FOLDER
        
        # Ensure upload folder exists
        os.makedirs(self.upload_folder, exist_ok=True)
        
        # Add user_id column if it doesn't exist (migration)
        self._add_user_id_column()
    
    def _add_user_id_column(self):
        """Add user_id column to manual_journal_entries table if it doesn't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user_id column exists
            cursor.execute("PRAGMA table_info(manual_journal_entries)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'user_id' not in columns:
                cursor.execute('ALTER TABLE manual_journal_entries ADD COLUMN user_id INTEGER DEFAULT 1')
                conn.commit()
                print("✅ Added user_id column to manual_journal_entries")
            
            conn.close()
        except Exception as e:
            print(f"❌ Error adding user_id column: {e}")
    
    def allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    def validate_image(self, file_data):
        """Validate image file format and size"""
        try:
            # Check file size
            if len(file_data) > MAX_FILE_SIZE:
                return False, "File size too large (max 10MB)"
            
            # If PIL is not available, just check file size
            if not PIL_AVAILABLE:
                return True, "Image validated (PIL not available for detailed validation)"
            
            # Try to open with PIL to validate image format
            image = Image.open(io.BytesIO(file_data))
            
            # Check dimensions
            width, height = image.size
            if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                return False, f"Image dimensions too large (max {MAX_IMAGE_DIMENSION}px)"
            
            # Check format
            if image.format.lower() not in ['png', 'jpeg', 'jpg', 'gif']:
                return False, "Invalid image format"
            
            return True, "Valid image"
            
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"
    
    def save_chart_image(self, file):
        """Save uploaded chart image with security validation"""
        try:
            if not file or file.filename == '':
                return None, "No file selected"
            
            if not self.allowed_file(file.filename):
                return None, "File type not allowed"
            
            # Read file data for validation
            file_data = file.read()
            file.seek(0)  # Reset file pointer
            
            # Validate image
            is_valid, message = self.validate_image(file_data)
            if not is_valid:
                return None, message
            
            # Generate secure filename
            original_filename = secure_filename(file.filename)
            file_extension = original_filename.rsplit('.', 1)[1].lower()
            
            # Create unique filename with timestamp and hash
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_hash = hashlib.md5(file_data).hexdigest()[:8]
            new_filename = f"chart_{timestamp}_{file_hash}.{file_extension}"
            
            # Save file
            file_path = os.path.join(self.upload_folder, new_filename)
            file.save(file_path)
            
            # Verify file was saved correctly
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                return file_path, "File uploaded successfully"
            else:
                return None, "Failed to save file"
                
        except Exception as e:
            return None, f"Upload error: {str(e)}"
    
    def create_journal_entry(self, entry_data):
        """Create a new manual journal entry"""
        try:
            import json
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Serialize array fields to JSON
            entry_prices_json = json.dumps(entry_data.get('entry_prices', [])) if entry_data.get('entry_prices') else None
            position_sizes_json = json.dumps(entry_data.get('position_sizes', [])) if entry_data.get('position_sizes') else None
            
            cursor.execute('''
                INSERT INTO manual_journal_entries 
                (symbol, trade_type, entry_price, exit_price, quantity, outcome, 
                 profit_loss, trade_date, entry_time, exit_time, notes, chart_image_path, 
                 chart_link, entry_prices, position_sizes, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry_data.get('symbol', '').upper(),
                entry_data.get('trade_type', '').upper(),
                float(entry_data.get('entry_price', 0)),
                float(entry_data.get('exit_price', 0)) if entry_data.get('exit_price') else None,
                int(float(entry_data.get('quantity', 1))),
                entry_data.get('outcome', 'PENDING').upper(),
                float(entry_data.get('profit_loss', 0)),
                entry_data.get('trade_date'),
                entry_data.get('entry_time'),
                entry_data.get('exit_time'),
                entry_data.get('notes', ''),
                entry_data.get('chart_image_path'),
                entry_data.get('chart_link', ''),
                entry_prices_json,
                position_sizes_json,
                entry_data.get('user_id', 1)  # Default to user_id 1 if not provided
            ))
            
            entry_id = cursor.lastrowid
            conn.commit()
            
            return entry_id, "Entry created successfully"
            
        except sqlite3.Error as e:
            return None, f"Database error: {str(e)}"
        except Exception as e:
            return None, f"Error creating entry: {str(e)}"
        finally:
            if conn:
                conn.close()
    
    def get_journal_entries(self, limit=50, offset=0, symbol=None, outcome=None, user_id=None):
        """Retrieve manual journal entries with optional filtering"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build query with optional filters
            query = '''
                SELECT id, symbol, trade_type, entry_price, exit_price, quantity, 
                       outcome, profit_loss, trade_date, entry_time, exit_time, 
                       notes, chart_image_path, chart_link, entry_prices, position_sizes,
                       created_at, updated_at
                FROM manual_journal_entries
                WHERE 1=1
            '''
            params = []
            
            # IMPORTANT: Always filter by user_id for security
            if user_id:
                query += ' AND user_id = ?'
                params.append(user_id)
            
            if symbol:
                query += ' AND symbol = ?'
                params.append(symbol.upper())
            
            if outcome:
                query += ' AND outcome = ?'
                params.append(outcome.upper())
            
            query += ' ORDER BY trade_date DESC, created_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            entries = cursor.fetchall()
            
            # Convert to list of dictionaries
            columns = [desc[0] for desc in cursor.description]
            entries_list = []
            
            for entry in entries:
                entry_dict = dict(zip(columns, entry))
                
                # Deserialize JSON fields
                import json
                if entry_dict.get('entry_prices'):
                    try:
                        entry_dict['entry_prices'] = json.loads(entry_dict['entry_prices'])
                    except (json.JSONDecodeError, TypeError):
                        entry_dict['entry_prices'] = []
                else:
                    entry_dict['entry_prices'] = []
                
                if entry_dict.get('position_sizes'):
                    try:
                        entry_dict['position_sizes'] = json.loads(entry_dict['position_sizes'])
                    except (json.JSONDecodeError, TypeError):
                        entry_dict['position_sizes'] = []
                else:
                    entry_dict['position_sizes'] = []
                
                entries_list.append(entry_dict)
            
            return entries_list, "Entries retrieved successfully"
            
        except sqlite3.Error as e:
            return [], f"Database error: {str(e)}"
        except Exception as e:
            return [], f"Error retrieving entries: {str(e)}"
        finally:
            if conn:
                conn.close()
    
    def get_journal_entry(self, entry_id, user_id=None):
        """Get a single journal entry by ID, optionally filtered by user_id for security"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build query with optional user_id filter for security
            query = '''
                SELECT id, symbol, trade_type, entry_price, exit_price, quantity, 
                       outcome, profit_loss, trade_date, entry_time, exit_time, 
                       notes, chart_image_path, chart_link, entry_prices, position_sizes,
                       created_at, updated_at
                FROM manual_journal_entries
                WHERE id = ?
            '''
            params = [entry_id]
            
            # IMPORTANT: Filter by user_id for security if provided
            if user_id:
                query += ' AND user_id = ?'
                params.append(user_id)
            
            cursor.execute(query, params)
            
            entry = cursor.fetchone()
            
            if entry:
                columns = [desc[0] for desc in cursor.description]
                entry_dict = dict(zip(columns, entry))
                
                # Deserialize JSON fields
                import json
                if entry_dict.get('entry_prices'):
                    try:
                        entry_dict['entry_prices'] = json.loads(entry_dict['entry_prices'])
                    except (json.JSONDecodeError, TypeError):
                        entry_dict['entry_prices'] = []
                else:
                    entry_dict['entry_prices'] = []
                
                if entry_dict.get('position_sizes'):
                    try:
                        entry_dict['position_sizes'] = json.loads(entry_dict['position_sizes'])
                    except (json.JSONDecodeError, TypeError):
                        entry_dict['position_sizes'] = []
                else:
                    entry_dict['position_sizes'] = []
                
                return entry_dict, "Entry found"
            else:
                return None, "Entry not found"
                
        except sqlite3.Error as e:
            return None, f"Database error: {str(e)}"
        except Exception as e:
            return None, f"Error retrieving entry: {str(e)}"
        finally:
            if conn:
                conn.close()
    
    def update_journal_entry(self, entry_id, entry_data, user_id=None):
        """Update an existing journal entry, optionally filtered by user_id for security"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if entry exists and user has access
            check_query = 'SELECT id FROM manual_journal_entries WHERE id = ?'
            check_params = [entry_id]
            
            # IMPORTANT: Filter by user_id for security if provided
            if user_id:
                check_query += ' AND user_id = ?'
                check_params.append(user_id)
            
            cursor.execute(check_query, check_params)
            if not cursor.fetchone():
                return False, "Entry not found or access denied"
            
            # Serialize array fields to JSON
            import json
            entry_prices_json = json.dumps(entry_data.get('entry_prices', [])) if entry_data.get('entry_prices') else None
            position_sizes_json = json.dumps(entry_data.get('position_sizes', [])) if entry_data.get('position_sizes') else None
            
            # Update entry
            cursor.execute('''
                UPDATE manual_journal_entries SET
                symbol = ?, trade_type = ?, entry_price = ?, exit_price = ?, 
                quantity = ?, outcome = ?, profit_loss = ?, trade_date = ?, 
                entry_time = ?, exit_time = ?, notes = ?, chart_image_path = ?,
                chart_link = ?, entry_prices = ?, position_sizes = ?
                WHERE id = ?
            ''', (
                entry_data.get('symbol', '').upper(),
                entry_data.get('trade_type', '').upper(),
                float(entry_data.get('entry_price', 0)),
                float(entry_data.get('exit_price', 0)) if entry_data.get('exit_price') else None,
                int(float(entry_data.get('quantity', 1))),
                entry_data.get('outcome', 'PENDING').upper(),
                float(entry_data.get('profit_loss', 0)),
                entry_data.get('trade_date'),
                entry_data.get('entry_time'),
                entry_data.get('exit_time'),
                entry_data.get('notes', ''),
                entry_data.get('chart_image_path'),
                entry_data.get('chart_link', ''),
                entry_prices_json,
                position_sizes_json,
                entry_id
            ))
            
            conn.commit()
            return True, "Entry updated successfully"
            
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"
        except Exception as e:
            return False, f"Error updating entry: {str(e)}"
        finally:
            if conn:
                conn.close()
    
    def delete_journal_entry(self, entry_id, user_id=None):
        """Delete a journal entry and its associated image, optionally filtered by user_id for security"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get entry to check for image file and user access
            check_query = 'SELECT chart_image_path FROM manual_journal_entries WHERE id = ?'
            check_params = [entry_id]
            
            # IMPORTANT: Filter by user_id for security if provided
            if user_id:
                check_query += ' AND user_id = ?'
                check_params.append(user_id)
            
            cursor.execute(check_query, check_params)
            result = cursor.fetchone()
            
            if not result:
                return False, "Entry not found or access denied"
            
            image_path = result[0]
            
            # Delete database entry with user_id filter for security
            delete_query = 'DELETE FROM manual_journal_entries WHERE id = ?'
            delete_params = [entry_id]
            
            # IMPORTANT: Filter by user_id for security if provided
            if user_id:
                delete_query += ' AND user_id = ?'
                delete_params.append(user_id)
            
            cursor.execute(delete_query, delete_params)
            conn.commit()
            
            # Delete associated image file if it exists
            if image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except OSError:
                    pass  # File might be in use or permission issue
            
            return True, "Entry deleted successfully"
            
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"
        except Exception as e:
            return False, f"Error deleting entry: {str(e)}"
        finally:
            if conn:
                conn.close()
    
    def get_journal_statistics(self, user_id=None):
        """Get comprehensive journal statistics, optionally filtered by user_id"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Overall statistics with optional user_id filter
            overall_query = '''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) as losses,
                    SUM(CASE WHEN outcome = 'BREAKEVEN' THEN 1 ELSE 0 END) as breakevens,
                    SUM(CASE WHEN outcome = 'PENDING' THEN 1 ELSE 0 END) as pending,
                    SUM(profit_loss) as total_pnl,
                    AVG(profit_loss) as avg_pnl,
                    MAX(profit_loss) as best_trade,
                    MIN(profit_loss) as worst_trade
                FROM manual_journal_entries
            '''
            overall_params = []
            
            if user_id:
                overall_query += ' WHERE user_id = ?'
                overall_params.append(user_id)
            
            cursor.execute(overall_query, overall_params)
            overall_stats = cursor.fetchone()
            
            # Statistics by symbol with optional user_id filter
            symbol_query = '''
                SELECT 
                    symbol,
                    COUNT(*) as trades,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                    SUM(profit_loss) as pnl
                FROM manual_journal_entries
            '''
            symbol_params = []
            
            if user_id:
                symbol_query += ' WHERE user_id = ?'
                symbol_params.append(user_id)
            
            symbol_query += ' GROUP BY symbol ORDER BY trades DESC'
            cursor.execute(symbol_query, symbol_params)
            symbol_stats = cursor.fetchall()
            
            # Statistics by trade type with optional user_id filter
            type_query = '''
                SELECT 
                    trade_type,
                    COUNT(*) as trades,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                    SUM(profit_loss) as pnl
                FROM manual_journal_entries
            '''
            type_params = []
            
            if user_id:
                type_query += ' WHERE user_id = ?'
                type_params.append(user_id)
            
            type_query += ' GROUP BY trade_type ORDER BY trades DESC'
            cursor.execute(type_query, type_params)
            type_stats = cursor.fetchall()
            
            return {
                'overall': overall_stats,
                'by_symbol': symbol_stats,
                'by_type': type_stats
            }, "Statistics retrieved successfully"
            
        except sqlite3.Error as e:
            return None, f"Database error: {str(e)}"
        except Exception as e:
            return None, f"Error retrieving statistics: {str(e)}"
        finally:
            if conn:
                conn.close()

# Global instance
journal_manager = ManualJournalManager()