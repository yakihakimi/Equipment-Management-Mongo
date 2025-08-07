#!/usr/bin/env python3
"""
Test script to verify that the encoding fix works for reading CSV backup files.
"""

import pandas as pd
import os
from pathlib import Path

def test_encoding_fix():
    """Test the encoding fix for CSV files."""
    
    print("🧪 Testing CSV Encoding Fix")
    print("=" * 50)
    
    # Test file path
    file_path = Path("restore_data_to_db/thursday/equipment_backup_20250807_095723.csv")
    
    if not file_path.exists():
        print("❌ Test file not found:", file_path)
        return False
    
    print(f"📁 Testing file: {file_path}")
    
    # Try different encodings to handle problematic characters
    encodings_to_try = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1']
    df = None
    successful_encoding = None
    
    for encoding in encodings_to_try:
        try:
            print(f"⚙️  Trying encoding: {encoding}")
            
            # Read CSV with specific encoding
            df = pd.read_csv(file_path, index_col=False, encoding=encoding)
            successful_encoding = encoding
            print(f"✅ SUCCESS with encoding: {encoding}")
            break  # Success, exit the loop
            
        except UnicodeDecodeError as e:
            print(f"❌ Unicode error with {encoding}: {str(e)[:100]}...")
            continue  # Try next encoding
            
        except Exception as e:
            print(f"❌ Other error with {encoding}: {str(e)[:100]}...")
            continue  # Try next encoding
    
    if df is None:
        print("❌ FAILED: Could not read file with any encoding")
        return False
    
    print(f"✅ SUCCESS: File loaded with {successful_encoding} encoding")
    print(f"📊 Data shape: {df.shape}")
    print(f"📋 Columns: {len(df.columns)} columns")
    
    # Test specific record lookup
    if 'ID' in df.columns:
        id_136 = df[df['ID'] == 136]
        if not id_136.empty:
            record = id_136.iloc[0]
            print(f"🔍 ID 136 found:")
            print(f"  Description: {repr(record.get('Description', 'N/A'))}")
            print(f"  Model: {repr(record.get('Model', 'N/A'))}")
            print(f"  Purchase Value: {repr(record.get('Purchase Value', 'N/A'))}")
            print(f"  Serial: {repr(record.get('Serial', 'N/A'))}")
        else:
            print("⚠️  ID 136 not found in data")
    else:
        print("⚠️  No ID column found in data")
    
    return True

if __name__ == "__main__":
    test_encoding_fix()
