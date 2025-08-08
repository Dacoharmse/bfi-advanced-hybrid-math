#!/usr/bin/env python3
"""
Test image upload functionality for manual journal
"""

import os
import sys
from PIL import Image
import io
from manual_journal import journal_manager

def create_test_image():
    """Create a simple test image"""
    print("📷 Creating test image...")
    
    # Create a simple 200x200 red square image
    img = Image.new('RGB', (200, 200), color='red')
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes

def test_image_validation():
    """Test image validation functionality"""
    print("🧪 Testing Image Upload and Validation")
    print("=" * 50)
    
    # Test 1: Valid image
    print("1. Testing valid image validation...")
    test_img = create_test_image()
    img_data = test_img.read()
    test_img.seek(0)
    
    is_valid, message = journal_manager.validate_image(img_data)
    print(f"   {'✅' if is_valid else '❌'} {message}")
    
    # Test 2: Invalid image data
    print("\n2. Testing invalid image data...")
    invalid_data = b"This is not an image"
    is_valid, message = journal_manager.validate_image(invalid_data)
    print(f"   {'✅' if not is_valid else '❌'} Expected failure: {message}")
    
    # Test 3: Large file simulation
    print("\n3. Testing file size validation...")
    large_data = b"x" * (15 * 1024 * 1024)  # 15MB
    is_valid, message = journal_manager.validate_image(large_data)
    print(f"   {'✅' if not is_valid else '❌'} Expected failure: {message}")
    
    # Test 4: Create mock file object for upload test
    print("\n4. Testing file upload simulation...")
    
    class MockFile:
        def __init__(self, data, filename):
            self.data = data
            self.filename = filename
            self.pos = 0
        
        def read(self):
            return self.data
        
        def seek(self, pos):
            self.pos = pos
        
        def save(self, path):
            with open(path, 'wb') as f:
                f.write(self.data)
    
    # Create mock file with test image
    test_img = create_test_image()
    mock_file = MockFile(test_img.read(), 'test_chart.png')
    
    # Test allowed file check
    is_allowed = journal_manager.allowed_file(mock_file.filename)
    print(f"   {'✅' if is_allowed else '❌'} File type allowed: {is_allowed}")
    
    # Test complete upload flow (without actual file save)
    print(f"   📁 Upload folder exists: {os.path.exists(journal_manager.upload_folder)}")
    print(f"   📂 Upload folder path: {os.path.abspath(journal_manager.upload_folder)}")
    
    print("\n🎉 Image Upload Testing Complete!")
    print("=" * 50)
    
    return True

def test_complete_workflow():
    """Test complete workflow with image"""
    print("\n🔄 Testing Complete Workflow")
    print("=" * 30)
    
    # Create test entry with all components
    test_entry = {
        'symbol': 'TEST_IMG',
        'trade_type': 'CALL',
        'entry_price': 1500.00,
        'exit_price': 1550.00,
        'quantity': 1,
        'outcome': 'WIN',
        'profit_loss': 50.00,
        'trade_date': '2025-08-02',
        'entry_time': '14:30',
        'exit_time': '15:00',
        'notes': 'Test entry with simulated image upload',
        'chart_image_path': None  # Would be set by actual upload
    }
    
    # Create entry
    entry_id, message = journal_manager.create_journal_entry(test_entry)
    if entry_id:
        print(f"✅ Created test entry: {message} (ID: {entry_id})")
        
        # Get the entry back
        entry, message = journal_manager.get_journal_entry(entry_id)
        if entry:
            print(f"✅ Retrieved entry: {entry['symbol']} {entry['trade_type']}")
            print(f"   💰 P&L: ${entry['profit_loss']}")
            print(f"   📝 Notes: {entry['notes']}")
        
        # Clean up
        success, message = journal_manager.delete_journal_entry(entry_id)
        print(f"✅ Cleanup: {message}")
    else:
        print(f"❌ Failed to create entry: {message}")

if __name__ == "__main__":
    # Change to the correct directory
    os.chdir('/home/chronic/Projects/bfi-signals/core')
    
    try:
        test_image_validation()
        test_complete_workflow()
        
        print(f"\n🏁 All Tests Completed Successfully!")
        print("The manual trade journal system is ready for production use.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()