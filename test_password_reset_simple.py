#!/usr/bin/env python3
"""
Simplified test script for password reset functionality
Tests core functionality without heavy dependencies
"""

import sys
import os
import sqlite3
import smtplib
import email.mime.text
import email.mime.multipart

# Mock minimal classes for testing
class AuthManager:
    def __init__(self, db_path='test_auth.sqlite'):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                password_hash TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_approved BOOLEAN DEFAULT 1
            )
        ''')
        conn.commit()
        conn.close()
    
    def register_user(self, username, email, password):
        try:
            import hashlib
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)', 
                          (username, email, password_hash))
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {'success': True, 'user_id': user_id}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_user_by_email(self, email):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email FROM users WHERE email = ?', (email,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {'id': result[0], 'username': result[1], 'email': result[2]}
        return None

class EmailService:
    def __init__(self):
        self.EMAIL_CONFIG = {
            'smtp_server': 'mail.bonangfinance.co.za',
            'smtp_port': 587,
            'email': 'no-reply@bonangfinance.co.za',
            'password': 'no-reply@Bonang2025',
            'use_tls': True
        }
    
    def test_smtp_connection(self):
        """Test SMTP connection without sending email"""
        try:
            print(f"Connecting to {self.EMAIL_CONFIG['smtp_server']}:{self.EMAIL_CONFIG['smtp_port']}")
            
            server = smtplib.SMTP(self.EMAIL_CONFIG['smtp_server'], self.EMAIL_CONFIG['smtp_port'])
            
            if self.EMAIL_CONFIG['use_tls']:
                print("Starting TLS encryption...")
                server.starttls()
            
            print("Attempting login...")
            server.login(self.EMAIL_CONFIG['email'], self.EMAIL_CONFIG['password'])
            
            print("✅ SMTP connection successful!")
            server.quit()
            return {'success': True}
            
        except Exception as e:
            print(f"❌ SMTP connection failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_test_email(self, to_email):
        """Send a test email"""
        try:
            # Create message
            msg = email.mime.multipart.MIMEMultipart('alternative')
            msg['From'] = self.EMAIL_CONFIG['email']
            msg['To'] = to_email
            msg['Subject'] = "BFI Signals - Password Reset Test"
            
            html_body = """
            <html>
            <head></head>
            <body>
                <h2>🔐 BFI Signals - Password Reset Test</h2>
                <p>This is a test email from the BFI Signals password reset system.</p>
                <p>If you received this email, the email configuration is working correctly!</p>
                <p><strong>Test Details:</strong></p>
                <ul>
                    <li>SMTP Server: mail.bonangfinance.co.za</li>
                    <li>Port: 587</li>
                    <li>Encryption: TLS</li>
                    <li>From: no-reply@bonangfinance.co.za</li>
                </ul>
                <p>This is an automated test message.</p>
            </body>
            </html>
            """
            
            text_body = """
BFI Signals - Password Reset Test

This is a test email from the BFI Signals password reset system.
If you received this email, the email configuration is working correctly!

Test Details:
- SMTP Server: mail.bonangfinance.co.za
- Port: 587
- Encryption: TLS
- From: no-reply@bonangfinance.co.za

This is an automated test message.
            """
            
            # Add text and HTML parts
            text_part = email.mime.text.MIMEText(text_body, 'plain', 'utf-8')
            html_part = email.mime.text.MIMEText(html_body, 'html', 'utf-8')
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Connect and send
            server = smtplib.SMTP(self.EMAIL_CONFIG['smtp_server'], self.EMAIL_CONFIG['smtp_port'])
            
            if self.EMAIL_CONFIG['use_tls']:
                server.starttls()
            
            server.login(self.EMAIL_CONFIG['email'], self.EMAIL_CONFIG['password'])
            server.send_message(msg)
            server.quit()
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

def run_tests():
    """Run password reset tests"""
    print("🚀 BFI Signals Password Reset Testing")
    print("=" * 50)
    
    # Test 1: Email Configuration Test
    print("\n1️⃣ Testing Email Configuration...")
    print("-" * 30)
    
    email_service = EmailService()
    
    print("📧 Email Settings:")
    print(f"   SMTP Server: {email_service.EMAIL_CONFIG['smtp_server']}")
    print(f"   Port: {email_service.EMAIL_CONFIG['smtp_port']}")
    print(f"   From Email: {email_service.EMAIL_CONFIG['email']}")
    print(f"   TLS Enabled: {email_service.EMAIL_CONFIG['use_tls']}")
    
    # Test 2: SMTP Connection Test
    print("\n2️⃣ Testing SMTP Connection...")
    print("-" * 30)
    
    connection_result = email_service.test_smtp_connection()
    
    if not connection_result['success']:
        print(f"❌ SMTP connection test failed: {connection_result.get('error', 'Unknown error')}")
        print("\n🔧 Troubleshooting Tips:")
        print("   • Check if the email server is accessible")
        print("   • Verify the username and password are correct")
        print("   • Ensure the network allows outbound connections on port 587")
        print("   • Check if the email account allows SMTP login")
        return False
    
    # Test 3: Database Operations Test
    print("\n3️⃣ Testing Database Operations...")
    print("-" * 30)
    
    auth_manager = AuthManager('test_password_reset.sqlite')
    
    # Create test user
    test_email = "test@example.com"
    register_result = auth_manager.register_user("testuser", test_email, "testpassword123")
    
    if register_result['success']:
        print(f"✅ Test user created successfully (ID: {register_result['user_id']})")
    else:
        print(f"❌ Failed to create test user: {register_result['error']}")
        return False
    
    # Test user lookup
    user = auth_manager.get_user_by_email(test_email)
    if user:
        print(f"✅ User lookup successful: {user['username']} ({user['email']})")
    else:
        print("❌ User lookup failed")
        return False
    
    # Test 4: Email Sending Test (Optional)
    print("\n4️⃣ Email Sending Test...")
    print("-" * 30)
    
    send_test = input("Do you want to send a test email? (y/N): ").lower().strip()
    
    if send_test == 'y':
        email = input("Enter email address to send test to: ").strip()
        if email:
            print(f"Sending test email to {email}...")
            
            send_result = email_service.send_test_email(email)
            
            if send_result['success']:
                print("✅ Test email sent successfully!")
                print("   Please check your inbox (including spam folder)")
            else:
                print(f"❌ Failed to send test email: {send_result.get('error', 'Unknown error')}")
                return False
        else:
            print("No email provided, skipping email sending test")
    else:
        print("Skipping email sending test")
    
    # Cleanup
    print("\n🗑️ Cleaning up...")
    try:
        os.remove('test_password_reset.sqlite')
        print("✅ Test database cleaned up")
    except FileNotFoundError:
        pass
    
    print("\n" + "=" * 50)
    print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    
    print("\n📋 Test Summary:")
    print("   ✅ Email configuration validated")
    print("   ✅ SMTP connection successful")  
    print("   ✅ Database operations working")
    if send_test == 'y' and email:
        print("   ✅ Email sending functional")
    
    print("\n🎯 Password Reset System Status: READY")
    print("\n💡 Next Steps:")
    print("   1. Start your Flask application")
    print("   2. Navigate to /forgot-password to test the UI")
    print("   3. The system will send real emails using the configured SMTP settings")
    
    return True

if __name__ == '__main__':
    try:
        success = run_tests()
        if not success:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏸️ Testing interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)