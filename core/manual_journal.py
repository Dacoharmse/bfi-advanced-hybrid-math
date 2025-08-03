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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO manual_journal_entries 
                (symbol, trade_type, entry_price, exit_price, quantity, outcome, 
                 profit_loss, trade_date, entry_time, exit_time, notes, chart_image_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry_data.get('symbol', '').upper(),
                entry_data.get('trade_type', '').upper(),
                float(entry_data.get('entry_price', 0)),
                float(entry_data.get('exit_price', 0)) if entry_data.get('exit_price') else None,
                int(entry_data.get('quantity', 1)),
                entry_data.get('outcome', 'PENDING').upper(),
                float(entry_data.get('profit_loss', 0)),
                entry_data.get('trade_date'),
                entry_data.get('entry_time'),
                entry_data.get('exit_time'),
                entry_data.get('notes', ''),
                entry_data.get('chart_image_path')
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
    
    def get_journal_entries(self, limit=50, offset=0, symbol=None, outcome=None):
        """Retrieve manual journal entries with optional filtering"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build query with optional filters
            query = '''
                SELECT id, symbol, trade_type, entry_price, exit_price, quantity, 
                       outcome, profit_loss, trade_date, entry_time, exit_time, 
                       notes, chart_image_path, created_at, updated_at
                FROM manual_journal_entries
                WHERE 1=1
            '''
            params = []
            
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
            entries_list = [dict(zip(columns, entry)) for entry in entries]
            
            return entries_list, "Entries retrieved successfully"
            
        except sqlite3.Error as e:
            return [], f"Database error: {str(e)}"
        except Exception as e:
            return [], f"Error retrieving entries: {str(e)}"
        finally:
            if conn:
                conn.close()
    
    def get_journal_entry(self, entry_id):
        """Get a single journal entry by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, symbol, trade_type, entry_price, exit_price, quantity, 
                       outcome, profit_loss, trade_date, entry_time, exit_time, 
                       notes, chart_image_path, created_at, updated_at
                FROM manual_journal_entries
                WHERE id = ?
            ''', (entry_id,))
            
            entry = cursor.fetchone()
            
            if entry:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, entry)), "Entry found"
            else:
                return None, "Entry not found"
                
        except sqlite3.Error as e:
            return None, f"Database error: {str(e)}"
        except Exception as e:
            return None, f"Error retrieving entry: {str(e)}"
        finally:
            if conn:
                conn.close()
    
    def update_journal_entry(self, entry_id, entry_data):
        """Update an existing journal entry"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if entry exists
            cursor.execute('SELECT id FROM manual_journal_entries WHERE id = ?', (entry_id,))
            if not cursor.fetchone():
                return False, "Entry not found"
            
            # Update entry
            cursor.execute('''
                UPDATE manual_journal_entries SET
                symbol = ?, trade_type = ?, entry_price = ?, exit_price = ?, 
                quantity = ?, outcome = ?, profit_loss = ?, trade_date = ?, 
                entry_time = ?, exit_time = ?, notes = ?, chart_image_path = ?
                WHERE id = ?
            ''', (
                entry_data.get('symbol', '').upper(),
                entry_data.get('trade_type', '').upper(),
                float(entry_data.get('entry_price', 0)),
                float(entry_data.get('exit_price', 0)) if entry_data.get('exit_price') else None,
                int(entry_data.get('quantity', 1)),
                entry_data.get('outcome', 'PENDING').upper(),
                float(entry_data.get('profit_loss', 0)),
                entry_data.get('trade_date'),
                entry_data.get('entry_time'),
                entry_data.get('exit_time'),
                entry_data.get('notes', ''),
                entry_data.get('chart_image_path'),
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
    
    def delete_journal_entry(self, entry_id):
        """Delete a journal entry and its associated image"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get entry to check for image file
            cursor.execute('SELECT chart_image_path FROM manual_journal_entries WHERE id = ?', (entry_id,))
            result = cursor.fetchone()
            
            if not result:
                return False, "Entry not found"
            
            image_path = result[0]
            
            # Delete database entry
            cursor.execute('DELETE FROM manual_journal_entries WHERE id = ?', (entry_id,))
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
    
    def get_journal_statistics(self):
        """Get comprehensive journal statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Overall statistics
            cursor.execute('''
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
            ''')
            overall_stats = cursor.fetchone()
            
            # Statistics by symbol
            cursor.execute('''
                SELECT 
                    symbol,
                    COUNT(*) as trades,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                    SUM(profit_loss) as pnl
                FROM manual_journal_entries
                GROUP BY symbol
                ORDER BY trades DESC
            ''')
            symbol_stats = cursor.fetchall()
            
            # Statistics by trade type
            cursor.execute('''
                SELECT 
                    trade_type,
                    COUNT(*) as trades,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                    SUM(profit_loss) as pnl
                FROM manual_journal_entries
                GROUP BY trade_type
                ORDER BY trades DESC
            ''')
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