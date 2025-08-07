# Smart Merge Restore Functionality

## Overview
The backup and restore system now includes an intelligent "Smart Merge" option that only restores rows with different values compared to the current database state. This prevents data duplication while ensuring only necessary changes are applied.

## Features

### 🔄 Restore Modes
1. **Replace All Data** - Deletes all current data and restores the complete backup
2. **Smart Merge (Only Different Rows)** - Only updates/adds rows that have different values

### 🔍 Smart Merge Process
1. **Unique Identifier Detection**: Automatically finds the best unique identifier column (ID, UUID, Serial, etc.)
2. **Record Comparison**: Compares each backup record with current database records
3. **Change Detection**: Identifies specific field-level differences
4. **Selective Updates**: Only updates records that have actually changed
5. **New Record Insertion**: Adds records that don't exist in the current database

### 📊 Smart Merge Preview
- **Analyze Changes Button**: Shows what changes will be made before applying them
- **Update Count**: Number of existing records that will be modified
- **Insert Count**: Number of new records that will be added
- **Unchanged Count**: Number of records that are identical (no action needed)
- **Detailed Changes**: Shows specific field changes for updated records
- **Sample Data**: Displays examples of records that will be updated or inserted

### 🎯 Benefits
- **No Data Duplication**: Prevents creating duplicate records
- **Minimal Database Changes**: Only applies necessary updates
- **Transparent Process**: Shows exactly what will change before making changes
- **Safe Operations**: Preserves data integrity
- **Efficient Performance**: Reduces unnecessary database operations

## How to Use

1. **Navigate to Backup & Restore Tab** in the main application
2. **Select "🔄 Restore Data" tab**
3. **Choose the day and specific backup** you want to restore from
4. **Select Data Type** (Equipment Records or Select Options)
5. **Choose "Smart Merge (Only Different Rows)"** as the restore mode
6. **Click "🔍 Analyze Changes"** to preview what will happen
7. **Review the changes** in the preview section
8. **Check the confirmation box** and click "🔄 Restore Data"

## Technical Details

### Unique Identifier Priority
The system looks for unique identifiers in this order:
1. `id` (exact match)
2. `uuid` (exact match)
3. Columns ending with `_id`
4. Columns starting with `id_`
5. Columns containing `uuid`
6. `serial` (exact match)
7. Columns containing `serial`

### Record Comparison Logic
- Compares all fields between backup and current records
- Handles null/empty values correctly
- Converts values to strings for consistent comparison
- Trims whitespace to avoid false differences

### Error Handling
- Falls back gracefully if no unique identifier is found
- Provides clear error messages for troubleshooting
- Maintains data safety even if comparison fails

## Example Usage Scenarios

### Scenario 1: Daily Equipment Updates
- Equipment technician updates several records during the day
- At end of day, restore from morning backup using Smart Merge
- Only the changed equipment records are updated, leaving new entries intact

### Scenario 2: Data Recovery
- Some records were accidentally modified
- Use Smart Merge to restore only the affected records
- Unchanged records remain untouched

### Scenario 3: Bulk Data Import
- Import new equipment from backup without duplicating existing items
- Smart Merge adds only new equipment and updates modified ones
- Prevents database bloat from duplicate entries

## Monitoring and Feedback
The system provides detailed feedback including:
- Number of records updated, inserted, and unchanged
- Specific field changes for updated records
- Sample data for verification
- Success/error messages with detailed information

This Smart Merge functionality makes the backup and restore system much more practical for real-world use cases where you want to selectively apply changes without disrupting the entire database.
