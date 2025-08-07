#!/usr/bin/env python3
"""
Script to check for and fix duplicate IDs in the Equipment database.
"""

import pandas as pd
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import sys

def check_and_fix_duplicate_ids():
    """
    Check for duplicate IDs in the Equipment collection and provide solutions.
    """
    try:
        # Connect to MongoDB
        client = MongoClient("mongodb://ascy00075.sc.altera.com:27017/mongo?readPreference=primary&ssl=false")
        client.admin.command("ping")
        
        db = client["Equipment_DB"]
        equipment_collection = db["Equipment"]
        
        # Get all records from database
        records = list(equipment_collection.find({}, {'_id': 0}))
        if not records:
            print("❌ No records found in the database")
            return
        
        df = pd.DataFrame(records)
        
        if 'ID' not in df.columns:
            print("❌ No ID column found in the data")
            return
        
        # Check for duplicates
        total_records = len(df)
        unique_ids = df['ID'].nunique()
        has_duplicates = total_records != unique_ids
        
        print("🔍 DUPLICATE ID ANALYSIS")
        print("=" * 50)
        print(f"📊 Total records: {total_records}")
        print(f"📊 Unique IDs: {unique_ids}")
        print(f"📊 Duplicate count: {total_records - unique_ids}")
        
        if not has_duplicates:
            print("✅ No duplicate IDs found!")
            return
        
        print(f"\n⚠️  FOUND {total_records - unique_ids} DUPLICATE IDs!")
        
        # Find duplicate records
        duplicates = df[df.duplicated('ID', keep=False)].sort_values('ID')
        
        # Group duplicates by ID
        duplicate_groups = []
        for id_val in duplicates['ID'].unique():
            dup_records = duplicates[duplicates['ID'] == id_val]
            group = {
                "id": id_val,
                "count": len(dup_records),
                "records": []
            }
            
            for idx, row in dup_records.iterrows():
                record_info = {
                    "Category": row.get("Category", "N/A"),
                    "Vendor": row.get("Vendor", "N/A"),
                    "Model": row.get("Model", "N/A"),
                    "Serial": row.get("Serial", "N/A"),
                    "Description": row.get("Description", "N/A")[:50] + "..." if len(str(row.get("Description", ""))) > 50 else row.get("Description", "N/A"),
                    "Location": row.get("Location", "N/A")
                }
                group["records"].append(record_info)
            
            duplicate_groups.append(group)
        
        # Display duplicate details
        print(f"\n📋 DUPLICATE ID DETAILS:")
        print("-" * 70)
        
        for group in duplicate_groups:
            print(f"\n🔍 ID {group['id']} appears {group['count']} times:")
            for i, record in enumerate(group["records"], 1):
                print(f"    Record {i}:")
                print(f"      Category: {record['Category']}")
                print(f"      Vendor: {record['Vendor']}")
                print(f"      Model: {record['Model']}")
                print(f"      Serial: {record['Serial']}")
                print(f"      Description: {record['Description']}")
                print(f"      Location: {record['Location']}")
        
        # Provide solutions
        print(f"\n🔧 RECOMMENDED SOLUTIONS:")
        print("-" * 50)
        print("1. **Manual Review**: Review each duplicate to determine which should keep the original ID")
        print("2. **Auto-Renumber**: Automatically assign new IDs to duplicates")
        print("3. **Merge Records**: If duplicates represent the same equipment, merge them")
        print("4. **Use Serial as ID**: Switch to using Serial numbers as unique identifiers")
        
        # Find next available ID for auto-renumbering
        max_id = df['ID'].max()
        next_available_id = max_id + 1
        
        print(f"\n📈 Next available ID for auto-renumbering: {next_available_id}")
        
        # Suggest specific fixes for ID 410
        id_410_records = df[df['ID'] == 410]
        if len(id_410_records) > 1:
            print(f"\n🎯 SPECIFIC SOLUTION FOR ID 410:")
            print("Based on your data, you have:")
            for idx, row in id_410_records.iterrows():
                print(f"  - {row.get('Category', 'N/A')} {row.get('Model', 'N/A')} (Serial: {row.get('Serial', 'N/A')})")
            
            print("\nRecommendation: Keep the older/more important equipment with ID 410,")
            print(f"and assign ID {next_available_id} to the other equipment.")
        
        return duplicate_groups
        
    except ConnectionFailure as e:
        print(f"❌ MongoDB connection failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Error checking duplicates: {str(e)}")
        return None

def auto_fix_duplicates(keep_first=True):
    """
    Automatically fix duplicate IDs by renumbering duplicates.
    
    Args:
        keep_first (bool): If True, keep the first occurrence and renumber others
    """
    try:
        # Connect to MongoDB
        client = MongoClient("mongodb://ascy00075.sc.altera.com:27017/mongo?readPreference=primary&ssl=false")
        db = client["Equipment_DB"]
        equipment_collection = db["Equipment"]
        
        # Get all records
        records = list(equipment_collection.find())
        df = pd.DataFrame(records)
        
        if 'ID' not in df.columns:
            print("❌ No ID column found")
            return False
        
        # Find duplicates
        duplicates = df[df.duplicated('ID', keep=False)]
        
        if duplicates.empty:
            print("✅ No duplicates to fix")
            return True
        
        # Find next available ID
        max_id = df['ID'].max()
        next_id = max_id + 1
        
        # Process each duplicate group
        updated_count = 0
        for id_val in duplicates['ID'].unique():
            dup_records = df[df['ID'] == id_val]
            
            # Keep the first record, renumber the rest
            records_to_update = dup_records.iloc[1:] if keep_first else dup_records.iloc[:-1]
            
            for idx, row in records_to_update.iterrows():
                # Update the record with new ID (convert to Python int to avoid numpy type issues)
                equipment_collection.update_one(
                    {"_id": row["_id"]},
                    {"$set": {"ID": int(next_id)}}
                )
                print(f"✅ Updated record {row['_id']}: ID {id_val} → ID {next_id}")
                print(f"   Equipment: {row.get('Category', 'N/A')} {row.get('Model', 'N/A')} (Serial: {row.get('Serial', 'N/A')})")
                next_id += 1
                updated_count += 1
        
        print(f"\n🎉 Successfully fixed {updated_count} duplicate ID records!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing duplicates: {str(e)}")
        return False

def main():
    """Main function to run the duplicate check and optionally fix them."""
    print("🔍 EQUIPMENT DATABASE - DUPLICATE ID CHECKER")
    print("=" * 60)
    
    # First, check for duplicates
    duplicate_groups = check_and_fix_duplicate_ids()
    
    if duplicate_groups:
        print(f"\n🤔 What would you like to do?")
        print("1. Just show the analysis (no changes)")
        print("2. Auto-fix by renumbering duplicates")
        print("3. Exit")
        
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "2":
                print("\n🔧 AUTO-FIXING DUPLICATES...")
                if auto_fix_duplicates(keep_first=True):
                    print("\n✅ Duplicates fixed! Re-running analysis to verify...")
                    check_and_fix_duplicate_ids()
                else:
                    print("\n❌ Failed to fix duplicates")
            elif choice == "1":
                print("\n📊 Analysis complete. No changes made.")
            else:
                print("\n👋 Exiting without changes.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Exiting...")
    else:
        print("\n🎉 No action needed - your database has unique IDs!")

if __name__ == "__main__":
    main()
