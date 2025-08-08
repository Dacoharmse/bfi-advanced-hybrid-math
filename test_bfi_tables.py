#!/usr/bin/env python3
"""
Test BFI Signals Tables in Supabase
"""

from supabase import create_client, Client

def test_bfi_tables():
    """Test if BFI tables exist and work"""
    print("🧪 TESTING BFI SIGNALS TABLES")
    print("=" * 40)
    
    # Your Supabase credentials
    url = "https://kiiugsmjybncvtrdshdk.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtpaXVnc21qeWJuY3Z0cmRzaGRrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4NzY2ODIsImV4cCI6MjA2OTQ1MjY4Mn0.4GRc469_WzsUERgsqikeGQ2SQZwJpR4HPW1kkqXR3Sw"
    
    try:
        # Create client
        print("📡 Creating Supabase client...")
        supabase: Client = create_client(url, key)
        print("✅ Client created")
        
        # Test market_close_data table
        print("\n📊 Testing market_close_data table...")
        try:
            response = supabase.table('market_close_data').select('*').limit(5).execute()
            print(f"✅ market_close_data table exists!")
            print(f"   📝 Records found: {len(response.data)}")
            
            if response.data:
                print("   📋 Sample data:")
                for record in response.data:
                    symbol = record.get('symbol', 'N/A')
                    price = record.get('price', 'N/A')
                    date = record.get('capture_date', 'N/A')
                    print(f"     {symbol}: {price} ({date})")
            
        except Exception as e:
            print(f"❌ market_close_data table error: {e}")
            return False
        
        # Test signals table
        print("\n📈 Testing signals table...")
        try:
            response = supabase.table('signals').select('*').limit(5).execute()
            print(f"✅ signals table exists!")
            print(f"   📝 Records found: {len(response.data)}")
            
        except Exception as e:
            print(f"❌ signals table error: {e}")
            return False
        
        # Test data_capture_log table
        print("\n📋 Testing data_capture_log table...")
        try:
            response = supabase.table('data_capture_log').select('*').limit(5).execute()
            print(f"✅ data_capture_log table exists!")
            print(f"   📝 Records found: {len(response.data)}")
            
        except Exception as e:
            print(f"❌ data_capture_log table error: {e}")
            return False
        
        # Test insert operation
        print("\n📝 Testing data insertion...")
        try:
            test_record = {
                'capture_date': '2025-07-30',
                'symbol': 'TEST',
                'price': 100.50,
                'change_amount': 2.50,
                'change_percent': 2.50,
                'previous_close': 98.00,
                'daily_high': 101.00,
                'daily_low': 99.00,
                'raw_change': 2.5,
                'source': 'connection_test'
            }
            
            response = supabase.table('market_close_data').insert(test_record).execute()
            print("✅ Test insertion successful!")
            print(f"   📝 Inserted record ID: {response.data[0]['id']}")
            
            # Test retrieval
            test_data = supabase.table('market_close_data').select('*').eq('symbol', 'TEST').execute()
            print(f"✅ Test retrieval successful! Found {len(test_data.data)} records")
            
            # Clean up test record
            supabase.table('market_close_data').delete().eq('symbol', 'TEST').execute()
            print("✅ Test cleanup completed")
            
        except Exception as e:
            print(f"❌ Insert/delete test failed: {e}")
            return False
        
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Database schema: Created correctly")
        print("✅ Table access: Working") 
        print("✅ Data operations: Functional")
        print("✅ Supabase integration: Ready for BFI Signals")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_bfi_tables()
    print("\n" + "=" * 40)
    
    if success:
        print("🎉 SUCCESS: Supabase database is fully working!")
        print("🚀 Ready to run full storage system test:")
        print("   source venv_storage/bin/activate && python3 test_storage_system.py")
    else:
        print("❌ FAILED: Check if database schema was executed correctly")
        print("💡 Make sure you ran the SQL schema in Supabase dashboard")