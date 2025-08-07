#!/usr/bin/env python3
"""
Test script to verify that the index column fix works correctly.
This script will test the backup creation and reading to ensure column counts are correct.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backup_csv_for_db_restore import DatabaseBackupRestore
import pandas as pd
from datetime import datetime

def test_index_column_fix():
    """Test that backup CSV files are created and read without extra index columns."""
    
    print("🧪 Testing Index Column Fix...")
    print("=" * 50)
    
    # Initialize backup system
    backup_system = DatabaseBackupRestore()
    
    # Check if we can connect to the database
    if not backup_system.connect_to_database():
        print("❌ Cannot connect to database. Skipping test.")
        return
    
    print("✅ Connected to database successfully")
    
    # Create a test backup
    print("\n📦 Creating test backup...")
    success, backup_file, message = backup_system.create_backup(backup_interval_hours=0.1)
    
    if success:
        print(f"✅ Backup created: {message}")
        
        # Get the latest backup
        current_day = datetime.now().weekday()
        day_name = backup_system.day_folders[current_day]
        backups = backup_system.get_backups_by_time_for_day(day_name)
        
        if backups:
            latest_backup = backups[0]
            
            print(f"\n📊 Testing latest backup from {day_name}...")
            print(f"Backup timestamp: {latest_backup['backup_datetime']}")
            
            # Test equipment data
            print("\n🔧 Testing Equipment data:")
            equipment_df = backup_system.preview_backup_data(latest_backup, "equipment")
            if not equipment_df.empty:
                print(f"Equipment columns: {len(equipment_df.columns)}")
                print(f"Equipment records: {len(equipment_df)}")
                print(f"Column names: {list(equipment_df.columns)}")
                
                # Check for any suspicious index columns
                index_like_columns = []
                for col in equipment_df.columns:
                    if (col.lower() in ['index', 'unnamed: 0'] or 
                        col.startswith('Unnamed:') or 
                        (col.isdigit() and len(col) <= 2)):
                        index_like_columns.append(col)
                
                if index_like_columns:
                    print(f"⚠️  Found index-like columns: {index_like_columns}")
                else:
                    print("✅ No index-like columns found in equipment data")
            else:
                print("📂 Equipment data is empty")
            
            # Test select options data
            print("\n⚙️  Testing Select Options data:")
            options_df = backup_system.preview_backup_data(latest_backup, "select_options")
            if not options_df.empty:
                print(f"Select Options columns: {len(options_df.columns)}")
                print(f"Select Options records: {len(options_df)}")
                print(f"Column names: {list(options_df.columns)}")
                
                # Check for any suspicious index columns
                index_like_columns = []
                for col in options_df.columns:
                    if (col.lower() in ['index', 'unnamed: 0'] or 
                        col.startswith('Unnamed:') or 
                        (col.isdigit() and len(col) <= 2)):
                        index_like_columns.append(col)
                
                if index_like_columns:
                    print(f"⚠️  Found index-like columns: {index_like_columns}")
                else:
                    print("✅ No index-like columns found in select options data")
            else:
                print("📂 Select Options data is empty")
                
            # Test reading the CSV directly to compare
            print("\n📄 Testing direct CSV reading:")
            
            try:
                # Read the equipment CSV directly
                if latest_backup["equipment_file_path"].exists():
                    direct_df = pd.read_csv(latest_backup["equipment_file_path"])
                    processed_df = pd.read_csv(latest_backup["equipment_file_path"], index_col=False)
                    
                    print(f"Direct read (no index_col param): {len(direct_df.columns)} columns")
                    print(f"With index_col=False: {len(processed_df.columns)} columns")
                    
                    if len(direct_df.columns) != len(processed_df.columns):
                        print("✅ Fix confirmed: index_col=False prevents extra columns")
                    else:
                        print("ℹ️  No difference - CSV was already clean")
                        
            except Exception as e:
                print(f"❌ Error testing direct CSV read: {e}")
        
        else:
            print("❌ No backups found after creation")
    else:
        print(f"❌ Backup creation failed: {message}")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    test_index_column_fix()
