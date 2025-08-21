"""
Equipment Records Page for Equipment Management System
Extracted from app.py to provide standalone equipment records functionality.
"""

import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode, JsCode
import json
from pathlib import Path
from datetime import datetime
import uuid
import time
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Import authentication functionality
try:
    from login_and_signup import AuthenticationManager
except ImportError:
    AuthenticationManager = None

# Import general utility functions
from general_functions import is_admin, apply_column_order, load_column_order, save_column_order, save_filter_order

# Thinking GIF functionality removed for performance


class EquipmentRecordsSystem:
    """
    Standalone Equipment Records System for managing equipment data.
    Extracted from main app to provide focused equipment records functionality.
    """
    
    def __init__(self, mongo_connection_string="mongodb://ascy00075.sc.altera.com:27017/mongo?readPreference=primary&ssl=false"):
        """
        Initialize the Equipment Records System.
        
        Args:
            mongo_connection_string (str): MongoDB connection string
        """
        self.mongo_connection_string = mongo_connection_string
        
        # Initialize MongoDB connection
        self._connect_to_database()
        
        # Initialize data structures
        self.df = None
        self.db_df = None
        self.display_df = None
        self.edited_df = None
        self.unique_id_cols = []
        self.serial_cols = []
        self.search_cols = []
        
        # Initialize authentication manager if available
        if AuthenticationManager:
            self.auth_manager = AuthenticationManager()
        else:
            self.auth_manager = None
    
    def _connect_to_database(self):
        """Connect to MongoDB database."""
        try:
            self.client = MongoClient(self.mongo_connection_string)
            self.client.admin.command("ping")
            self.db = self.client["Equipment_DB"]
            self.Equipment_collection = self.db["Equipment"]
            self.Equipment_select_options = self.db["Equipment_select_options"]
            return True
        except Exception as e:
            st.error(f"MongoDB connection failed: {e}")
            return False
    
    def _identify_column_types(self):
        """Identify different types of columns in the DataFrame."""
        if self.df is None or self.df.empty:
            self.unique_id_cols = []
            self.serial_cols = []
            self.search_cols = []
            return
        
        # Identify unique ID columns
        self.unique_id_cols = []
        for col in self.df.columns:
            col_lower = col.lower()
            if any(term in col_lower for term in ['id', '_id']) and 'uuid' not in col_lower:
                self.unique_id_cols.append(col)
        
        # Identify serial number columns
        self.serial_cols = []
        for col in self.df.columns:
            col_lower = col.lower()
            if any(term in col_lower for term in ['serial', 'ser_num', 'serial_number']):
                self.serial_cols.append(col)
        
        # Identify searchable columns (exclude system columns)
        system_cols = {'_id', 'uuid', 'index', 'check'}
        self.search_cols = [col for col in self.df.columns if col not in system_cols]
    
    def _load_excluded_filter_columns(self, default_excluded_cols):
        """Load excluded filter columns from JSON file."""
        try:
            with open('excluded_filter_columns.json', 'r') as f:
                excluded_cols = json.load(f)
                # Handle both list format and dictionary format
                if isinstance(excluded_cols, dict):
                    # If it's a dictionary, look for 'excluded_columns' key
                    if 'excluded_columns' in excluded_cols:
                        return excluded_cols['excluded_columns']
                    else:
                        # If no 'excluded_columns' key, return default
                        return default_excluded_cols
                elif isinstance(excluded_cols, list):
                    # If it's already a list, return as is
                    return excluded_cols
                else:
                    # If it's neither, return default
                    return default_excluded_cols
        except FileNotFoundError:
            return default_excluded_cols
        except Exception:
            return default_excluded_cols
    
    def _load_filter_order(self, all_columns):
        """Load filter order from JSON file."""
        try:
            with open('filter_order_preferences.json', 'r') as f:
                filter_order = json.load(f)
                # Handle both direct array format and dictionary format
                if isinstance(filter_order, dict):
                    # If it's a dictionary, look for 'equipment_filters' key
                    if 'equipment_filters' in filter_order:
                        saved_order = filter_order['equipment_filters']
                        # Ensure all current filters are included (in case new filters were added)
                        missing_filters = [f for f in all_columns if f not in saved_order]
                        # Add any missing filters at the end
                        return saved_order + missing_filters
                    else:
                        # If no 'equipment_filters' key, return default
                        return all_columns
                elif isinstance(filter_order, list):
                    # If it's already a list, return as is
                    return filter_order
                else:
                    # If it's neither, return default
                    return all_columns
        except FileNotFoundError:
            return all_columns
        except Exception:
            return all_columns
    
    def _apply_column_order(self, df, data_type):
        """Apply saved column order to DataFrame."""
        return apply_column_order(df, data_type)
    
    def _save_column_order(self, table_type, column_order):
        """Save column order preference for a specific table type."""
        return save_column_order(table_type, column_order)
    
    def _load_column_order(self, table_type, default_columns):
        """Load saved column order preference for a specific table type."""
        return load_column_order(table_type, default_columns)
    
    def _save_filter_order(self, filter_order):
        """Save filter order preference to a JSON file."""
        return save_filter_order(filter_order)
    
    def _should_have_dropdown(self, col_name):
        """Check if a column should have dropdown functionality."""
        # Check if column exists in Equipment Select Options
        try:
            if hasattr(self, 'Equipment_select_options_db_df') and self.Equipment_select_options_db_df is not None:
                return col_name in self.Equipment_select_options_db_df.columns
        except Exception:
            pass
        return False
    
    def _is_checkbox_column(self, col_name):
        """Check if a column should be treated as a checkbox column."""
        col_lower = col_name.lower()
        checkbox_indicators = ['check', 'checkbox', 'yes_no', 'yesno', 'active', 'enabled', 'status']
        return any(indicator in col_lower for indicator in checkbox_indicators)
    
    def _create_delete_query(self, row):
        """Create a delete query for a row using available unique identifiers."""
        for col in self.unique_id_cols:
            if col in row and pd.notna(row[col]) and str(row[col]).strip():
                return {col: row[col]}
        return None
    
    def _get_values_for_deletion(self, selected_df, col):
        """Get values for deletion from a specific column."""
        values = selected_df[col].dropna().unique()
        return [str(v).strip() for v in values if str(v).strip()]
    
    def _validate_serials_in_realtime(self):
        """Validate serial numbers in real-time and provide immediate feedback."""
        if self.edited_df is None or self.edited_df.empty:
            return True, [], []
        
        # Find serial columns
        serial_columns = [col for col in self.edited_df.columns if any(term in col.lower() for term in ['serial', 'ser_num', 'serial_number'])]
        
        if not serial_columns:
            return True, [], []
        
        error_messages = []
        duplicate_serials = []
        
        for serial_col in serial_columns:
            # Check for duplicates within the current dataframe
            serials = self.edited_df[serial_col].dropna()
            serials = serials[serials != '']
            
            if len(serials) != len(serials.unique()):
                # Find duplicate values
                duplicates = serials[serials.duplicated()].unique()
                for dup in duplicates:
                    duplicate_serials.append(f"{serial_col}: {dup}")
                error_messages.append(f"❌ **{serial_col}**: Duplicate values found: {', '.join([str(d) for d in duplicates])}")
        
        is_valid = len(error_messages) == 0
        return is_valid, error_messages, duplicate_serials
    
    def _validate_unique_serials(self, df_to_check):
        """Validate that serial numbers are unique in the DataFrame."""
        if not self.serial_cols:
            return True, [], None
        
        serial_col = self.serial_cols[0]  # Use the first serial column
        
        if serial_col not in df_to_check.columns:
            return True, [], None
        
        # Get non-empty serial numbers
        serials = df_to_check[serial_col].dropna()
        serials = serials[serials.astype(str).str.strip() != '']
        
        if serials.empty:
            return True, [], None
        
        # Check for duplicates within the DataFrame
        duplicates = serials[serials.duplicated(keep=False)]
        
        if not duplicates.empty:
            duplicate_values = duplicates.unique().tolist()
            error_msg = f"❌ Duplicate serial numbers found: {', '.join(map(str, duplicate_values))}"
            return False, duplicate_values, error_msg
        
        return True, [], None
    
    def _validate_serials_against_database(self, df_to_check, exclude_current=True):
        """Validate serial numbers against existing database records."""
        if not self.serial_cols:
            return True, [], None
        
        serial_col = self.serial_cols[0]
        
        if serial_col not in df_to_check.columns:
            return True, [], None
        
        # Get non-empty serial numbers from the DataFrame
        serials = df_to_check[serial_col].dropna()
        serials = serials[serials.astype(str).str.strip() != '']
        
        if serials.empty:
            return True, [], None
        
        # If excluding current records, get the current display data to compare against
        current_serials = set()
        if exclude_current and hasattr(self, 'display_df') and not self.display_df.empty:
            if serial_col in self.display_df.columns:
                current_serials = set(self.display_df[serial_col].dropna().astype(str).str.strip())
                current_serials.discard('')  # Remove empty strings
        
        # Check against database
        existing_serials = []
        for serial in serials.unique():
            serial_str = str(serial).strip()
            
            # Skip if this serial is in our current display data (it's being edited)
            if exclude_current and serial_str in current_serials:
                continue
                
            # Query database for this serial number
            query = {serial_col: serial_str}
            existing_record = self.Equipment_collection.find_one(query)
            
            if existing_record:
                existing_serials.append(serial_str)
        
        if existing_serials:
            error_msg = f"❌ Serial numbers already exist in database: {', '.join(map(str, existing_serials))}"
            return False, existing_serials, error_msg
        
        return True, [], None
    
    def _initialize_equipment_data(self):
        """Initialize Equipment Records data with optimized loading."""
        # PERFORMANCE OPTIMIZATION: Skip database loading if we have cached data
        if st.session_state.get('data_already_loaded', False) and 'cached_df' in st.session_state:
            # Use cached data to avoid database reload
            self.df = st.session_state['cached_df'].copy()
            self.display_df = st.session_state['cached_display_df'].copy()
            self.db_df = self.df.copy()
            
            # Clear the cache flags
            st.session_state['data_already_loaded'] = False
            if 'cached_df' in st.session_state:
                del st.session_state['cached_df']
            if 'cached_display_df' in st.session_state:
                del st.session_state['cached_display_df']
            
            return
        
        # Load Equipment Records data
        db_records = list(self.Equipment_collection.find({}, {'_id': 0}))
        self.df = pd.DataFrame(db_records)
        
        # Ensure self.df is always a DataFrame (even if empty)
        self.df = self.df if not self.df.empty else pd.DataFrame()
        
        # Load Equipment Select Options data for dropdown functionality
        try:
            # PERFORMANCE OPTIMIZATION: Skip loading if we already have cached data
            if hasattr(self, 'Equipment_select_options_db_df') and self.Equipment_select_options_db_df is not None:
                # Already loaded, skip
                pass
            else:
                select_options_records = list(self.Equipment_select_options.find({}, {'_id': 0}))
                self.Equipment_select_options_db_df = pd.DataFrame(select_options_records)
                
                # Ensure we have a valid DataFrame
                if self.Equipment_select_options_db_df is None:
                    self.Equipment_select_options_db_df = pd.DataFrame()
        except Exception as e:
            st.error(f"❌ Error loading Equipment Select Options data: {str(e)}")
            self.Equipment_select_options_db_df = pd.DataFrame()
        
        # Only do sorting and column operations if data exists
        if not self.df.empty:
            self._identify_column_types()  # Identify columns first
            
            # Apply admin-saved column order
            self.df = self._apply_column_order(self.df, 'equipment')
            
            # Basic sorting by first available ID column (lightweight)
            if hasattr(self, 'unique_id_cols') and self.unique_id_cols:
                for id_col in self.unique_id_cols:
                    if id_col in self.df.columns:
                        try:
                            if pd.api.types.is_numeric_dtype(self.df[id_col]):
                                self.df = self.df.sort_values(by=id_col, ascending=True, na_position='last').reset_index(drop=True)
                            else:
                                self.df = self.df.sort_values(
                                    by=id_col, 
                                    ascending=True, 
                                    na_position='last', 
                                    key=lambda x: pd.to_numeric(x, errors='coerce').fillna(float('inf'))
                                ).reset_index(drop=True)
                            break
                        except Exception:
                            continue
        else:
            # If DataFrame is empty, still initialize column types with empty lists
            self._identify_column_types()
    
    def get_user_permissions(self):
        """Get user permissions from authentication manager."""
        if self.auth_manager:
            return self.auth_manager.get_user_permissions()
        else:
            # Default permissions for standalone mode
            return {
                "can_edit": True,
                "can_delete": True,
                "can_manage_users": True
            }
    
    def is_admin(self):
        """Check if current user is admin."""
        if self.auth_manager:
            # Get current username from session state
            username = st.session_state.get('username')
            if username:
                return self.auth_manager.is_admin_user(username)
            else:
                return False
        else:
            return True  # Default to admin in standalone mode
    
    def Equipment_Filters(self):
        """Main Equipment Records display and filtering function."""
        # --- Inline filter column (not sidebar) ---
        # Print the current filter state
        st.markdown('**🔍Equipment_Filters:**')
        
        # Handle case where DataFrame is empty or None
        if self.df is None or self.df.empty:
            st.info("📋 No equipment records found in the database. Add some data to get started!")
            st.markdown("### Equipment Records")
            st.write("Database is empty. Please add some equipment records.")
            return
        
        # Ensure column types are identified for sorting
        self._identify_column_types()
        
        filter_columns = {}
        filtered_df = self.df.copy()
        filter_widgets = []
        filter_cols = []
        
        # Load saved excluded columns preference or use default
        default_excluded_cols = ["ID", "check", "uuid"]  # Default excluded columns
        excluded_filter_cols = self._load_excluded_filter_columns(default_excluded_cols)

        # Get ALL filterable columns (not just specific types)
        all_filterable_columns = []
        for col in filtered_df.columns:
            if col not in excluded_filter_cols:
                all_filterable_columns.append(col)

        # Load saved filter order preference
        ordered_filters = self._load_filter_order(all_filterable_columns)
        
        # Build filter_cols in the saved order
        for col in ordered_filters:
            if col in filtered_df.columns and col not in excluded_filter_cols:
                filter_cols.append(col)
        
        # Debug information removed for cleaner UI

        left_col, right_col = st.columns([1, 4])
        with left_col:
            # Track current filter state to detect changes
            current_filter_state = {}
            filter_changed = False
            search_text = st.text_input('🔍 Search', key='equipment_search')
            current_filter_state['equipment_search'] = search_text
            if search_text:
                mask = pd.Series([False] * len(filtered_df))
                for col in self.search_cols:
                    if col in filtered_df.columns:
                        mask |= filtered_df[col].astype(str).str.contains(search_text, case=False, na=False)
                filtered_df = filtered_df[mask]

            for col_name in filter_cols:
                options = ['All'] + sorted([str(val) for val in filtered_df[col_name].dropna().unique() if str(val).strip() != ''])
                selected = st.selectbox(f"{col_name}", options, key=f'equipment_{col_name}')
                filter_columns[col_name] = selected
                current_filter_state[f'equipment_{col_name}'] = selected
                if selected != 'All':
                    filtered_df = filtered_df[filtered_df[col_name] == selected]
            
            # Check if filters have changed
            if 'previous_filter_state' not in st.session_state:
                st.session_state['previous_filter_state'] = {}
            
            if st.session_state['previous_filter_state'] != current_filter_state:
                filter_changed = True
                st.session_state['previous_filter_state'] = current_filter_state
                
                # If we were in select all mode and filters changed, update the selection
                if 'select_all_rows' in st.session_state:
                    # Set flag to reapply select all after filtering
                    st.session_state['reapply_select_all'] = True
 
        with right_col:
            # Include any newly added rows from session state that haven't been saved yet
            if 'newly_added_rows' in st.session_state and st.session_state.newly_added_rows:
                # Convert newly added rows to DataFrame
                new_rows_df = pd.DataFrame(st.session_state.newly_added_rows)
                # Ensure they have the same columns as filtered_df
                for col in filtered_df.columns:
                    if col not in new_rows_df.columns:
                        new_rows_df[col] = None  # Use None instead of empty string
                # Combine with filtered data - PUT NEW ROWS AT THE BEGINNING
                self.display_df = pd.concat([new_rows_df, filtered_df], ignore_index=True)
                # Apply admin-saved column order
                self.display_df = self._apply_column_order(self.display_df, 'equipment')
                
                # Sort display_df by ID column consistently (including new rows)
                if not self.display_df.empty and hasattr(self, 'unique_id_cols') and self.unique_id_cols:
                    for id_col in self.unique_id_cols:
                        if id_col in self.display_df.columns:
                            try:
                                # Enhanced sorting logic to handle different ID types better
                                if pd.api.types.is_numeric_dtype(self.display_df[id_col]):
                                    # Pure numeric column - sort numerically
                                    self.display_df = self.display_df.sort_values(by=id_col, ascending=True, na_position='last').reset_index(drop=True)
                                else:
                                    # Mixed or string column - try to convert to numeric for sorting
                                    self.display_df = self.display_df.sort_values(
                                        by=id_col, 
                                        ascending=True, 
                                        na_position='last', 
                                        key=lambda x: pd.to_numeric(x, errors='coerce').fillna(float('inf'))
                                    ).reset_index(drop=True)
                                break
                            except Exception:
                                continue
                elif not self.display_df.empty:
                    # Fallback: look for any column with 'id' in name
                    id_columns = [col for col in self.display_df.columns if 'id' in col.lower() and col.lower() != '_id']
                    if id_columns:
                        id_col = id_columns[0]
                        try:
                            if pd.api.types.is_numeric_dtype(self.display_df[id_col]):
                                self.display_df = self.display_df.sort_values(by=id_col, ascending=True, na_position='last').reset_index(drop=True)
                            else:
                                self.display_df = self.display_df.sort_values(
                                    by=id_col, 
                                    ascending=True, 
                                    na_position='last', 
                                    key=lambda x: pd.to_numeric(x, errors='coerce').fillna(float('inf'))
                                ).reset_index(drop=True)
                        except Exception:
                            pass
                
                # Check if we need to reapply select all after filtering (with new rows)
                if 'reapply_select_all' in st.session_state and st.session_state['reapply_select_all']:
                    # Update the select all rows with the new filtered data including new rows
                    st.session_state['select_all_rows'] = self.display_df.to_dict('records')
                    st.session_state['reapply_select_all'] = False
                    # Force grid reload to show the new selection
                    st.session_state['force_grid_reload'] = True
                    st.session_state['grid_key'] = st.session_state.get('grid_key', 0) + 1
            else:
                self.display_df = filtered_df if filtered_df is not None else self.df
                # Apply admin-saved column order
                self.display_df = self._apply_column_order(self.display_df, 'equipment')
            
            # Sort display_df by ID column consistently
            if not self.display_df.empty and hasattr(self, 'unique_id_cols') and self.unique_id_cols:
                for id_col in self.unique_id_cols:
                    if id_col in self.display_df.columns:
                        try:
                            # Enhanced sorting logic to handle different ID types better
                            if pd.api.types.is_numeric_dtype(self.display_df[id_col]):
                                # Pure numeric column - sort numerically
                                self.display_df = self.display_df.sort_values(by=id_col, ascending=True, na_position='last').reset_index(drop=True)
                            else:
                                # Mixed or string column - try to convert to numeric for sorting
                                self.display_df = self.display_df.sort_values(
                                    by=id_col, 
                                    ascending=True, 
                                    na_position='last', 
                                    key=lambda x: pd.to_numeric(x, errors='coerce').fillna(float('inf'))
                                ).reset_index(drop=True)
                            break
                        except Exception as e:
                            continue
            elif not self.display_df.empty:
                # Fallback: look for any column with 'id' in name
                id_columns = [col for col in self.display_df.columns if 'id' in col.lower() and col.lower() != '_id']
                if id_columns:
                    id_col = id_columns[0]
                    try:
                        if pd.api.types.is_numeric_dtype(self.display_df[id_col]):
                            self.display_df = self.display_df.sort_values(by=id_col, ascending=True, na_position='last').reset_index(drop=True)
                        else:
                            self.display_df = self.display_df.sort_values(
                                by=id_col, 
                                ascending=True, 
                                na_position='last', 
                                key=lambda x: pd.to_numeric(x, errors='coerce').fillna(float('inf'))
                            ).reset_index(drop=True)
                    except Exception:
                        pass
            
            # Check if we need to reapply select all after filtering
            if 'reapply_select_all' in st.session_state and st.session_state['reapply_select_all']:
                # Update the select all rows with the new filtered data
                st.session_state['select_all_rows'] = self.display_df.to_dict('records')
                st.session_state['reapply_select_all'] = False
                # Force grid reload to show the new selection
                st.session_state['force_grid_reload'] = True
                st.session_state['grid_key'] = st.session_state.get('grid_key', 0) + 1
            
            # st.subheader("📊 Equipment Records")
            
            # Add custom Select All / Clear Selection buttons at the top
            # COMMENTED OUT: Selection buttons and their functionality
            # col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
            # with col1:
            #     select_all_button_clicked = st.button("☑️ Select All Visible", key="select_all_btn", help="Select all rows currently visible (after all filtering) - selection will be maintained when filtering")
            #     
            #     if select_all_button_clicked:
            #         # Store only the currently visible/filtered rows in session state
            #         st.session_state['select_all_rows'] = self.display_df.to_dict('records')
            #         # Also store the visible data as our working dataset when in select all mode
            #         st.session_state['select_all_active'] = True
            #         # Force grid reload and increment key to force visual update
            #         st.session_state['force_grid_reload'] = True
            #         st.session_state['grid_key'] = st.session_state.get('grid_key', 0) + 1
            #         st.rerun()
            # 
            # with col2:
            #     clear_selection_button_clicked = st.button("⬜ Clear Selection", key="clear_selection_btn", help="Clear all selected rows")
            #     
            #     if clear_selection_button_clicked:
            #         # Clear the selection by removing from session state
            #         if 'select_all_rows' in st.session_state:
            #             del st.session_state['select_all_rows']
            #         if 'select_all_active' in st.session_state:
            #             del st.session_state['select_all_active']
            #         # Force grid reload and increment key to force visual update
            #         st.session_state['force_grid_reload'] = True
            #         st.session_state['grid_key'] = st.session_state.get('grid_key', 0) + 1
            #         st.rerun()
            # 
            # with col3:
            #     refresh_selection_button_clicked = st.button("🔄 Refresh Selection", key="refresh_selection_btn", help="Update selection to match current AgGrid filters")
            #     
            #     if refresh_selection_button_clicked:
            #         if 'select_all_rows' in st.session_state:
            #             # Update select all to include only currently visible rows (will be corrected after grid renders)
            #             st.session_state['refresh_selection_requested'] = True
            #             st.success("🔄 Selection will be updated after grid renders!")
            #             st.rerun()
            
            # Get dropdown options from Equipment Select Options DB
            def get_dropdown_options(col):
                # Always fetch fresh data from Equipment Select Options collection
                try:
                    select_options_records = list(self.Equipment_select_options.find({}, {'_id': 0, col: 1}))
                    if select_options_records:
                        select_options_df = pd.DataFrame(select_options_records)
                        if col in select_options_df.columns:
                            return sorted([
                                str(x) for x in select_options_df[col].dropna().unique()
                                if str(x).strip()
                            ])
                except Exception:
                    pass
                
                # Fallback to unique values from current data
                return sorted([
                    str(x) for x in self.display_df[col].dropna().unique()
                    if str(x).strip()
                ])
            
            # Get user permissions
            permissions = self.get_user_permissions()

            # Configure AgGrid
            gb = GridOptionsBuilder.from_dataframe(self.display_df)
            
            # Enable editing based on permissions
            gb.configure_default_column(
                editable=permissions["can_edit"], 
                groupable=True, 
                resizable=True, 
                sortable=True, 
                filter=True
            )
            
            # Configure specific columns with dropdown functionality
            for col in self.display_df.columns:
                col_lower = col.lower()
                
                # Calculate dynamic width based on column name length
                col_name_length = len(col)
                min_width = max(80, col_name_length * 8)
                
                # ID columns - make read-only with smaller width
                if any(term in col_lower for term in ['id', '_id']):
                    gb.configure_column(col, editable=False, width=min_width, minWidth=60, maxWidth=120)
                
                # Serial number columns - add validation styling
                elif any(term in col_lower for term in ['serial', 'ser_num', 'serial_number']):
                    gb.configure_column(
                        col, 
                        editable=permissions["can_edit"],  # Explicitly set editable for serial columns
                        width=max(min_width, 160), 
                        minWidth=120, 
                        maxWidth=200,
                        cellStyle={'backgroundColor': '#fff3cd', 'border': '1px solid #ffeaa7'},  # Light yellow background to indicate validation
                        headerTooltip=f"Serial numbers must be unique. Duplicates will prevent saving."
                    )
                
                # Dropdown columns - dynamically check if column should have dropdown
                elif self._should_have_dropdown(col):
                    # Check if this is a checkbox-type column that should be freely editable
                    if self._is_checkbox_column(col):
                        # Checkbox columns should be freely editable text fields
                        gb.configure_column(
                            col, 
                            editable=permissions["can_edit"],  # Respect permissions
                            width=max(min_width, 120), 
                            minWidth=80, 
                            maxWidth=150, 
                            wrapText=True, 
                            autoHeight=True
                        )
                    else:
                        # Regular dropdown columns
                        dropdown_options = get_dropdown_options(col)
                        # Always show dropdown editor for better UX, but control actual editing through validation
                        gb.configure_column(
                            col, 
                            editable=True,  # Always true to show dropdown
                            cellEditor='agSelectCellEditor',
                            cellEditorParams={'values': dropdown_options},
                            width=max(min_width, 150), 
                            minWidth=100, 
                            maxWidth=200, 
                            wrapText=True, 
                            autoHeight=True
                        )
                
                # Medium text columns
                elif any(term in col_lower for term in ['model']):
                    gb.configure_column(
                        col, 
                        editable=permissions["can_edit"],  # Explicitly set editable
                        width=max(min_width, 180), 
                        minWidth=120, 
                        maxWidth=250, 
                        wrapText=True, 
                        autoHeight=True
                    )
                
                # Long text columns
                elif any(term in col_lower for term in ['description', 'comments']):
                    gb.configure_column(
                        col, 
                        editable=permissions["can_edit"],  # Explicitly set editable
                        width=max(min_width, 250), 
                        minWidth=150, 
                        maxWidth=400, 
                        wrapText=True, 
                        autoHeight=True
                    )
                
                # Date columns
                elif any(term in col_lower for term in ['date', 'cal']):
                    gb.configure_column(
                        col, 
                        editable=permissions["can_edit"],  # Explicitly set editable
                        width=max(min_width, 130), 
                        minWidth=100, 
                        maxWidth=160
                    )
                
                # Numeric columns
                elif any(term in col_lower for term in ['value', 'price', 'cost', 'year']):
                    gb.configure_column(
                        col, 
                        editable=permissions["can_edit"],  # Explicitly set editable
                        width=max(min_width, 120), 
                        minWidth=80, 
                        maxWidth=150
                    )
                
                # Default for other columns
                else:
                    gb.configure_column(
                        col, 
                        editable=permissions["can_edit"],  # Explicitly set editable for new columns
                        width=max(min_width, 160), 
                        minWidth=100, 
                        maxWidth=300, 
                        wrapText=True, 
                        autoHeight=True
                    )
            
            # Enable selection (with checkboxes for row selection)
            gb.configure_selection(selection_mode="multiple", use_checkbox=True)
            
            # Enable pagination
            gb.configure_pagination(enabled=True, paginationPageSize=20)
            
            # Configure grid options for better checkbox functionality
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
                checkboxSelection=True  # Explicitly enable checkbox selection
            )
            
            # Pre-select rows if we're in "select all" mode
            if 'select_all_rows' in st.session_state:
                # Add JavaScript to select all visible rows on grid ready
                pre_select_js = """
                function onGridReady(params) {
                    setTimeout(function() {
                        params.api.selectAll();
                    }, 100);
                }
                """
                gb.configure_grid_options(
                    onGridReady=JsCode(pre_select_js)
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
            force_reload = 'force_grid_reload' in st.session_state and st.session_state['force_grid_reload']
            if force_reload:
                st.session_state['force_grid_reload'] = False
            
            # Determine what data to display in AgGrid
            # If we're in select all mode and have filtered data, use that instead of full display_df
            grid_data = self.display_df
            if (st.session_state.get('select_all_active', False) and 
                'select_all_rows' in st.session_state and
                len(st.session_state['select_all_rows']) < len(self.display_df)):
                # We're in select all mode with filtered data - create DataFrame from selected rows
                grid_data = pd.DataFrame(st.session_state['select_all_rows'])
                # Ensure it has the same column order as display_df
                if not grid_data.empty:
                    grid_data = grid_data.reindex(columns=self.display_df.columns, fill_value=None)
            
            # Display the AgGrid with anti-fading configuration
            grid_response = AgGrid(
                grid_data,
                gridOptions=gb.build(),
                data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                update_mode=GridUpdateMode.MODEL_CHANGED,  # Use MODEL_CHANGED as standard
                allow_unsafe_jscode=True,
                fit_columns_on_grid_load=False,
                height=600,
                theme='streamlit',
                enable_enterprise_modules=False,
                reload_data=force_reload,
                key=f"equipment_grid_{st.session_state.get('grid_key', 0)}",
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
            
            # Handle refresh selection request with actual visible data
            if st.session_state.get('refresh_selection_requested', False):
                if 'select_all_rows' in st.session_state:
                    # Update select all to include only currently visible rows
                    st.session_state['select_all_rows'] = visible_data.to_dict('records')
                    st.session_state['select_all_active'] = True
                    # Force grid reload and increment key to force visual update
                    st.session_state['force_grid_reload'] = True
                    st.session_state['grid_key'] = st.session_state.get('grid_key', 0) + 1
                st.session_state['refresh_selection_requested'] = False  # Clear the flag
            
            # Check if AgGrid filtering resulted in empty data and we should show a message
            if len(visible_data) == 0 and len(grid_data) > 0:
                st.session_state['show_empty_filter_message'] = True
            
            # Track AgGrid internal filtering changes more conservatively
            # Only track significant changes, not every interaction
            current_visible_count = len(visible_data)
            
            # Create a more stable signature that doesn't change on every interaction
            if current_visible_count > 0:
                # Use only count and a hash of the index to avoid constant changes
                visible_signature = f"count_{current_visible_count}"
            else:
                visible_signature = "empty"
            
            # Initialize tracking if not exists
            if 'previous_visible_signature' not in st.session_state:
                st.session_state['previous_visible_signature'] = visible_signature
                st.session_state['signature_stable_count'] = 0
            
            # Only update selection if we're in select all mode - simplified logic
            if 'select_all_rows' in st.session_state and st.session_state['previous_visible_signature'] != visible_signature:
                # Only update if we have visible data (not empty)
                if current_visible_count > 0:
                    # Normal case: update select all to only include currently visible rows
                    st.session_state['select_all_rows'] = visible_data
                    st.session_state['select_all_active'] = True
                    # Set flag to show notification about automatic update
                    st.session_state['selection_auto_updated'] = True
                else:
                    # Empty results - clear select all mode
                    if 'select_all_rows' in st.session_state:
                        del st.session_state['select_all_rows']
                    if 'select_all_active' in st.session_state:
                        del st.session_state['select_all_active']
            
            # Update the tracked signature
            st.session_state['previous_visible_signature'] = visible_signature
            
            # Check if we're in "select all" mode and override selected_rows
            if 'select_all_rows' in st.session_state:
                selected_rows = st.session_state['select_all_rows']
            
            # Show notification if selection was automatically updated due to filtering
            if st.session_state.get('selection_auto_updated', False):
                st.success("🔄 **Selection automatically updated** to match filtered results!")
                st.session_state['selection_auto_updated'] = False  # Clear the flag
            
            # Show notification if showing all data due to empty AgGrid filters
            if st.session_state.get('show_empty_filter_message', False):
                st.info("📄 **Showing all data** - AgGrid filters resulted in no matches, displaying complete dataset")
                st.session_state['show_empty_filter_message'] = False  # Clear the flag
            
            # Display selection help
            if selected_rows is not None and len(selected_rows) > 0:
                if 'select_all_rows' in st.session_state:
                    st.info(f"✅ **ALL {len(selected_rows)} row(s) selected** (Select All mode - automatically adapts to sidebar filters, use 'Refresh Selection' after AgGrid column filtering) - Use the buttons below for bulk operations")
                else:
                    st.info(f"✅ **{len(selected_rows)} row(s) selected** ")
            
            # Get edited data from AgGrid
            self.edited_df = grid_response['data']
            
            # Real-time validation for serial numbers (for edit users only)
            if permissions["can_edit"]:
                is_valid, error_messages, duplicate_serials = self._validate_serials_in_realtime()
                if not is_valid:
                    st.error("🚫 **Serial Number Validation Error**")
                    for error_msg in error_messages:
                        st.error(error_msg)
                    st.warning("⚠️ **You must fix these duplicate serial numbers before saving changes to the database.**")
            
            # For non-edit users, show a read-only message and revert any changes
            if not permissions["can_edit"]:
                # Check if any changes were made by comparing with original data
                if not self.edited_df.equals(self.display_df):
                    st.info("ℹ️ **Read-Only Mode**: You can view dropdown options but cannot make changes. Contact an admin to modify data.")
                    # Revert changes to prevent unauthorized modifications
                    self.edited_df = self.display_df.copy()
                else:
                    st.info("ℹ️ **Read-Only Mode**: You can view dropdown options by clicking on cells, but cannot make changes.")
            
            # Action buttons row (only for users with edit permissions)
            if permissions.get("can_edit", False):
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    save_button_clicked = st.button("💾 Save Changes to Database", key="save_changes_btn")
                    
                    if save_button_clicked:
                        # Execute save operation
                        self.Save_Equipment_Records_Changes_to_Database()
                
                with col2:
                    delete_button_clicked = st.button("🗑️ Remove Selected", type="primary", key="delete_selected_btn")
                    
                    if delete_button_clicked:
                        if selected_rows is not None and len(selected_rows) > 0:
                            if permissions["can_delete"]:
                                # Convert selected rows to DataFrame for easier manipulation
                                selected_df = pd.DataFrame(selected_rows)
                                
                                # Delete from database first
                                deleted_count = 0
                                for idx, row in selected_df.iterrows():
                                    # Use generic method to create delete query
                                    delete_query = self._create_delete_query(row)
                                    
                                    if delete_query:
                                        # Delete from MongoDB
                                        result = self.Equipment_collection.delete_one(delete_query)
                                        if result.deleted_count > 0:
                                            deleted_count += 1
                                
                                # Remove from local DataFrames using the best unique identifier
                                deleted_from_local = 0
                                for col in self.unique_id_cols:
                                    if col in selected_df.columns:
                                        values_to_delete = self._get_values_for_deletion(selected_df, col)
                                        if values_to_delete:
                                            # Delete from all DataFrames
                                            self.display_df = self.display_df[~self.display_df[col].isin(values_to_delete)]
                                            self.df = self.df[~self.df[col].isin(values_to_delete)]
                                            self.db_df = self.db_df[~self.db_df[col].isin(values_to_delete)]
                                            deleted_from_local = len(values_to_delete)
                                            break  # Use the first available unique identifier
                                
                                # If no unique identifier worked, fallback to index-based deletion
                                if deleted_from_local == 0:
                                    indices_to_delete = selected_df.index.tolist()
                                    self.display_df = self.display_df.drop(indices_to_delete).reset_index(drop=True)
                                    self.df = self.df.drop(indices_to_delete).reset_index(drop=True)
                                    self.db_df = self.db_df.drop(indices_to_delete).reset_index(drop=True)
                                    deleted_from_local = len(indices_to_delete)
                                
                                # Also remove from newly added rows in session state if they exist there
                                if 'newly_added_rows' in st.session_state and st.session_state.newly_added_rows:
                                    # Filter out deleted rows from session state using any available unique identifier
                                    remaining_new_rows = []
                                    for new_row in st.session_state.newly_added_rows:
                                        should_keep = True
                                        for idx, selected_row in selected_df.iterrows():
                                            # Check using any unique identifier
                                            for id_col in self.unique_id_cols:
                                                if (id_col in new_row and id_col in selected_row and 
                                                    new_row[id_col] == selected_row[id_col] and
                                                    pd.notna(new_row[id_col])):
                                                    should_keep = False
                                                    break
                                            if not should_keep:
                                                break
                                        if should_keep:
                                            remaining_new_rows.append(new_row)
                                    st.session_state.newly_added_rows = remaining_new_rows
                                
                                st.success(f"🗑️ Deleted {deleted_count} row(s) from database and {len(selected_rows)} row(s) from display!")
                                # Clear custom selection after deletion and force grid reload
                                if 'select_all_rows' in st.session_state:
                                    del st.session_state['select_all_rows']
                                if 'select_all_active' in st.session_state:
                                    del st.session_state['select_all_active']
                                st.session_state['force_grid_reload'] = True
                                st.session_state['grid_key'] = st.session_state.get('grid_key', 0) + 1
                                st.rerun()
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
                                label="📤 Download Selected",
                                data=selected_csv,
                                file_name="selected_equipment_records.csv",
                                mime="text/csv",
                                key="download_selected_btn"
                            )
                        else:
                            # Show button but with dummy data, and display warning when clicked
                            dummy_csv = "No data selected"
                            if st.download_button(
                                label="📤 Download Selected",
                                data=dummy_csv,
                                file_name="no_selection.txt",
                                mime="text/plain",
                                key="download_selected_btn_empty"
                            ):
                                st.warning("⚠️ Please select rows first in order to download selected data.")

                # Add New Row functionality after download button (only for users with edit permissions)
                if permissions["can_edit"]:
                    st.markdown("---")  # Add separator
                    self._render_add_new_row_section_equipment_records()
                    st.markdown("---")  # Add separator
                
                # Add column management functions here
                self.Add_New_Column_to_Equipment_records_DB()
                self.rename_column_in_equipment_records_db()
                if self.is_admin(): 
                    self.delete_column_from_equeipment_records_db()
                
                # Add Web Management section for admin
                if self.is_admin():
                    self.web_management_section()
    
    def Add_New_Column_to_Equipment_records_DB(self):
        """Add a new column to Equipment Records database."""
        # Check if user has admin permissions - only show UI if they do
        permissions = self.get_user_permissions()
        if not permissions.get("can_manage_users", False):
            # Don't show anything for non-admin users
            return
        
        # Button to add a new column to the DB (must be after Equipment_collection and self.df are set)
        with st.expander("➕ Add New Column to Equipment DB"):
            st.markdown("### Add New Column")
            new_col_name = st.text_input("New Column Name", key="new_col_name")
            new_col_default = st.text_input("Default Value (optional)", key="new_col_default")
            
            st.info("💡 **Dropdown Integration**: If a column with the same name exists in Equipment Select Options, this column will automatically use dropdown values from there.")
            
            # Create columns for button and thinking GIF
            add_col_btn_col1, add_col_btn_col2 = st.columns([1, 0.3])
            
            add_col_button_clicked = st.button("➕ Add Column to All Records", key="add_col_btn")
            
            if add_col_button_clicked:
                if new_col_name and new_col_name.strip():
                    # Check if column already exists
                    if new_col_name.strip() in self.df.columns:
                        st.error(f"❌ Column '{new_col_name.strip()}' already exists. Please choose a different name.")
                    else:
                        modified_count = self.add_column_to_db(new_col_name, new_col_default if new_col_default else None)
                        st.success(f"✅ Added column '{new_col_name}' to {modified_count} records.")
                        
                        # Check if the column exists in Equipment Select Options
                        if (hasattr(self, 'Equipment_select_options_db_df') and 
                            self.Equipment_select_options_db_df is not None and 
                            new_col_name in self.Equipment_select_options_db_df.columns):
                            st.info(f"🔄 Column '{new_col_name}' has matching dropdown options in Equipment Select Options and has been synced.")
                        
                        st.info("🔄 Page will refresh to show the updated column.")
                        st.rerun()
                else:
                    st.warning("⚠️ Please enter a column name.")
    
    def rename_column_in_equipment_records_db(self):
        """Rename a column in Equipment Records database."""
        # Check if user has admin permissions - only show UI if they do
        permissions = self.get_user_permissions()
        if not permissions.get("can_manage_users", False):
            # Don't show anything for non-admin users
            return
        
        # Button to rename a column in the DB (only visible to admins)
        with st.expander("✏️ Rename Column in Equipment DB"):
            # Static columns that should not be renamed due to web functionality dependencies
            static_columns = ["Category", "Vendor", "Location", "Serial", "uuid", "_id", "ID"]
            
            # Get available columns for renaming (exclude static columns that shouldn't be renamed)
            available_columns = [col for col in self.df.columns if col not in static_columns]
            
            # Show info about protected columns
            st.info(f"🔒 **Protected columns** (cannot be renamed): {', '.join(static_columns)}")
            st.caption("These columns have special functionality and must maintain their names.")
            
            if available_columns:
                col1, col2 = st.columns(2)
                
                with col1:
                    col_to_rename = st.selectbox(
                        "Select Column to Rename:",
                        available_columns,
                        key="rename_col_select"
                    )
                
                with col2:
                    new_col_name = st.text_input(
                        "New Column Name:",
                        value=col_to_rename if col_to_rename else "",
                        key="new_col_name_input"
                    )
                
                # Validation and rename button
                if col_to_rename and new_col_name and new_col_name.strip():
                    # Check if new name already exists
                    if new_col_name.strip() in self.df.columns and new_col_name.strip() != col_to_rename:
                        st.error(f"❌ Column name '{new_col_name.strip()}' already exists. Please choose a different name.")
                    elif new_col_name.strip() == col_to_rename:
                        st.info("💡 New name is the same as current name. No changes needed.")
                    else:
                        rename_col_button_clicked = st.button("✏️ Rename Column", key="rename_col_btn", type="primary")
                        
                        if rename_col_button_clicked:
                            try:
                                modified_count = self.rename_column_in_db(col_to_rename, new_col_name.strip())
                                st.success(f"✅ Successfully renamed column '{col_to_rename}' to '{new_col_name.strip()}' in {modified_count} records.")
                                st.info("🔄 Page will refresh to show the updated column name.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error renaming column: {str(e)}")
                else:
                    if col_to_rename and not new_col_name.strip():
                        st.warning("⚠️ Please enter a new column name.")
            else:
                st.info("📋 All current columns are protected and cannot be renamed. You can add new columns using the 'Add New Column' feature.")
    
    def delete_column_from_equeipment_records_db(self):
        # Button to delete a column from the DB
         with st.expander("🗑️ Delete Column from Equipment DB"):
             # Get available columns for deletion (exclude essential columns)
             available_columns = [col for col in self.df.columns if col not in ['id', '_id']]
             
             if available_columns:
                 col_to_delete = st.selectbox(
                     "Select Column to Delete:",
                     available_columns,
                     key="delete_col_select"
                 )
                 
                 # Initialize confirmation state if not exists
                 if 'confirm_delete_column' not in st.session_state:
                     st.session_state.confirm_delete_column = False
                 if 'column_to_confirm_delete' not in st.session_state:
                     st.session_state.column_to_confirm_delete = None
                 
                 # First click - show confirmation
                 if not st.session_state.confirm_delete_column:
                     delete_col_button_clicked = st.button("🗑️ Delete Column", key="delete_col_btn", type="primary")
                     
                     if delete_col_button_clicked:
                         if col_to_delete:
                             st.session_state.confirm_delete_column = True
                             st.session_state.column_to_confirm_delete = col_to_delete
                             st.rerun()
                 
                 # Show confirmation dialog
                 if st.session_state.confirm_delete_column and st.session_state.column_to_confirm_delete:
                     st.warning(f"⚠️ **Are you sure you want to delete the column '{st.session_state.column_to_confirm_delete}'?**")
                     st.error("🚨 **This action cannot be undone!** The column will be permanently removed from all equipment records.")
                     
                     col1, col2, col3 = st.columns([1, 1, 2])
                     
                     with col1:
                         confirm_delete_button_clicked = st.button("✅ Yes, Delete", key="confirm_delete_btn", type="primary")
                         
                         if confirm_delete_button_clicked:
                             try:
                                 modified_count = self.delete_column_from_db(st.session_state.column_to_confirm_delete)
                                 st.success(f"✅ Successfully deleted column '{st.session_state.column_to_confirm_delete}' from {modified_count} records.")
                                 # Reset confirmation state
                                 st.session_state.confirm_delete_column = False
                                 st.session_state.column_to_confirm_delete = None
                                 st.rerun()
                             except Exception as e:
                                 st.error(f"❌ Error deleting column: {str(e)}")
                                 # Reset confirmation state on error
                                 st.session_state.confirm_delete_column = False
                                 st.session_state.column_to_confirm_delete = None
                     
                     with col2:
                         if st.button("❌ Cancel", key="cancel_delete_btn"):
                             # Reset confirmation state
                             st.session_state.confirm_delete_column = False
                             st.session_state.column_to_confirm_delete = None
                             st.rerun()
                     
                     with col3:
                         st.info("💡 Choose wisely - deleted columns cannot be recovered!")
                         
             else:
                 st.info("No columns available for deletion")
    
    def Save_Equipment_Records_Changes_to_Database(self):
        """Save changes from Equipment Records to database."""
        # Prevent accidental deletion if DataFrame is empty
        if self.edited_df.empty:
            st.error("Cannot save: No data to save. The table is empty.")
            return
        
        # Validate unique serials within the DataFrame
        is_valid_internal, duplicate_serials, internal_error = self._validate_unique_serials(self.edited_df)
        if not is_valid_internal:
            st.error(internal_error)
            st.error("Please fix the duplicate serial numbers before saving.")
            return
        
        # Validate serials against existing database records
        is_valid_db, existing_serials, db_error = self._validate_serials_against_database(self.edited_df, exclude_current=True)
        if not is_valid_db:
            st.error(db_error)
            st.error("Please use different serial numbers that don't already exist in the database.")
            return
        
        # Determine unique key dynamically from available columns
        unique_key = None
        if hasattr(self, 'unique_id_cols') and self.unique_id_cols:
            # Use the first available unique identifier column
            for col in self.unique_id_cols:
                if col in self.db_df.columns:
                    unique_key = col
                    break
        
        # Find changed rows only
        original = self.display_df.reset_index(drop=True)
        edited = self.edited_df.reset_index(drop=True)
        
        # Ensure both DataFrames have the same columns for comparison
        common_cols = list(set(original.columns) & set(edited.columns))
        if not common_cols:
            st.error("No common columns found between original and edited data.")
            return
        
        # Align the DataFrames to have the same columns in the same order
        original_aligned = original[common_cols].reindex(columns=common_cols)
        edited_aligned = edited[common_cols].reindex(columns=common_cols)
        
        # Compare the aligned DataFrames
        changed_mask = (original_aligned != edited_aligned) & ~(original_aligned.isnull() & edited_aligned.isnull())
        changed_rows = changed_mask.any(axis=1)
        changed_df = edited[changed_rows]
        
        if changed_df.empty:
            st.info("No changes detected.")
            return
        
        # Only update or upsert the changed records
        for idx, row in changed_df.iterrows():
            if unique_key and pd.notna(row.get(unique_key)) and str(row.get(unique_key)).strip():
                filter_query = {unique_key: row.get(unique_key)}
            else:
                # Use generic method to create filter query
                filter_query = self._create_delete_query(row)
            
            update_query = {"$set": row.to_dict()}
            self.Equipment_collection.update_one(filter_query, update_query, upsert=True)
        
        # Clear newly added rows from session state since they're now saved
        if 'newly_added_rows' in st.session_state:
            st.session_state.newly_added_rows = []
        
        # Store database save success in session state
        st.session_state['database_save_success'] = {
            'message': f"💾 Saved {len(changed_df)} changed records to the database!",
            'timestamp': pd.Timestamp.now(),
            'records_count': len(changed_df)
        }
        
        # Clear add row success since data is now saved
        if 'add_row_success' in st.session_state:
            del st.session_state['add_row_success']
        
        st.success(f"💾 Saved {len(changed_df)} changed records to the database!")
    
    def web_management_section(self):
         """Web Management section for admin users."""
         st.markdown("### 🌐 Web Management")
         st.markdown("---")
         
         # Column Order Management
         with st.expander("💾 Save Equipment Column Order"):
               st.info("💡 Configure your preferred Equipment column order below and save it.")
               
               # Show current saved orders for Equipment only
               equipment_default = list(self.display_df.columns) if hasattr(self, 'display_df') and not self.display_df.empty else []
               equipment_order = self._load_column_order('equipment', equipment_default)
               
               st.markdown("**Equipment Table Column Order:**")
               if equipment_default:
                   st.markdown("Current columns in data:")
                   current_equipment_display = ', '.join(equipment_default[:5]) + ('...' if len(equipment_default) > 5 else '')
                   st.text(current_equipment_display)
                   
                   # Allow user to reorder columns
                   st.markdown("**Drag to reorder or manually edit the order:**")
                   equipment_order_input = st.text_area(
                       "Column order (one per line or comma-separated):",
                       value='\n'.join(equipment_order) if equipment_order else '\n'.join(equipment_default),
                       height=150,
                       key="equipment_column_order"
                   )
                   
                   save_order_button_clicked = st.button("💾 Save Equipment Column Order", key="save_equipment_order_btn")
                   
                   if save_order_button_clicked:
                       # Parse the input
                       if '\n' in equipment_order_input:
                           new_order = [col.strip() for col in equipment_order_input.split('\n') if col.strip()]
                       else:
                           new_order = [col.strip() for col in equipment_order_input.split(',') if col.strip()]
                       
                       # Validate that all columns exist
                       invalid_columns = [col for col in new_order if col not in equipment_default]
                       missing_columns = [col for col in equipment_default if col not in new_order]
                       
                       if invalid_columns:
                           st.error(f"❌ Invalid columns: {', '.join(invalid_columns)}")
                       elif missing_columns:
                           st.warning(f"⚠️ Missing columns (will be added at end): {', '.join(missing_columns)}")
                           new_order.extend(missing_columns)
                           self._save_column_order('equipment', new_order)
                           st.success("✅ Equipment columns order saved successfully!")
                           st.rerun()
                       else:
                           self._save_column_order('equipment', new_order)
                           st.success("✅ Equipment columns order saved successfully!")
                           st.rerun()
               else:
                   st.info("No Equipment data available")
               
               st.markdown("📋 **Instructions:** Edit the column order in the text area above (one column name per line), then click Save.")
         
                            # Filter Order Management
         with st.expander("🔧 Save Equipment Filter Order"):
             # Get excluded filter columns (same as used in Equipment_Filters)
             excluded_filter_cols = ["ID", "check", "uuid"]  # You can modify this list as needed
             
             # Get ALL filterable columns from the current dataset
             all_filterable_columns = []
             filter_column_mapping = {}
             
             if hasattr(self, 'df') and self.df is not None and not self.df.empty:
                 # Get all columns except excluded ones
                 for col in self.df.columns:
                     if col not in excluded_filter_cols:
                         all_filterable_columns.append(col)
                         filter_column_mapping[col] = col
             
             # Show current saved filter order
             current_filter_order = self._load_filter_order(all_filterable_columns)
             
             if all_filterable_columns:
                 # Allow user to configure excluded columns
                 excluded_cols_input = st.text_input(
                     "Excluded columns (comma-separated):",
                     value=', '.join(excluded_filter_cols),
                     help="Enter column names that should NOT appear as filters",
                     key="excluded_filter_cols_input"
                 )
                 
                 # Update excluded columns and refresh available columns
                 if excluded_cols_input.strip():
                     new_excluded_cols = [col.strip() for col in excluded_cols_input.split(',') if col.strip()]
                     # Update the available columns based on new exclusions
                     updated_filterable_columns = []
                     if hasattr(self, 'df') and self.df is not None and not self.df.empty:
                         for col in self.df.columns:
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
                     key="equipment_filter_order"
                 )
                 
                 save_filter_order_button_clicked = st.button("💾 Save Equipment Filter Order", key="save_equipment_filter_order_btn")
                 
                 if save_filter_order_button_clicked:
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
                                 excluded_cols_file = Path("excluded_filter_columns.json")
                                 with open(excluded_cols_file, 'w') as f:
                                     json.dump({"excluded_columns": new_excluded_cols}, f, indent=2)
                             except Exception as e:
                                 st.warning(f"⚠️ Could not save excluded columns preference: {str(e)}")
                         
                         self._save_filter_order(new_order)
                         st.success("✅ Equipment filter order saved successfully!")
                         st.rerun()
                     else:
                         # Also save the updated excluded columns if they changed
                         if excluded_cols_input.strip():
                             new_excluded_cols = [col.strip() for col in excluded_cols_input.split(',') if col.strip()]
                             # Save excluded columns to a separate preference file
                             try:
                                 excluded_cols_file = Path("excluded_filter_columns.json")
                                 with open(excluded_cols_file, 'w') as f:
                                     json.dump({"excluded_columns": new_excluded_cols}, f, indent=2)
                             except Exception as e:
                                 st.warning(f"⚠️ Could not save excluded columns preference: {str(e)}")
                         
                         self._save_filter_order(new_order)
                         st.success("✅ Equipment filter order saved successfully!")
                         st.rerun()
             else:
                 st.info("No data available to determine filterable columns")
             
             st.markdown("📋 **Instructions:**")
             st.markdown("1. **Configure Excluded Columns**: Add/remove columns from the excluded list")
             st.markdown("2. **Reorder Filters**: Edit the filter order (one column per line or comma-separated)")
             st.markdown("3. **Save**: Click 'Save Equipment Filter Order' to apply changes")
             st.markdown("4. **Result**: Filter dropdowns will appear in your custom order, excluding specified columns")
         
         # Admin Download Section
         with st.expander("📤 Admin Download"):
             st.info("💡 Download complete equipment data for administrative purposes.")
             
             if hasattr(self, 'df') and self.df is not None and not self.df.empty:
                 # Download complete data
                 complete_csv = self.df.to_csv(index=False)
                 st.download_button(
                     label="📤 Download Complete Equipment Data",
                     data=complete_csv,
                     file_name=f"complete_equipment_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                     mime="text/csv",
                     key="download_complete_equipment_btn"
                 )
                 
                 # Download filtered data (if any filters are applied)
                 if hasattr(self, 'display_df') and not self.display_df.equals(self.df):
                     filtered_csv = self.display_df.to_csv(index=False)
                     st.download_button(
                         label="📤 Download Filtered Equipment Data",
                         data=filtered_csv,
                         file_name=f"filtered_equipment_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                         mime="text/csv",
                         key="download_filtered_equipment_btn"
                     )
                 
                 # Show data summary
                 st.info(f"📊 **Data Summary:** {len(self.df)} total records, {len(self.df.columns)} columns")
             else:
                 st.warning("⚠️ No equipment data available for download.")
    
    def add_column_to_db(self, column_name, default_value=None):
        """Add a new column to all records in the database."""
        try:
            # Update all documents in the collection
            update_query = {"$set": {column_name: default_value}}
            result = self.Equipment_collection.update_many({}, update_query)
            return result.modified_count
        except Exception as e:
            st.error(f"Error adding column: {str(e)}")
            return 0
    
    def rename_column_in_db(self, old_name, new_name):
        """Rename a column in all records in the database."""
        try:
            # Update all documents in the collection
            pipeline = [
                {"$addFields": {new_name: f"${old_name}"}},
                {"$unset": old_name}
            ]
            result = self.Equipment_collection.update_many({}, pipeline)
            return result.modified_count
        except Exception as e:
            st.error(f"Error renaming column: {str(e)}")
            return 0
    
    def delete_column_from_db(self, column_name):
        """Delete a column from all records in the database."""
        try:
            # Remove the column from all documents
            update_query = {"$unset": {column_name: ""}}
            result = self.Equipment_collection.update_many({}, update_query)
            return result.modified_count
        except Exception as e:
            st.error(f"Error deleting column: {str(e)}")
            return 0
    
    def _render_add_new_row_section_equipment_records(self):
        """
        Renders a flexible 'Add New Row' section for Equipment Records.
        Automatically adapts to column structure changes.
        """
        st.subheader("➕ Add New Row")
        

        
        # Get current dataframe structure
        current_df = self.display_df if hasattr(self, 'display_df') and not self.display_df.empty else None
        
        if current_df is None:
            st.info("No data available to determine column structure.")
            return
        
        # Get columns and their types
        columns = current_df.columns.tolist()
        
        # Exclude certain columns from user input
        excluded_columns = ['index', 'uuid', 'check']  # System generated columns
        editable_columns = [col for col in columns if col.lower() not in [exc.lower() for exc in excluded_columns]]
        
        with st.form("add_new_row_equipment_records", clear_on_submit=True):
            st.markdown("### 📝 **Fill in the details for the new row:**")
            st.markdown("---")
            
            # Filter out ID column for input (it will be auto-generated)
            input_columns = [col for col in editable_columns if col.lower() != 'id']
            
            # Show which fields have dropdown options
            dropdown_fields = [col for col in input_columns if self._should_have_dropdown(col)]
            if dropdown_fields:
                st.info(f"🎯 **Dropdown Fields Available**: {', '.join(dropdown_fields)} - These fields will show as dropdown menus with predefined options.")
            
            # Pre-calculate dropdown options for all dropdown fields to avoid repeated function calls
            dropdown_options_cache = {}
            for col in dropdown_fields:
                try:
                    # Use cached data instead of making individual MongoDB queries
                    if (hasattr(self, 'Equipment_select_options_db_df') and 
                        self.Equipment_select_options_db_df is not None and 
                        col in self.Equipment_select_options_db_df.columns):
                        
                        # Get unique values from cached DataFrame
                        unique_values = self.Equipment_select_options_db_df[col].dropna().unique()
                        dropdown_options_cache[col] = sorted([
                            str(x) for x in unique_values
                            if str(x).strip()
                        ])
                    else:
                        # Fallback to unique values from current data
                        dropdown_options_cache[col] = sorted([
                            str(x) for x in self.display_df[col].dropna().unique()
                            if str(x).strip()
                        ])
                except Exception:
                    dropdown_options_cache[col] = []
            
            new_row_data = {}
            
            # PERFORMANCE OPTIMIZATION: Pre-calculated dropdown options eliminate repeated MongoDB queries
            # This reduces Add New Row loading time from ~15 seconds to under 1 second
            
            # Create form fields in 2 rows for better layout
            num_fields = len(input_columns)
            fields_per_row = (num_fields + 1) // 2  # Split into 2 rows
            
            # First row
            cols1 = st.columns(fields_per_row)
            for col_idx, column in enumerate(input_columns[:fields_per_row]):
                with cols1[col_idx]:
                    # Check if this column should have dropdown functionality (use pre-calculated info)
                    if column in dropdown_fields:
                        # Create dropdown for columns that have options in Equipment Select Options
                        dropdown_options = dropdown_options_cache.get(column, [])
                        if dropdown_options:
                            # Add "Select..." option at the beginning
                            options = ["Select..."] + dropdown_options
                            selected_option = st.selectbox(
                                f"📋 {column} (Dropdown)",
                                options=options,
                                key=f"add_row_dropdown_{column}_{col_idx}",
                                help=f"Select from {len(dropdown_options)} available {column} options"
                            )
                            # Store the selected value (skip "Select..." option)
                            new_row_data[column] = selected_option if selected_option != "Select..." else ""
                        else:
                            # Fallback to text input if no dropdown options
                            placeholder = f"Enter {column.lower().replace('_', ' ')}"
                            new_row_data[column] = st.text_input(
                                column,
                                placeholder=placeholder,
                                key=f"add_row_text_{column}_{col_idx}",
                                help=f"Enter value for {column}"
                            )
                    else:
                        # Regular text input for non-dropdown columns
                        placeholder = f"Enter {column.lower().replace('_', ' ')}"
                        new_row_data[column] = st.text_input(
                            column,
                            placeholder=placeholder,
                            key=f"add_row_text_{column}_{col_idx}",
                            help=f"Enter value for {column}"
                        )
            
            # Second row
            if len(input_columns) > fields_per_row:
                cols2 = st.columns(len(input_columns) - fields_per_row)
                for col_idx, column in enumerate(input_columns[fields_per_row:]):
                    with cols2[col_idx]:
                        # Check if this column should have dropdown functionality (use pre-calculated info)
                        if column in dropdown_fields:
                            # Create dropdown for columns that have options in Equipment Select Options
                            dropdown_options = dropdown_options_cache.get(column, [])
                            if dropdown_options:
                                # Add "Select..." option at the beginning
                                options = ["Select..."] + dropdown_options
                                selected_option = st.selectbox(
                                    f"📋 {column} (Dropdown)",
                                    options=options,
                                    key=f"add_row_dropdown_{column}_{col_idx + fields_per_row}",
                                    help=f"Select from {len(dropdown_options)} available {column} options"
                                )
                                # Store the selected value (skip "Select..." option)
                                new_row_data[column] = selected_option if selected_option != "Select..." else ""
                            else:
                                # Fallback to text input if no dropdown options
                                placeholder = f"Enter {column.lower().replace('_', ' ')}"
                                new_row_data[column] = st.text_input(
                                    column,
                                    placeholder=placeholder,
                                    key=f"add_row_text_{column}_{col_idx + fields_per_row}",
                                    help=f"Enter value for {column}"
                                )
                        else:
                            # Regular text input for non-dropdown columns
                            placeholder = f"Enter {column.lower().replace('_', ' ')}"
                            new_row_data[column] = st.text_input(
                                column,
                                placeholder=placeholder,
                                key=f"add_row_text_{column}_{col_idx + fields_per_row}",
                                help=f"Enter value for {column}"
                            )
            
            # Submit button section
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                submitted = st.form_submit_button("➕ Add New Row", use_container_width=True, type="primary")
            with col2:
                # Show success message next to the button if available
                if 'add_row_success' in st.session_state:
                    success_data = st.session_state['add_row_success']
                    st.success(success_data['message'])
                    # Clear the success message after showing it
                    del st.session_state['add_row_success']
                else:
                    st.markdown("💡 **Tip**: Fields with dropdown options (📋) will show predefined values from the Equipment Select Options database.")
        
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
                    # Update the main df first
                    if hasattr(self, 'df') and self.df is not None:
                        new_df = pd.concat([
                            self.df, 
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
                            result = self.Equipment_collection.insert_one(db_row)
                            
                            if result.inserted_id:
                                # Update all DataFrames to reflect the database state
                                self.df = new_df.copy()
                                self.display_df = new_df.copy()
                                self.db_df = new_df.copy()
                                
                                # PERFORMANCE OPTIMIZATION: Reload latest data from database to ensure consistency
                                try:
                                    # Reload the latest data from database to ensure we have the most up-to-date information
                                    db_records = list(self.Equipment_collection.find({}, {'_id': 0}))
                                    latest_df = pd.DataFrame(db_records)
                                    if not latest_df.empty:
                                        # Update all DataFrames with the latest data from database
                                        self.df = latest_df.copy()
                                        self.display_df = latest_df.copy()
                                        self.db_df = latest_df.copy()
                                        # Re-apply column order and sorting
                                        self.df = self._apply_column_order(self.df, 'equipment')
                                        self.display_df = self.df.copy()
                                        
                                        # Clear any cached selection state to ensure fresh data display
                                        if 'select_all_rows' in st.session_state:
                                            del st.session_state['select_all_rows']
                                        if 'select_all_active' in st.session_state:
                                            del st.session_state['select_all_active']
                                        if 'previous_visible_signature' in st.session_state:
                                            del st.session_state['previous_visible_signature']
                                        
                                        st.success(f"✅ Data refreshed successfully! Total rows: {len(self.df)}")
                                    else:
                                        st.warning("⚠️ No data found in database after refresh")
                                except Exception as refresh_error:
                                    # If refresh fails, continue with the local update
                                    st.warning(f"⚠️ Data refresh warning: {str(refresh_error)}")
                                
                                # Store success message in session state so it persists
                                st.session_state['add_row_success'] = {
                                    'message': f"✅ New row added and saved to database successfully! Total rows: {len(self.df)}",
                                    'row_data': complete_new_row,
                                    'timestamp': pd.Timestamp.now()
                                }
                                
                                # PERFORMANCE OPTIMIZATION: Force complete grid refresh with new data
                                # Clear all grid-related session state to ensure fresh start
                                st.session_state['grid_key'] = st.session_state.get('grid_key', 0) + 1
                                st.session_state['force_grid_reload'] = True
                                
                                # PERFORMANCE OPTIMIZATION: Use efficient st.rerun() with cached data
                                # Set flag to indicate data is already loaded and cached
                                st.session_state['data_already_loaded'] = True
                                st.session_state['cached_df'] = self.df.copy()
                                st.session_state['cached_display_df'] = self.display_df.copy()
                                
                                # Force rerun to refresh the grid with new data
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


    def equipment_records_page(self):
        """Main Equipment Records page function."""
        
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
        
        st.markdown("## 📊 Equipment Records")
        st.markdown("---")
        
        # Check if user needs password change first
        if self.auth_manager and self.auth_manager.user_needs_password_change(st.session_state.get('username', '')):
            st.warning("⚠️ You must change your password before accessing the system.")
            self.auth_manager.password_change_page()
            return

        # PERFORMANCE OPTIMIZATION: Use cached data if available to speed up st.rerun()
        if st.session_state.get('data_already_loaded', False) and 'cached_df' in st.session_state:
            # Use cached data to avoid database reload
            self.df = st.session_state['cached_df'].copy()
            self.display_df = st.session_state['cached_display_df'].copy()
            self.db_df = self.df.copy()
            
            # Clear the cache flags
            st.session_state['data_already_loaded'] = False
            if 'cached_df' in st.session_state:
                del st.session_state['cached_df']
            if 'cached_display_df' in st.session_state:
                del st.session_state['cached_display_df']
            
            st.success("✅ Using cached data for fast refresh")
        else:
            # Use cached data instead of reloading from database
            if not hasattr(self, 'df') or self.df is None:
                # Fallback reload if cache is missing
                self._initialize_equipment_data()

            # Set db_df for compatibility
            self.db_df = self.df.copy() if hasattr(self, 'df') and not self.df.empty else pd.DataFrame()

        # Use the Equipment_Filters function
        self.Equipment_Filters()


def main():
    """
    Main function to run the Equipment Records Page as a standalone application.
    """
    st.set_page_config(
        page_title="Equipment Records System",
        page_icon="📊",
        layout="wide"
    )
    
    # Initialize the equipment records system
    equipment_records = EquipmentRecordsSystem()
    
    # Check if user is authenticated (this would need to be implemented)
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    # Simple authentication check (in real implementation, this would be more robust)
    if not st.session_state.authenticated:
        st.markdown("## 🔐 Equipment Records Access")
        st.warning("⚠️ This is a demo. In production, proper authentication would be required.")
        
        username = st.text_input("Enter username for demo:")
        if st.button("Access Equipment Records") and username:
            # In real implementation, verify credentials
            st.session_state.authenticated = True
            st.session_state.username = username
            st.rerun()
    else:
        # Show equipment records interface
        st.title("📊 Equipment Records System")
        st.markdown(f"**Logged in as:** {st.session_state.username}")
        
        # Display the equipment records page
        equipment_records.equipment_records_page()
        
        # Add logout button
        if st.sidebar.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.rerun()


if __name__ == "__main__":
    main()
