import pandas as pd
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import streamlit as st
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import hashlib
import uuid


class DatabaseBackupRestore:
    def __init__(self, mongo_connection_string="mongodb://ascy00075.sc.altera.com:27017/mongo?readPreference=primary&ssl=false"):
        """
        Initialize the backup and restore system.
        
        Args:
            mongo_connection_string (str): MongoDB connection string
        """
        self.mongo_connection_string = mongo_connection_string
        self.base_backup_folder = Path("restore_data_to_db")
        self.setup_backup_folders()
        self.connect_to_database()
    
    def setup_backup_folders(self):
        """Create backup folder structure organized by days of the week."""
        self.base_backup_folder.mkdir(exist_ok=True)
        
        # Create folders for each day of the week (Sunday = 6, Monday = 0 in Python weekday())
        # But we want Sunday first in our display order
        self.day_folders = {
            0: "monday",
            1: "tuesday", 
            2: "wednesday",
            3: "thursday",
            4: "friday",
            5: "saturday",
            6: "sunday"
        }
        
        # Display order starting with Sunday
        self.day_display_order = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
        
        for day_name in self.day_folders.values():
            day_folder = self.base_backup_folder / day_name
            day_folder.mkdir(exist_ok=True)
    
    def connect_to_database(self):
        """Connect to MongoDB database."""
        try:
            self.client = MongoClient(self.mongo_connection_string)
            self.client.admin.command("ping")
            self.db = self.client["Equipment_DB"]
            self.Equipment_collection = self.db["Equipment"]
            self.Equipment_select_options = self.db["Equipment_select_options"]
            return True
        except ConnectionFailure as e:
            st.error(f"MongoDB connection failed: {e}")
            return False
    
    def create_backup(self, backup_interval_hours=1):
        """
        Create a backup of the current database state.
        
        Args:
            backup_interval_hours (int): Backup interval in hours (for flexibility and debugging)
        
        Returns:
            tuple: (success, backup_file_path, message)
        """
        try:
            current_time = datetime.now()
            day_of_week = current_time.weekday()  # 0=Monday, 6=Sunday
            day_name = self.day_folders[day_of_week]
            day_folder = self.base_backup_folder / day_name
            
            # Create timestamp for filename
            timestamp = current_time.strftime("%Y%m%d_%H%M%S")
            
            # Check if we need to create a backup based on interval
            last_backup_time = self.get_last_backup_time(day_folder)
            if last_backup_time:
                time_since_last_backup = current_time - last_backup_time
                if time_since_last_backup < timedelta(hours=backup_interval_hours):
                    return False, None, f"Backup not needed. Last backup was {time_since_last_backup} ago (interval: {backup_interval_hours} hours)"
            
            # Create backup files
            equipment_backup_file = day_folder / f"equipment_backup_{timestamp}.csv"
            select_options_backup_file = day_folder / f"select_options_backup_{timestamp}.csv"
            metadata_file = day_folder / f"backup_metadata_{timestamp}.json"
            
            # Backup Equipment collection
            equipment_records = list(self.Equipment_collection.find({}, {'_id': 0}))
            equipment_df = pd.DataFrame(equipment_records)
            
            if not equipment_df.empty:
                # Remove any index columns that might exist
                if 'index' in equipment_df.columns:
                    equipment_df = equipment_df.drop(columns=['index'])
                equipment_df.to_csv(equipment_backup_file, index=False, encoding='utf-8')
            
            # Backup Equipment_select_options collection
            select_options_records = list(self.Equipment_select_options.find({}, {'_id': 0}))
            select_options_df = pd.DataFrame(select_options_records)
            
            if not select_options_df.empty:
                # For Equipment Select Options, keep ALL columns including index (UUID)
                # Don't remove the index column - it's needed for proper restoration
                select_options_df.to_csv(select_options_backup_file, index=False, encoding='utf-8')
            
            # Create metadata
            metadata = {
                "backup_timestamp": current_time.isoformat(),
                "backup_interval_hours": backup_interval_hours,
                "day_of_week": day_name,
                "equipment_records_count": len(equipment_records),
                "select_options_records_count": len(select_options_records),
                "equipment_file": equipment_backup_file.name,
                "select_options_file": select_options_backup_file.name,
                "backup_hash": self.generate_backup_hash(equipment_df, select_options_df)
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Clean up old backups (keep only last week)
            self.cleanup_old_backups(day_folder, keep_days=7)
            
            return True, equipment_backup_file, f"Backup created successfully in {day_name} folder"
            
        except Exception as e:
            return False, None, f"Backup failed: {str(e)}"
    
    def generate_backup_hash(self, equipment_df, select_options_df):
        """Generate a hash for the backup to verify integrity."""
        try:
            equipment_hash = hashlib.md5(equipment_df.to_string().encode()).hexdigest() if not equipment_df.empty else "empty"
            select_options_hash = hashlib.md5(select_options_df.to_string().encode()).hexdigest() if not select_options_df.empty else "empty"
            combined_hash = hashlib.md5(f"{equipment_hash}_{select_options_hash}".encode()).hexdigest()
            return combined_hash
        except Exception:
            return str(uuid.uuid4())
    
    def get_last_backup_time(self, day_folder):
        """Get the timestamp of the last backup in a day folder."""
        try:
            metadata_files = list(day_folder.glob("backup_metadata_*.json"))
            if not metadata_files:
                return None
            
            latest_file = max(metadata_files, key=lambda x: x.stat().st_mtime)
            with open(latest_file, 'r') as f:
                metadata = json.load(f)
            
            return datetime.fromisoformat(metadata["backup_timestamp"])
        except Exception:
            return None
    
    def cleanup_old_backups(self, day_folder, keep_days=7):
        """Clean up backups older than specified days."""
        try:
            cutoff_time = datetime.now() - timedelta(days=keep_days)
            
            # Get all backup files
            backup_files = list(day_folder.glob("*_backup_*.csv")) + list(day_folder.glob("backup_metadata_*.json"))
            
            for backup_file in backup_files:
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_time < cutoff_time:
                    backup_file.unlink()
            
        except Exception as e:
            st.warning(f"Cleanup warning: {str(e)}")
    
    def get_available_backups(self):
        """Get list of all available backups organized by day."""
        backups = {}
        
        # Process days in Sunday to Saturday order
        for day_name in self.day_display_order:
            day_folder = self.base_backup_folder / day_name
            metadata_files = list(day_folder.glob("backup_metadata_*.json"))
            
            day_backups = []
            for metadata_file in metadata_files:
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    # Add file paths
                    metadata["equipment_file_path"] = day_folder / metadata["equipment_file"]
                    metadata["select_options_file_path"] = day_folder / metadata["select_options_file"]
                    metadata["metadata_file_path"] = metadata_file
                    
                    day_backups.append(metadata)
                except Exception as e:
                    st.warning(f"Could not read metadata from {metadata_file}: {str(e)}")
            
            # Sort by timestamp (newest first)
            day_backups.sort(key=lambda x: x["backup_timestamp"], reverse=True)
            backups[day_name] = day_backups
        
        return backups
    
    def preview_backup_data(self, backup_metadata, collection_type="equipment"):
        """
        Preview backup data before restoration.
        
        Args:
            backup_metadata (dict): Backup metadata
            collection_type (str): "equipment" or "select_options"
        
        Returns:
            pandas.DataFrame: Preview data
        """
        try:
            if collection_type == "equipment":
                file_path = backup_metadata["equipment_file_path"]
            else:
                file_path = backup_metadata["select_options_file_path"]
            
            if file_path.exists():
                # Try different encodings to handle problematic characters
                encodings_to_try = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1']
                df = None
                
                for encoding in encodings_to_try:
                    try:
                        # Read CSV with specific encoding
                        df = pd.read_csv(file_path, index_col=False, encoding=encoding)
                        break  # Success, exit the loop
                    except UnicodeDecodeError:
                        continue  # Try next encoding
                    except Exception as e:
                        # Other error, try next encoding but save the error
                        last_error = e
                        continue
                
                if df is None:
                    st.error(f"Could not read CSV file with any common encoding. Last error: {str(last_error) if 'last_error' in locals() else 'Unknown encoding error'}")
                    return pd.DataFrame()
                
                # Remove any unwanted index columns that might have been saved
                columns_to_remove = []
                for col in df.columns:
                    # Remove columns that look like pandas index columns
                    if (col.lower() in ['index', 'unnamed: 0'] or 
                        col.startswith('Unnamed:') or 
                        (col.isdigit() and len(col) <= 2)):
                        columns_to_remove.append(col)
                
                if columns_to_remove:
                    df = df.drop(columns=columns_to_remove)
                
                return df
            else:
                st.error(f"Backup file not found: {file_path}")
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"Error reading backup: {str(e)}")
            return pd.DataFrame()
    
    def compare_csv_backups(self, backup1_metadata, backup2_metadata, collection_type="equipment"):
        """
        Compare two CSV backup files and show differences.
        
        Args:
            backup1_metadata (dict): First backup metadata
            backup2_metadata (dict): Second backup metadata  
            collection_type (str): "equipment" or "select_options"
        
        Returns:
            dict: Detailed comparison results
        """
        try:
            # Get backup data
            df1 = self.preview_backup_data(backup1_metadata, collection_type)
            df2 = self.preview_backup_data(backup2_metadata, collection_type)
            
            comparison_result = {
                "backup1_timestamp": backup1_metadata["backup_timestamp"],
                "backup2_timestamp": backup2_metadata["backup_timestamp"],
                "backup1_count": len(df1),
                "backup2_count": len(df2),
                "columns_backup1": list(df1.columns) if not df1.empty else [],
                "columns_backup2": list(df2.columns) if not df2.empty else [],
                "new_columns": [],
                "removed_columns": [],
                "common_columns": [],
                "record_differences": [],
                "summary": {}
            }
            
            if not df1.empty and not df2.empty:
                # Check column differences
                cols1 = set(df1.columns)
                cols2 = set(df2.columns)
                comparison_result["new_columns"] = list(cols2 - cols1)
                comparison_result["removed_columns"] = list(cols1 - cols2)
                comparison_result["common_columns"] = list(cols1 & cols2)
                
                # Record count changes
                count_diff = len(df2) - len(df1)
                comparison_result["summary"]["record_count_change"] = count_diff
                
                # Try to find detailed differences if there's a common identifier
                common_id_cols = []
                for id_col in ['id', 'act_id', 'ID', '_id', 'uuid', 'Serial']:
                    if id_col in comparison_result["common_columns"]:
                        common_id_cols.append(id_col)
                
                if common_id_cols and len(df1) < 1000 and len(df2) < 1000:  # Only for smaller datasets
                    id_col = common_id_cols[0]
                    
                    # Find records that exist in df2 but not df1 (new records)
                    df1_ids = set(df1[id_col].astype(str))
                    df2_ids = set(df2[id_col].astype(str))
                    
                    new_record_ids = df2_ids - df1_ids
                    deleted_record_ids = df1_ids - df2_ids
                    
                    comparison_result["summary"]["new_records"] = len(new_record_ids)
                    comparison_result["summary"]["deleted_records"] = len(deleted_record_ids)
                    
                    # Sample of new/deleted records (limit to 5 each)
                    if new_record_ids:
                        new_records_sample = df2[df2[id_col].astype(str).isin(list(new_record_ids)[:5])]
                        comparison_result["new_records_sample"] = new_records_sample.to_dict('records')
                    
                    if deleted_record_ids:
                        deleted_records_sample = df1[df1[id_col].astype(str).isin(list(deleted_record_ids)[:5])]
                        comparison_result["deleted_records_sample"] = deleted_records_sample.to_dict('records')
            
            return comparison_result
            
        except Exception as e:
            st.error(f"Error comparing backups: {str(e)}")
            return {}

    def get_backups_by_time_for_day(self, day_name):
        """
        Get backups for a specific day organized by time.
        
        Args:
            day_name (str): Name of the day (e.g., 'sunday', 'monday')
        
        Returns:
            list: List of backup metadata sorted by time (newest first)
        """
        try:
            day_folder = self.base_backup_folder / day_name
            metadata_files = list(day_folder.glob("backup_metadata_*.json"))
            
            day_backups = []
            for metadata_file in metadata_files:
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    # Add file paths and time information
                    metadata["equipment_file_path"] = day_folder / metadata["equipment_file"]
                    metadata["select_options_file_path"] = day_folder / metadata["select_options_file"]
                    metadata["metadata_file_path"] = metadata_file
                    
                    # Parse timestamp for easier handling
                    backup_time = datetime.fromisoformat(metadata["backup_timestamp"])
                    metadata["backup_datetime"] = backup_time
                    metadata["time_display"] = backup_time.strftime("%H:%M:%S")
                    metadata["date_display"] = backup_time.strftime("%Y-%m-%d")
                    
                    day_backups.append(metadata)
                except Exception as e:
                    st.warning(f"Could not read metadata from {metadata_file}: {str(e)}")
            
            # Sort by timestamp (newest first)
            day_backups.sort(key=lambda x: x["backup_timestamp"], reverse=True)
            return day_backups
            
        except Exception as e:
            st.error(f"Error getting backups for {day_name}: {str(e)}")
            return []

    def compare_backup_with_current(self, backup_metadata, collection_type="equipment"):
        """
        Compare backup data with current database state.
        
        Args:
            backup_metadata (dict): Backup metadata
            collection_type (str): "equipment" or "select_options"
        
        Returns:
            dict: Comparison results with differences
        """
        try:
            # Get backup data
            backup_df = self.preview_backup_data(backup_metadata, collection_type)
            
            # Get current data
            if collection_type == "equipment":
                current_records = list(self.Equipment_collection.find({}, {'_id': 0}))
            else:
                current_records = list(self.Equipment_select_options.find({}, {'_id': 0}))
            
            current_df = pd.DataFrame(current_records)
            
            # Find differences
            comparison_result = {
                "backup_count": len(backup_df),
                "current_count": len(current_df),
                "columns_backup": list(backup_df.columns) if not backup_df.empty else [],
                "columns_current": list(current_df.columns) if not current_df.empty else [],
                "new_columns": [],
                "removed_columns": [],
                "modified_records": [],
                "new_records": [],
                "deleted_records": []
            }
            
            if not backup_df.empty and not current_df.empty:
                # Check column differences
                backup_cols = set(backup_df.columns)
                current_cols = set(current_df.columns)
                comparison_result["new_columns"] = list(current_cols - backup_cols)
                comparison_result["removed_columns"] = list(backup_cols - current_cols)
                
                # For detailed record comparison, we'd need a unique identifier
                # This is a simplified comparison based on row count and basic structure
                
            return comparison_result
            
        except Exception as e:
            st.error(f"Error comparing data: {str(e)}")
            return {}
    
    def restore_from_backup(self, backup_metadata, collection_type="equipment", restore_mode="replace"):
        """
        Restore data from backup with support for replace and smart merge modes.
        
        Args:
            backup_metadata (dict): Backup metadata
            collection_type (str): "equipment" or "select_options"
            restore_mode (str): "replace" (replace all) or "smart_merge" (only different rows)
        
        Returns:
            tuple: (success, message)
        """
        try:
            # Get backup data
            backup_df = self.preview_backup_data(backup_metadata, collection_type)
            
            if backup_df.empty:
                return False, "No data found in backup file"
            
            # Select collection
            if collection_type == "equipment":
                collection = self.Equipment_collection
            else:
                collection = self.Equipment_select_options
            
            if restore_mode == "replace":
                # Clear existing data and insert all backup data
                result = collection.delete_many({})
                st.info(f"Cleared {result.deleted_count} existing records")
                
                # Prepare backup data for insertion
                records = backup_df.to_dict('records')
                
                # For Equipment Select Options, ensure all records have proper index (UUID)
                if collection_type == "select_options":
                    import uuid
                    for record in records:
                        if 'index' not in record or not record['index'] or record['index'] in ['nan', 'None', '']:
                            record['index'] = str(uuid.uuid4())
                
                if records:
                    collection.insert_many(records)
                
                return True, f"Successfully restored {len(records)} records (replaced all existing data)"
                
            elif restore_mode == "smart_merge":
                # Smart merge: only update/insert rows that are different
                return self._smart_merge_restore(backup_df, collection, collection_type)
            
        except Exception as e:
            return False, f"Restore failed: {str(e)}"
    
    def _smart_merge_restore(self, backup_df, collection, collection_type):
        """
        Perform smart merge restoration by comparing backup data with current data.
        Only updates/inserts rows that have different values.
        
        Args:
            backup_df (pandas.DataFrame): Backup data to restore
            collection: MongoDB collection object
            collection_type (str): Type of collection for logging
        
        Returns:
            tuple: (success, message)
        """
        try:
            import uuid  # Import uuid for generating new indices
            
            # Get current data from database
            current_records = list(collection.find({}, {'_id': 0}))
            current_df = pd.DataFrame(current_records)
            
            # Special handling for Equipment Select Options to ensure proper UUID indices
            if collection_type == "select_options":
                # Ensure all backup records have proper index (UUID)
                if 'index' not in backup_df.columns:
                    # If backup doesn't have index column, create it
                    backup_df['index'] = [str(uuid.uuid4()) for _ in range(len(backup_df))]
                else:
                    # Check for missing or invalid indices and assign new UUIDs
                    missing_indices = backup_df['index'].isna() | (backup_df['index'] == 'nan') | (backup_df['index'] == 'None') | (backup_df['index'] == '') | backup_df['index'].isnull()
                    if missing_indices.any():
                        backup_df.loc[missing_indices, 'index'] = [str(uuid.uuid4()) for _ in range(missing_indices.sum())]
                    
                    # Convert index column to string for consistency
                    backup_df['index'] = backup_df['index'].astype(str)
            
            # Find the best unique identifier column
            unique_id_col = self._find_best_unique_identifier(backup_df, current_df, collection_type)
            
            # For Equipment Select Options, prefer 'index' as the unique identifier
            if collection_type == "select_options" and 'index' in backup_df.columns:
                unique_id_col = 'index'
            
            if not unique_id_col:
                # If no unique identifier, fall back to inserting all backup records
                # For Equipment Select Options, ensure each record has a unique index
                records = backup_df.to_dict('records')
                if collection_type == "select_options":
                    for record in records:
                        if 'index' not in record or not record['index'] or record['index'] in ['nan', 'None', '']:
                            record['index'] = str(uuid.uuid4())
                
                if records:
                    collection.insert_many(records)
                return True, f"No unique identifier found. Inserted {len(records)} records (may contain duplicates)"
            
            # Find the best unique identifier column
            unique_id_col = self._find_best_unique_identifier(backup_df, current_df)
            
            if not unique_id_col:
                # If no unique identifier, fall back to inserting all backup records
                # (this might create duplicates, but it's better than doing nothing)
                records = backup_df.to_dict('records')
                if records:
                    collection.insert_many(records)
                return True, f"No unique identifier found. Inserted {len(records)} records (may contain duplicates)"
            
            # Track changes
            updated_count = 0
            inserted_count = 0
            unchanged_count = 0
            
            # Process each backup record
            for _, backup_row in backup_df.iterrows():
                backup_record = backup_row.to_dict()
                backup_id_value = backup_record.get(unique_id_col)
                
                # Check if backup record has a valid UUID
                has_valid_uuid = not (pd.isna(backup_id_value) or backup_id_value == "" or backup_id_value is None or str(backup_id_value) in ['nan', 'None'])
                
                # For Equipment Select Options, handle records without UUID differently
                if collection_type == "select_options":
                    if not has_valid_uuid:
                        # No valid UUID = new record, assign UUID and insert
                        new_uuid = str(uuid.uuid4())
                        backup_record['index'] = new_uuid
                        collection.insert_one(backup_record)
                        inserted_count += 1
                        continue
                    else:
                        # Has valid UUID = existing record, update backup_id_value for comparison
                        backup_id_value = backup_record.get('index', backup_id_value)
                        unique_id_col = 'index'
                else:
                    # For Equipment records, skip if no valid identifier
                    if not has_valid_uuid:
                        continue
                
                # Find matching current record
                if not current_df.empty and unique_id_col in current_df.columns:
                    matching_current = current_df[current_df[unique_id_col] == backup_id_value]
                    
                    if not matching_current.empty:
                        # Record exists, check if it's different
                        current_record = matching_current.iloc[0].to_dict()
                        
                        if self._records_are_different(backup_record, current_record):
                            # Update existing record
                            collection.update_one(
                                {unique_id_col: backup_id_value},
                                {"$set": backup_record}
                            )
                            updated_count += 1
                        else:
                            # Record is the same, no update needed
                            unchanged_count += 1
                    else:
                        # Record doesn't exist, insert it
                        collection.insert_one(backup_record)
                        inserted_count += 1
                else:
                    # No current data or unique column doesn't exist, insert new record
                    collection.insert_one(backup_record)
                    inserted_count += 1
            
            # Prepare summary message
            changes = []
            if updated_count > 0:
                changes.append(f"{updated_count} updated")
            if inserted_count > 0:
                changes.append(f"{inserted_count} inserted")
            if unchanged_count > 0:
                changes.append(f"{unchanged_count} unchanged")
            
            if changes:
                summary = ", ".join(changes)
                return True, f"Smart merge completed: {summary} records"
            else:
                return True, "Smart merge completed: No changes needed (all records were identical)"
                
        except Exception as e:
            return False, f"Smart merge failed: {str(e)}"
    
    def _find_best_unique_identifier(self, backup_df, current_df, collection_type=None):
        """
        Find the best unique identifier column that exists in both DataFrames.
        
        Args:
            backup_df (pandas.DataFrame): Backup data
            current_df (pandas.DataFrame): Current data
            collection_type (str): Type of collection for special handling
        
        Returns:
            str or None: Best unique identifier column name
        """
        # For Equipment Select Options, always prefer 'index' if it exists
        if collection_type == "select_options" and 'index' in backup_df.columns:
            return 'index'
        
        # Priority order for unique identifiers
        priority_patterns = [
            lambda col: col.lower() == 'index',  # Prioritize 'index' column for Equipment Select Options
            lambda col: col.lower() == 'id',
            lambda col: col.lower() == 'uuid',
            lambda col: col.lower().endswith('_id'),
            lambda col: col.lower().startswith('id_'),
            lambda col: 'uuid' in col.lower(),
            lambda col: col.lower() == 'serial',
            lambda col: 'serial' in col.lower(),
            lambda col: col.lower() == '_id'
        ]
        
        backup_cols = set(backup_df.columns)
        current_cols = set(current_df.columns) if not current_df.empty else backup_cols
        common_cols = backup_cols & current_cols
        
        # Try each pattern in priority order
        for pattern in priority_patterns:
            for col in common_cols:
                if pattern(col):
                    # For Equipment Select Options with 'index' column, be more lenient
                    if collection_type == "select_options" and col.lower() == 'index':
                        return col
                    
                    # Verify this column has mostly unique values in backup data
                    unique_ratio = backup_df[col].nunique() / len(backup_df) if len(backup_df) > 0 else 0
                    if unique_ratio > 0.8:  # At least 80% unique values
                        return col
        
        # If no good unique identifier found, return None
        return None
    
    def _records_are_different(self, record1, record2):
        """
        Compare two records to see if they have different values.
        
        Args:
            record1 (dict): First record
            record2 (dict): Second record
        
        Returns:
            bool: True if records are different, False if they're the same
        """
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
                    return True
                
                # Try numeric comparison first for numeric values
                try:
                    # Check if both values can be converted to numbers
                    num1 = float(val1)
                    num2 = float(val2)
                    # If both are numeric, compare as numbers
                    if num1 != num2:
                        return True
                    continue
                except (ValueError, TypeError):
                    # If either value is not numeric, fall back to string comparison
                    pass
                
                # Convert to strings for comparison to handle different data types
                str_val1 = str(val1).strip()
                str_val2 = str(val2).strip()
                
                if str_val1 != str_val2:
                    return True
            
            return False
            
        except Exception as e:
            # If comparison fails, assume they're different to be safe
            return True
    
    def preview_smart_merge_changes(self, backup_metadata, collection_type="equipment"):
        """
        Preview what changes smart merge will make without actually applying them.
        
        Args:
            backup_metadata (dict): Backup metadata
            collection_type (str): "equipment" or "select_options"
        
        Returns:
            dict: Preview information about what will change
        """
        try:
            # Get backup data
            backup_df = self.preview_backup_data(backup_metadata, collection_type)
            
            if backup_df.empty:
                return None
            
            # Get current data from database
            if collection_type == "equipment":
                collection = self.Equipment_collection
            else:
                collection = self.Equipment_select_options
            
            current_records = list(collection.find({}, {'_id': 0}))
            current_df = pd.DataFrame(current_records)
            
            # Find the best unique identifier column
            unique_id_col = self._find_best_unique_identifier(backup_df, current_df, collection_type)
            
            if not unique_id_col:
                return {
                    "error": "No suitable unique identifier found",
                    "update_count": 0,
                    "insert_count": len(backup_df),
                    "unchanged_count": 0,
                    "unique_id_col": None,
                    "debug_info": f"Backup columns: {list(backup_df.columns)}, Current columns: {list(current_df.columns) if not current_df.empty else 'Empty'}"
                }
            
            # Track changes
            updates = []
            inserts = []
            unchanged = []
            
            # Process each backup record
            for _, backup_row in backup_df.iterrows():
                backup_record = backup_row.to_dict()
                backup_id_value = backup_record.get(unique_id_col)
                
                # Check if backup record has a valid UUID
                has_valid_uuid = not (pd.isna(backup_id_value) or backup_id_value == "" or backup_id_value is None or str(backup_id_value) in ['nan', 'None'])
                
                # For Equipment Select Options, handle records without UUID differently
                if collection_type == "select_options":
                    if not has_valid_uuid:
                        # No valid UUID = new record, will be assigned UUID and inserted
                        inserts.append(backup_record)
                        continue
                    else:
                        # Has valid UUID = existing record, use index for comparison
                        backup_id_value = backup_record.get('index', backup_id_value)
                        unique_id_col = 'index'
                else:
                    # For Equipment records, skip if no valid identifier
                    if not has_valid_uuid:
                        continue
                
                # Find matching current record
                if not current_df.empty and unique_id_col in current_df.columns:
                    matching_current = current_df[current_df[unique_id_col] == backup_id_value]
                    
                    if not matching_current.empty:
                        # Record exists, check if it's different
                        current_record = matching_current.iloc[0].to_dict()
                        
                        if self._records_are_different(backup_record, current_record):
                            # Record will be updated - find specific changes
                            changes = self._find_record_changes(current_record, backup_record)
                            updates.append((current_record, backup_record, changes))
                        else:
                            # Record is the same
                            unchanged.append(backup_record)
                    else:
                        # Record doesn't exist, will be inserted
                        inserts.append(backup_record)
                else:
                    # No current data, will be inserted
                    inserts.append(backup_record)
            
            # Prepare preview data
            preview = {
                "update_count": len(updates),
                "insert_count": len(inserts),
                "unchanged_count": len(unchanged),
                "unique_id_col": unique_id_col,
                "update_samples": updates[:10],  # First 10 updates
                "insert_samples": inserts[:10],   # First 10 inserts
                "debug_info": {
                    "backup_data_count": len(backup_df),
                    "current_data_count": len(current_df),
                    "backup_sample_ids": backup_df[unique_id_col].head(5).tolist() if unique_id_col in backup_df.columns else [],
                    "current_sample_ids": current_df[unique_id_col].head(5).tolist() if not current_df.empty and unique_id_col in current_df.columns else [],
                    "backup_columns": list(backup_df.columns),
                    "current_columns": list(current_df.columns) if not current_df.empty else [],
                    "unique_id_column": unique_id_col,
                    "uuid_logic": f"Records without valid UUID ({collection_type}): treated as new inserts",
                    "backup_uuid_count": backup_df[unique_id_col].count() if unique_id_col in backup_df.columns else 0,
                    "backup_total_count": len(backup_df)
                }
            }
            
            return preview
            
        except Exception as e:
            return {
                "error": f"Preview failed: {str(e)}",
                "update_count": 0,
                "insert_count": 0,
                "unchanged_count": 0
            }
    
    def _find_record_changes(self, old_record, new_record):
        """
        Find specific field changes between two records.
        
        Args:
            old_record (dict): Current record
            new_record (dict): New record from backup
        
        Returns:
            dict: Dictionary of changes {field: (old_value, new_value)}
        """
        changes = {}
        
        # Get all keys from both records
        all_keys = set(old_record.keys()) | set(new_record.keys())
        
        for key in all_keys:
            old_val = old_record.get(key)
            new_val = new_record.get(key)
            
            # Improved empty value handling (NaN, None, empty string)
            old_is_empty = pd.isna(old_val) or old_val == '' or old_val is None
            new_is_empty = pd.isna(new_val) or new_val == '' or new_val is None
            
            if old_is_empty and new_is_empty:
                continue
                
            if old_is_empty != new_is_empty:
                changes[key] = (old_val, new_val)
                continue
            
            # Try numeric comparison first for numeric values
            try:
                # Check if both values can be converted to numbers
                num1 = float(old_val)
                num2 = float(new_val)
                # If both are numeric, compare as numbers
                if num1 != num2:
                    changes[key] = (old_val, new_val)
                continue
            except (ValueError, TypeError):
                # If either value is not numeric, fall back to string comparison
                pass
            
            # Convert to strings for comparison
            old_str = str(old_val).strip() if not old_is_empty else ""
            new_str = str(new_val).strip() if not new_is_empty else ""
            
            if old_str != new_str:
                changes[key] = (old_val, new_val)
        
        return changes
    
    def automatic_backup_scheduler(self, backup_interval_hours=1):
        """
        Run automatic backup if enough time has passed.
        This should be called periodically by the main application.
        
        Args:
            backup_interval_hours (int): Hours between backups
        
        Returns:
            tuple: (backup_created, message)
        """
        success, backup_file_path, message = self.create_backup(backup_interval_hours)
        return success, message


def backup_restore_ui(app_instance):
    """
    Streamlit UI for backup and restore functionality.
    
    Args:
        app_instance: Instance of the main EquipmentManagementApp
    """
    # Check if user has admin permissions
    if st.session_state.get("user_role") != "admin":
        st.warning("🔒 Backup and Restore functionality is only available to administrators.")
        return
    
    st.header("🗂️ Database Backup & Restore System")
    
    # Initialize backup system
    backup_system = DatabaseBackupRestore()
    
    # Create tabs for different operations
    backup_tab, restore_tab, schedule_tab = st.tabs(["📦 Create Backup", "🔄 Restore Data", "⏰ Auto Backup"])
    
    with backup_tab:
        st.subheader("Create Manual Backup")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info("💡 **Manual Backup**: Creates a backup immediately when you click the button.")
        
        with col2:
            if st.button("🔄 Create Backup Now", type="primary"):
                with st.spinner("Creating backup..."):
                    # Always create backup immediately (use very small interval)
                    success, backup_file, message = backup_system.create_backup(0.01)
                
                if success:
                    st.success(f"✅ {message}")
                    if backup_file:
                        st.info(f"📁 Backup saved to: {backup_file}")
                    # Auto-refresh to show new backup in the list
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
        
        # Show current backup status
        st.markdown("### 📊 Current Backup Status")
        try:
            available_backups = backup_system.get_available_backups()
            total_backups = sum(len(day_backups) for day_backups in available_backups.values())
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Backups", total_backups)
            
            # Show today's backups
            current_day = datetime.now().weekday()
            today_name = backup_system.day_folders[current_day]
            today_backups = available_backups.get(today_name, [])
            
            with col2:
                st.metric(f"Today ({today_name.title()})", len(today_backups))
            
            with col3:
                if today_backups:
                    latest_backup = today_backups[0]  # First one is latest
                    backup_time = datetime.fromisoformat(latest_backup["backup_timestamp"])
                    time_ago = datetime.now() - backup_time
                    hours_ago = int(time_ago.total_seconds() / 3600)
                    minutes_ago = int((time_ago.total_seconds() % 3600) / 60)
                    
                    if hours_ago > 0:
                        last_backup_text = f"{hours_ago}h {minutes_ago}m ago"
                    else:
                        last_backup_text = f"{minutes_ago}m ago"
                    
                    st.metric("Last Backup", last_backup_text)
                else:
                    st.metric("Last Backup", "None today")
            
            # Show recent backups
            if today_backups:
                st.markdown("#### 📋 Recent Backups Today")
                for backup in today_backups[:3]:  # Show last 3 backups
                    backup_time = datetime.fromisoformat(backup["backup_timestamp"])
                    st.text(f"🕐 {backup_time.strftime('%H:%M:%S')} - Equipment: {backup['equipment_records_count']}, Options: {backup['select_options_records_count']}")
            
        except Exception as e:
            st.warning(f"Could not load backup status: {str(e)}")
    
    with restore_tab:
        st.subheader("Restore from Backup")
        
        # Get available backups
        available_backups = backup_system.get_available_backups()
        
        if not any(available_backups.values()):
            st.info("📂 No backups found. Create a backup first.")
            return
        
        # Day selection with Sunday first
        available_days = [day for day in backup_system.day_display_order if available_backups.get(day)]
        
        if not available_days:
            st.info("📂 No backups found. Create a backup first.")
            return
            
        selected_day = st.selectbox(
            "Select Day of Week",
            options=available_days,
            format_func=lambda x: x.title(),
            help="Backups are organized by day of the week (Sunday to Saturday)"
        )
        
        if selected_day:
            # Get backups for the selected day with time details
            day_backups = backup_system.get_backups_by_time_for_day(selected_day)
            
            if not day_backups:
                st.info(f"📂 No backups found for {selected_day.title()}.")
                return
            
            st.markdown(f"### 📅 {selected_day.title()} Backups")
            
            # Display backup comparison section
            if len(day_backups) >= 2:
                with st.expander("🔍 Compare CSV Backups"):
                    st.markdown("**Select two backups to compare:**")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        backup1_options = []
                        for i, backup in enumerate(day_backups):
                            backup_time = backup["backup_datetime"]
                            option_text = f"{backup_time.strftime('%H:%M:%S')} - {backup['equipment_records_count']} equipment, {backup['select_options_records_count']} options"
                            backup1_options.append((option_text, i))
                        
                        backup1_idx = st.selectbox(
                            "First Backup (Older)",
                            options=range(len(backup1_options)),
                            format_func=lambda x: backup1_options[x][0],
                            key="backup1_select"
                        )
                    
                    with col2:
                        backup2_idx = st.selectbox(
                            "Second Backup (Newer)",
                            options=range(len(backup1_options)),
                            format_func=lambda x: backup1_options[x][0],
                            key="backup2_select"
                        )
                    
                    # Collection type for comparison
                    compare_collection_type = st.selectbox(
                        "Data Type to Compare",
                        options=["equipment", "select_options"],
                        format_func=lambda x: "Equipment Records" if x == "equipment" else "Select Options",
                        key="compare_collection_type"
                    )
                    
                    if backup1_idx != backup2_idx and st.button("🔍 Compare Selected Backups"):
                        backup1 = day_backups[backup1_idx]
                        backup2 = day_backups[backup2_idx]
                        
                        with st.spinner("Comparing backups..."):
                            comparison = backup_system.compare_csv_backups(backup1, backup2, compare_collection_type)
                        
                        if comparison:
                            st.markdown("#### 📊 Comparison Results")
                            
                            # Summary metrics
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                time1 = datetime.fromisoformat(comparison["backup1_timestamp"]).strftime("%H:%M:%S")
                                st.metric(f"First Backup ({time1})", comparison["backup1_count"])
                            with col2:
                                time2 = datetime.fromisoformat(comparison["backup2_timestamp"]).strftime("%H:%M:%S")
                                st.metric(f"Second Backup ({time2})", comparison["backup2_count"])
                            with col3:
                                count_change = comparison["backup2_count"] - comparison["backup1_count"]
                                st.metric("Record Change", count_change, delta=count_change)
                            
                            # Column changes
                            if comparison["new_columns"]:
                                st.success(f"🆕 **New Columns**: {', '.join(comparison['new_columns'])}")
                            if comparison["removed_columns"]:
                                st.warning(f"🗑️ **Removed Columns**: {', '.join(comparison['removed_columns'])}")
                            
                            # Record changes summary
                            if "summary" in comparison:
                                summary = comparison["summary"]
                                if "new_records" in summary or "deleted_records" in summary:
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if "new_records" in summary:
                                            st.info(f"➕ **New Records**: {summary['new_records']}")
                                    with col2:
                                        if "deleted_records" in summary:
                                            st.info(f"➖ **Deleted Records**: {summary['deleted_records']}")
                                
                                # Show sample new/deleted records
                                if "new_records_sample" in comparison:
                                    with st.expander("📋 Sample New Records"):
                                        new_df = pd.DataFrame(comparison["new_records_sample"])
                                        st.dataframe(new_df, use_container_width=True)
                                
                                if "deleted_records_sample" in comparison:
                                    with st.expander("📋 Sample Deleted Records"):
                                        deleted_df = pd.DataFrame(comparison["deleted_records_sample"])
                                        st.dataframe(deleted_df, use_container_width=True)
            
            # Backup selection for restore
            st.markdown("### 🔄 Select Backup to Restore")
            
            # Create backup selection with time-based display
            backup_options = []
            for i, backup in enumerate(day_backups):
                backup_time = backup["backup_datetime"]
                option_text = f"{backup_time.strftime('%Y-%m-%d %H:%M:%S')} - Equipment: {backup['equipment_records_count']} records, Options: {backup['select_options_records_count']} records"
                backup_options.append((option_text, i))
            
            selected_backup_idx = st.selectbox(
                "Select Backup by Time",
                options=range(len(backup_options)),
                format_func=lambda x: backup_options[x][0],
                help="Select which backup to restore from (sorted by time, newest first)"
            )
            
            if selected_backup_idx is not None:
                selected_backup = day_backups[selected_backup_idx]
                
                # Collection type selection
                collection_type = st.selectbox(
                    "Select Data Type",
                    options=["equipment", "select_options"],
                    format_func=lambda x: "Equipment Records" if x == "equipment" else "Select Options",
                    help="Choose which type of data to restore"
                )
                
                # Restore mode selection with smart merge option
                restore_mode = st.selectbox(
                    "Restore Mode",
                    options=["smart_merge", "replace"],
                    format_func=lambda x: "Smart Merge (Only Different Rows)" if x == "smart_merge" else "Replace All Data",
                    help="Smart Merge: Only updates/adds rows that have different values from current data. Replace: Deletes all current data and restores backup."
                )
                
                # Preview section
                with st.expander("🔍 Preview Backup Data"):
                    preview_df = backup_system.preview_backup_data(selected_backup, collection_type)
                    if not preview_df.empty:
                        st.dataframe(preview_df.head(10), use_container_width=True)
                        st.info(f"Showing first 10 rows of {len(preview_df)} total records")
                    else:
                        st.warning("No data found in backup file")
                
                # Comparison section
                with st.expander("📊 Compare with Current Data"):
                    comparison = backup_system.compare_backup_with_current(selected_backup, collection_type)
                    if comparison:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Backup Records", comparison["backup_count"])
                            st.write("**Backup Columns:**", len(comparison["columns_backup"]))
                        with col2:
                            st.metric("Current Records", comparison["current_count"])
                            st.write("**Current Columns:**", len(comparison["columns_current"]))
                        
                        if comparison["new_columns"]:
                            st.info(f"🆕 New columns in current data: {', '.join(comparison['new_columns'])}")
                        if comparison["removed_columns"]:
                            st.warning(f"📉 Columns removed since backup: {', '.join(comparison['removed_columns'])}")
                
                # Smart merge preview section
                if restore_mode == "smart_merge":
                    with st.expander("🔬 Smart Merge Preview - What Will Change"):
                        if st.button("🔍 Analyze Changes", help="Click to see what changes smart merge will make"):
                            with st.spinner("Analyzing differences..."):
                                changes_preview = backup_system.preview_smart_merge_changes(selected_backup, collection_type)
                            
                            if changes_preview:
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Records to Update", changes_preview["update_count"])
                                with col2:
                                    st.metric("Records to Insert", changes_preview["insert_count"])
                                with col3:
                                    st.metric("Unchanged Records", changes_preview["unchanged_count"])
                                
                                if changes_preview["update_count"] > 0:
                                    st.markdown("#### 📝 Records That Will Be Updated:")
                                    if "update_samples" in changes_preview:
                                        for i, (old_record, new_record, changes) in enumerate(changes_preview["update_samples"][:5]):
                                            with st.expander(f"Update #{i+1}: {changes_preview['unique_id_col']} = {old_record.get(changes_preview['unique_id_col'], 'N/A')}"):
                                                st.markdown("**Changes:**")
                                                for field, (old_val, new_val) in changes.items():
                                                    st.markdown(f"- **{field}**: `{old_val}` → `{new_val}`")
                                
                                if changes_preview["insert_count"] > 0:
                                    st.markdown("#### ➕ New Records That Will Be Inserted:")
                                    if "insert_samples" in changes_preview:
                                        insert_df = pd.DataFrame(changes_preview["insert_samples"][:5])
                                        st.dataframe(insert_df, use_container_width=True)
                                
                                # Debug information
                                if "debug_info" in changes_preview:
                                    with st.expander("🔧 Debug Information"):
                                        debug = changes_preview["debug_info"]
                                        st.json({
                                            "Unique ID Column": debug.get("unique_id_column"),
                                            "UUID Logic": debug.get("uuid_logic"),
                                            "Backup Records with UUID": f"{debug.get('backup_uuid_count', 0)} of {debug.get('backup_total_count', 0)}",
                                            "Backup Sample IDs": debug.get("backup_sample_ids", []),
                                            "Current Sample IDs": debug.get("current_sample_ids", []),
                                            "Backup Count": debug.get("backup_data_count"),
                                            "Current Count": debug.get("current_data_count")
                                        })
                                
                                if changes_preview["update_count"] == 0 and changes_preview["insert_count"] == 0:
                                    st.success("✅ No changes needed - all backup data matches current data!")
                            else:
                                st.error("❌ Could not analyze changes. Smart merge may still work during actual restore.")
                
                # Restore confirmation
                st.warning("⚠️ **Warning**: This operation will modify your database. Make sure you have a current backup!")
                
                confirm_restore = st.checkbox(
                    f"I understand that this will {'replace all' if restore_mode == 'replace' else 'smart merge only different rows of'} {collection_type} data",
                    help="Check this box to confirm you want to proceed with the restore operation"
                )
                
                if confirm_restore:
                    if st.button("🔄 Restore Data", type="primary"):
                        with st.spinner("Restoring data..."):
                            success, message = backup_system.restore_from_backup(
                                selected_backup, collection_type, restore_mode
                            )
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.info("🔄 Please refresh the page to see the restored data in the main application.")
                        else:
                            st.error(f"❌ {message}")
    
    with schedule_tab:
        st.subheader("Automatic Backup Scheduler")
        
        st.info("💡 **Tip**: Call the automatic backup function periodically in your main application to maintain regular backups.")
        
        # Manual trigger for auto backup
        auto_backup_interval = st.number_input(
            "Auto Backup Interval (hours)",
            min_value=0.5,
            max_value=24.0,
            value=1.0,
            step=0.5,
            help="Interval for automatic backups"
        )
        
        if st.button("🤖 Run Auto Backup Check"):
            with st.spinner("Checking if backup is needed..."):
                backup_created, message = backup_system.automatic_backup_scheduler(auto_backup_interval)
            
            if backup_created:
                st.success(f"✅ {message}")
            else:
                st.info(f"ℹ️ {message}")
        
        # Display backup schedule information
        st.markdown("### 📅 Backup Organization")
        st.markdown("""
        - **Folder Structure**: Backups are organized by day of the week
        - **Retention**: Backups older than 1 week are automatically deleted
        - **Files Created**: 
          - `equipment_backup_YYYYMMDD_HHMMSS.csv`
          - `select_options_backup_YYYYMMDD_HHMMSS.csv`
          - `backup_metadata_YYYYMMDD_HHMMSS.json`
        """)
        
        # Show current backup status
        current_backups = backup_system.get_available_backups()
        total_backups = sum(len(day_backups) for day_backups in current_backups.values())
        st.metric("Total Available Backups", total_backups)
        
        # Show backups by day (in Sunday to Saturday order)
        for day in backup_system.day_display_order:
            if day in current_backups and current_backups[day]:
                backups = current_backups[day]
                latest_backup = backups[0]  # First one is latest due to sorting
                backup_time = datetime.fromisoformat(latest_backup["backup_timestamp"])
                st.text(f"{day.title()}: {len(backups)} backups (Latest: {backup_time.strftime('%Y-%m-%d %H:%M')})")


# Function to integrate automatic backup into main app
def integrate_auto_backup_into_main_app(app_instance, backup_interval_hours=1):
    """
    Function to be called from the main app to handle automatic backups.
    
    Args:
        app_instance: Instance of the main EquipmentManagementApp
        backup_interval_hours (int): Hours between automatic backups
    """
    # Only run for admin users to avoid unnecessary backup attempts
    if st.session_state.get("user_role") == "admin":
        try:
            backup_system = DatabaseBackupRestore()
            backup_created, message = backup_system.automatic_backup_scheduler(backup_interval_hours)
            
            # Store backup status in session state to show notifications
            if backup_created:
                st.session_state["backup_notification"] = f"✅ Automatic backup created: {message}"
            
        except Exception as e:
            # Silent error handling for automatic backups
            st.session_state["backup_error"] = f"Backup system error: {str(e)}"


if __name__ == "__main__":
    # Test the backup system
    st.set_page_config(page_title="Database Backup System", page_icon="🗂️", layout="wide")
    
    # Mock app instance for testing
    class MockApp:
        pass
    
    mock_app = MockApp()
    backup_restore_ui(mock_app)
