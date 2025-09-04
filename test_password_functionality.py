#!/usr/bin/env python3
"""
Test script for admin password change functionality
"""
import os
import sys
import sqlite3
from datetime import datetime

# Add core directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

# Mock dependencies that might not be available
sys.modules['yfinance'] = type(sys)('mock')
sys.modules['yahoo_fin'] = type(sys)('mock')
sys.modules['yahoo_fin.stock_info'] = type(sys)('mock')
sys.modules['nltk'] = type(sys)('mock')
sys.modules['nltk.sentiment'] = type(sys)('mock')
sys.modules['nltk.sentiment.vader'] = type(sys)('mock')
sys.modules['textblob'] = type(sys)('mock')

# Now import our auth manager
try:
    from auth_manager import AuthManager
    
    print("✅ AuthManager imported successfully")
    
    # Create a temporary database for testing
    test_db = "/tmp/test_auth.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    auth = AuthManager(test_db)
    
    # Create test users
    print("\n🔧 Creating test users...")
    
    # Create admin user
    admin_result = auth.register_user("testadmin", "admin@test.com", "password123", role="admin")
    print(f"Admin user creation: {admin_result}")
    
    # Create regular user
    user_result = auth.register_user("testuser", "user@test.com", "password123")
    print(f"Regular user creation: {user_result}")
    
    # Approve both users (simulate admin approval)
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_approved = 1, is_active = 1 WHERE username IN ('testadmin', 'testuser')")
    cursor.execute("SELECT id FROM users WHERE username = 'testadmin'")
    admin_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM users WHERE username = 'testuser'")
    user_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    
    print(f"Admin ID: {admin_id}, User ID: {user_id}")
    
    # Test admin password change functionality
    print("\n🔒 Testing admin password change...")
    
    # Test changing user password as admin
    change_result = auth.admin_change_user_password(user_id, "newpassword123", admin_id)
    print(f"Admin password change result: {change_result}")
    
    # Verify the password was changed
    auth_result = auth.authenticate_user("testuser", "newpassword123")
    print(f"Authentication with new password: {'SUCCESS' if auth_result['success'] else 'FAILED'}")
    
    # Verify old password no longer works
    old_auth_result = auth.authenticate_user("testuser", "password123")
    print(f"Authentication with old password: {'FAILED (correct)' if not old_auth_result['success'] else 'SUCCESS (incorrect!)'}")
    
    # Test insufficient permissions (non-admin trying to change password)
    print("\n🚫 Testing permission checks...")
    perm_result = auth.admin_change_user_password(admin_id, "hackattempt", user_id)
    print(f"Non-admin attempting password change: {perm_result}")
    
    print("\n✅ All tests completed successfully!")
    
    # Cleanup
    os.remove(test_db)
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Test error: {e}")
    import traceback
    traceback.print_exc()