import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
import pandas as pd
from pathlib import Path
import numpy as np
import json
import time
import uuid
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Import general utility functions
from general_functions import is_admin, apply_column_order, load_column_order, save_column_order, save_filter_order

class EquipmentSelectOptionsSystem:
    """
    A standalone system for managing Equipment Select Options data.
    Extracted from the main EquipmentManagementApp for better modularity.
    """
    
    def __init__(self):
        """Initialize the Equipment Select Options System."""
        # Initialize MongoDB connection
        try:
            client = MongoClient("mongodb://ascy00075.sc.altera.com:27017/mongo?readPreference=primary&ssl=false")
            client.admin.command("ping")
            db = client["Equipment_DB"]
            self.Equipment_select_options = db["Equipment_select_options"]
            self.Equipment_collection = db["Equipment"]
        except ConnectionFailure as e:
            st.error(f"MongoDB connection failed: {e}")
            st.stop()
        
        # Initialize data structures
        self.Equipment_select_options_db_df = None
        self.Equipment_select_options_db_records = None
        self.display_select_options_df = None
        self.edited_select_options_df = None
        
        # Initialize column type identification
        self.available_columns = []
        self.category_cols = []
        self.vendor_cols = []
        self.location_cols = []
        self.serial_cols = []
        self.check_cols = []
        self.search_cols = []
    
    def _apply_column_order(self, df, data_type):
        """Apply saved column order to DataFrame."""
        return apply_column_order(df, data_type)
    
    def _identify_column_types(self):
        """Identify different types of columns based on their names."""
        # Check if self.df exists and is not None
        if self.Equipment_select_options_db_df is None or self.Equipment_select_options_db_df.empty:
            # Initialize empty lists for all column types
            self.available_columns = []
            self.category_cols = []
            self.vendor_cols = []
            self.location_cols = []
            self.serial_cols = []
            self.check_cols = []
            self.search_cols = []
            self.unique_id_cols = []
            return
        
        self.available_columns = self.Equipment_select_options_db_df.columns.tolist()
        
        # Look for category-like columns
        self.category_cols = [col for col in self.available_columns if 'category' in col.lower()]
        
        # Look for vendor-like columns
        self.vendor_cols = [col for col in self.available_columns if 'vendor' in col.lower()]
        
        # Look for location-like columns
        self.location_cols = [col for col in self.available_columns if 'location' in col.lower()]
        
        # Look for serial-like columns
        self.serial_cols = [col for col in self.available_columns if 'serial' in col.lower()]
        
        # Look for check/status-like columns
        self.check_cols = [col for col in self.available_columns if any(term in col.lower() for term in ['check', 'status', 'active'])]
        
        # Text search columns
        self.search_cols = [col for col in self.available_columns if any(term in col.lower() for term in ['description', 'model', 'serial', 'comments'])]
        
        # Identify unique identifier columns (in order of preference)
        self.unique_id_cols = []
        
        # More precise pattern matching for ID columns - prioritize actual ID over serial
        id_patterns = [
            ('id', lambda col: col.lower() == 'id' or col.lower().endswith('_id') or col.lower().startswith('id_')),
            ('uuid', lambda col: 'uuid' in col.lower()),
            ('serial', lambda col: 'serial' in col.lower()),
            ('_id', lambda col: col.lower() == '_id')
        ]
        
        for pattern_name, pattern_func in id_patterns:
            matching_cols = [col for col in self.available_columns if pattern_func(col)]
            self.unique_id_cols.extend(matching_cols)
        
        # Remove duplicates while preserving order
        self.unique_id_cols = list(dict.fromkeys(self.unique_id_cols))

    def add_column_to_select_options_db(self, col_name, default_value=None):
        """
        Add a new column to all records in the Equipment_select_options collection.
        Args:
            col_name (str): Name of the new column
            default_value: Default value for the new column (optional)
        Returns:
            int: Number of records updated
        """
        update_result = self.Equipment_select_options.update_many(
            {},
            {"$set": {col_name: default_value}}
        )
        # Also update the DataFrame in memory
        if hasattr(self, 'Equipment_select_options_db_df') and self.Equipment_select_options_db_df is not None:
            if col_name not in self.Equipment_select_options_db_df.columns:
                self.Equipment_select_options_db_df[col_name] = default_value
                # Apply saved column order for select options table
                self.Equipment_select_options_db_df = self._apply_column_order(self.Equipment_select_options_db_df, 'select_options')
        else:
            # Initialize the DataFrame if it doesn't exist
            try:
                self.Equipment_select_options_db_records = list(self.Equipment_select_options.find({}, {'_id': 0}))
                self.Equipment_select_options_db_df = pd.DataFrame(self.Equipment_select_options_db_records)
                if self.Equipment_select_options_db_df is None:
                    self.Equipment_select_options_db_df = pd.DataFrame()
                if col_name not in self.Equipment_select_options_db_df.columns:
                    self.Equipment_select_options_db_df[col_name] = default_value
            except Exception as e:
                st.warning(f"⚠️ Warning: Could not update DataFrame in memory: {str(e)}")
        
        # Auto-sync Equipment Records column if it exists
        try:
            self._sync_equipment_column_with_select_options(col_name)
        except Exception as e:
            # Log the error but don't fail the column addition
            st.warning(f"⚠️ Warning: Could not sync column '{col_name}' with Equipment Records: {str(e)}")
        
        return update_result.modified_count
    
    def delete_column_from_select_options_db(self, col_name):
        """
        Delete a column from all records in the Equipment_select_options collection.
        Args:
            col_name (str): Name of the column to delete
        Returns:
            int: Number of records updated
        """
        update_result = self.Equipment_select_options.update_many(
            {},
            {"$unset": {col_name: ""}}
        )
        # Also update the DataFrame in memory
        if hasattr(self, 'Equipment_select_options_db_df') and self.Equipment_select_options_db_df is not None:
            if col_name in self.Equipment_select_options_db_df.columns:
                self.Equipment_select_options_db_df = self.Equipment_select_options_db_df.drop(columns=[col_name])
        else:
            # Initialize the DataFrame if it doesn't exist
            try:
                self.Equipment_select_options_db_records = list(self.Equipment_select_options.find({}, {'_id': 0}))
                self.Equipment_select_options_db_df = pd.DataFrame(self.Equipment_select_options_db_records)
                if self.Equipment_select_options_db_df is None:
                    self.Equipment_select_options_db_df = pd.DataFrame()
            except Exception as e:
                st.warning(f"⚠️ Warning: Could not update DataFrame in memory: {str(e)}")
        
        return update_result.modified_count
    
    def rename_column_in_select_options_db(self, old_col_name, new_col_name):
        """
        Rename a column in all records in the Equipment_select_options collection.
        Column position is preserved in all DataFrames.
        Args:
            old_col_name (str): Current name of the column
            new_col_name (str): New name for the column
        Returns:
            int: Number of records updated
        """
        try:
            # Use MongoDB's $rename operator to rename the field
            update_result = self.Equipment_select_options.update_many(
                {},
                {"$rename": {old_col_name: new_col_name}}
            )
            
            # Also update the DataFrame in memory - preserving column order and putting ID first
            if hasattr(self, 'Equipment_select_options_db_df') and self.Equipment_select_options_db_df is not None:
                if old_col_name in self.Equipment_select_options_db_df.columns:
                    # Store original column order
                    original_columns = self.Equipment_select_options_db_df.columns.tolist()
                    # Rename the column (preserves order automatically)
                    self.Equipment_select_options_db_df = self.Equipment_select_options_db_df.rename(columns={old_col_name: new_col_name})
                    # Verify order is preserved (this is just for safety, pandas.rename should preserve order)
                    new_columns = [new_col_name if col == old_col_name else col for col in original_columns]
                    self.Equipment_select_options_db_df = self.Equipment_select_options_db_df[new_columns]
                    # Apply saved column order for select options table
                    self.Equipment_select_options_db_df = self._apply_column_order(self.Equipment_select_options_db_df, 'select_options')
            else:
                # Initialize the DataFrame if it doesn't exist
                try:
                    self.Equipment_select_options_db_records = list(self.Equipment_select_options.find({}, {'_id': 0}))
                    self.Equipment_select_options_db_df = pd.DataFrame(self.Equipment_select_options_db_records)
                    if self.Equipment_select_options_db_df is None:
                        self.Equipment_select_options_db_df = pd.DataFrame()
                except Exception as e:
                    st.warning(f"⚠️ Warning: Could not update DataFrame in memory: {str(e)}")
            
            # Update the edited DataFrame if it exists - preserving column order and putting ID first
            if hasattr(self, 'edited_select_options_df') and self.edited_select_options_df is not None:
                if old_col_name in self.edited_select_options_df.columns:
                    original_columns = self.edited_select_options_df.columns.tolist()
                    self.edited_select_options_df = self.edited_select_options_df.rename(columns={old_col_name: new_col_name})
                    new_columns = [new_col_name if col == old_col_name else col for col in original_columns]
                    self.edited_select_options_df = self.edited_select_options_df[new_columns]
                    # Apply saved column order for select options table
                    self.edited_select_options_df = self._apply_column_order(self.edited_select_options_df, 'select_options')
            else:
                # Initialize the edited DataFrame if it doesn't exist
                try:
                    if hasattr(self, 'Equipment_select_options_db_df') and self.Equipment_select_options_db_df is not None:
                        self.edited_select_options_df = self.Equipment_select_options_db_df.copy()
                    else:
                        self.edited_select_options_df = pd.DataFrame()
                except Exception as e:
                    st.warning(f"⚠️ Warning: Could not update edited DataFrame: {str(e)}")
            
            # Re-identify column types after rename to update category lists
            try:
                self._identify_column_types()
            except Exception as e:
                st.warning(f"⚠️ Warning: Could not re-identify column types: {str(e)}")
            
            return update_result.modified_count
        except Exception as e:
            raise Exception(f"Error renaming column in select options database: {str(e)}")
    
    def filter_select_options_df(self, df, filter_columns, search_text):
        """Filter the select options DataFrame based on filter columns and search text."""
        filtered_df = df.copy()
        # Category
        if self.category_cols and 'category' in filter_columns and filter_columns['category'] != 'All' and self.category_cols[0] in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[self.category_cols[0]] == filter_columns['category']]
        # Vendor
        if self.vendor_cols and 'vendor' in filter_columns and filter_columns['vendor'] != 'All' and self.vendor_cols[0] in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[self.vendor_cols[0]] == filter_columns['vendor']]
        # Location
        if self.location_cols and 'location' in filter_columns and filter_columns['location'] != 'All' and self.location_cols[0] in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[self.location_cols[0]] == filter_columns['location']]
        # Check
        if self.check_cols and 'check' in filter_columns and filter_columns['check'] != 'All' and self.check_cols[0] in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[self.check_cols[0]].astype(str) == filter_columns['check']]
        # Serial
        if self.serial_cols and 'serial' in filter_columns and filter_columns['serial'] != 'All' and self.serial_cols[0] in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[self.serial_cols[0]] == filter_columns['serial']]
        # Text search
        if search_text and self.search_cols:
            mask = pd.Series([False] * len(filtered_df))
            for col in self.search_cols:
                if col in filtered_df.columns:
                    mask |= filtered_df[col].astype(str).str.contains(search_text, case=False, na=False)
            filtered_df = filtered_df[mask]
        return filtered_df
    
    def init_db_Equipment_select_options(self, unique_key=None):
        """Initialize the Equipment_select_options collection from CSV."""
        # Insert unique, case-insensitive, trimmed values for Location, Vendor, Category into Equipment_select_options DB
        # Read the CSV as a DataFrame to preserve the structure
        csv_path = Path("csv_init/‏‏select_options_csv.csv")
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            st.warning(f"Could not read Equipment_select_options.csv: {e}")
            return

        # Remove all existing records in the Equipment_select_options collection
        self.Equipment_select_options.delete_many({})

        # Insert each row from the DataFrame as a document in MongoDB
        for _, row in df.iterrows():
            doc = row.to_dict()
            # Ensure a unique index for each row
            doc["index"] = str(uuid.uuid4())
            # Check for duplicates before inserting
            if not self.Equipment_select_options.find_one({k: doc[k] for k in doc if k != "index"}):
                self.Equipment_select_options.insert_one(doc)
    
    def _sync_equipment_column_with_select_options(self, col_name):
        """
        Sync Equipment Records column values with Equipment Select Options dropdown values.
        If a column exists in both tables, ensure Equipment Records only contains values 
        that are available in Equipment Select Options for that column.
        
        Args:
            col_name (str): Name of the column to sync
        """
        try:
            # Load Equipment Records data if not available
            if not hasattr(self, 'df') or self.df is None:
                try:
                    db_records = list(self.Equipment_collection.find({}, {'_id': 0}))
                    self.df = pd.DataFrame(db_records)
                except Exception as e:
                    st.warning(f"⚠️ Cannot sync column '{col_name}': Unable to load Equipment Records data: {str(e)}")
                    return
            
            # Check if column exists in both Equipment Records and Equipment Select Options
            if (hasattr(self, 'df') and self.df is not None and col_name in self.df.columns and
                hasattr(self, 'Equipment_select_options_db_df') and 
                self.Equipment_select_options_db_df is not None and
                col_name in self.Equipment_select_options_db_df.columns):
                
                # Get valid options from Equipment Select Options
                valid_options = set(
                    str(x) for x in self.Equipment_select_options_db_df[col_name].dropna().unique()
                    if str(x).strip()
                )
                
                if valid_options:
                    # Get current values in Equipment Records for this column
                    current_values = self.df[col_name].dropna().unique()
                    
                    # Find values that are not in valid options
                    invalid_values = [
                        str(val) for val in current_values 
                        if str(val).strip() and str(val) not in valid_options
                    ]
                    
                    if invalid_values:
                        # Update Equipment Records to use first valid option for invalid values
                        first_valid_option = sorted(list(valid_options))[0] if valid_options else ""
                        
                        # Update DataFrame in memory
                        mask = self.df[col_name].isin(invalid_values)
                        if mask.any():
                            self.df.loc[mask, col_name] = first_valid_option
                        
                        # Update database
                        for invalid_value in invalid_values:
                            update_result = self.Equipment_collection.update_many(
                                {col_name: invalid_value},
                                {"$set": {col_name: first_valid_option}}
                            )
                            if update_result.modified_count > 0:
                                st.info(f"🔄 Updated {update_result.modified_count} records in '{col_name}' column from '{invalid_value}' to '{first_valid_option}' to match dropdown options.")
                
                # Re-identify column types to update dropdown lists
                try:
                    self._identify_column_types()
                except Exception as e:
                    st.warning(f"⚠️ Warning: Could not re-identify column types: {str(e)}")
                
        except Exception as e:
            st.warning(f"⚠️ Error syncing column '{col_name}' with select options: {str(e)}")
    
    def _sync_all_columns_with_select_options(self):
        """
        Sync all matching columns between Equipment Records and Equipment Select Options.
        This ensures that all Equipment Records columns that have corresponding columns 
        in Equipment Select Options only contain values from the dropdown options.
        """
        # Load Equipment Records data if not available
        if not hasattr(self, 'df') or self.df is None:
            try:
                db_records = list(self.Equipment_collection.find({}, {'_id': 0}))
                self.df = pd.DataFrame(db_records)
            except Exception as e:
                st.warning(f"⚠️ Cannot sync: Unable to load Equipment Records data: {str(e)}")
                return
        
        if (not hasattr(self, 'Equipment_select_options_db_df') or 
            self.Equipment_select_options_db_df is None or
            not hasattr(self, 'df') or self.df is None):
            st.warning("⚠️ Cannot sync: Equipment Records or Select Options data not available.")
            return
        
        # Find common columns between Equipment Records and Equipment Select Options
        equipment_columns = set(self.df.columns)
        select_options_columns = set(self.Equipment_select_options_db_df.columns)
        common_columns = equipment_columns.intersection(select_options_columns)
        
        # Exclude system columns that shouldn't be synced
        system_columns = {'_id', 'uuid', 'index'}
        common_columns = common_columns - system_columns
        
        if common_columns:
            st.info(f"🔄 Syncing {len(common_columns)} common columns: {', '.join(sorted(common_columns))}")
            
            for col_name in common_columns:
                self._sync_equipment_column_with_select_options(col_name)
            
            st.success(f"✅ Column synchronization completed for {len(common_columns)} columns.")
        else:
            st.info("ℹ️ No common columns found between Equipment Records and Equipment Select Options.")
    

    
    def _process_select_options_id_column(self):
        """Efficiently process ID column for Equipment Select Options (called only once per session)."""
        # Use MongoDB's _id as a persistent unique index
        if '_id' in self.Equipment_select_options_db_df.columns:
            self.Equipment_select_options_db_df.rename(columns={'_id': 'id'}, inplace=True)
        
        # Ensure 'index' column is present for deletion logic
        if 'index' not in self.Equipment_select_options_db_df.columns:
            self.Equipment_select_options_db_df['index'] = self.Equipment_select_options_db_df.index
        
        # Add sequential ID column if it doesn't exist
        if 'ID' not in self.Equipment_select_options_db_df.columns:
            # Create sequential ID starting from 1, convert to regular Python int
            self.Equipment_select_options_db_df['ID'] = [int(i) for i in range(1, len(self.Equipment_select_options_db_df) + 1)]
            # Batch update records in the database with the new ID
            updates = []
            for idx, row in self.Equipment_select_options_db_df.iterrows():
                if 'index' in row and pd.notna(row['index']):
                    updates.append({
                        "filter": {"index": row['index']},
                        "update": {"$set": {"ID": row['ID']}}
                    })
            # Execute batch updates if any
            if updates:
                for update in updates:
                    try:
                        self.Equipment_select_options.update_one(update["filter"], update["update"], upsert=False)
                    except Exception:
                        pass  # Skip failed updates
        else:
            # Ensure ID column has proper sequential values
            if self.Equipment_select_options_db_df['ID'].isna().any() or self.Equipment_select_options_db_df['ID'].duplicated().any():
                self.Equipment_select_options_db_df['ID'] = [int(i) for i in range(1, len(self.Equipment_select_options_db_df) + 1)]
                # Batch update records in database
                updates = []
                for idx, row in self.Equipment_select_options_db_df.iterrows():
                    if 'index' in row and pd.notna(row['index']):
                        updates.append({
                            "filter": {"index": row['index']},
                            "update": {"$set": {"ID": row['ID']}}
                        })
                # Execute batch updates if any
                if updates:
                    for update in updates:
                        try:
                            self.Equipment_select_options.update_one(update["filter"], update["update"], upsert=False)
                        except Exception:
                            pass  # Skip failed updates

    def _initialize_select_options_data(self):
        """Initialize Equipment Select Options data with lazy loading."""
        # Only load if not already cached
        if (not hasattr(self, 'Equipment_select_options_db_df') or 
            self.Equipment_select_options_db_df is None):
            
            try:
                self.Equipment_select_options_db_records = list(self.Equipment_select_options.find({}, {'_id': 0}))
                self.Equipment_select_options_db_df = pd.DataFrame(self.Equipment_select_options_db_records)
                
                # Ensure we have a valid DataFrame
                if self.Equipment_select_options_db_df is None:
                    self.Equipment_select_options_db_df = pd.DataFrame()
            except Exception as e:
                st.error(f"❌ Error initializing select options data: {str(e)}")
                self.Equipment_select_options_db_df = pd.DataFrame()

    def _prepare_display_data_select_options(self):
        """
        Prepare Equipment Select Options data for display by applying column order.
        Returns:
            pandas.DataFrame: DataFrame with columns in saved order
        """
        if not hasattr(self, 'Equipment_select_options_db_df') or self.Equipment_select_options_db_df is None:
            return pd.DataFrame()
        
        # Apply column order and return the prepared data
        return self._apply_column_order(self.Equipment_select_options_db_df, 'select_options')

    def _load_select_options_filter_order(self, default_filters):
        """
        Load saved filter order preference for Equipment Select Options.
        Args:
            default_filters (list): Default filter order to use if no saved preference
        Returns:
            list: Ordered list of filter names
        """
        try:
            filter_order_file = Path("filter_order_preferences.json")
            
            if filter_order_file.exists():
                with open(filter_order_file, 'r') as f:
                    preferences = json.load(f)
                
                if 'select_options_filters' in preferences:
                    saved_order = preferences['select_options_filters']
                    # Ensure all current filters are included (in case new filters were added)
                    missing_filters = [f for f in default_filters if f not in saved_order]
                    # Add any missing filters at the end
                    return saved_order + missing_filters
            
            # Return default order if no saved preference
            return default_filters
        except Exception as e:
            # Return default order if there's an error loading preferences
            return default_filters

    def _save_select_options_filter_order(self, filter_order):
        """
        Save filter order preference for Equipment Select Options to a JSON file.
        Args:
            filter_order (list): List of filter column names in desired order
        Returns:
            bool: Success status
        """
        try:
            filter_order_file = Path("filter_order_preferences.json")
            
            preferences = {}
            if filter_order_file.exists():
                with open(filter_order_file, 'r') as f:
                    preferences = json.load(f)
            
            preferences['select_options_filters'] = filter_order
            
            with open(filter_order_file, 'w') as f:
                json.dump(preferences, f, indent=2)
            
            return True
        except Exception as e:
            st.error(f"Error saving select options filter order: {str(e)}")
            return False

    def save_select_options_column_order_ui(self):
        """UI for admin to save the current Select Options column order"""
        if is_admin():
            with st.expander("💾 Save Select Options Column Order"):
                st.info("💡 Configure your preferred Select Options column order below and save it.")
                
                # Show current saved orders for Select Options only
                select_options_default = list(self.Equipment_select_options_db_df.columns) if hasattr(self, 'Equipment_select_options_db_df') and not self.Equipment_select_options_db_df.empty else []
                select_options_order = load_column_order('select_options', select_options_default)
                
                st.markdown("**Select Options Table Column Order:**")
                if select_options_default:
                    st.markdown("Current columns in data:")
                    current_select_options_display = ', '.join(select_options_default[:5]) + ('...' if len(select_options_default) > 5 else '')
                    st.text(current_select_options_display)
                    
                    # Allow user to reorder columns
                    st.markdown("**Drag to reorder or manually edit the order:**")
                    select_options_order_input = st.text_area(
                        "Column order (one per line or comma-separated):",
                        value='\n'.join(select_options_order) if select_options_order else '\n'.join(select_options_default),
                        height=150,
                        key="select_options_column_order"
                    )
                    
                    if st.button("💾 Save Select Options Column Order", key="save_select_options_order_btn"):
                        # Parse the input
                        if '\n' in select_options_order_input:
                            new_order = [col.strip() for col in select_options_order_input.split('\n') if col.strip()]
                        else:
                            new_order = [col.strip() for col in select_options_order_input.split(',') if col.strip()]
                        
                        # Validate that all columns exist
                        invalid_columns = [col for col in new_order if col not in select_options_default]
                        missing_columns = [col for col in select_options_default if col not in new_order]
                        
                        if invalid_columns:
                            st.error(f"❌ Invalid columns: {', '.join(invalid_columns)}")
                        elif missing_columns:
                            st.warning(f"⚠️ Missing columns (will be added at end): {', '.join(missing_columns)}")
                            new_order.extend(missing_columns)
                            save_column_order('select_options', new_order)
                            st.success("✅ Select Options columns order saved successfully!")
                            st.rerun()
                        else:
                            save_column_order('select_options', new_order)
                            st.success("✅ Select Options columns order saved successfully!")
                            st.rerun()
                else:
                    st.info("No Select Options data available")
                
                st.markdown("📋 **Instructions:** Edit the column order in the text area above (one column name per line), then click Save.")

    def save_select_options_filter_order_ui(self):
        """UI for admin to save the current Equipment Select Options Filter order"""
        if is_admin():
            with st.expander("🔧 Save Equipment Select Options Filter Order"):
                # Get excluded filter columns (same as used in Equipment_select_options_Filters)
                excluded_filter_cols = ["ID", "check", "uuid", "index"]  # You can modify this list as needed
                
                # Get ALL filterable columns from the current dataset
                all_filterable_columns = []
                filter_column_mapping = {}
                
                if hasattr(self, 'Equipment_select_options_db_df') and self.Equipment_select_options_db_df is not None and not self.Equipment_select_options_db_df.empty:
                    # Get all columns except excluded ones
                    for col in self.Equipment_select_options_db_df.columns:
                        if col not in excluded_filter_cols:
                            all_filterable_columns.append(col)
                            filter_column_mapping[col] = col
                
                # Show current saved filter order
                current_filter_order = self._load_select_options_filter_order(all_filterable_columns)
                
                if all_filterable_columns:
                    # Allow user to configure excluded columns
                    excluded_cols_input = st.text_input(
                        "Excluded columns (comma-separated):",
                        value=', '.join(excluded_filter_cols),
                        help="Enter column names that should NOT appear as filters",
                        key="excluded_select_options_filter_cols_input"
                    )
                    
                    # Update excluded columns and refresh available columns
                    if excluded_cols_input.strip():
                        new_excluded_cols = [col.strip() for col in excluded_cols_input.split(',') if col.strip()]
                        # Update the available columns based on new exclusions
                        updated_filterable_columns = []
                        if hasattr(self, 'Equipment_select_options_db_df') and self.Equipment_select_options_db_df is not None and not self.Equipment_select_options_db_df.empty:
                            for col in self.Equipment_select_options_db_df.columns:
                                if col not in new_excluded_cols:
                                    updated_filterable_columns.append(col)
                        
                        # Update current filter order to remove newly excluded columns
                        current_filter_order = [col for col in current_filter_order if col not in new_excluded_cols]
                        all_filterable_columns = updated_filterable_columns
                    
                    # Allow user to reorder filters
                    st.markdown("---")
                    st.markdown("**📋 Reorder Filters:**")
                    filter_order_input = st.text_area(
                        "Filter order (one column per line or comma-separated):",
                        value='\n'.join(current_filter_order) if current_filter_order else '\n'.join(all_filterable_columns),
                        height=200,
                        key="select_options_filter_order"
                    )
                    
                    if st.button("💾 Save Equipment Select Options Filter Order", key="save_select_options_filter_order_btn"):
                        # Parse the input
                        if '\n' in filter_order_input:
                            new_order = [f.strip() for f in filter_order_input.split('\n') if f.strip()]
                        else:
                            new_order = [f.strip() for f in filter_order_input.split(',') if f.strip()]
                        
                        # Validate that all filters exist in available columns
                        invalid_filters = [f for f in new_order if f not in all_filterable_columns]
                        missing_filters = [f for f in all_filterable_columns if f not in new_order]
                        
                        if invalid_filters:
                            st.error(f"❌ Invalid column names: {', '.join(invalid_filters)}")
                            st.info(f"📋 Available columns: {', '.join(all_filterable_columns)}")
                        elif missing_filters:
                            st.warning(f"⚠️ Missing columns (will be added at end): {', '.join(missing_filters)}")
                            new_order.extend(missing_filters)
                            
                            # Also save the updated excluded columns if they changed
                            if excluded_cols_input.strip():
                                new_excluded_cols = [col.strip() for col in excluded_cols_input.split(',') if col.strip()]
                                # Save excluded columns to a separate preference file
                                try:
                                    excluded_cols_file = Path("excluded_select_options_filter_columns.json")
                                    with open(excluded_cols_file, 'w') as f:
                                        json.dump({"excluded_columns": new_excluded_cols}, f, indent=2)
                                except Exception as e:
                                    st.warning(f"⚠️ Could not save excluded columns preference: {str(e)}")
                            
                            self._save_select_options_filter_order(new_order)
                            st.success("✅ Equipment Select Options filter order saved successfully!")
                            st.rerun()
                        else:
                            # Also save the updated excluded columns if they changed
                            if excluded_cols_input.strip():
                                new_excluded_cols = [col.strip() for col in excluded_cols_input.split(',') if col.strip()]
                                # Save excluded columns to a separate preference file
                                try:
                                    excluded_cols_file = Path("excluded_select_options_filter_columns.json")
                                    with open(excluded_cols_file, 'w') as f:
                                        json.dump({"excluded_columns": new_excluded_cols}, f, indent=2)
                                except Exception as e:
                                    st.warning(f"⚠️ Could not save excluded columns preference: {str(e)}")
                            
                            self._save_select_options_filter_order(new_order)
                            st.success("✅ Equipment Select Options filter order saved successfully!")
                            st.rerun()
                else:
                    st.info("No data available to determine filterable columns")
                
                st.markdown("📋 **Instructions:**")
                st.markdown("1. **Configure Excluded Columns**: Add/remove columns from the excluded list")
                st.markdown("2. **Reorder Filters**: Edit the filter order (one column per line or comma-separated)")
                st.markdown("3. **Save**: Click 'Save Equipment Select Options Filter Order' to apply changes")
                st.markdown("4. **Result**: Filter dropdowns will appear in your custom order, excluding specified columns")

    def download_select_options_ui(self):
        """UI for downloading Equipment Select Options as CSV"""
        if hasattr(self, 'Equipment_select_options_db_df') and not self.Equipment_select_options_db_df.empty:
            select_options_csv = self.Equipment_select_options_db_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Equipment Select Options",
                data=select_options_csv,
                file_name="equipment_select_options.csv",
                mime="text/csv",
                key="download_select_options_all"
            )
        else:
            st.info("No Equipment Select Options data available for download")

    def add_new_column_to_select_options_db(self):
        """UI for adding a new column to the Equipment Select Options DB"""
        with st.expander("➕ Add New Column to Equipment Select Options DB"):
            st.markdown("### Add New Column")
            new_col_name = st.text_input("New Column Name", key="new_select_col_name")
            new_col_default = st.text_input("Default Value (optional)", key="new_select_col_default")
            
            st.info("💡 **Auto-Sync Feature**: If a column with the same name exists in Equipment Records, it will be automatically updated to use only values from this dropdown list.")
            
            if st.button("➕ Add Column to All Records", key="add_select_col_btn"):
                if new_col_name and new_col_name.strip():
                    try:
                        modified_count = self.add_column_to_select_options_db(new_col_name, new_col_default if new_col_default else None)
                        st.success(f"✅ Added column '{new_col_name}' to {modified_count} select option records.")
                        
                        # Check if the column exists in Equipment Records
                        if hasattr(self, 'df') and new_col_name in self.df.columns:
                            st.info(f"🔄 Column '{new_col_name}' also exists in Equipment Records and has been synced with dropdown options.")
                        
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error adding column: {str(e)}")
            
            # Manual sync section
            st.markdown("### Manual Column Synchronization")
            st.info("🔧 **Manual Sync**: Force sync all matching columns between Equipment Records and Equipment Select Options.")
            
            if st.button("🔄 Sync All Matching Columns", key="sync_all_columns_btn"):
                self._sync_all_columns_with_select_options()

    def delete_column_from_select_options_db_ui(self):
        """UI for deleting a column from the Equipment Select Options DB"""
        with st.expander("🗑️ Delete Column from Equipment Select Options DB"):
            # Get available columns for deletion (exclude essential columns)
            if hasattr(self, 'Equipment_select_options_db_df') and self.Equipment_select_options_db_df is not None:
                available_columns = [col for col in self.Equipment_select_options_db_df.columns if col not in ['index', '_id']]
                
                if available_columns:
                    col_to_delete = st.selectbox(
                        "Select Column to Delete:",
                        available_columns,
                        key="delete_select_col_select"
                    )
                    
                    # Check if we're showing confirmation for this column
                    confirm_key = f"confirm_delete_select_col_{col_to_delete}" if col_to_delete else None
                    
                    if confirm_key and st.session_state.get(confirm_key, False):
                        # Show warning popup
                        st.warning(f"⚠️ **Delete Column '{col_to_delete}' from Equipment Select Options?**")
                        st.write(f"This will permanently remove the **'{col_to_delete}'** column from all Equipment Select Options records.")
                        st.write("⚠️ **This action cannot be undone!**")
                        
                        col_yes, col_no = st.columns(2)
                        with col_yes:
                            if st.button("✅ Yes, Delete", key=f"confirm_delete_yes_{col_to_delete}"):
                                try:
                                    modified_count = self.delete_column_from_select_options_db(col_to_delete)
                                    
                                    # Refresh the DataFrame from database to ensure consistency
                                    self.Equipment_select_options_db_records = list(self.Equipment_select_options.find({}, {'_id': 0}))
                                    self.Equipment_select_options_db_df = pd.DataFrame(self.Equipment_select_options_db_records)
                                    
                                    # Apply column order after refresh
                                    if not self.Equipment_select_options_db_df.empty:
                                        # Ensure 'index' column is present for deletion logic
                                        if 'index' not in self.Equipment_select_options_db_df.columns:
                                            self.Equipment_select_options_db_df['index'] = self.Equipment_select_options_db_df.index
                                        # Apply admin-saved column order
                                        self.Equipment_select_options_db_df = self._apply_column_order(self.Equipment_select_options_db_df, 'select_options')
                                    
                                    st.success(f"✅ Successfully deleted column '{col_to_delete}' from {modified_count} select option records.")
                                    # Clear confirmation state
                                    st.session_state[confirm_key] = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error deleting column: {str(e)}")
                                    # Clear confirmation state on error too
                                    st.session_state[confirm_key] = False
                        
                        with col_no:
                            if st.button("❌ Cancel", key=f"confirm_delete_no_{col_to_delete}"):
                                # Clear confirmation state
                                st.session_state[confirm_key] = False
                                st.rerun()
                    else:
                        # Show initial delete button
                        if st.button("🗑️ Delete Column", key="delete_select_col_btn", type="primary"):
                            if col_to_delete and confirm_key:
                                # Set confirmation state
                                st.session_state[confirm_key] = True
                                st.rerun()
                else:
                    st.info("No columns available for deletion")
            else:
                st.info("No select options data available")

    def rename_column_in_select_options_db_ui(self):
        """UI for renaming a column in the Equipment Select Options DB"""
        with st.expander("✏️ Rename Column in Equipment Select Options DB"):
            # Get available columns for renaming (exclude essential columns that shouldn't be renamed)
            if hasattr(self, 'Equipment_select_options_db_df') and self.Equipment_select_options_db_df is not None:
                available_columns = [col for col in self.Equipment_select_options_db_df.columns if col not in ['_id']]
                
                if available_columns:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        col_to_rename = st.selectbox(
                            "Select Column to Rename:",
                            available_columns,
                            key="rename_select_col_select"
                        )
                    
                    with col2:
                        new_col_name = st.text_input(
                            "New Column Name:",
                            value=col_to_rename if col_to_rename else "",
                            key="new_select_col_name_input"
                        )
                    
                    # Validation and rename button
                    if col_to_rename and new_col_name and new_col_name.strip():
                        # Check if new name already exists
                        if new_col_name.strip() in self.Equipment_select_options_db_df.columns and new_col_name.strip() != col_to_rename:
                            st.error(f"❌ Column name '{new_col_name.strip()}' already exists. Please choose a different name.")
                        elif new_col_name.strip() == col_to_rename:
                            st.info("💡 New name is the same as current name. No changes needed.")
                        else:
                            if st.button("✏️ Rename Column", key="rename_select_col_btn", type="primary"):
                                try:
                                    modified_count = self.rename_column_in_select_options_db(col_to_rename, new_col_name.strip())
                                    st.success(f"✅ Successfully renamed column '{col_to_rename}' to '{new_col_name.strip()}' in {modified_count} select option records.")
                                    st.info("🔄 Page will refresh to show the updated column name.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error renaming column: {str(e)}")
                    else:
                        if col_to_rename and not new_col_name.strip():
                            st.warning("⚠️ Please enter a new column name.")
                else:
                    st.info("No columns available for renaming")
            else:
                st.info("No select options data available")

    def equipment_select_options_page(self):
        """Main Equipment Select Options page function."""
        
        # Add anti-fading CSS for AgGrid interactions
        st.markdown("""
            <style>
            /* Prevent fading during AgGrid interactions */
            * {
                transition: none !important;
                animation: none !important;
            }
            
            .stApp {
                background-color: #ffffff !important;
                background-image: none !important;
            }
            
            .main .block-container {
                background-color: #ffffff !important;
                background-image: none !important;
                transition: none !important;
            }
            
            /* Specific fixes for AgGrid interactions */
            .ag-root-wrapper,
            .ag-root,
            .ag-body-viewport,
            .ag-body-viewport-wrapper {
                background-color: #ffffff !important;
                transition: none !important;
            }
            
            .ag-theme-streamlit {
                background-color: #ffffff !important;
                transition: none !important;
            }
            
            /* Prevent any opacity changes */
            .stApp > div,
            .main > div,
            .block-container > div {
                opacity: 1 !important;
                background-color: #ffffff !important;
            }
            </style>
            
            <script>
            // Fix for AgGrid fading
            document.addEventListener('DOMContentLoaded', function() {
                function fixAgGridFading() {
                    const agGridElements = document.querySelectorAll('.ag-root-wrapper, .ag-root, .ag-body-viewport, .ag-theme-streamlit');
                    agGridElements.forEach(function(element) {
                        element.style.backgroundColor = '#ffffff';
                        element.style.transition = 'none';
                        element.style.opacity = '1';
                    });
                }
                
                fixAgGridFading();
                setInterval(fixAgGridFading, 50);
            });
            </script>
        """, unsafe_allow_html=True)
        
        # Initialize session state to reduce notification noise during cell selection
        if 'show_selection_messages' not in st.session_state:
            st.session_state['show_selection_messages'] = False  # Reduce notification noise
        
        # Display persistent database save success message
        if 'database_save_success' in st.session_state:
            save_data = st.session_state['database_save_success']
            st.success(save_data['message'])
            st.info(f"💡 **Timestamp:** {save_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            if st.button("✅ Clear Database Save Message", key="clear_db_save_msg"):
                del st.session_state['database_save_success']
                st.rerun()
        
        # --- Inline filter column (not sidebar) ---
        # Print the current filter state
        st.markdown('**🔍Equipment_select_options Filters:**')
        
        # Handle case where DataFrame is empty or None
        if self.Equipment_select_options_db_df is None or self.Equipment_select_options_db_df.empty:
            st.info("📋 No Equipment Select Options found in the database. Add some data to get started!")
            st.markdown("### Equipment Select Options")
            st.write("Database is empty. Please add some Equipment Select Options records.")
            return
        
        # Ensure column types are identified for sorting
        self._identify_column_types()
        
        filter_columns = {}
        filtered_select_options_df = self.Equipment_select_options_db_df.copy()
        filter_widgets = []
        filter_cols = []
        
        # Build filter columns using saved filter order or default logic
        filter_cols = []
        
        # Get excluded filter columns
        try:
            excluded_cols_file = Path("excluded_select_options_filter_columns.json")
            if excluded_cols_file.exists():
                with open(excluded_cols_file, 'r') as f:
                    preferences = json.load(f)
                excluded_filter_cols = preferences.get("excluded_columns", ["ID", "check", "uuid", "index"])
            else:
                excluded_filter_cols = ["ID", "check", "uuid", "index"]
        except Exception:
            excluded_filter_cols = ["ID", "check", "uuid", "index"]
        
        # Get all available filterable columns (excluding the excluded ones)
        all_available_cols = []
        if hasattr(self, 'Equipment_select_options_db_df') and self.Equipment_select_options_db_df is not None:
            for col in self.Equipment_select_options_db_df.columns:
                if col not in excluded_filter_cols:
                    all_available_cols.append(col)
        
        # Load saved filter order
        saved_filter_order = self._load_select_options_filter_order(all_available_cols)
        
        # Use saved order for filter columns, but only include columns that actually exist
        for col in saved_filter_order:
            if col in self.Equipment_select_options_db_df.columns and col not in filter_cols:
                filter_cols.append(col)

        left_col, right_col = st.columns([1, 4])
        with left_col:
            # Track current filter state to detect changes
            current_filter_state = {}
            filter_changed = False
            search_text = st.text_input('🔍 Search', key='select_options_search')
            current_filter_state['select_options_search'] = search_text
            if search_text:
                mask = pd.Series([False] * len(filtered_select_options_df))
                for col in self.search_cols:
                    if col in filtered_select_options_df.columns:
                        mask |= filtered_select_options_df[col].astype(str).str.contains(search_text, case=False, na=False)
                filtered_select_options_df = filtered_select_options_df[mask]

            # Apply column filters
            for col_name in filter_cols:
                options = ['All'] + sorted([str(val) for val in self.Equipment_select_options_db_df[col_name].dropna().unique() if str(val).strip() != ''])
                selected = st.selectbox(f"{col_name}", options, key=f'select_options_{col_name}')
                filter_columns[col_name] = selected
                current_filter_state[f'select_options_{col_name}'] = selected
                if selected != 'All':
                    filtered_select_options_df = filtered_select_options_df[filtered_select_options_df[col_name] == selected]

            # Check if filters have changed
            if 'previous_select_options_filter_state' not in st.session_state:
                st.session_state['previous_select_options_filter_state'] = current_filter_state
            
            if st.session_state['previous_select_options_filter_state'] != current_filter_state:
                filter_changed = True
                st.session_state['previous_select_options_filter_state'] = current_filter_state
                
                # COMMENTED OUT: Select all mode filter handling
                # if 'select_all_select_options_rows' in st.session_state:
                #     # Set flag to reapply select all after filtering
                #     st.session_state['reapply_select_all_select_options'] = True

        with right_col:
            # Use filtered data directly since new rows are now saved immediately to database
            self.display_select_options_df = filtered_select_options_df.copy()
            
            # Sort display_df by ID column consistently (or fall back to index)
            if not self.display_select_options_df.empty:
                if 'ID' in self.display_select_options_df.columns:
                    try:
                        # Sort by ID column in ascending order
                        if pd.api.types.is_numeric_dtype(self.display_select_options_df['ID']):
                            self.display_select_options_df = self.display_select_options_df.sort_values(
                                by='ID', ascending=True, na_position='last'
                            ).reset_index(drop=True)
                        else:
                            # Handle mixed/string ID column
                            self.display_select_options_df = self.display_select_options_df.sort_values(
                                by='ID', 
                                ascending=True, 
                                na_position='last', 
                                key=lambda x: pd.to_numeric(x, errors='coerce').fillna(float('inf'))
                            ).reset_index(drop=True)
                    except Exception:
                        # If ID sorting fails, fall back to index sorting
                        if 'index' in self.display_select_options_df.columns:
                            try:
                                self.display_select_options_df = self.display_select_options_df.sort_values(by='index', ascending=True, na_position='last').reset_index(drop=True)
                            except Exception:
                                pass
                elif 'index' in self.display_select_options_df.columns:
                    try:
                        self.display_select_options_df = self.display_select_options_df.sort_values(by='index', ascending=True, na_position='last').reset_index(drop=True)
                    except Exception:
                        # If sorting fails, leave data unsorted
                        pass
            
            # COMMENTED OUT: Reapply select all after filtering
            # if 'reapply_select_all_select_options' in st.session_state and st.session_state['reapply_select_all_select_options']:
            #     # Update the select all rows with the new filtered data
            #     st.session_state['select_all_select_options_rows'] = self.display_select_options_df.to_dict('records')
            #     st.session_state['reapply_select_all_select_options'] = False
            #     # Force grid reload to show the new selection
            #     st.session_state['force_select_options_grid_reload'] = True
            #     st.session_state['select_options_grid_key'] = st.session_state.get('select_options_grid_key', 0) + 1
            
            st.subheader("📊 Equipment Select Options")
            
            # Add custom Select All / Clear Selection buttons at the top
            # COMMENTED OUT: Selection buttons and their functionality
            # col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
            # with col1:
            #     if st.button("☑️ Select All Visible", key="select_all_select_options_btn", help="Select all rows currently visible (after all filtering) - selection will be maintained when filtering"):
            #         # Store the selection data
            #         st.session_state['select_all_select_options_rows'] = self.display_select_options_df.to_dict('records')
            #         st.session_state['select_all_select_options_active'] = True
            #         st.session_state['force_select_options_grid_reload'] = True
            #         st.session_state['select_options_grid_key'] = st.session_state.get('select_options_grid_key', 0) + 1
            #         # Ensure we stay on the current page after rerun
            #         st.session_state['current_page'] = "Equipment Select Options"
            # 
            # with col2:
            #     if st.button("⬜ Clear Selection", key="clear_selection_select_options_btn", help="Clear all selected rows"):
            #         # Clear the selection by removing from session state
            #         if 'select_all_select_options_rows' in st.session_state:
            #             del st.session_state['select_all_select_options_rows']
            #         if 'select_all_select_options_active' in st.session_state:
            #             del st.session_state['select_all_select_options_active']
            #         # Force grid reload and increment key to force visual update
            #         st.session_state['force_select_options_grid_reload'] = True
            #         st.session_state['select_options_grid_key'] = st.session_state.get('select_options_grid_key', 0) + 1
            #         # Force grid reload and increment key to force visual update
            #         st.session_state['force_select_options_grid_reload'] = True
            #         st.session_state['select_options_grid_key'] = st.session_state.get('select_options_grid_key', 0) + 1
            #         # st.rerun()
            # 
            # with col3:
            #     if st.button("🔄 Refresh Selection", key="refresh_selection_select_options_btn", help="Refresh the current selection based on filters"):
            #         # Reapply select all to current filtered data if select all was active
            #         if st.session_state.get('select_all_select_options_active', False):
            #             st.session_state['select_all_select_options_rows'] = self.display_select_options_df.to_dict('records')
            #             st.session_state['force_select_options_grid_reload'] = True
            #             st.session_state['select_options_grid_key'] = st.session_state.get('select_options_grid_key', 0) + 1
            #         st.rerun()
            
            # Get user permissions - for now assume admin permissions
            permissions = {"can_edit": True, "can_delete": True, "can_export": True}

            # Configure AgGrid for Select Options
            gb = GridOptionsBuilder.from_dataframe(self.display_select_options_df)
            
            # Enable editing based on permissions
            gb.configure_default_column(
                editable=permissions["can_edit"], 
                groupable=True, 
                resizable=True, 
                sortable=True, 
                filter=True,
                flex=1,  # Enable flexible column sizing
                minWidth=80,  # Set minimum width for all columns
                singleClickEdit=True,  # Enable single-click editing for better responsiveness
                stopEditingWhenCellsLoseFocus=True  # Save edits when cell loses focus
            )
            
            # Configure specific columns with flexible sizing
            for col in self.display_select_options_df.columns:
                col_lower = col.lower()
                
                if col == 'index':
                    # Make index column non-editable and fixed narrow width (not pinned to allow checkboxes on the left)
                    gb.configure_column(col, editable=False, width=100, flex=0)
                elif any(term in col_lower for term in ['id', '_id']):
                    # ID columns - make read-only with small flex ratio
                    gb.configure_column(col, editable=False, flex=0.5, minWidth=60, maxWidth=120)
                elif any(term in col_lower for term in ['serial', 'ser_num', 'serial_number']):
                    # Serial number columns - medium flex ratio with validation styling
                    gb.configure_column(
                        col, 
                        editable=permissions["can_edit"],
                        flex=1, 
                        minWidth=120, 
                        maxWidth=250,
                        cellStyle={'backgroundColor': '#fff3cd', 'border': '1px solid #ffeaa7'},  # Light yellow background
                        headerTooltip=f"Serial numbers should be unique for better organization."
                    )
                elif any(term in col_lower for term in ['description', 'comments']):
                    # Description columns - large text editor with higher flex ratio
                    gb.configure_column(
                        col, 
                        editable=permissions["can_edit"], 
                        cellEditor='agLargeTextCellEditor', 
                        cellEditorPopup=True,
                        flex=2,  # Give more space to description columns
                        minWidth=150
                    )
                elif any(term in col_lower for term in ['date', 'cal']):
                    # Date columns - smaller flex ratio
                    gb.configure_column(
                        col, 
                        editable=permissions["can_edit"], 
                        type=["dateColumnFilter", "customDateTimeFormat"], 
                        custom_format_string='yyyy-MM-dd',
                        flex=0.8,
                        minWidth=100
                    )
                elif any(term in col_lower for term in ['value', 'price', 'cost', 'year']):
                    # Numeric columns - smaller flex ratio
                    gb.configure_column(
                        col, 
                        editable=permissions["can_edit"], 
                        type=["numericColumn", "numberColumnFilter", "customNumericFormat"], 
                        precision=2,
                        flex=0.7,
                        minWidth=80
                    )
                else:
                    # Default columns - standard flex ratio
                    gb.configure_column(col, editable=permissions["can_edit"], flex=1, minWidth=100)
            
            # Enable selection (with checkboxes for row selection on the left)
            gb.configure_selection(
                selection_mode="multiple", 
                use_checkbox=True
            )
            
            # Enable pagination
            gb.configure_pagination(enabled=True, paginationPageSize=20)
            
            # Configure grid options for better checkbox functionality and left-side checkboxes
            gb.configure_grid_options(
                suppressColumnVirtualisation=False,
                suppressRowVirtualisation=False,
                enableRangeSelection=True,
                rowSelection='multiple',
                rowMultiSelectWithClick=True,  # Enable multi-select
                suppressRowDeselection=False,  # Allow deselection
                animateRows=True,
                suppressMovableColumns=False,
                enableCellTextSelection=True,
                headerHeight=40,  # Ensure header is tall enough for checkbox
                checkboxSelection=True,  # Enable checkbox selection on the left
                headerCheckboxSelection=True,  # Enable header checkbox for select all
                suppressRowClickSelection=False  # Allow row click selection
            )
            
            # COMMENTED OUT: Pre-select rows functionality for "select all" mode
            # if 'select_all_select_options_rows' in st.session_state:
            #     # Add JavaScript to select all visible rows on grid ready
            #     pre_select_js = """
            #     function onGridReady(params) {
            #         setTimeout(function() {
            #             params.api.selectAll();
            #         }, 100);
            #     }
            #     """
            #     
            #     # Custom JS for cell editing that doesn't trigger page refresh
            #     cell_edit_js = """
            #     function(event) {
            #         console.log('Cell value changed:', event);
            #         // Don't trigger Streamlit rerun on cell change
            #         // Let VALUE_CHANGED mode handle the updates
            #         return false;
            #     }
            #     """
            #     
            #     # Custom JS for better row selection feedback
            #     selection_changed_js = """
            #     function(event) {
            #         console.log('Selection changed:', event.api.getSelectedRows().length + ' rows selected');
            #         // Update selection indicator without full rerun
            #         const selectedRows = event.api.getSelectedRows();
            #         if (selectedRows.length > 0) {
            #             console.log('Selected rows:', selectedRows);
            #         }
            #         return true;
            #     }
            #     """
            #     
            #     # Enhanced cell editing JS to prevent unnecessary refreshes
            #     cell_edit_js = """
            #     function(event) {
            #         console.log('Cell value changed - Select All Mode:', event.oldValue, '->', event.newValue);
            #         // Minimal processing to prevent refresh
            #         return false;
            #     }
            #     """
            #     
            #     # Enhanced selection JS for better feedback
            #     selection_changed_js = """
            #     function(event) {
            #         const rowCount = event.api.getSelectedRows().length;
            #         console.log('Selection changed - Select All Mode:', rowCount + ' rows selected');
            #         return true;
            #     }
            #     """
            #     
            #     gb.configure_grid_options(
            #         onGridReady=JsCode(pre_select_js),
            #         onCellValueChanged=JsCode(cell_edit_js),
            #         onSelectionChanged=JsCode(selection_changed_js)
            #     )
            # else:
            # Optimized JS for normal mode - prevents refresh on first edit
            cell_edit_optimized_js = """
            function(event) {
                console.log('Cell edit (Normal Mode):', event.colDef.field, ':', event.oldValue, '->', event.newValue);
                // Let AgGrid handle the edit without triggering immediate Streamlit refresh
                // This prevents the "first edit refresh" issue
                return false;
            }
            """
            
            # Selection handling for normal mode
            selection_optimized_js = """
            function(event) {
                const selectedRows = event.api.getSelectedRows();
                console.log('Row selection (Normal Mode):', selectedRows.length + ' rows selected');
                // Ensure selection indicators are reliable
                if (selectedRows.length > 0) {
                    console.log('Selected row IDs:', selectedRows.map(row => row.ID || row.id || 'no-id'));
                }
                return true;
            }
            """
            
            gb.configure_grid_options(
                onCellValueChanged=JsCode(cell_edit_optimized_js),
                onSelectionChanged=JsCode(selection_optimized_js)
            )
            
            # Enable adding new rows (only for users with edit permissions)
            if permissions["can_edit"]:
                gb.configure_grid_options(
                    enableRangeSelection=True,
                    rowSelection='multiple',
                    suppressRowClickSelection=False,
                    suppressCellSelection=False,  # Allow cell selection without triggering rerun
                    suppressRowDeselection=False,
                    suppressMultiRangeSelection=False,
                    stopEditingWhenCellsLoseFocus=True,  # Auto-save when losing focus
                    undoRedoCellEditing=True,  # Enable undo/redo for better UX
                    undoRedoCellEditingLimit=20,  # Limit undo history
                    # Additional options for better cell editing
                    suppressClickEdit=False,  # Allow click to edit
                    enterMovesDownAfterEdit=True,  # Enter moves to next row after edit
                    enterMovesDown=True,  # Enter moves down in general
                    tabToNextCell=True,  # Tab moves to next cell
                    tabToNextRow=True,  # Tab moves to next row when at end
                    singleClickEdit=True,  # Enable single click to edit
                    suppressNavigationWithArrowKeys=False,  # Allow arrow key navigation
                    # Prevent unnecessary refreshes
                    deltaSort=False,
                    deltaColumnMode=False,
                    immutableData=False
                )
            
            # Check for select all mode and force grid reload if needed
            force_reload = 'force_select_options_grid_reload' in st.session_state and st.session_state['force_select_options_grid_reload']
            if force_reload:
                st.session_state['force_select_options_grid_reload'] = False
            
            # Initialize stable grid key to prevent unnecessary reloads
            if 'select_options_grid_key' not in st.session_state:
                st.session_state['select_options_grid_key'] = 0
            
            # Add New Row functionality will be moved AFTER AgGrid for better UX
            
            # COMMENTED OUT: Select all mode data handling
            # Determine what data to display in AgGrid
            grid_data = self.display_select_options_df
            # if (st.session_state.get('select_all_select_options_active', False) and 
            #     'select_all_select_options_rows' in st.session_state and
            #     len(st.session_state['select_all_select_options_rows']) < len(self.display_select_options_df)):
            #     # We're in select all mode with filtered data - create DataFrame from selected rows
            #     grid_data = pd.DataFrame(st.session_state['select_all_select_options_rows'])
            #     # Ensure it has the same column order as display_select_options_df
            #     if not grid_data.empty:
            #         grid_data = grid_data.reindex(columns=self.display_select_options_df.columns, fill_value='')
            
            # Display the AgGrid with optimized settings and anti-fading configuration
            grid_response = AgGrid(
                grid_data,
                gridOptions=gb.build(),
                data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                update_mode=GridUpdateMode.MODEL_CHANGED,  # Use MODEL_CHANGED as requested
                allow_unsafe_jscode=True,
                fit_columns_on_grid_load=True,  # Enable auto-fitting columns to content
                height=600,
                theme='streamlit',
                enable_enterprise_modules=False,
                reload_data=force_reload,
                key=f"select_options_grid_{st.session_state.get('select_options_grid_key', 0)}",
                custom_css={
                    ".ag-root-wrapper": {"background-color": "#ffffff !important", "transition": "none !important"},
                    ".ag-root": {"background-color": "#ffffff !important", "transition": "none !important"},
                    ".ag-body-viewport": {"background-color": "#ffffff !important", "transition": "none !important"},
                    ".ag-theme-streamlit": {"background-color": "#ffffff !important", "transition": "none !important"}
                }
            )
            
            # Get the selected rows for use in row management below
            selected_rows = grid_response['selected_rows']
            
            # Get the currently visible/filtered data from AgGrid (after internal filtering)
            visible_data = grid_response['data']  # This contains only the rows visible after AgGrid filtering
            
            # COMMENTED OUT: Refresh selection request handling
            # if st.session_state.get('refresh_select_options_selection_requested', False):
            #     if 'select_all_select_options_rows' in st.session_state:
            #         # Convert visible_data to the correct format if it's a DataFrame
            #         if isinstance(visible_data, pd.DataFrame):
            #             st.session_state['select_all_select_options_rows'] = visible_data.to_dict('records')
            #         else:
            #             st.session_state['select_all_select_options_rows'] = visible_data
            #         st.session_state['selection_auto_updated'] = True
            #     st.session_state['refresh_select_options_selection_requested'] = False  # Clear the flag
            
            # Check if AgGrid filtering resulted in empty data and we should show a message
            if len(visible_data) == 0 and len(grid_data) > 0:
                st.session_state['show_empty_filter_message'] = True
            
            # Track AgGrid internal filtering changes more conservatively
            current_visible_count = len(visible_data)
            
            # Create a more stable signature that doesn't change on every interaction
            if current_visible_count > 0:
                visible_signature = f"count_{current_visible_count}"
            else:
                visible_signature = "empty"
            
            # Initialize tracking if not exists
            if 'previous_visible_select_options_signature' not in st.session_state:
                st.session_state['previous_visible_select_options_signature'] = visible_signature
                st.session_state['select_options_signature_stable_count'] = 0
            
            # COMMENTED OUT: Select all mode selection update logic
            # if 'select_all_select_options_rows' in st.session_state and st.session_state['previous_visible_select_options_signature'] != visible_signature:
            #     # Only update if we have visible data (not empty)
            #     if current_visible_count > 0:
            #         # Convert visible_data to the correct format if it's a DataFrame
            #         if isinstance(visible_data, pd.DataFrame):
            #             st.session_state['select_all_select_options_rows'] = visible_data.to_dict('records')
            #         else:
            #             st.session_state['select_all_select_options_rows'] = visible_data
            #         st.session_state['selection_auto_updated'] = True
            #     else:
            #         st.session_state['show_empty_filter_message'] = True
            
            # Update the tracked signature
            st.session_state['previous_visible_select_options_signature'] = visible_signature
            
            # COMMENTED OUT: Select all mode selected rows override
            # if 'select_all_select_options_rows' in st.session_state:
            #     selected_rows = st.session_state['select_all_select_options_rows']
            
            # COMMENTED OUT: Selection auto-update notification
            # if st.session_state.get('selection_auto_updated', False) and st.session_state.get('show_selection_messages', True):
            #     st.success("🔄 **Selection automatically updated** to match filtered results!")
            #     st.session_state['selection_auto_updated'] = False  # Clear the flag
            
            # Show notification if showing all data due to empty AgGrid filters (reduce noise)  
            if st.session_state.get('show_empty_filter_message', False) and st.session_state.get('show_selection_messages', True):
                st.info("📄 **Showing all data** - AgGrid filters resulted in no matches, displaying complete dataset")
                st.session_state['show_empty_filter_message'] = False  # Clear the flag
            
            # Display selection help
            if selected_rows is not None and len(selected_rows) > 0:
                if 'select_all_select_options_rows' in st.session_state:
                    st.info(f"✅ **ALL {len(selected_rows)} row(s) selected** (Select All mode - automatically adapts to sidebar filters, use 'Refresh Selection' after AgGrid column filtering) - Use the buttons below for bulk operations")
                else:
                    st.info(f"✅ **{len(selected_rows)} row(s) selected** ")
            
            # Get edited data from AgGrid
            self.edited_select_options_df = grid_response['data']
            
            # Add New Row functionality AFTER AgGrid (only for users with edit permissions)
            if permissions["can_edit"]:
                st.markdown("---")  # Add separator
                self._render_add_new_row_section_select_options()
                st.markdown("---")  # Add separator
            
            # Save Changes to Database button moved to row management section for better UX
            
            # For non-edit users, show a read-only message and revert any changes
            if not permissions["can_edit"]:
                # Check if any changes were made by comparing with original data
                if not self.edited_select_options_df.equals(self.display_select_options_df):
                    st.info("ℹ️ **Read-Only Mode**: You can view dropdown options but cannot make changes. Contact an admin to modify data.")
                    # Revert changes to prevent unauthorized modifications
                    self.edited_select_options_df = self.display_select_options_df.copy()
                else:
                    st.info("👀 **Read-only mode** - You can view data but cannot make changes.")
            
            # Add row management below the grid (only for users with edit permissions)
            if permissions["can_edit"]:
                col1, col2, col3 = st.columns([1, 1, 2])
                
                # Note: The "Add New Row" button is now positioned below the grid for better user experience
                # via the form-based implementation below the grid
                
                with col1:
                    if st.button("💾 Save Changes to Database", key="save_changes_btn_select_options"):
                        self._save_select_options_changes_to_database()
                
                with col2:
                    if st.button("🗑️ Remove Selected", type="primary", key="delete_select_options_selected_btn"):
                        if selected_rows is not None and len(selected_rows) > 0:
                            if permissions.get("can_delete", True):  # Default to True for select options if not specified
                                try:
                                    # Handle different selected_rows formats
                                    if isinstance(selected_rows, pd.DataFrame):
                                        # Convert DataFrame to list of dictionaries
                                        selected_rows = selected_rows.to_dict('records')
                                    elif not isinstance(selected_rows, (list, tuple)):
                                        st.error(f"❌ Invalid selected_rows type: {type(selected_rows)}")
                                        return
                                    
                                    # Delete from database
                                    delete_count = 0
                                    errors = []
                                    
                                    for i, selected_row in enumerate(selected_rows):
                                        try:
                                            # Handle both dict and non-dict selected rows
                                            if isinstance(selected_row, dict) and 'index' in selected_row:
                                                result = self.Equipment_select_options.delete_one({"index": selected_row['index']})
                                                if result.deleted_count > 0:
                                                    delete_count += 1
                                                else:
                                                    errors.append(f"Row {i+1}: No document found with index {selected_row['index']}")
                                            elif hasattr(selected_row, 'get') and selected_row.get('index'):
                                                result = self.Equipment_select_options.delete_one({"index": selected_row.get('index')})
                                                if result.deleted_count > 0:
                                                    delete_count += 1
                                                else:
                                                    errors.append(f"Row {i+1}: No document found with index {selected_row.get('index')}")
                                            else:
                                                errors.append(f"Row {i+1}: Missing or invalid 'index' field - type: {type(selected_row)}, data: {selected_row}")
                                        except Exception as e:
                                            errors.append(f"Row {i+1}: Error - {str(e)}")
                                    
                                    if delete_count > 0:
                                        st.success(f"🗑️ Deleted {delete_count} selected rows from the database.")
                                        if errors:
                                            st.warning(f"⚠️ {len(errors)} row(s) had issues: {'; '.join(errors[:3])}{'...' if len(errors) > 3 else ''}")
                                        
                                        # Reload data
                                        self.Equipment_select_options_db_records = list(self.Equipment_select_options.find({}, {'_id': 0}))
                                        self.Equipment_select_options_db_df = pd.DataFrame(self.Equipment_select_options_db_records)
                                        if 'index' not in self.Equipment_select_options_db_df.columns:
                                            self.Equipment_select_options_db_df['index'] = self.Equipment_select_options_db_df.index
                                        
                                        # Reassign sequential IDs after deletion to maintain continuity
                                        if not self.Equipment_select_options_db_df.empty:
                                            self.Equipment_select_options_db_df['ID'] = [int(i) for i in range(1, len(self.Equipment_select_options_db_df) + 1)]
                                            # Update IDs in database
                                            for idx, row in self.Equipment_select_options_db_df.iterrows():
                                                if 'index' in row and pd.notna(row['index']):
                                                    self.Equipment_select_options.update_one(
                                                        {"index": row['index']},
                                                        {"$set": {"ID": row['ID']}}
                                                    )
                                            
                                            # Sort by ID after reassignment
                                            try:
                                                self.Equipment_select_options_db_df = self.Equipment_select_options_db_df.sort_values(
                                                    by='ID', ascending=True, na_position='last'
                                                ).reset_index(drop=True)
                                            except Exception:
                                                pass
                                        
                                        # Apply admin-saved column order after data reload
                                        self.Equipment_select_options_db_df = self._apply_column_order(self.Equipment_select_options_db_df, 'select_options')
                                        
                                        # COMMENTED OUT: Clear selection after deletion
                                        # if 'select_all_select_options_rows' in st.session_state:
                                        #     del st.session_state['select_all_select_options_rows']
                                        # st.session_state['select_all_select_options_active'] = False
                                        st.session_state['force_select_options_grid_reload'] = True
                                        st.session_state['select_options_grid_key'] = st.session_state.get('select_options_grid_key', 0) + 1
                                        # No st.rerun() needed - grid reload mechanism will handle the refresh
                                    else:
                                        error_msg = f"❌ Failed to delete selected rows. Errors: {'; '.join(errors[:5])}{'...' if len(errors) > 5 else ''}"
                                        st.error(error_msg)
                                except Exception as e:
                                    st.error(f"❌ Error during deletion: {str(e)}")
                            else:
                                st.error("🚫 You don't have permission to delete rows.")
                        else:
                            st.warning("⚠️ Please select rows first in order to delete them.")
                
                with col3:
                    # Add download selected option for admin (always show button)
                    if st.session_state.get("user_role") == "admin":
                        if selected_rows is not None and len(selected_rows) > 0:
                            selected_df = pd.DataFrame(selected_rows)
                            selected_csv = selected_df.to_csv(index=False)
                            st.download_button(
                                label=f"📤 Download Selected ({len(selected_rows)} rows)",
                                data=selected_csv,
                                file_name="selected_select_options.csv",
                                mime="text/csv",
                                key="download_select_options_selected_btn"
                            )
                        else:
                            st.button(
                                "📤 Download Selected (0 rows)", 
                                disabled=True, 
                                key="download_select_options_selected_disabled_btn",
                                help="Select rows first to enable download"
                            )
            
            # Add admin UI elements
            if st.session_state.get("user_role") == "admin":
                st.markdown("---")
                st.subheader("🔧 Admin Tools")
                
                # Save Filter Order UI
                self.save_select_options_filter_order_ui()
                
                # Download CSV UI
                self.download_select_options_ui()
                
                # Column Management UI
                self.add_new_column_to_select_options_db()
                self.delete_column_from_select_options_db_ui()
                self.rename_column_in_select_options_db_ui()

    def _render_add_new_row_section_select_options(self):
        """
        Renders a flexible 'Add New Row' section for Equipment Select Options.
        Automatically adapts to column structure changes.
        """
        st.subheader("➕ Add New Row")
        
        # Display persistent success message and debug info
        if 'add_row_success' in st.session_state:
            success_data = st.session_state['add_row_success']
            st.success(success_data['message'])
            st.info("💡 **Tip:** The row has been saved directly to the database.")
            
            # Show what was added
            st.write("**Added row:**")
            st.dataframe(pd.DataFrame([success_data['row_data']]), use_container_width=True)
            
            # Clear the success message after showing it
            if st.button("✅ Clear Success Message", key="clear_success_msg"):
                del st.session_state['add_row_success']
                st.rerun()
        
        # Display debug information
        if 'debug_add_row' in st.session_state:
            with st.expander("🔍 Debug Information"):
                debug_data = st.session_state['debug_add_row']
                st.json(debug_data)
                
                if st.button("🗑️ Clear Debug Info", key="clear_debug_info"):
                    del st.session_state['debug_add_row']
                    st.rerun()
        
        # Get current dataframe structure
        current_df = self.display_select_options_df if hasattr(self, 'display_select_options_df') and not self.display_select_options_df.empty else None
        
        if current_df is None:
            st.info("No data available to determine column structure.")
            return
        
        # Get columns and their types
        columns = current_df.columns.tolist()
        
        # Exclude certain columns from user input
        excluded_columns = ['index', 'uuid', 'check']  # System generated columns
        editable_columns = [col for col in columns if col.lower() not in [exc.lower() for exc in excluded_columns]]
        
        with st.form("add_new_row_select_options", clear_on_submit=True):
            st.markdown("**Fill in the details for the new row:**")
            
            # Filter out ID column for input (it will be auto-generated)
            input_columns = [col for col in editable_columns if col.lower() != 'id']
            
            # Calculate number of columns for layout - ALWAYS use horizontal layout
            num_cols = len(input_columns)
            # Always use all columns in one row for horizontal layout
            cols = st.columns(num_cols)
            
            new_row_data = {}
            col_idx = 0
            
            for column in input_columns:
                # Get current column for layout - always horizontal
                current_col = cols[col_idx]
                
                with current_col:
                    # Create appropriate placeholder based on column name
                    placeholder = f"Enter {column.lower().replace('_', ' ')}"
                    new_row_data[column] = st.text_input(
                        column, 
                        placeholder=placeholder,
                        help=f"Enter value for {column}"
                    )
                
                col_idx += 1
            
            # Submit button
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                submitted = st.form_submit_button("➕ Add New Row", use_container_width=True)
            
            if submitted:
                # Validate that at least some fields are filled
                filled_fields = [k for k, v in new_row_data.items() if v and str(v).strip()]
                
                if not filled_fields:
                    st.error("❌ Please fill in at least one field before adding the row.")
                    return
                
                # Create the new row with all columns from the original dataframe
                complete_new_row = {}
                
                for col in current_df.columns:
                    if col.lower() == 'id':
                        # Auto-generate ID
                        max_id = current_df['ID'].max() if 'ID' in current_df.columns else 0
                        # Convert to Python native type to avoid numpy issues
                        if hasattr(max_id, 'item'):  # numpy scalar
                            max_id = max_id.item()
                        complete_new_row[col] = int(max_id + 1)
                    elif col.lower() in [exc.lower() for exc in excluded_columns]:
                        # Auto-generate system columns
                        if col.lower() == 'index':
                            import uuid
                            complete_new_row[col] = str(uuid.uuid4())
                        elif col.lower() == 'uuid':
                            import uuid
                            complete_new_row[col] = str(uuid.uuid4())
                        elif col.lower() == 'check':
                            complete_new_row[col] = False
                        else:
                            complete_new_row[col] = ""
                    else:
                        # Use user input or empty string
                        complete_new_row[col] = new_row_data.get(col, "")
                
                # Add the new row to the dataframe and save directly to database
                try:
                    # Update the main Equipment_select_options_db_df first
                    if hasattr(self, 'Equipment_select_options_db_df') and self.Equipment_select_options_db_df is not None:
                        new_df = pd.concat([
                            self.Equipment_select_options_db_df, 
                            pd.DataFrame([complete_new_row])
                        ], ignore_index=True)
                        
                        # Save the new row directly to the database
                        try:
                            # Remove the '_id' field if it exists to avoid MongoDB conflicts
                            db_row = complete_new_row.copy()
                            if '_id' in db_row:
                                del db_row['_id']
                            
                            # Convert numpy types to Python native types for MongoDB compatibility
                            import numpy as np
                            for key, value in db_row.items():
                                if pd.isna(value):
                                    db_row[key] = ""  # Convert NaN to empty string
                                elif hasattr(value, 'item'):  # numpy scalar
                                    db_row[key] = value.item()
                                elif isinstance(value, np.integer):
                                    db_row[key] = int(value)
                                elif isinstance(value, np.floating):
                                    db_row[key] = float(value)
                                elif isinstance(value, np.bool_):
                                    db_row[key] = bool(value)
                                elif isinstance(value, (pd.Int64Dtype, pd.Float64Dtype)):
                                    db_row[key] = float(value) if pd.notna(value) else ""
                            
                            # Insert the new row into the database
                            result = self.Equipment_select_options.insert_one(db_row)
                            
                            if result.inserted_id:
                                # Update all DataFrames to reflect the database state
                                self.Equipment_select_options_db_df = new_df.copy()
                                self.display_select_options_df = new_df.copy()
                                self.edited_select_options_df = new_df.copy()
                                
                                # Store success message in session state so it persists
                                st.session_state['add_row_success'] = {
                                    'message': f"✅ New row added and saved to database successfully! Total rows: {len(new_df)}",
                                    'row_data': complete_new_row,
                                    'timestamp': pd.Timestamp.now()
                                }
                                
                                # Force grid refresh by incrementing grid key
                                if 'select_options_grid_key' in st.session_state:
                                    st.session_state['select_options_grid_key'] += 1
                                else:
                                    st.session_state['select_options_grid_key'] = 1
                                
                                # Debug info - store in session state
                                st.session_state['debug_add_row'] = {
                                    'attempt': st.session_state.get('debug_add_row', {}).get('attempt', 0) + 1,
                                    'dataframes_updated': True,
                                    'grid_key_incremented': True,
                                    'new_df_length': len(new_df),
                                    'complete_row': complete_new_row,
                                    'database_saved': True
                                }
                                
                                # Mark that we need to refresh the data display
                                st.session_state['refresh_display_needed'] = True
                                
                                # Rerun to refresh the grid - this ensures the new data appears
                                st.rerun()
                            else:
                                st.error("❌ Error: Failed to save row to database.")
                        except Exception as db_error:
                            st.error(f"❌ Database error: {str(db_error)}")
                            st.error("The row was not saved to the database. Please try again.")
                    else:
                        st.error("❌ Error: No data source available.")
                    
                except Exception as e:
                    st.error(f"❌ Error adding new row: {str(e)}")
                    st.error("Please check the data types and try again.")

    def _save_select_options_changes_to_database(self):
        """
        Save changes from the edited select options DataFrame to the database.
        Handles both updates to existing rows and insertion of new rows.
        """
        import uuid  # Import at the proper scope level
        import numpy as np  # Import numpy for type checking
        
        # Helper function to convert numpy types to Python native types
        def convert_to_python_type(value):
            """Convert numpy types to Python native types for MongoDB compatibility"""
            if pd.isna(value):
                return ""  # Convert NaN to empty string for MongoDB
            elif hasattr(value, 'item'):  # numpy scalar
                return value.item()
            elif isinstance(value, np.integer):
                return int(value)
            elif isinstance(value, np.floating):
                return float(value)
            elif isinstance(value, np.bool_):
                return bool(value)
            elif isinstance(value, (pd.Int64Dtype, pd.Float64Dtype)):
                return float(value) if pd.notna(value) else ""
            else:
                return value
        
        # Prevent accidental deletion if DataFrame is empty
        if self.edited_select_options_df is None or self.edited_select_options_df.empty:
            st.error("Cannot save: No data to save. The table is empty.")
            return

        # Smart save: Only save actual changes at the cell level
        original_data = self.Equipment_select_options_db_df.copy()
        edited_data = self.edited_select_options_df.copy()
        
        if len(edited_data) > len(original_data):
            st.info(f"🆕 **Detected {len(edited_data) - len(original_data)} new rows** to be saved to database.")
        elif len(edited_data) < len(original_data):
            st.warning(f"⚠️ **Detected {len(original_data) - len(edited_data)} fewer rows** - some may have been deleted.")
        
        if original_data.empty or edited_data.empty:
            st.info("No data to compare for changes.")
            return
        
        # Clean up invalid column names that might cause KeyErrors
        def clean_column_names(df):
            """Remove or rename invalid column names"""
            valid_columns = []
            for col in df.columns:
                # Skip columns with invalid names
                if pd.isna(col) or str(col).lower() in ['nan', 'none', ''] or str(col).strip() == '':
                    continue
                valid_columns.append(col)
            return df[valid_columns]
        
        # Apply column cleaning
        original_data = clean_column_names(original_data)
        edited_data = clean_column_names(edited_data)
        
        # Ensure both DataFrames have 'index' column for matching
        if 'index' not in original_data.columns or 'index' not in edited_data.columns:
            st.error("Index column missing - cannot determine which records to update.")
            return
        
        # Convert index columns to string for reliable matching
        original_data['index'] = original_data['index'].astype(str)
        edited_data['index'] = edited_data['index'].astype(str)
        
        # Fix missing or duplicate indices - ensure each row has a unique index
        import uuid
        
        # Check for and fix missing indices in original data
        missing_indices_orig = original_data['index'].isna() | (original_data['index'] == 'nan') | (original_data['index'] == 'None') | (original_data['index'] == '')
        if missing_indices_orig.any():
            # Batch update approach - much faster than individual updates
            updates_to_make = []
            
            for idx in original_data[missing_indices_orig].index:
                new_uuid = str(uuid.uuid4())
                original_data.loc[idx, 'index'] = new_uuid
                
                # Create update info for batch processing
                filter_query = {"index": {"$exists": False}}
                # Try to find a more specific filter if possible
                row_data = original_data.iloc[idx].to_dict()
                for col, val in row_data.items():
                    if col != 'index' and pd.notna(val):
                        filter_query = {col: val}
                        break
                
                updates_to_make.append({
                    'filter': filter_query,
                    'new_index': new_uuid
                })
            
            # Execute batch updates
            if updates_to_make:
                try:
                    for update_info in updates_to_make:
                        filter_query = update_info['filter']
                        self.Equipment_select_options.update_one(
                            filter_query,
                            {"$set": {"index": update_info['new_index']}}
                        )
                except Exception as e:
                    st.warning(f"Batch update encountered error: {e}")
        
        
        # Check for and fix missing indices in edited data
        missing_indices_edit = edited_data['index'].isna() | (edited_data['index'] == 'nan') | (edited_data['index'] == 'None') | (edited_data['index'] == '')
        if missing_indices_edit.any():
            for idx in edited_data[missing_indices_edit].index:
                # Use the corresponding index from original_data if it was fixed
                if idx < len(original_data):
                    edited_data.loc[idx, 'index'] = original_data.iloc[idx]['index']
                else:
                    # New row, assign new UUID
                    edited_data.loc[idx, 'index'] = str(uuid.uuid4())
        
        # Since we have issues with UUID-based matching, let's use row-by-row comparison instead
        # This is more reliable for detecting changes in data editor scenarios
        
        update_count = 0
        insert_count = 0
        changes_detected = []
        
        # Compare row by row using pandas index positions
        min_rows = min(len(original_data), len(edited_data))
        
        # First pass: identify which rows actually have changes
        rows_with_changes = []
        for row_idx in range(min_rows):
            original_row = original_data.iloc[row_idx]
            edited_row = edited_data.iloc[row_idx]
            
            # Skip comparison if critical data is missing
            if pd.isna(original_row.get('index')) or pd.isna(edited_row.get('index')):
                continue
                
            # Check if any column values have changed
            has_changes = False
            for col in original_data.columns:
                if col in edited_data.columns:
                    orig_val = original_row[col]
                    edit_val = edited_row[col]
                    
                    # Handle NaN comparisons properly
                    if pd.isna(orig_val) and pd.isna(edit_val):
                        continue  # Both are NaN, no change
                    elif pd.isna(orig_val) or pd.isna(edit_val):
                        has_changes = True  # One is NaN, the other isn't
                        break
                    elif str(orig_val) != str(edit_val):
                        has_changes = True
                        break
            
            if has_changes:
                rows_with_changes.append(row_idx)
        
        # Second pass: update only the rows that have changes
        for row_idx in rows_with_changes:
            try:
                original_row = original_data.iloc[row_idx]
                edited_row = edited_data.iloc[row_idx]
                
                # Convert pandas Series to dict and handle data types properly
                update_data = {}
                for col, value in edited_row.items():
                    update_data[col] = convert_to_python_type(value)
                
                # Update the document by its index
                filter_query = {"index": str(original_row['index'])}
                result = self.Equipment_select_options.update_one(
                    filter_query,
                    {"$set": update_data}
                )
                
                if result.modified_count > 0:
                    update_count += 1
                    changes_detected.append(f"Row {row_idx + 1}")
                
            except Exception as e:
                st.error(f"Error updating row {row_idx + 1}: {e}")
        
        # Handle new rows (if edited_data has more rows than original_data)
        if len(edited_data) > len(original_data):
            for row_idx in range(len(original_data), len(edited_data)):
                try:
                    new_row = edited_data.iloc[row_idx]
                    
                    # Convert new row to dict and handle data types
                    insert_data = {}
                    for col, value in new_row.items():
                        insert_data[col] = convert_to_python_type(value)
                    
                    # Ensure new row has a unique index
                    if not insert_data.get('index'):
                        insert_data['index'] = str(uuid.uuid4())
                    
                    self.Equipment_select_options.insert_one(insert_data)
                    insert_count += 1
                    changes_detected.append(f"New row {row_idx + 1}")
                    
                except Exception as e:
                    st.error(f"Error inserting new row {row_idx + 1}: {e}")
        
        # Show results
        if update_count > 0 or insert_count > 0:
            if update_count > 0 and insert_count > 0:
                st.success(f"💾 **Successfully saved!** Updated {update_count} rows and added {insert_count} new rows.")
            elif update_count > 0:
                st.success(f"💾 **Successfully updated {update_count} rows!**")
            else:
                st.success(f"💾 **Successfully added {insert_count} new rows!**")
            
            # with st.expander("📝 Show changed rows", expanded=False):
            #     st.write(f"**Modified:** {', '.join(changes_detected)}")
            
            # Reload the data to reflect changes
            with st.spinner('Refreshing data...'):
                self.Equipment_select_options_db_records = list(self.Equipment_select_options.find({}, {'_id': 0}))
                self.Equipment_select_options_db_df = pd.DataFrame(self.Equipment_select_options_db_records)
                
                # Ensure ID column exists and is properly formatted
                if not self.Equipment_select_options_db_df.empty:
                    if 'ID' not in self.Equipment_select_options_db_df.columns:
                        # Create sequential ID starting from 1, convert to regular Python int
                        self.Equipment_select_options_db_df['ID'] = [int(i) for i in range(1, len(self.Equipment_select_options_db_df) + 1)]
                        
                        # Update MongoDB records to include ID
                        for idx, row in self.Equipment_select_options_db_df.iterrows():
                            self.Equipment_select_options.update_one(
                                {"index": row['index']}, 
                                {"$set": {"ID": row['ID']}}
                            )
                
                # Apply column order and prepare display data
                self.Equipment_select_options_db_df = self._apply_column_order(self.Equipment_select_options_db_df, 'select_options')
                self.display_select_options_df = self._prepare_display_data_select_options()
                
            st.rerun()
        else:
            st.info("📋 No changes detected - nothing to save.")

    def initialize_select_options_data(self):
        """Initialize Equipment Select Options data and setup."""
        # Load Equipment Select Options data only when this tab is accessed
        if not hasattr(self, 'Equipment_select_options_db_df') or self.Equipment_select_options_db_df is None:
            with st.spinner('Loading select options data...'):
                self._initialize_select_options_data()
        
        # Process ID column and indexing only if data exists
        if not self.Equipment_select_options_db_df.empty:
            # Lazy ID column processing - only do this once per session
            if 'select_options_id_processed' not in st.session_state:
                with st.spinner('Setting up ID column...'):
                    self._process_select_options_id_column()
                st.session_state.select_options_id_processed = True
        
        # Sort DataFrame by ID column if it exists and is not empty
        if not self.Equipment_select_options_db_df.empty and 'ID' in self.Equipment_select_options_db_df.columns:
            try:
                # Sort by ID column in ascending order
                if pd.api.types.is_numeric_dtype(self.Equipment_select_options_db_df['ID']):
                    # Pure numeric column - sort numerically
                    self.Equipment_select_options_db_df = self.Equipment_select_options_db_df.sort_values(
                        by='ID', ascending=True, na_position='last'
                    ).reset_index(drop=True)
                else:
                    # Mixed or string column - try to convert to numeric for sorting
                    self.Equipment_select_options_db_df = self.Equipment_select_options_db_df.sort_values(
                        by='ID', 
                        ascending=True, 
                        na_position='last', 
                        key=lambda x: pd.to_numeric(x, errors='coerce').fillna(float('inf'))
                    ).reset_index(drop=True)
            except Exception as e:
                # If sorting fails, continue without sorting
                pass
        
        # Apply admin-saved column order (this will handle positioning of all columns including id and index)
        self.Equipment_select_options_db_df = self._apply_column_order(self.Equipment_select_options_db_df, 'select_options')

    def render_add_new_row_section_select_options(self):
        """
        Renders a flexible 'Add New Row' section for Equipment Select Options.
        Automatically adapts to column structure changes.
        """
        st.subheader("➕ Add New Row")
        
        # Display persistent success message and debug info
        if 'add_row_success' in st.session_state:
            success_data = st.session_state['add_row_success']
            st.success(success_data['message'])
            st.info("💡 **Tip:** The row has been saved directly to the database.")
            
            # Show what was added
            st.write("**Added row:**")
            st.dataframe(pd.DataFrame([success_data['row_data']]), use_container_width=True)
            
            # Clear the success message after showing it
            if st.button("✅ Clear Success Message", key="clear_success_msg"):
                del st.session_state['add_row_success']
                st.rerun()
        
        # Display debug information
        if 'debug_add_row' in st.session_state:
            with st.expander("🔍 Debug Information"):
                debug_data = st.session_state['debug_add_row']
                st.json(debug_data)
                
                if st.button("🗑️ Clear Debug Info", key="clear_debug_info"):
                    del st.session_state['debug_add_row']
                    st.rerun()
        
        # Get current dataframe structure
        current_df = self.display_select_options_df if hasattr(self, 'display_select_options_df') and not self.display_select_options_df.empty else None
        
        if current_df is None:
            st.info("No data available to determine column structure.")
            return
        
        # Get columns and their types
        columns = current_df.columns.tolist()
        
        # Exclude certain columns from user input
        excluded_columns = ['index', 'uuid', 'check']  # System generated columns
        editable_columns = [col for col in columns if col.lower() not in [exc.lower() for exc in excluded_columns]]
        
        with st.form("add_new_row_select_options", clear_on_submit=True):
            st.markdown("**Fill in the details for the new row:**")
            
            # Filter out ID column for input (it will be auto-generated)
            input_columns = [col for col in editable_columns if col.lower() != 'id']
            
            # Calculate number of columns for layout - ALWAYS use horizontal layout
            num_cols = len(input_columns)
            # Always use all columns in one row for horizontal layout
            cols = st.columns(num_cols)
            
            new_row_data = {}
            col_idx = 0
            
            for column in input_columns:
                # Get current column for layout - always horizontal
                current_col = cols[col_idx]
                
                with current_col:
                    # Create appropriate placeholder based on column name
                    placeholder = f"Enter {column.lower().replace('_', ' ')}"
                    new_row_data[column] = st.text_input(
                        column, 
                        placeholder=placeholder,
                        help=f"Enter value for {column}"
                    )
                
                col_idx += 1
            
            # Submit button
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                submitted = st.form_submit_button("➕ Add New Row", use_container_width=True)
            
            if submitted:
                # Validate that at least some fields are filled
                filled_fields = [k for k, v in new_row_data.items() if v and str(v).strip()]
                
                if not filled_fields:
                    st.error("❌ Please fill in at least one field before adding the row.")
                    return
                
                # Create the new row with all columns from the original dataframe
                complete_new_row = {}
                
                for col in current_df.columns:
                    if col.lower() == 'id':
                        # Auto-generate ID
                        max_id = current_df['ID'].max() if 'ID' in current_df.columns else 0
                        # Convert to Python native type to avoid numpy issues
                        if hasattr(max_id, 'item'):  # numpy scalar
                            max_id = max_id.item()
                        complete_new_row[col] = int(max_id + 1)
                    elif col.lower() in [exc.lower() for exc in excluded_columns]:
                        # Auto-generate system columns
                        if col.lower() == 'index':
                            complete_new_row[col] = str(uuid.uuid4())
                        elif col.lower() == 'uuid':
                            complete_new_row[col] = str(uuid.uuid4())
                        elif col.lower() == 'check':
                            complete_new_row[col] = False
                        else:
                            complete_new_row[col] = ""
                    else:
                        # Use user input or empty string
                        complete_new_row[col] = new_row_data.get(col, "")
                
                # Add the new row to the dataframe and save directly to database
                try:
                    # Update the main Equipment_select_options_db_df first
                    if hasattr(self, 'Equipment_select_options_db_df') and self.Equipment_select_options_db_df is not None:
                        new_df = pd.concat([
                            self.Equipment_select_options_db_df, 
                            pd.DataFrame([complete_new_row])
                        ], ignore_index=True)
                        
                        # Save the new row directly to the database
                        try:
                            # Remove the '_id' field if it exists to avoid MongoDB conflicts
                            db_row = complete_new_row.copy()
                            if '_id' in db_row:
                                del db_row['_id']
                            
                            # Convert numpy types to Python native types for MongoDB compatibility
                            for key, value in db_row.items():
                                if pd.isna(value):
                                    db_row[key] = ""  # Convert NaN to empty string
                                elif hasattr(value, 'item'):  # numpy scalar
                                    db_row[key] = value.item()
                                elif isinstance(value, np.integer):
                                    db_row[key] = int(value)
                                elif isinstance(value, np.floating):
                                    db_row[key] = float(value)
                                elif isinstance(value, np.bool_):
                                    db_row[key] = bool(value)
                                elif isinstance(value, (pd.Int64Dtype, pd.Float64Dtype)):
                                    db_row[key] = float(value) if pd.notna(value) else ""
                            
                            # Insert the new row into the database
                            result = self.Equipment_select_options.insert_one(db_row)
                            
                            if result.inserted_id:
                                # Update all DataFrames to reflect the database state
                                self.Equipment_select_options_db_df = new_df.copy()
                                self.display_select_options_df = new_df.copy()
                                self.edited_select_options_df = new_df.copy()
                                
                                # Store success message in session state so it persists
                                st.session_state['add_row_success'] = {
                                    'message': f"✅ New row added and saved to database successfully! Total rows: {len(new_df)}",
                                    'row_data': complete_new_row,
                                    'timestamp': pd.Timestamp.now()
                                }
                                
                                # Force grid refresh by incrementing grid key
                                if 'select_options_grid_key' in st.session_state:
                                    st.session_state['select_options_grid_key'] += 1
                                else:
                                    st.session_state['select_options_grid_key'] = 1
                                
                                # Debug info - store in session state
                                st.session_state['debug_add_row'] = {
                                    'attempt': st.session_state.get('debug_add_row', {}).get('attempt', 0) + 1,
                                    'dataframes_updated': True,
                                    'grid_key_incremented': True,
                                    'new_df_length': len(new_df),
                                    'complete_row': complete_new_row,
                                    'database_saved': True
                                }
                                
                                # Mark that we need to refresh the data display
                                st.session_state['refresh_display_needed'] = True
                                
                                # Rerun to refresh the grid - this ensures the new data appears
                                st.rerun()
                            else:
                                st.error("❌ Error: Failed to save row to database.")
                        except Exception as db_error:
                            st.error(f"❌ Database error: {str(db_error)}")
                            st.error("The row was not saved to the database. Please try again.")
                    else:
                        st.error("❌ Error: No data source available.")
                    
                except Exception as e:
                    st.error(f"❌ Error adding new row: {str(e)}")
                    st.error("Please check the data types and try again.")

    def save_select_options_changes_to_database(self):
        """
        Save changes from the edited select options DataFrame to the database.
        Handles both updates to existing rows and insertion of new rows.
        """
        # Helper function to convert numpy types to Python native types
        def convert_to_python_type(value):
            """Convert numpy types to Python native types for MongoDB compatibility"""
            if pd.isna(value):
                return ""  # Convert NaN to empty string for MongoDB
            elif hasattr(value, 'item'):  # numpy scalar
                return value.item()
            elif isinstance(value, np.integer):
                return int(value)
            elif isinstance(value, np.floating):
                return float(value)
            elif isinstance(value, np.bool_):
                return bool(value)
            elif isinstance(value, (pd.Int64Dtype, pd.Float64Dtype)):
                return float(value) if pd.notna(value) else ""
            else:
                return value
        
        # Prevent accidental deletion if DataFrame is empty
        if self.edited_select_options_df is None or self.edited_select_options_df.empty:
            st.error("Cannot save: No data to save. The table is empty.")
            return

        # Smart save: Only save actual changes at the cell level
        original_data = self.Equipment_select_options_db_df.copy()
        edited_data = self.edited_select_options_df.copy()
        
        if len(edited_data) > len(original_data):
            st.info(f"🆕 **Detected {len(edited_data) - len(original_data)} new rows** to be saved to database.")
        elif len(edited_data) < len(original_data):
            st.warning(f"⚠️ **Detected {len(original_data) - len(edited_data)} fewer rows** - some may have been deleted.")
        
        if original_data.empty or edited_data.empty:
            st.info("No data to compare for changes.")
            return
        
        # Clean up invalid column names that might cause KeyErrors
        def clean_column_names(df):
            """Remove or rename invalid column names"""
            valid_columns = []
            for col in df.columns:
                # Skip columns with invalid names
                if pd.isna(col) or str(col).lower() in ['nan', 'none', ''] or str(col).strip() == '':
                    continue
                valid_columns.append(col)
            return df[valid_columns]
        
        # Apply column cleaning
        original_data = clean_column_names(original_data)
        edited_data = clean_column_names(edited_data)
        
        # Ensure both DataFrames have 'index' column for matching
        if 'index' not in original_data.columns or 'index' not in edited_data.columns:
            st.error("Index column missing - cannot determine which records to update.")
            return
        
        # Convert index columns to string for reliable matching
        original_data['index'] = original_data['index'].astype(str)
        edited_data['index'] = edited_data['index'].astype(str)
        
        # Fix missing or duplicate indices - ensure each row has a unique index
        
        # Check for and fix missing indices in original data
        missing_indices_orig = original_data['index'].isna() | (original_data['index'] == 'nan') | (original_data['index'] == 'None') | (original_data['index'] == '')
        if missing_indices_orig.any():
            # Batch update approach - much faster than individual updates
            updates_to_make = []
            
            for idx in original_data[missing_indices_orig].index:
                new_uuid = str(uuid.uuid4())
                original_data.loc[idx, 'index'] = new_uuid
                
                # Create update info for batch processing
                filter_query = {"index": {"$exists": False}}
                # Try to find a more specific filter if possible
                row_data = original_data.iloc[idx].to_dict()
                for col, val in row_data.items():
                    if col != 'index' and pd.notna(val):
                        filter_query = {col: val}
                        break
                
                updates_to_make.append({
                    'filter': filter_query,
                    'new_index': new_uuid
                })
            
            # Execute batch updates
            if updates_to_make:
                try:
                    for update_info in updates_to_make:
                        filter_query = update_info['filter']
                        self.Equipment_select_options.update_one(
                            filter_query,
                            {"$set": {"index": update_info['new_index']}}
                        )
                except Exception as e:
                    st.warning(f"Batch update encountered error: {e}")
        
        
        # Check for and fix missing indices in edited data
        missing_indices_edit = edited_data['index'].isna() | (edited_data['index'] == 'nan') | (edited_data['index'] == 'None') | (edited_data['index'] == '')
        if missing_indices_edit.any():
            for idx in edited_data[missing_indices_edit].index:
                # Use the corresponding index from original_data if it was fixed
                if idx < len(original_data):
                    edited_data.loc[idx, 'index'] = original_data.iloc[idx]['index']
                else:
                    # New row, assign new UUID
                    edited_data.loc[idx, 'index'] = str(uuid.uuid4())
        
        # Since we have issues with UUID-based matching, let's use row-by-row comparison instead
        # This is more reliable for detecting changes in data editor scenarios
        
        update_count = 0
        insert_count = 0
        changes_detected = []
        
        # Compare row by row using pandas index positions
        min_rows = min(len(original_data), len(edited_data))
        
        # First pass: identify which rows actually have changes
        rows_with_changes = []
        for row_idx in range(min_rows):
            original_row = original_data.iloc[row_idx]
            edited_row = edited_data.iloc[row_idx]
            
            # Skip comparison if critical data is missing
            if pd.isna(original_row.get('index')) or pd.isna(edited_row.get('index')):
                continue
                
            # Check if any column values have changed
            has_changes = False
            for col in original_data.columns:
                if col in edited_data.columns:
                    orig_val = original_row[col]
                    edit_val = edited_row[col]
                    
                    # Handle NaN comparisons properly
                    if pd.isna(orig_val) and pd.isna(edit_val):
                        continue  # Both are NaN, no change
                    elif pd.isna(orig_val) or pd.isna(edit_val):
                        has_changes = True  # One is NaN, the other isn't
                        break
                    elif str(orig_val) != str(edit_val):
                        has_changes = True
                        break
            
            if has_changes:
                rows_with_changes.append(row_idx)
        
        # Second pass: update only the rows that have changes
        for row_idx in rows_with_changes:
            try:
                original_row = original_data.iloc[row_idx]
                edited_row = edited_data.iloc[row_idx]
                
                # Convert pandas Series to dict and handle data types properly
                update_data = {}
                for col, value in edited_row.items():
                    update_data[col] = convert_to_python_type(value)
                
                # Update the document by its index
                filter_query = {"index": str(original_row['index'])}
                result = self.Equipment_select_options.update_one(
                    filter_query,
                    {"$set": update_data}
                )
                
                if result.modified_count > 0:
                    update_count += 1
                    changes_detected.append(f"Row {row_idx + 1}")
                
            except Exception as e:
                st.error(f"Error updating row {row_idx + 1}: {e}")
        
        # Handle new rows (if edited_data has more rows than original_data)
        if len(edited_data) > len(original_data):
            for row_idx in range(len(original_data), len(edited_data)):
                try:
                    new_row = edited_data.iloc[row_idx]
                    
                    # Convert new row to dict and handle data types
                    insert_data = {}
                    for col, value in new_row.items():
                        insert_data[col] = convert_to_python_type(value)
                    
                    # Ensure new row has a unique index
                    if not insert_data.get('index'):
                        insert_data['index'] = str(uuid.uuid4())
                    
                    self.Equipment_select_options.insert_one(insert_data)
                    insert_count += 1
                    changes_detected.append(f"New row {row_idx + 1}")
                    
                except Exception as e:
                    st.error(f"Error inserting new row {row_idx + 1}: {e}")
        
        # Show results
        if update_count > 0 or insert_count > 0:
            if update_count > 0 and insert_count > 0:
                st.success(f"💾 **Successfully saved!** Updated {update_count} rows and added {insert_count} new rows.")
            elif update_count > 0:
                st.success(f"💾 **Successfully updated {update_count} rows!**")
            else:
                st.success(f"💾 **Successfully added {insert_count} new rows!**")
            
            with st.expander("📝 Show changed rows", expanded=False):
                st.write(f"**Modified:** {', '.join(changes_detected)}")
            
            # Reload the data to reflect changes
            with st.spinner('Refreshing data...'):
                self.Equipment_select_options_db_records = list(self.Equipment_select_options.find({}, {'_id': 0}))
                self.Equipment_select_options_db_df = pd.DataFrame(self.Equipment_select_options_db_records)
                
                # Ensure ID column exists and is properly formatted
                if not self.Equipment_select_options_db_df.empty:
                    if 'ID' not in self.Equipment_select_options_db_df.columns:
                        # Create sequential ID starting from 1, convert to regular Python int
                        self.Equipment_select_options_db_df['ID'] = [int(i) for i in range(1, len(self.Equipment_select_options_db_df) + 1)]
                        
                        # Update MongoDB records to include ID
                        for idx, row in self.Equipment_select_options_db_df.iterrows():
                            self.Equipment_select_options.update_one(
                                {"index": row['index']}, 
                                {"$set": {"ID": row['ID']}}
                            )
                
                # Apply column order and prepare display data
                self.Equipment_select_options_db_df = self._apply_column_order(self.Equipment_select_options_db_df, 'select_options')
                self.display_select_options_df = self._prepare_display_data_select_options()
                
            st.rerun()
        else:
            st.info("📋 No changes detected - nothing to save.")
