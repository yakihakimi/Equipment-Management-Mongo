# Database Backup & Restore System

## Overview

This system provides comprehensive backup and restore functionality for the Equipment Management MongoDB database. It automatically organizes backups by day of the week, maintains data integrity, and provides a user-friendly interface for restoration.

## Features

### 🔄 Automatic Backups
- **Configurable Intervals**: Set backup frequency (default: 1 hour)
- **Day-Based Organization**: Backups organized into folders by day of week
- **Automatic Cleanup**: Old backups (>1 week) are automatically deleted
- **Integrity Checking**: Each backup includes metadata and hash verification

### 📦 Backup Contents
Each backup creates three files:
- `equipment_backup_YYYYMMDD_HHMMSS.csv` - Equipment records
- `select_options_backup_YYYYMMDD_HHMMSS.csv` - Select options data
- `backup_metadata_YYYYMMDD_HHMMSS.json` - Backup metadata and verification

### 🔄 Restore Options
- **Preview Mode**: View backup contents before restoring
- **Comparison Tool**: Compare backup data with current database
- **Restore Modes**:
  - **Replace**: Complete database replacement
  - **Merge**: Merge backup data with existing records
- **Selective Restore**: Choose between Equipment or Select Options data

## File Structure

```
restore_data_to_db/
├── monday/
│   ├── equipment_backup_20250807_143022.csv
│   ├── select_options_backup_20250807_143022.csv
│   └── backup_metadata_20250807_143022.json
├── tuesday/
├── wednesday/
├── thursday/
├── friday/
├── saturday/
└── sunday/
```

## Usage

### For Users (Admin Only)

1. **Access Backup System**:
   - Login as admin user
   - Navigate to "Backup & Restore" tab

2. **Create Manual Backup**:
   - Go to "Create Backup" tab
   - Set backup interval (hours)
   - Click "Create Backup Now"

3. **Restore from Backup**:
   - Go to "Restore Data" tab
   - Select day of week
   - Choose specific backup
   - Select data type (Equipment/Select Options)
   - Choose restore mode (Replace/Merge)
   - Preview and compare data
   - Confirm and restore

4. **Monitor Auto Backups**:
   - Check "Auto Backup" tab for status
   - View backup statistics
   - Trigger manual auto-backup checks

### For Developers

#### Integration in Main App

```python
# Import backup functionality
from backup_csv_for_db_restore import backup_restore_ui, integrate_auto_backup_into_main_app

# In your main app run() method
if st.session_state.user_role == "admin":
    # Add backup tab
    with tab3:  # Backup & Restore tab
        # Automatic backup check
        integrate_auto_backup_into_main_app(self, backup_interval_hours=1)
        
        # Backup UI
        backup_restore_ui(self)
```

#### Standalone Usage

```python
from backup_csv_for_db_restore import DatabaseBackupRestore

# Initialize backup system
backup_system = DatabaseBackupRestore()

# Create backup
success, backup_file, message = backup_system.create_backup(backup_interval_hours=1)

# Get available backups
backups = backup_system.get_available_backups()

# Restore from backup
success, message = backup_system.restore_from_backup(
    backup_metadata, 
    collection_type="equipment", 
    restore_mode="replace"
)
```

## Configuration Options

### Backup Intervals
- **Minimum**: 0.1 hours (6 minutes) - for testing
- **Default**: 1 hour - recommended for production
- **Maximum**: 168 hours (1 week)

### Retention Policy
- **Duration**: 1 week (7 days)
- **Organization**: By day of week
- **Cleanup**: Automatic deletion of expired backups

### Restore Modes
- **Replace Mode**: 
  - Deletes all current data
  - Restores complete backup dataset
  - Use for complete rollbacks

- **Merge Mode**:
  - Keeps existing data
  - Adds/updates from backup
  - Uses unique identifiers for conflict resolution

## Security Considerations

1. **Admin Access Only**: Backup/restore functionality restricted to admin users
2. **Data Validation**: Backup integrity verified with hashes
3. **Confirmation Required**: Restore operations require explicit confirmation
4. **Preview Available**: Always preview data before restoration

## Troubleshooting

### Common Issues

1. **"Backup not needed" Message**:
   - Backup interval not reached
   - Reduce interval or wait for next backup window

2. **"Database connection failed"**:
   - Check MongoDB connection string
   - Verify database server is running
   - Check network connectivity

3. **"Backup file not found"**:
   - Backup may have been manually deleted
   - Check backup folder structure
   - Create new backup

4. **"No backups found"**:
   - Create initial backup first
   - Check folder permissions
   - Verify backup system initialization

### Testing

Run the test script to verify system functionality:

```bash
python test_backup_system.py
```

## File Dependencies

- `app.py` - Main application (integration point)
- `backup_csv_for_db_restore.py` - Core backup system
- `test_backup_system.py` - Testing script

## MongoDB Collections

- `Equipment` - Main equipment records
- `Equipment_select_options` - Dropdown options data

## Backup Metadata Schema

```json
{
  "backup_timestamp": "2025-08-07T14:30:22.123456",
  "backup_interval_hours": 1,
  "day_of_week": "tuesday",
  "equipment_records_count": 150,
  "select_options_records_count": 45,
  "equipment_file": "equipment_backup_20250807_143022.csv",
  "select_options_file": "select_options_backup_20250807_143022.csv",
  "backup_hash": "a1b2c3d4e5f6..."
}
```

## Future Enhancements

- **Incremental Backups**: Only backup changed records
- **Compression**: Compress backup files to save space
- **Remote Storage**: Support for cloud storage backends
- **Scheduled Backups**: Cron-style scheduling options
- **Email Notifications**: Alert on backup success/failure
- **Encrypted Backups**: Add encryption for sensitive data

## Support

For issues or questions about the backup system:
1. Check this documentation
2. Run the test script for diagnostics
3. Review error messages in the Streamlit interface
4. Check backup folder permissions and disk space
