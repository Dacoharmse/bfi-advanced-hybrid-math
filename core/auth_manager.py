#!/usr/bin/env python3
"""
User Authentication and Authorization Manager for BFI Signals
Handles user registration, login, role-based access control, and session management
"""

import sqlite3
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import session, request, jsonify, redirect, url_for
import bcrypt

class AuthManager:
    def __init__(self, db_path='ai_learning.db'):
        self.db_path = db_path
        self.init_auth_tables()
    
    def init_auth_tables(self):
        """Initialize authentication-related database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                is_active BOOLEAN DEFAULT 0,
                is_approved BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                email_verified BOOLEAN DEFAULT 0,
                verification_token TEXT,
                approved_by INTEGER,
                approved_at DATETIME,
                profile_picture TEXT,
                full_name TEXT,
                timezone TEXT DEFAULT 'UTC'
            )
        ''')
        
        # User sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE NOT NULL,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # User notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                notification_type TEXT DEFAULT 'signal',
                is_read BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                signal_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create default admin user if none exists
        cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin"')
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            # Create default admin user: admin / admin123
            admin_password = self.hash_password('admin123')
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role, is_active, is_approved, email_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('admin', 'admin@bfisignals.com', admin_password, 'admin', 1, 1, 1))
            print("✅ Default admin user created: admin / admin123")
        
        # Add new columns to existing users table if they don't exist
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN is_approved BOOLEAN DEFAULT 0')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN approved_by INTEGER')
        except sqlite3.OperationalError:
            pass  # Column already exists
            
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN approved_at DATETIME')
        except sqlite3.OperationalError:
            pass  # Column already exists
            
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN profile_picture TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists
            
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN full_name TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists
            
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN timezone TEXT DEFAULT "UTC"')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Update existing admin users to be approved
        cursor.execute('''
            UPDATE users 
            SET is_approved = 1, is_active = 1 
            WHERE role = "admin" AND (is_approved IS NULL OR is_approved = 0)
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password, password_hash):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def register_user(self, username, email, password, role='user'):
        """Register a new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user already exists
            cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
            if cursor.fetchone():
                return {'success': False, 'error': 'Username or email already exists'}
            
            # Hash password and create user
            password_hash = self.hash_password(password)
            verification_token = str(uuid.uuid4())
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role, verification_token)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, role, verification_token))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'user_id': user_id,
                'verification_token': verification_token
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def authenticate_user(self, username, password):
        """Authenticate user login"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, password_hash, role, is_active, is_approved 
                FROM users WHERE username = ? OR email = ?
            ''', (username, username))
            
            user = cursor.fetchone()
            
            if not user:
                return {'success': False, 'error': 'Invalid username or password'}
            
            user_id, username, email, password_hash, role, is_active, is_approved = user
            
            if not is_active:
                return {'success': False, 'error': 'Account is deactivated'}
            
            if not is_approved:
                return {'success': False, 'error': 'Account is pending admin approval'}
            
            if not self.verify_password(password, password_hash):
                return {'success': False, 'error': 'Invalid username or password'}
            
            # Update last login
            cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                          (datetime.now(), user_id))
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'user': {
                    'id': user_id,
                    'username': username,
                    'email': email,
                    'role': role
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_session(self, user_id, ip_address=None, user_agent=None):
        """Create a new user session"""
        try:
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(days=30)  # 30-day session
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_sessions (user_id, session_token, expires_at, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, session_token, expires_at, ip_address, user_agent))
            
            conn.commit()
            conn.close()
            
            return session_token
            
        except Exception as e:
            print(f"Error creating session: {e}")
            return None
    
    def validate_session(self, session_token):
        """Validate a session token"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.id, u.username, u.email, u.role, u.is_active, s.expires_at
                FROM users u
                JOIN user_sessions s ON u.id = s.user_id
                WHERE s.session_token = ? AND s.expires_at > ?
            ''', (session_token, datetime.now()))
            
            session_data = cursor.fetchone()
            conn.close()
            
            if session_data:
                user_id, username, email, role, is_active, expires_at = session_data
                
                if is_active:
                    return {
                        'valid': True,
                        'user': {
                            'id': user_id,
                            'username': username,
                            'email': email,
                            'role': role
                        }
                    }
            
            return {'valid': False}
            
        except Exception as e:
            print(f"Error validating session: {e}")
            return {'valid': False}
    
    def logout_user(self, session_token):
        """Logout user by invalidating session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM user_sessions WHERE session_token = ?', (session_token,))
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error logging out user: {e}")
            return False
    
    def get_user_by_id(self, user_id):
        """Get user details by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, role, is_active, created_at, last_login
                FROM users WHERE id = ?
            ''', (user_id,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'role': user[3],
                    'is_active': user[4],
                    'created_at': user[5],
                    'last_login': user[6]
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def create_notification(self, user_id, title, message, notification_type='signal', signal_id=None):
        """Create a notification for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_notifications (user_id, title, message, notification_type, signal_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, title, message, notification_type, signal_id))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error creating notification: {e}")
            return False
    
    def get_user_notifications(self, user_id, unread_only=False):
        """Get notifications for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT id, title, message, notification_type, is_read, created_at, signal_id
                FROM user_notifications 
                WHERE user_id = ?
            '''
            
            if unread_only:
                query += ' AND is_read = 0'
            
            query += ' ORDER BY created_at DESC LIMIT 50'
            
            cursor.execute(query, (user_id,))
            notifications = cursor.fetchall()
            conn.close()
            
            return [{
                'id': n[0],
                'title': n[1],
                'message': n[2],
                'type': n[3],
                'is_read': n[4],
                'created_at': n[5],
                'signal_id': n[6]
            } for n in notifications]
            
        except Exception as e:
            print(f"Error getting notifications: {e}")
            return []
    
    def mark_notification_read(self, notification_id, user_id):
        """Mark a notification as read"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE user_notifications 
                SET is_read = 1 
                WHERE id = ? AND user_id = ?
            ''', (notification_id, user_id))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            return False
    
    def get_all_users(self, include_admins=True):
        """Get all users for admin management"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT id, username, email, role, is_active, is_approved, created_at, last_login
                FROM users
            '''
            
            if not include_admins:
                query += ' WHERE role != "admin"'
            
            query += ' ORDER BY created_at DESC'
            
            cursor.execute(query)
            users = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'role': user[3],
                    'is_active': bool(user[4]),
                    'is_approved': bool(user[5]),
                    'created_at': user[6],
                    'last_login': user[7]
                }
                for user in users
            ]
            
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
    
    def get_pending_users(self):
        """Get users pending approval"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, created_at
                FROM users 
                WHERE is_approved = 0 AND role != "admin"
                ORDER BY created_at ASC
            ''')
            
            users = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'created_at': user[3]
                }
                for user in users
            ]
            
        except Exception as e:
            print(f"Error getting pending users: {e}")
            return []
    
    def approve_user(self, user_id, approved_by_admin_id):
        """Approve a user registration"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET is_approved = 1, is_active = 1, approved_by = ?, approved_at = ?
                WHERE id = ? AND role != "admin"
            ''', (approved_by_admin_id, datetime.now(), user_id))
            
            if cursor.rowcount > 0:
                # Create welcome notification for the user
                self.create_notification(
                    user_id=user_id,
                    title="🎉 Account Approved!",
                    message="Your account has been approved by an administrator. Welcome to BFI Signals!",
                    notification_type="system"
                )
                
                conn.commit()
                conn.close()
                return True
            else:
                conn.close()
                return False
            
        except Exception as e:
            print(f"Error approving user: {e}")
            return False
    
    def reject_user(self, user_id):
        """Reject a user registration (delete the user)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete user sessions first
            cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
            
            # Delete user notifications
            cursor.execute('DELETE FROM user_notifications WHERE user_id = ?', (user_id,))
            
            # Delete the user
            cursor.execute('DELETE FROM users WHERE id = ? AND role != "admin"', (user_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                return True
            else:
                conn.close()
                return False
            
        except Exception as e:
            print(f"Error rejecting user: {e}")
            return False
    
    def admin_create_user(self, username, email, password, role='user', admin_id=None):
        """Admin creates a new user (pre-approved)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user already exists
            cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
            if cursor.fetchone():
                return {'success': False, 'error': 'Username or email already exists'}
            
            # Hash password and create user
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (
                    username, email, password_hash, role, is_active, is_approved, 
                    email_verified, approved_by, approved_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, role, 1, 1, 1, admin_id, datetime.now()))
            
            user_id = cursor.lastrowid
            
            # Create welcome notification
            self.create_notification(
                user_id=user_id,
                title="🎉 Welcome to BFI Signals!",
                message="Your account has been created by an administrator. You can now access all features.",
                notification_type="system"
            )
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'user_id': user_id,
                'message': 'User created successfully'
            }
            
        except Exception as e:
            print(f"Error creating user: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_user_role(self, user_id, new_role, admin_id):
        """Update a user's role"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET role = ?
                WHERE id = ? AND id != ?
            ''', (new_role, user_id, admin_id))  # Prevent admin from changing their own role
            
            if cursor.rowcount > 0:
                # Create notification for role change
                role_name = "Administrator" if new_role == "admin" else "User"
                self.create_notification(
                    user_id=user_id,
                    title="🔄 Role Updated",
                    message=f"Your account role has been updated to {role_name}.",
                    notification_type="system"
                )
                
                conn.commit()
                conn.close()
                return True
            else:
                conn.close()
                return False
            
        except Exception as e:
            print(f"Error updating user role: {e}")
            return False
    
    def deactivate_user(self, user_id, admin_id):
        """Deactivate a user account"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET is_active = 0
                WHERE id = ? AND id != ?
            ''', (user_id, admin_id))  # Prevent admin from deactivating themselves
            
            if cursor.rowcount > 0:
                # Delete all user sessions to log them out
                cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
                
                conn.commit()
                conn.close()
                return True
            else:
                conn.close()
                return False
            
        except Exception as e:
            print(f"Error deactivating user: {e}")
            return False
    
    def reactivate_user(self, user_id):
        """Reactivate a user account"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET is_active = 1
                WHERE id = ?
            ''', (user_id,))
            
            if cursor.rowcount > 0:
                # Create reactivation notification
                self.create_notification(
                    user_id=user_id,
                    title="🔄 Account Reactivated",
                    message="Your account has been reactivated by an administrator.",
                    notification_type="system"
                )
                
                conn.commit()
                conn.close()
                return True
            else:
                conn.close()
                return False
            
        except Exception as e:
            print(f"Error reactivating user: {e}")
            return False
    
    def get_user_profile(self, user_id):
        """Get complete user profile information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, role, is_active, created_at, last_login,
                       profile_picture, full_name, timezone, email_verified, is_approved
                FROM users WHERE id = ?
            ''', (user_id,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                from datetime import datetime
                # Convert string dates to datetime objects if they exist
                created_at = None
                if user[5]:
                    try:
                        created_at = datetime.strptime(user[5], '%Y-%m-%d %H:%M:%S')
                    except:
                        created_at = datetime.now()
                
                last_login = None  
                if user[6]:
                    try:
                        last_login = datetime.strptime(user[6], '%Y-%m-%d %H:%M:%S')
                    except:
                        last_login = datetime.now()
                
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'role': user[3],
                    'is_active': bool(user[4]),
                    'created_at': created_at,
                    'last_login': last_login,
                    'profile_picture': user[7],
                    'full_name': user[8] or user[1],  # fallback to username
                    'timezone': user[9] or 'UTC',
                    'email_verified': bool(user[10]),
                    'is_approved': bool(user[11]),
                    'notification_preferences': {
                        'email_notifications': True,
                        'push_notifications': True,
                        'signal_alerts': True,
                        'trading_updates': True
                    }
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None
    
    def update_user_profile(self, user_id, profile_data):
        """Update user profile information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build dynamic update query based on provided data
            update_fields = []
            values = []
            
            allowed_fields = ['username', 'email', 'full_name', 'timezone', 'profile_picture']
            
            for field in allowed_fields:
                if field in profile_data:
                    update_fields.append(f"{field} = ?")
                    values.append(profile_data[field])
            
            if not update_fields:
                return {'success': False, 'error': 'No valid fields to update'}
            
            # Check for username/email uniqueness if being updated
            if 'username' in profile_data:
                cursor.execute('SELECT id FROM users WHERE username = ? AND id != ?', 
                             (profile_data['username'], user_id))
                if cursor.fetchone():
                    return {'success': False, 'error': 'Username already exists'}
            
            if 'email' in profile_data:
                cursor.execute('SELECT id FROM users WHERE email = ? AND id != ?', 
                             (profile_data['email'], user_id))
                if cursor.fetchone():
                    return {'success': False, 'error': 'Email already exists'}
            
            # Add user_id to values for WHERE clause
            values.append(user_id)
            
            # Execute update
            update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(update_query, values)
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                
                # Create notification for profile update
                self.create_notification(
                    user_id=user_id,
                    title="✅ Profile Updated",
                    message="Your profile information has been updated successfully.",
                    notification_type="system"
                )
                
                return {'success': True, 'message': 'Profile updated successfully'}
            else:
                conn.close()
                return {'success': False, 'error': 'User not found'}
            
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return {'success': False, 'error': str(e)}
    
    def change_user_password(self, user_id, current_password, new_password):
        """Change user password"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current password hash
            cursor.execute('SELECT password_hash FROM users WHERE id = ?', (user_id,))
            result = cursor.fetchone()
            
            if not result:
                return {'success': False, 'error': 'User not found'}
            
            current_hash = result[0]
            
            # Verify current password
            if not self.verify_password(current_password, current_hash):
                return {'success': False, 'error': 'Current password is incorrect'}
            
            # Hash new password and update
            new_hash = self.hash_password(new_password)
            cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', 
                          (new_hash, user_id))
            
            if cursor.rowcount > 0:
                # Create notification for password change
                self.create_notification(
                    user_id=user_id,
                    title="🔒 Password Changed",
                    message="Your password has been changed successfully.",
                    notification_type="security"
                )
                
                conn.commit()
                conn.close()
                return {'success': True, 'message': 'Password changed successfully'}
            else:
                conn.close()
                return {'success': False, 'error': 'Failed to update password'}
            
        except Exception as e:
            print(f"Error changing password: {e}")
            return {'success': False, 'error': str(e)}
    
    def admin_change_user_password(self, user_id, new_password, admin_id):
        """Admin changes user password (no current password required)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verify admin permissions
            cursor.execute('SELECT role FROM users WHERE id = ?', (admin_id,))
            admin_result = cursor.fetchone()
            if not admin_result or admin_result[0] != 'admin':
                return {'success': False, 'error': 'Insufficient permissions'}
            
            # Check if target user exists
            cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
            user_result = cursor.fetchone()
            if not user_result:
                return {'success': False, 'error': 'User not found'}
            
            # Hash new password and update
            new_hash = self.hash_password(new_password)
            cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', 
                          (new_hash, user_id))
            
            if cursor.rowcount > 0:
                # Create notification for password change
                self.create_notification(
                    user_id=user_id,
                    title="🔒 Password Reset by Administrator",
                    message="Your password has been reset by an administrator. Please log in with your new password.",
                    notification_type="security"
                )
                
                # Delete all user sessions to force re-login
                cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
                
                conn.commit()
                conn.close()
                return {'success': True, 'message': 'Password changed successfully'}
            else:
                conn.close()
                return {'success': False, 'error': 'Failed to update password'}
            
        except Exception as e:
            print(f"Error changing password: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_notification_preferences(self, user_id, preferences):
        """Update user notification preferences"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # For now, we'll store preferences as JSON in a new column
            # In a more complex setup, you'd have a separate table
            import json
            preferences_json = json.dumps(preferences)
            
            # Add notification_preferences column if it doesn't exist
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN notification_preferences TEXT')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            cursor.execute('''
                UPDATE users SET notification_preferences = ? WHERE id = ?
            ''', (preferences_json, user_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                return {'success': True, 'message': 'Notification preferences updated'}
            else:
                conn.close()
                return {'success': False, 'error': 'User not found'}
            
        except Exception as e:
            print(f"Error updating notification preferences: {e}")
            return {'success': False, 'error': str(e)}
    
    def initiate_password_reset(self, email_or_username):
        """Initiate password reset process by sending email"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find user by email or username
            cursor.execute('''
                SELECT id, username, email FROM users 
                WHERE email = ? OR username = ?
            ''', (email_or_username, email_or_username))
            
            user = cursor.fetchone()
            conn.close()
            
            if not user:
                # Don't reveal whether email exists for security
                return {'success': True, 'message': 'If an account with that email exists, you will receive a password reset link.'}
            
            user_id, username, email = user
            
            # Generate reset token using email service
            from email_config import email_service
            token_result = email_service.generate_password_reset_token(user_id)
            
            if not token_result['success']:
                return {'success': False, 'error': 'Failed to generate reset token'}
            
            # Send reset email
            email_result = email_service.send_password_reset_email(email, token_result['token'], username)
            
            if email_result['success']:
                return {'success': True, 'message': 'Password reset link has been sent to your email.'}
            else:
                return {'success': False, 'error': 'Failed to send reset email'}
                
        except Exception as e:
            print(f"Error initiating password reset: {e}")
            return {'success': False, 'error': 'An error occurred while processing your request'}
    
    def reset_password_with_token(self, token, new_password):
        """Reset password using a valid token"""
        try:
            from email_config import email_service
            
            # Validate token
            token_data = email_service.validate_password_reset_token(token)
            
            if not token_data['valid']:
                return {'success': False, 'error': 'Invalid or expired reset token'}
            
            user_id = token_data['user_id']
            
            # Hash new password and update
            new_hash = self.hash_password(new_password)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', 
                          (new_hash, user_id))
            
            if cursor.rowcount > 0:
                # Mark token as used
                email_service.use_password_reset_token(token)
                
                # Create notification for password reset
                self.create_notification(
                    user_id=user_id,
                    title="🔒 Password Reset Successful",
                    message="Your password has been reset successfully. If this wasn't you, please contact support immediately.",
                    notification_type="security"
                )
                
                # Delete all user sessions to force re-login
                cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
                
                conn.commit()
                conn.close()
                return {'success': True, 'message': 'Password has been reset successfully'}
            else:
                conn.close()
                return {'success': False, 'error': 'Failed to update password'}
                
        except Exception as e:
            print(f"Error resetting password: {e}")
            return {'success': False, 'error': 'An error occurred while resetting your password'}
    
    def get_notification_preferences(self, user_id):
        """Get user notification preferences"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT notification_preferences FROM users WHERE id = ?', (user_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                import json
                return json.loads(result[0])
            else:
                # Return default preferences
                return {
                    'signalNotifications': True,
                    'marketNotifications': False,
                    'systemNotifications': True,
                    'emailNotifications': False
                }
            
        except Exception as e:
            print(f"Error getting notification preferences: {e}")
            return {
                'signalNotifications': True,
                'marketNotifications': False,
                'systemNotifications': True,
                'emailNotifications': False
            }

# Authentication decorators
def login_required(f):
    """Decorator to require login for route access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role for route access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        if session.get('user_role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# Initialize auth manager
auth_manager = AuthManager()