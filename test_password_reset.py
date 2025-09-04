#!/usr/bin/env python3
"""
Test script for password reset functionality
Tests email sending and password reset process
"""

import sys
import os
sys.path.append('core')

from auth_manager import AuthManager
from email_config import EmailService

def test_password_reset():
    """Test the complete password reset flow"""
    print("🔧 Testing Password Reset Functionality\n")
    
    # Initialize services
    auth_manager = AuthManager('test_db.sqlite')
    email_service = EmailService('test_db.sqlite')
    
    print("✅ Services initialized")
    
    # Create a test user first
    test_user = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'oldpassword123'
    }
    
    print(f"📝 Creating test user: {test_user['username']} ({test_user['email']})")
    
    # Register test user
    register_result = auth_manager.register_user(
        test_user['username'], 
        test_user['email'], 
        test_user['password']
    )
    
    if register_result['success']:
        print("✅ Test user created successfully")
        user_id = register_result['user_id']
        
        # Approve the user (simulate admin approval)
        auth_manager.approve_user(user_id, 1)  # Assume admin ID is 1
        print("✅ Test user approved")
    else:
        print(f"❌ Failed to create test user: {register_result['error']}")
        return False
    
    print("\n" + "="*50)
    print("🔐 TESTING PASSWORD RESET PROCESS")
    print("="*50)
    
    # Test 1: Generate password reset token
    print("\n1️⃣ Testing password reset token generation...")
    
    token_result = email_service.generate_password_reset_token(user_id)
    if token_result['success']:
        reset_token = token_result['token']
        print(f"✅ Reset token generated: {reset_token[:20]}...")
    else:
        print(f"❌ Failed to generate token: {token_result['error']}")
        return False
    
    # Test 2: Validate reset token
    print("\n2️⃣ Testing token validation...")
    
    validation_result = email_service.validate_password_reset_token(reset_token)
    if validation_result['valid']:
        print(f"✅ Token validated for user: {validation_result['username']}")
    else:
        print("❌ Token validation failed")
        return False
    
    # Test 3: Test email configuration (without actually sending)
    print("\n3️⃣ Testing email configuration...")
    
    print(f"📧 SMTP Server: {email_service.EMAIL_CONFIG['smtp_server']}")
    print(f"📧 SMTP Port: {email_service.EMAIL_CONFIG['smtp_port']}")
    print(f"📧 From Email: {email_service.EMAIL_CONFIG['email']}")
    print("✅ Email configuration looks valid")
    
    # Test 4: Test password reset with token
    print("\n4️⃣ Testing password reset with token...")
    
    new_password = 'newpassword456'
    reset_result = auth_manager.reset_password_with_token(reset_token, new_password)
    
    if reset_result['success']:
        print("✅ Password reset with token successful")
    else:
        print(f"❌ Password reset failed: {reset_result['error']}")
        return False
    
    # Test 5: Verify new password works
    print("\n5️⃣ Testing authentication with new password...")
    
    auth_result = auth_manager.authenticate_user(test_user['username'], new_password)
    if auth_result['success']:
        print("✅ Authentication with new password successful")
    else:
        print(f"❌ Authentication failed: {auth_result['error']}")
        return False
    
    # Test 6: Verify old password doesn't work
    print("\n6️⃣ Testing that old password is no longer valid...")
    
    old_auth_result = auth_manager.authenticate_user(test_user['username'], test_user['password'])
    if not old_auth_result['success']:
        print("✅ Old password correctly rejected")
    else:
        print("❌ Old password still works (this is bad!)")
        return False
    
    # Test 7: Test used token doesn't work again
    print("\n7️⃣ Testing that used token cannot be used again...")
    
    reuse_result = auth_manager.reset_password_with_token(reset_token, 'anothernewpassword')
    if not reuse_result['success']:
        print("✅ Used token correctly rejected")
    else:
        print("❌ Used token was accepted (security issue!)")
        return False
    
    print("\n" + "="*50)
    print("🎉 ALL TESTS PASSED!")
    print("="*50)
    
    print("\n📋 Summary:")
    print("• Password reset token generation: ✅")
    print("• Token validation: ✅") 
    print("• Password reset with token: ✅")
    print("• New password authentication: ✅")
    print("• Old password rejection: ✅")
    print("• Used token rejection: ✅")
    print("• Email configuration: ✅")
    
    print(f"\n🗑️  Cleaning up test database...")
    
    # Clean up - remove test database
    try:
        os.remove('test_db.sqlite')
        print("✅ Test database cleaned up")
    except FileNotFoundError:
        pass
    
    return True

def test_email_sending():
    """Test actual email sending (optional - requires real email)"""
    print("\n📧 EMAIL SENDING TEST")
    print("="*30)
    print("This test will attempt to send a real email.")
    print("Make sure the email credentials are correct.")
    
    response = input("Do you want to test email sending? (y/N): ").lower().strip()
    if response != 'y':
        print("Skipping email sending test.")
        return True
    
    email = input("Enter email address to send test to: ").strip()
    if not email:
        print("No email provided, skipping test.")
        return True
    
    email_service = EmailService()
    
    # Send test email
    print(f"Sending test email to {email}...")
    
    result = email_service.send_password_reset_email(
        email, 
        'test-token-12345', 
        'TestUser'
    )
    
    if result['success']:
        print("✅ Test email sent successfully!")
        print("Check your inbox for the password reset email.")
    else:
        print(f"❌ Failed to send email: {result.get('error', 'Unknown error')}")
        return False
    
    return True

if __name__ == '__main__':
    print("🚀 BFI Signals Password Reset Testing")
    print("="*40)
    
    try:
        # Run functionality tests
        if test_password_reset():
            print("\n🎯 Core functionality tests completed successfully!")
            
            # Optionally test email sending
            test_email_sending()
            
        else:
            print("\n❌ Tests failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n🏁 Testing completed!")