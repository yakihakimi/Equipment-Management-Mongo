#!/usr/bin/env python3
"""
Test script to verify that the Smart Merge logic correctly handles data type differences.
"""

import pandas as pd
import sys
import os
from pathlib import Path

# Add the current directory to path so we can import the backup module
sys.path.append(str(Path(__file__).parent))

def test_smart_merge_logic():
    """Test the Smart Merge comparison logic."""
    
    print("🧪 Testing Smart Merge Logic")
    print("=" * 50)
    
    # Load the backup data
    file_path = Path("restore_data_to_db/thursday/equipment_backup_20250807_095723.csv")
    
    if not file_path.exists():
        print("❌ Test file not found:", file_path)
        return False
    
    # Read backup data with encoding handling
    encodings_to_try = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1']
    backup_df = None
    
    for encoding in encodings_to_try:
        try:
            backup_df = pd.read_csv(file_path, index_col=False, encoding=encoding)
            break
        except:
            continue
    
    if backup_df is None:
        print("❌ Could not read backup file")
        return False
    
    print(f"✅ Backup loaded: {backup_df.shape[0]} records")
    
    # Get record 136 from backup
    backup_record_136 = backup_df[backup_df['ID'] == 136]
    if backup_record_136.empty:
        print("❌ ID 136 not found in backup")
        return False
    
    backup_record = backup_record_136.iloc[0].to_dict()
    print(f"🔍 Testing with ID 136:")
    print(f"  Description: {repr(backup_record.get('Description'))}")
    print(f"  Model: {repr(backup_record.get('Model'))}")
    print(f"  check: {repr(backup_record.get('check'))} (type: {type(backup_record.get('check')).__name__})")
    
    # Simulate what the database record might look like
    # This simulates the common issue: CSV stores floats, MongoDB stores ints
    db_record = backup_record.copy()
    db_record['check'] = int(backup_record['check']) if not pd.isna(backup_record['check']) else None
    db_record['Serial'] = None  # MongoDB might store None instead of NaN
    
    print(f"🗄️  Simulated DB record:")
    print(f"  check: {repr(db_record.get('check'))} (type: {type(db_record.get('check')).__name__})")
    print(f"  Serial: {repr(db_record.get('Serial'))} (type: {type(db_record.get('Serial')).__name__})")
    
    # Test the improved comparison logic
    def _records_are_different_improved(record1, record2):
        """Improved comparison logic that handles numeric values and empty values properly."""
        try:
            # Get all keys from both records
            all_keys = set(record1.keys()) | set(record2.keys())
            
            for key in all_keys:
                val1 = record1.get(key)
                val2 = record2.get(key)
                
                # Improved empty value handling (NaN, None, empty string)
                val1_is_empty = pd.isna(val1) or val1 == '' or val1 is None
                val2_is_empty = pd.isna(val2) or val2 == '' or val2 is None
                
                if val1_is_empty and val2_is_empty:
                    continue
                if val1_is_empty or val2_is_empty:
                    print(f"  DIFF in {key}: empty difference {repr(val1)} vs {repr(val2)}")
                    return True
                
                # Try numeric comparison first for numeric values
                try:
                    # Check if both values can be converted to numbers
                    num1 = float(val1)
                    num2 = float(val2)
                    # If both are numeric, compare as numbers
                    if num1 != num2:
                        print(f"  DIFF in {key}: numeric difference {num1} vs {num2}")
                        return True
                    continue
                except (ValueError, TypeError):
                    # If either value is not numeric, fall back to string comparison
                    pass
                
                # Convert to strings for comparison to handle different data types
                str_val1 = str(val1).strip()
                str_val2 = str(val2).strip()
                
                if str_val1 != str_val2:
                    print(f"  DIFF in {key}: string difference {repr(str_val1)} vs {repr(str_val2)}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"  ERROR in comparison: {e}")
            return True
    
    print(f"\n🔬 Comparison Result:")
    are_different = _records_are_different_improved(backup_record, db_record)
    print(f"Records are different: {are_different}")
    
    if are_different:
        print("❌ Records incorrectly flagged as different")
        return False
    else:
        print("✅ Records correctly identified as same")
        return True

if __name__ == "__main__":
    success = test_smart_merge_logic()
    if success:
        print("\n🎉 Smart Merge logic test PASSED")
    else:
        print("\n💥 Smart Merge logic test FAILED")
