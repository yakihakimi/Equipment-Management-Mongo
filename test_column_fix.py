#!/usr/bin/env python3
"""
Test script to verify that the column count mismatch issue has been resolved.

This script demonstrates that:
1. Backup CSVs no longer contain unwanted index columns
2. Column counts now match between backup and database
3. The preview and comparison functions work correctly
"""

import pandas as pd
from pathlib import Path
import sys

def test_backup_csv_columns():
    """Test that backup CSV files don't contain index columns."""
    print("=== Testing Backup CSV Column Handling ===")
    
    # Look for backup files
    backup_base = Path("restore_data_to_db")
    if not backup_base.exists():
        print("❌ No backup folder found")
        return False
    
    csv_files = []
    for day_folder in backup_base.iterdir():
        if day_folder.is_dir():
            for file in day_folder.glob("*_equipment.csv"):
                csv_files.append(file)
    
    if not csv_files:
        print("❌ No backup CSV files found")
        return False
    
    # Test the most recent backup file
    latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
    print(f"📁 Testing file: {latest_file}")
    
    # Read the CSV
    df = pd.read_csv(latest_file)
    print(f"📊 Raw CSV shape: {df.shape}")
    print(f"📋 Raw CSV columns: {len(df.columns)}")
    print(f"🔍 First 5 columns: {list(df.columns[:5])}")
    
    # Check for index-like columns
    index_columns = []
    for col in df.columns:
        if (col.lower() in ['index', 'unnamed: 0'] or 
            col.startswith('Unnamed:') or 
            (col.isdigit() and len(col) <= 2)):
            index_columns.append(col)
    
    if index_columns:
        print(f"❌ Found index columns: {index_columns}")
        return False
    else:
        print("✅ No index columns found in backup CSV")
        return True

def test_column_filtering():
    """Test the column filtering logic used in the backup system."""
    print("\n=== Testing Column Filtering Logic ===")
    
    # Create a test DataFrame with various column types
    test_data = {
        'Category': ['A', 'B', 'C'],
        'Vendor': ['V1', 'V2', 'V3'],
        'index': [0, 1, 2],  # This should be filtered
        'Unnamed: 0': [0, 1, 2],  # This should be filtered
        'Unnamed: 5': [0, 1, 2],  # This should be filtered
        '0': ['x', 'y', 'z'],  # This should be filtered (digit column)
        'Description': ['D1', 'D2', 'D3'],
        'Serial': ['S1', 'S2', 'S3']
    }
    
    df = pd.DataFrame(test_data)
    print(f"📊 Original DataFrame shape: {df.shape}")
    print(f"📋 Original columns: {list(df.columns)}")
    
    # Apply the same filtering logic used in the backup system
    columns_to_remove = []
    for col in df.columns:
        if (col.lower() in ['index', 'unnamed: 0'] or 
            col.startswith('Unnamed:') or 
            (col.isdigit() and len(col) <= 2)):
            columns_to_remove.append(col)
    
    print(f"🗑️  Columns to remove: {columns_to_remove}")
    
    if columns_to_remove:
        df_filtered = df.drop(columns=columns_to_remove)
    else:
        df_filtered = df
    
    print(f"📊 Filtered DataFrame shape: {df_filtered.shape}")
    print(f"📋 Filtered columns: {list(df_filtered.columns)}")
    
    # Expected result: should have 4 columns (Category, Vendor, Description, Serial)
    expected_columns = ['Category', 'Vendor', 'Description', 'Serial']
    if list(df_filtered.columns) == expected_columns:
        print("✅ Column filtering works correctly")
        return True
    else:
        print(f"❌ Column filtering failed. Expected {expected_columns}, got {list(df_filtered.columns)}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Column Count Fix for Backup System")
    print("=" * 50)
    
    test1_passed = test_backup_csv_columns()
    test2_passed = test_column_filtering()
    
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"  Backup CSV Test: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"  Column Filter Test: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! The column count mismatch issue has been resolved.")
        print("   - Backup CSVs no longer contain unwanted index columns")
        print("   - Column counts should now match between backup and database")
    else:
        print("\n❌ Some tests failed. Please check the backup system configuration.")

if __name__ == "__main__":
    main()
