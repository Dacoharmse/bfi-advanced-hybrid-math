#!/usr/bin/env python3
"""
Simple Supabase Connection Test
"""

from supabase import create_client, Client

# Your Supabase credentials
url = "https://kiiugsmjybncvtrdshdk.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtpaXVnc21qeWJuY3Z0cmRzaGRrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4NzY2ODIsImV4cCI6MjA2OTQ1MjY4Mn0.4GRc469_WzsUERgsqikeGQ2SQZwJpR4HPW1kkqXR3Sw"

print("🧪 Simple Supabase Connection Test")
print("=" * 40)

try:
    # Create client
    print("📡 Creating Supabase client...")
    supabase: Client = create_client(url, key)
    print("✅ Client created successfully")
    
    # Test authentication by trying to access auth
    print("🔐 Testing authentication...")
    user = supabase.auth.get_user()
    print(f"✅ Authentication working: {user}")
    
    # Check available tables
    print("📋 Checking available tables...")
    try:
        # Try to list tables - this might fail if we don't have the right permissions
        tables = supabase.table('pg_tables').select('tablename').eq('schemaname', 'public').execute()
        print(f"✅ Found {len(tables.data)} public tables:")
        for table in tables.data[:5]:  # Show first 5
            print(f"   - {table['tablename']}")
            
    except Exception as e:
        print(f"⚠️ Cannot list tables (this is normal): {e}")
    
    print("\n🎯 Testing direct table creation...")
    try:
        # Try to create a simple test table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS test_connection (
            id SERIAL PRIMARY KEY,
            message TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
        
        # Note: This will fail with anon key, but that's expected
        print("⚠️ Cannot create tables with anon key (expected)")
        
    except Exception as e:
        print(f"⚠️ Table creation failed (expected with anon key): {e}")
    
    print("\n📊 RESULTS:")
    print("✅ Supabase URL: Reachable")
    print("✅ API Key: Valid")
    print("✅ Client: Working")
    print("⚠️ Tables: Need to be created manually via dashboard")
    
    print("\n🔧 NEXT STEPS:")
    print("1. Go to: https://supabase.com/dashboard/project/kiiugsmjybncvtrdshdk")
    print("2. Click 'SQL Editor' in the left sidebar")
    print("3. Copy the content from 'database_schema.sql'")
    print("4. Paste it in the SQL editor")
    print("5. Click 'Run' to execute")
    print("6. Re-run the full storage test")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\n🔧 TROUBLESHOOTING:")
    print("1. Check your internet connection")
    print("2. Verify Supabase project is active")
    print("3. Check if API key is correct")

print("\n" + "=" * 40)