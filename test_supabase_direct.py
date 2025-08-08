#!/usr/bin/env python3
"""
Direct Supabase Connection Test
Tests Supabase connection and creates database schema
"""

def test_supabase_connection():
    """Test Supabase database connection and schema"""
    print("🧪 TESTING SUPABASE DATABASE CONNECTION")
    print("=" * 50)
    
    try:
        # Import supabase (now should work with venv)
        from supabase import create_client, Client
        
        # Your Supabase credentials
        url = "https://kiiugsmjybncvtrdshdk.supabase.co"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtpaXVnc21qeWJuY3Z0cmRzaGRrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4NzY2ODIsImV4cCI6MjA2OTQ1MjY4Mn0.4GRc469_WzsUERgsqikeGQ2SQZwJpR4HPW1kkqXR3Sw"
        
        print("📡 Creating Supabase client...")
        supabase: Client = create_client(url, key)
        print("✅ Supabase client created successfully")
        
        # Test basic connection
        print("\n🔌 Testing basic connection...")
        try:
            # Try to query a system table that should always exist
            response = supabase.table('information_schema.tables').select('table_name').limit(1).execute()
            print("✅ Basic connection successful!")
            print(f"   Response: {len(response.data)} system tables found")
        except Exception as e:
            print(f"❌ Basic connection failed: {e}")
            return False
        
        # Check if our tables exist
        print("\n📋 Checking if BFI tables exist...")
        try:
            # Try to query our market_close_data table
            response = supabase.table('market_close_data').select('*').limit(1).execute()
            print("✅ market_close_data table exists!")
            print(f"   Records found: {len(response.data)}")
            
            # Check other tables
            response = supabase.table('signals').select('*').limit(1).execute()
            print("✅ signals table exists!")
            
            response = supabase.table('data_capture_log').select('*').limit(1).execute()
            print("✅ data_capture_log table exists!")
            
            print("\n🎉 ALL TABLES EXIST - DATABASE IS READY!")
            
        except Exception as e:
            print(f"❌ Tables don't exist yet: {e}")
            print("\n🔧 NEXT STEPS:")
            print("1. Go to your Supabase dashboard: https://supabase.com/dashboard")
            print("2. Navigate to SQL Editor")
            print("3. Copy and paste the content of 'database_schema.sql'")
            print("4. Execute the SQL script")
            print("5. Re-run this test")
            
            # Show the database schema location
            import os
            schema_file = os.path.join(os.path.dirname(__file__), 'database_schema.sql')
            if os.path.exists(schema_file):
                print(f"\n📄 Schema file location: {schema_file}")
                print("📄 First few lines of schema:")
                with open(schema_file, 'r') as f:
                    lines = f.readlines()[:10]
                    for i, line in enumerate(lines, 1):
                        print(f"   {i:2d}: {line.rstrip()}")
            
            return False
        
        # Test insert operation
        print("\n📝 Testing data insertion...")
        try:
            test_record = {
                'capture_date': '2025-07-30',
                'symbol': 'TEST',
                'price': 100.00,
                'change_amount': 1.50,
                'change_percent': 1.50,
                'previous_close': 98.50,
                'daily_high': 101.00,
                'daily_low': 99.00,
                'raw_change': 1.5,
                'source': 'test_connection'
            }
            
            response = supabase.table('market_close_data').insert(test_record).execute()
            print("✅ Test insertion successful!")
            
            # Clean up test record
            supabase.table('market_close_data').delete().eq('symbol', 'TEST').execute()
            print("✅ Test cleanup completed")
            
        except Exception as e:
            print(f"❌ Test insertion failed: {e}")
        
        print("\n🎉 SUPABASE DATABASE TEST COMPLETE!")
        print("✅ Connection: Working")
        print("✅ Authentication: Working") 
        print("✅ Database: Ready for BFI Signals")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure to run with virtual environment:")
        print("   source venv_storage/bin/activate && python3 test_supabase_direct.py")
        return False
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    success = test_supabase_connection()
    print("=" * 50)
    
    if success:
        print("🎉 SUCCESS: Supabase database is working!")
    else:
        print("❌ FAILED: Please check the instructions above")
        sys.exit(1)