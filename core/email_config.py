#!/usr/bin/env python3
"""
Email Configuration and Service for BFI Signals
Handles email sending for password reset and notifications
"""

import smtplib
import secrets
import email.mime.text
import email.mime.multipart
from datetime import datetime, timedelta
from db_service import db_service

# Email configuration
EMAIL_CONFIG = {
    'smtp_server': 'mail.bonangfinance.co.za',
    'smtp_port': 587,
    'email': 'no-reply@bonangfinance.co.za',
    'password': 'no-reply@Bonang2025',
    'use_tls': True
}

class EmailService:
    def __init__(self):
        self.db = db_service
        self.init_password_reset_table()
    
    def init_password_reset_table(self):
        """Initialize password reset tokens table"""
        # Tables are managed in Supabase
        pass
    
    def send_email(self, to_email, subject, body_html, body_text=None):
        """Send an email using the configured SMTP server"""
        try:
            # Create message
            msg = email.mime.multipart.MIMEMultipart('alternative')
            msg['From'] = EMAIL_CONFIG['email']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text version if provided
            if body_text:
                text_part = email.mime.text.MIMEText(body_text, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML version
            html_part = email.mime.text.MIMEText(body_html, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Connect to server and send
            server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
            
            if EMAIL_CONFIG['use_tls']:
                server.starttls()
            
            server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
            server.send_message(msg)
            server.quit()
            
            return {'success': True}
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_password_reset_token(self, user_id):
        """Generate a password reset token for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute('SELECT email FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Generate token and expiry (24 hours from now)
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)
            
            # Store token in database
            cursor.execute('''
                INSERT INTO password_reset_tokens (user_id, token, expires_at)
                VALUES (?, ?, ?)
            ''', (user_id, token, expires_at))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'token': token, 'expires_at': expires_at}
            
        except Exception as e:
            print(f"Error generating reset token: {e}")
            return {'success': False, 'error': str(e)}
    
    def validate_password_reset_token(self, token):
        """Validate a password reset token"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT prt.user_id, prt.expires_at, u.email, u.username
                FROM password_reset_tokens prt
                JOIN users u ON prt.user_id = u.id
                WHERE prt.token = ? AND prt.used = 0 AND prt.expires_at > ?
            ''', (token, datetime.now()))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'valid': True,
                    'user_id': result[0],
                    'expires_at': result[1],
                    'email': result[2],
                    'username': result[3]
                }
            else:
                return {'valid': False}
                
        except Exception as e:
            print(f"Error validating reset token: {e}")
            return {'valid': False}
    
    def use_password_reset_token(self, token):
        """Mark a password reset token as used"""
        try:
            return self.db.mark_token_used(token)
            
        except Exception as e:
            print(f"Error using reset token: {e}")
            return False
    
    def send_password_reset_email(self, user_email, reset_token, username):
        """Send password reset email to user"""
        # Use production URL for live site
        import os
        base_url = os.getenv('BASE_URL', 'https://trading.bonangfinance.co.za')
        reset_url = f"{base_url}/reset-password?token={reset_token}"
        
        subject = "Password Reset - BFI Dashboard"
        
        # HTML email template
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Password Reset - BFI Dashboard</title>
    <style>
        body {{
            font-family: 'Inter', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #d4af37, #f4d03f);
            color: #000;
            padding: 30px;
            text-align: center;
            position: relative;
        }}
        .logo {{
            width: 60px;
            height: 60px;
            margin: 0 auto 15px;
            display: block;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: bold;
        }}
        .content {{
            padding: 40px 30px;
        }}
        .content h2 {{
            color: #333;
            margin-bottom: 20px;
        }}
        .reset-button {{
            display: inline-block;
            background: linear-gradient(135deg, #d4af37, #f4d03f);
            color: #000;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin: 20px 0;
        }}
        .footer {{
            background: #f8f8f8;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #666;
        }}
        .warning {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="{base_url}/static/bfi-logo.png" alt="BFI Logo" class="logo">
            <h1>BFI Dashboard</h1>
        </div>
        
        <div class="content">
            <h2>Password Reset Request</h2>
            
            <p>Hello <strong>{username}</strong>,</p>
            
            <p>We received a request to reset your password for your BFI Dashboard account. If you made this request, click the button below to reset your password:</p>
            
            <center>
                <a href="{reset_url}" class="reset-button">Reset My Password</a>
            </center>
            
            <div class="warning">
                <strong>⚠️ Security Notice:</strong>
                <ul>
                    <li>This link will expire in 24 hours</li>
                    <li>If you didn't request this reset, please ignore this email</li>
                    <li>Never share this link with anyone</li>
                </ul>
            </div>
            
            <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #666;">{reset_url}</p>
            
            <p>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
        </div>
        
        <div class="footer">
            <p>This is an automated message from BFI Dashboard.<br>
            Please do not reply to this email.</p>
            <p>&copy; 2024 BFI Dashboard. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Plain text version
        text_body = f"""
Password Reset Request - BFI Dashboard

Hello {username},

We received a request to reset your password for your BFI Dashboard account.

To reset your password, please visit this link:
{reset_url}

This link will expire in 24 hours.

If you didn't request a password reset, you can safely ignore this email.

---
BFI Dashboard Team
This is an automated message. Please do not reply.
        """
        
        return self.send_email(user_email, subject, html_body, text_body)

# Initialize email service
email_service = EmailService()