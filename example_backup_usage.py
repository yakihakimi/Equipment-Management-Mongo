"""
Example script showing manual usage of the backup system.
This demonstrates how to programmatically create and restore backups.
"""

from backup_csv_for_db_restore import DatabaseBackupRestore
from datetime import datetime
import json

def example_backup_operations():
    """Example of manual backup operations."""
    print("🔧 Manual Backup System Example")
    print("=" * 40)
    
    # Initialize the backup system
    backup_system = DatabaseBackupRestore()
    
    # 1. Create a backup immediately (ignore interval)
    print("\n1️⃣ Creating immediate backup...")
    success, backup_file, message = backup_system.create_backup(backup_interval_hours=0.1)
    
    if success:
        print(f"✅ {message}")
        print(f"📄 Backup file: {backup_file}")
    else:
        print(f"ℹ️ {message}")
    
    # 2. List all available backups
    print("\n2️⃣ Listing available backups...")
    available_backups = backup_system.get_available_backups()
    
    for day, backups in available_backups.items():
        if backups:
            print(f"📅 {day.title()}: {len(backups)} backup(s)")
            for i, backup in enumerate(backups[:2]):  # Show only first 2
                backup_time = datetime.fromisoformat(backup["backup_timestamp"])
                print(f"   {i+1}. {backup_time.strftime('%Y-%m-%d %H:%M:%S')} - "
                      f"Equipment: {backup['equipment_records_count']} records, "
                      f"Options: {backup['select_options_records_count']} records")
    
    # 3. Preview backup data (if backups exist)
    print("\n3️⃣ Previewing latest backup...")
    for day, backups in available_backups.items():
        if backups:
            latest_backup = backups[0]  # Most recent
            print(f"📋 Previewing latest backup from {day}...")
            
            # Preview equipment data
            equipment_preview = backup_system.preview_backup_data(latest_backup, "equipment")
            if not equipment_preview.empty:
                print(f"   📊 Equipment data: {len(equipment_preview)} rows, {len(equipment_preview.columns)} columns")
                print(f"   📋 Columns: {', '.join(equipment_preview.columns[:5])}{'...' if len(equipment_preview.columns) > 5 else ''}")
            
            # Preview select options data
            options_preview = backup_system.preview_backup_data(latest_backup, "select_options")
            if not options_preview.empty:
                print(f"   📊 Select options data: {len(options_preview)} rows, {len(options_preview.columns)} columns")
            
            break
    
    # 4. Compare with current database
    print("\n4️⃣ Comparing with current database...")
    for day, backups in available_backups.items():
        if backups:
            latest_backup = backups[0]
            comparison = backup_system.compare_backup_with_current(latest_backup, "equipment")
            
            if comparison:
                print(f"📊 Comparison results:")
                print(f"   Backup records: {comparison['backup_count']}")
                print(f"   Current records: {comparison['current_count']}")
                if comparison['new_columns']:
                    print(f"   New columns: {', '.join(comparison['new_columns'])}")
                if comparison['removed_columns']:
                    print(f"   Removed columns: {', '.join(comparison['removed_columns'])}")
            break
    
    # 5. Example restore (commented out for safety)
    print("\n5️⃣ Restore example (commented out for safety)...")
    print("   # To restore, uncomment the following lines:")
    print("   # success, message = backup_system.restore_from_backup(")
    print("   #     latest_backup, 'equipment', 'replace')")
    print("   # if success:")
    print("   #     print(f'✅ Restore successful: {message}')")
    print("   # else:")
    print("   #     print(f'❌ Restore failed: {message}')")
    
    print("\n🎉 Manual backup example completed!")
    print("\n💡 To use in production:")
    print("   - Always preview and compare before restoring")
    print("   - Use 'merge' mode to avoid data loss")
    print("   - Test restore operations on non-production data first")

if __name__ == "__main__":
    example_backup_operations()
