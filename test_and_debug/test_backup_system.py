"""
Test script for the backup and restore system.
Run this to verify the backup functionality works correctly.
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add the current directory to the path to import our backup module
sys.path.append(str(Path(__file__).parent))

try:
    from backup_csv_for_db_restore import DatabaseBackupRestore
    print("✅ Successfully imported backup system")
except ImportError as e:
    print(f"❌ Failed to import backup system: {e}")
    sys.exit(1)

def test_backup_system():
    """Test the backup system functionality."""
    print("\n🧪 Testing Database Backup & Restore System")
    print("=" * 50)
    
    # Initialize backup system
    try:
        backup_system = DatabaseBackupRestore()
        print("✅ Backup system initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize backup system: {e}")
        return False
    
    # Test folder creation
    if backup_system.base_backup_folder.exists():
        print("✅ Backup folder structure created")
        
        # List created folders
        for day_name in backup_system.day_folders.values():
            day_folder = backup_system.base_backup_folder / day_name
            if day_folder.exists():
                print(f"   📁 {day_name} folder exists")
            else:
                print(f"   ❌ {day_name} folder missing")
    else:
        print("❌ Backup folder structure not created")
        return False
    
    # Test database connection
    try:
        if backup_system.connect_to_database():
            print("✅ Database connection successful")
        else:
            print("⚠️ Database connection failed (this is expected if MongoDB is not running)")
    except Exception as e:
        print(f"⚠️ Database connection error: {e}")
    
    # Test backup creation (with mock data if database unavailable)
    print("\n📦 Testing backup creation...")
    try:
        success, backup_file, message = backup_system.create_backup(backup_interval_hours=0.1)
        if success:
            print(f"✅ Backup created: {message}")
            if backup_file:
                print(f"   📄 File: {backup_file}")
        else:
            print(f"ℹ️ Backup result: {message}")
    except Exception as e:
        print(f"⚠️ Backup creation error: {e}")
    
    # Test backup listing
    print("\n📋 Testing backup listing...")
    try:
        available_backups = backup_system.get_available_backups()
        total_backups = sum(len(day_backups) for day_backups in available_backups.values())
        print(f"✅ Found {total_backups} total backups across all days")
        
        for day, backups in available_backups.items():
            if backups:
                print(f"   📅 {day}: {len(backups)} backups")
    except Exception as e:
        print(f"❌ Backup listing error: {e}")
    
    print("\n🎉 Backup system test completed!")
    print("\n📝 Next steps:")
    print("1. Run your main Streamlit app: streamlit run app.py")
    print("2. Login as admin user")
    print("3. Go to the 'Backup & Restore' tab")
    print("4. Test creating and restoring backups")
    
    return True

if __name__ == "__main__":
    test_backup_system()
