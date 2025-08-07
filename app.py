
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
import pandas as pd
from pathlib import Path
import numpy as np
import hashlib
import json
import time
import uuid
from datetime import datetime, timedelta
from streamlit_cookies_controller import CookieController
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import sys

# Import backup and restore functionality
try:
    from backup_csv_for_db_restore import backup_restore_ui, integrate_auto_backup_into_main_app
except ImportError:
    st.warning("⚠️ Backup system not available. Please ensure backup_csv_for_db_restore.py is in the same directory.")
    backup_restore_ui = None
    integrate_auto_backup_into_main_app = None

class EquipmentManagementApp:
    def add_column_to_db(self, col_name, default_value=None):
        """
        Add a new column to all records in the Equipment collection and update the DataFrame.
        Args:
            col_name (str): Name of the new column
            default_value: Default value for the new column (optional)
        Returns:
            int: Number of records updated
        """
        update_result = self.Equipment_collection.update_many(
            {},
            {"$set": {col_name: default_value}}
        )
        # Also update the DataFrame in memory
        if col_name not in self.df.columns:
            self.df[col_name] = default_value
            # Apply saved column order for equipment table
            self.df = self._apply_column_order(self.df, 'equipment')
        return update_result.modified_count
    
    def delete_column_from_db(self, col_name):
        """
        Delete a column from all records in the Equipment collection and update the DataFrame.
        Args:
            col_name (str): Name of the column to delete
        Returns:
            int: Number of records updated
        """
        update_result = self.Equipment_collection.update_many(
            {},
            {"$unset": {col_name: ""}}
        )
        # Also update the DataFrame in memory
        if col_name in self.df.columns:
            self.df = self.df.drop(columns=[col_name])
        return update_result.modified_count
    
    def _save_column_order(self, table_type, column_order):
        """
        Save column order preference for a specific table type.
        Args:
            table_type (str): 'equipment' or 'select_options'
            column_order (list): List of column names in preferred order
        """
        try:
            # Save to a JSON file for persistence
            column_order_file = Path("column_order_preferences.json")
            
            # Load existing preferences if file exists
            preferences = {}
            if column_order_file.exists():
                try:
                    with open(column_order_file, 'r') as f:
                        preferences = json.load(f)
                except:
                    preferences = {}
            
            # Update preferences for this table type
            preferences[table_type] = column_order
            
            # Save back to file
            with open(column_order_file, 'w') as f:
                json.dump(preferences, f, indent=2)
            
            return True
        except Exception as e:
            st.error(f"Error saving column order: {str(e)}")
            return False
    
    def _load_column_order(self, table_type, default_columns):
        """
        Load saved column order preference for a specific table type.
        Args:
            table_type (str): 'equipment' or 'select_options'
            default_columns (list): Default column order to use if no saved preference
        Returns:
            list: Ordered list of column names
        """
        try:
            column_order_file = Path("column_order_preferences.json")
            
            if column_order_file.exists():
                with open(column_order_file, 'r') as f:
                    preferences = json.load(f)
                
                if table_type in preferences:
                    saved_order = preferences[table_type]
                    # Ensure all current columns are included (in case new columns were added)
                    missing_columns = [col for col in default_columns if col not in saved_order]
                    # Add any missing columns at the end
                    return saved_order + missing_columns
            
            # Return default order if no saved preference
            return default_columns
        except Exception as e:
            # Return default order if there's an error loading preferences
            return default_columns
    
    def _apply_column_order(self, df, table_type):
        """
        Apply saved column order to a DataFrame.
        Args:
            df (pandas.DataFrame): DataFrame to reorder
            table_type (str): 'equipment' or 'select_options'
        Returns:
            pandas.DataFrame: DataFrame with columns in saved order
        """
        if df is None or df.empty:
            return df
        
        current_columns = list(df.columns)
        ordered_columns = self._load_column_order(table_type, current_columns)
        
        # Filter to only include columns that actually exist in the DataFrame
        valid_ordered_columns = [col for col in ordered_columns if col in current_columns]
        
        # Add any columns that weren't in the saved order at the end
        missing_columns = [col for col in current_columns if col not in valid_ordered_columns]
        final_order = valid_ordered_columns + missing_columns
        
        return df[final_order]
    
    def rename_column_in_db(self, old_col_name, new_col_name):
        """
        Rename a column in all records in the Equipment collection and update the DataFrame.
        Column position is preserved in all DataFrames.
        Args:
            old_col_name (str): Current name of the column
            new_col_name (str): New name for the column
        Returns:
            int: Number of records updated
        """
        try:
            # Use MongoDB's $rename operator to rename the field
            update_result = self.Equipment_collection.update_many(
                {},
                {"$rename": {old_col_name: new_col_name}}
            )
            
            # Also update the DataFrame in memory - preserving column order and putting ID first
            if old_col_name in self.df.columns:
                # Store original column order
                original_columns = self.df.columns.tolist()
                # Rename the column (preserves order automatically)
                self.df = self.df.rename(columns={old_col_name: new_col_name})
                # Verify order is preserved (this is just for safety, pandas.rename should preserve order)
                new_columns = [new_col_name if col == old_col_name else col for col in original_columns]
                self.df = self.df[new_columns]
                # Apply saved column order for equipment table
                self.df = self._apply_column_order(self.df, 'equipment')
            
            # Update other DataFrames if they exist - preserving column order and putting ID first
            if hasattr(self, 'db_df') and self.db_df is not None and old_col_name in self.db_df.columns:
                original_columns = self.db_df.columns.tolist()
                self.db_df = self.db_df.rename(columns={old_col_name: new_col_name})
                new_columns = [new_col_name if col == old_col_name else col for col in original_columns]
                self.db_df = self.db_df[new_columns]
                # Apply saved column order for equipment table
                self.db_df = self._apply_column_order(self.db_df, 'equipment')
            
            if hasattr(self, 'display_df') and self.display_df is not None and old_col_name in self.display_df.columns:
                original_columns = self.display_df.columns.tolist()
                self.display_df = self.display_df.rename(columns={old_col_name: new_col_name})
                new_columns = [new_col_name if col == old_col_name else col for col in original_columns]
                self.display_df = self.display_df[new_columns]
                # Apply saved column order for equipment table
                self.display_df = self._apply_column_order(self.display_df, 'equipment')
            
            # Re-identify column types after rename to update category lists
            self._identify_column_types()
            
            return update_result.modified_count
        except Exception as e:
            raise Exception(f"Error renaming column in database: {str(e)}")
    
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
            
            # Update the edited DataFrame if it exists - preserving column order and putting ID first
            if hasattr(self, 'edited_select_options_df') and self.edited_select_options_df is not None:
                if old_col_name in self.edited_select_options_df.columns:
                    original_columns = self.edited_select_options_df.columns.tolist()
                    self.edited_select_options_df = self.edited_select_options_df.rename(columns={old_col_name: new_col_name})
                    new_columns = [new_col_name if col == old_col_name else col for col in original_columns]
                    self.edited_select_options_df = self.edited_select_options_df[new_columns]
                    # Apply saved column order for select options table
                    self.edited_select_options_df = self._apply_column_order(self.edited_select_options_df, 'select_options')
            
            # Re-identify column types after rename to update category lists
            self._identify_column_types()
            
            return update_result.modified_count
        except Exception as e:
            raise Exception(f"Error renaming column in select options database: {str(e)}")
    def init_db_from_csv(self, unique_key=None):
        """
        Initialize the Equipment collection from CSV, inserting only unique rows based on a unique key.
        Args:
            unique_key (str or list): Column(s) to use as unique key. If None, use all columns.
        """
        # Load and clean data
        df = self.load_data()
        if df.empty:
            return
        # Remove duplicates in DataFrame
        if unique_key:
            df = df.drop_duplicates(subset=unique_key)
        else:
            df = df.drop_duplicates()

        records = df.to_dict(orient='records')
        # Insert only unique records not already in DB
        for record in records:
            # Build filter for uniqueness
            if unique_key:
                if isinstance(unique_key, list):
                    filter_query = {k: record.get(k) for k in unique_key}
                else:
                    filter_query = {unique_key: record.get(unique_key)}
            else:
                filter_query = record.copy()
            if not self.Equipment_collection.find_one(filter_query):
                self.Equipment_collection.insert_one(record)
    """
    A class-based Streamlit application for managing equipment data from CSV files.
    """

    def filter_select_options_df(self, df, filter_columns, search_text):

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

        # Insert unique, case-insensitive, trimmed values for Location, Vendor, Category into Equipment_select_options DB
        # Read the CSV as a DataFrame to preserve the structure
        csv_path = Path("‏‏select_options_csv.csv")
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            st.warning(f"Could not read Equipment_select_options.csv: {e}")
            

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



    def __init__(self, csv_filename="ACT-LAB-Equipment-List.csv"):
        """
        Initialize the Equipment Management App.
        
        Args:
            csv_filename (str): Name of the CSV file to load
        """
        self.csv_filename = csv_filename
        self.df = None
        self.filtered_df = None
        self.available_columns = []
        self.category_cols = []
        self.vendor_cols = []
        self.location_cols = []
        self.serial_cols = []
        self.check_cols = []
        self.search_cols = []
        
        self.login = "Altera Lab Equipment"
        self.main_page_titel = "🔬 Altera Lab Equipment Management System"

        # Initialize cookie controller for persistent sessions
        self.cookie_controller = CookieController()
        
        # FIXED: Create a simple file-based session storage that persists across restarts
        self.sessions_file = Path("sessions_storage.json")
        
        # Session storage - in production, use a database like MongoDB
        # Initialize persistent session storage that survives app restarts
        if 'sessions_storage' not in st.session_state:
            st.session_state.sessions_storage = self._load_sessions_from_file()
        
        # Also store sessions in a more persistent way using multiple session state keys
        if 'persistent_sessions' not in st.session_state:
            st.session_state.persistent_sessions = st.session_state.sessions_storage.copy()

        # Initialize users (in production, this should be in a database)
        self.users = {
            "admin": {
                "password": self._hash_password("admin123"),
                "role": "admin",
                "name": "Administrator"
            },
            "lab_manager": {
                "password": self._hash_password("labmgr123"),
                "role": "manager",
                "name": "Lab Manager"
            },
            "technician": {
                "password": self._hash_password("tech123"),
                "role": "technician",
                "name": "Lab Technician"
            },
            "user": {
                "password": self._hash_password("123"),
                "role": "user",
                "name": "Lab user"
            },         
            "tech": {
                "password": self._hash_password("123"),
                "role": "tech",  # Changed from "technician" to "tech"
                "name": "Lab Technician"
            }
        }
    
    def _hash_password(self, password):
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, username, password):
        """Verify username and password."""
        if username in self.users:
            hashed_password = self._hash_password(password)
            return self.users[username]["password"] == hashed_password
        return False
    
    def _load_sessions_from_file(self):
        """Load sessions from file storage."""
        try:
            if self.sessions_file.exists():
                with open(self.sessions_file, 'r') as f:
                    data = json.load(f)
                    # Convert timestamp strings back to datetime objects
                    for session_id, session_data in data.items():
                        if 'timestamp' in session_data and isinstance(session_data['timestamp'], str):
                            session_data['timestamp'] = datetime.fromisoformat(session_data['timestamp'])
                    return data
        except Exception as e:
            # If file is corrupted, start fresh
            pass
        return {}
    
    def _save_sessions_to_file(self):
        """Save sessions to file storage."""
        try:
            # Convert datetime objects to strings for JSON serialization
            data_to_save = {}
            for session_id, session_data in st.session_state.sessions_storage.items():
                data_copy = session_data.copy()
                if 'timestamp' in data_copy and isinstance(data_copy['timestamp'], datetime):
                    data_copy['timestamp'] = data_copy['timestamp'].isoformat()
                data_to_save[session_id] = data_copy
            
            with open(self.sessions_file, 'w') as f:
                json.dump(data_to_save, f, indent=2)
        except Exception as e:
            # Silent error handling for file operations
            pass
    
    def set_cookie(self, cookie_name, value):
        """Set cookie with better error handling and verification."""
        try:
            expires = datetime.now() + timedelta(minutes=480)
            self.cookie_controller.set(cookie_name, value, path="/", same_site="Lax", expires=expires)
            time.sleep(0.1)
            verify_cookie = self.cookie_controller.get(cookie_name)
            if verify_cookie == value:
                return True
            return False
        except Exception as e:
            st.error(f"Cookie set error: {e}")
            return False
    
    def save_session(self, username, role):
        """Save session to cookies and storage."""
        try:
            session_token = str(uuid.uuid4())
            timestamp = datetime.now()
            
            # Create session data
            session_data = {
                "username": username,
                "role": role,
                "timestamp": timestamp,
                "session_token": session_token
            }
            
            # Store session in multiple places for redundancy
            st.session_state.sessions_storage[session_token] = session_data
            st.session_state.persistent_sessions[session_token] = session_data
            
            # Also store individual session data directly in session state for backup
            st.session_state[f'session_backup_{session_token}'] = session_data
            
            # FIXED: Save to file for true persistence
            self._save_sessions_to_file()
            
            # Store session token in cookie using the new set_cookie method
            if not self.set_cookie("session_token", session_token):
                st.error("Failed to set session cookie. Session may not persist after refresh.")
                return False
            
            # Also update current session state
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.user_role = role
            st.session_state.login_time = timestamp.timestamp()
            st.session_state.session_id = session_token
            
            return True
        except Exception as e:
            st.error(f"Session save error: {e}")
            return False
    
    def load_session(self):
        """Load session from cookies similar to your MongoDB version."""
        try:
            session_token = self.cookie_controller.get("session_token")
            if session_token:
                # FIXED: First reload sessions from file to get latest state
                file_sessions = self._load_sessions_from_file()
                
                # Try to find session in multiple places
                session = None
                
                # First try file storage (most reliable)
                if session_token in file_sessions:
                    session = file_sessions[session_token]
                    # Restore to session state
                    st.session_state.sessions_storage[session_token] = session
                    st.session_state.persistent_sessions[session_token] = session
                
                # If not in file, try main storage
                elif session_token in st.session_state.sessions_storage:
                    session = st.session_state.sessions_storage[session_token]
                
                # If not found, try persistent storage
                elif session_token in st.session_state.persistent_sessions:
                    session = st.session_state.persistent_sessions[session_token]
                    # Restore to main storage
                    st.session_state.sessions_storage[session_token] = session
                
                # If still not found, try backup storage
                elif f'session_backup_{session_token}' in st.session_state:
                    session = st.session_state[f'session_backup_{session_token}']
                    # Restore to main storage
                    st.session_state.sessions_storage[session_token] = session
                    st.session_state.persistent_sessions[session_token] = session
                
                # If we found a session, validate and restore it
                if session:
                    # Check if session is still valid (within 480 minutes)
                    if datetime.now() - session["timestamp"] <= timedelta(minutes=480):
                        # Session is valid, restore it
                        st.session_state.authenticated = True
                        st.session_state.username = session["username"]
                        st.session_state.user_role = session["role"]
                        st.session_state.login_time = session["timestamp"].timestamp()
                        st.session_state.session_id = session_token
                        return True
                    else:
                        # Session expired, clean up everywhere
                        self._cleanup_session(session_token)
                else:
                    # No session found but we have a cookie - this is the problem case
                    # Clean up the orphaned cookie
                    try:
                        self.cookie_controller.remove("session_token")
                    except:
                        pass
            return False
        except Exception as e:
            # Silent error handling for session loading to avoid UI disruption
            return False
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions from storage."""
        try:
            current_time = datetime.now()
            expired_sessions = []
            
            # Check main storage
            for token, session in st.session_state.sessions_storage.items():
                if current_time - session["timestamp"] > timedelta(minutes=480):
                    expired_sessions.append(token)
            
            # Clean up expired sessions from all storages
            for token in expired_sessions:
                self._cleanup_session(token)
                
        except Exception as e:
            # Silent cleanup - don't show errors to users
            pass
    
    def _cleanup_session(self, session_token):
        """Clean up a specific session from all storage locations."""
        try:
            # Remove from main storage
            if session_token in st.session_state.sessions_storage:
                del st.session_state.sessions_storage[session_token]
            
            # Remove from persistent storage
            if session_token in st.session_state.persistent_sessions:
                del st.session_state.persistent_sessions[session_token]
            
            # Remove backup
            backup_key = f'session_backup_{session_token}'
            if backup_key in st.session_state:
                del st.session_state[backup_key]
            
            # FIXED: Remove from file storage
            self._save_sessions_to_file()
            
            # Remove cookie
            try:
                self.cookie_controller.remove("session_token")
            except:
                pass
        except Exception as e:
            # Silent cleanup
            pass
    
    def _initialize_session(self):
        """Initialize session state with default values if not already set."""
        # Try to load session from cookies first ONLY if not already authenticated
        if not st.session_state.get('authenticated', False):
            self.load_session()
        
        # Only set defaults for keys that literally don't exist in session state
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'username' not in st.session_state:
            st.session_state.username = None
        if 'user_role' not in st.session_state:
            st.session_state.user_role = None
        if 'login_time' not in st.session_state:
            st.session_state.login_time = None
        if 'session_id' not in st.session_state:
            st.session_state.session_id = None
            
        # These are safe to initialize always as they don't affect authentication
        if 'app_initialized' not in st.session_state:
            st.session_state.app_initialized = True
        if 'session_persistent' not in st.session_state:
            st.session_state.session_persistent = True
    
    def login_page(self):
        """Display the login page."""
        # Check if user is already authenticated via cookies
        if self.load_session():
            # User has valid session, redirect to main app
            st.rerun()
            return
        
        # Debug: Check current authentication status
        current_auth = st.session_state.get('authenticated', False)
        current_session_id = st.session_state.get('session_id')
        current_username = st.session_state.get('username')
        
        # Check if user is already authenticated (session persistence)
        if (current_auth and 
            bool(current_session_id) and 
            bool(current_username)):
            # User has valid session, redirect to main app by returning
            return
        
        # Custom CSS for login page
        st.markdown("""
            <style>
            /* Hide Streamlit's default elements */
            #MainMenu {visibility: hidden;}
            .stDeployButton {display: none !important;}
            footer {visibility: hidden;}
            .stApp > header {visibility: hidden;}
            
            /* Center the login form and set width to 50% */
            .main .block-container {
            padding-top: 2rem;
            background-color: #ffffff;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            }
            
            .login-container {
            width: 100%;
            min-width: 350px;
            max-width: 450px;
            margin: 2rem auto;
            padding: 2.5rem;
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
            background-color: #ffffff !important;
            border: 1px solid #e0e0e0;
            position: relative;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            align-items: center;
            }
            
            .login-header {
            text-align: center;
            color: #1f77b4 !important;
            font-size: 2.2rem;
            font-weight: bold;
            margin-bottom: 1.5rem;
            text-shadow: none;
            }
            
            .login-info {
            background-color: #e3f2fd !important;
            padding: 1.2rem;
            border-radius: 8px;
            margin: 1.5rem 0;
            border-left: 4px solid #1f77b4;
            color: #333 !important;
            }
            
            .stButton > button {
            width: 100%;
            background-color: #1f77b4 !important;
            color: white !important;
            border: none;
            padding: 0.7rem;
            border-radius: 8px;
            font-weight: bold;
            font-size: 1rem;
            margin-top: 1rem;
            }
            
            .stButton > button:hover {
            background-color: #1565c0 !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }
            
            /* Make form visible */
            .stForm {
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            display: flex;
            flex-direction: column;
            align-items: center;
            }
            
            /* Style form inputs - More aggressive targeting */
            .stTextInput > div > div > input,
            input[type="text"],
            input[type="password"] {
            background-color: #f8f9fa !important;
            border: 1px solid #ddd !important;
            border-radius: 6px !important;
            padding: 0.4rem !important;
            height: 2.2rem !important;
            font-size: 0.9rem !important;
            line-height: 1.1 !important;
            min-height: 2.2rem !important;
            max-height: 2.2rem !important;
            box-sizing: border-box !important;
            width: 100% !important; /* Full width inside the container */
            margin: 0 auto;
            display: block;
            }
            
            /* Make input containers more compact and centered */
            .stTextInput > div {
            margin-bottom: 0.3rem !important;
            height: auto !important;
            display: flex;
            justify-content: center;
            }
            
            .stTextInput > div > div {
            height: 2.2rem !important;
            min-height: 2.2rem !important;
            max-height: 2.2rem !important;
            overflow: hidden !important;
            }
            
            .stTextInput > label {
            font-size: 0.85rem !important;
            margin-bottom: 0.2rem !important;
            font-weight: 500 !important;
            line-height: 1.1 !important;
            display: block;
            text-align: center;
            }
            
            /* Override any default form spacing */
            .stForm > div {
            gap: 0.3rem !important;
            display: flex;
            flex-direction: column;
            align-items: center;
            }
            
            /* Force compact form elements */
            .stForm [data-testid="stVerticalBlock"] > div {
            gap: 0.3rem !important;
            display: flex;
            flex-direction: column;
            align-items: center;
            }
            
            /* Ensure text is visible */
            div[data-testid="stMarkdownContainer"] {
            color: #333 !important;
            }
            
            /* Style the subtitle */
            h3 {
            color: #666 !important;
            text-align: center;
            margin-bottom: 2rem;
            }
            </style>
        """, unsafe_allow_html=True)
        # Remove the login-container div wrapper (do not add <div class="login-container">)
        # st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # st.markdown('<h1 class="login-header">🔬 ACT Lab Equipment</h1>', unsafe_allow_html=True)
        st.markdown(f'<h1 class="login-header">🔬 {self.login}</h1>', unsafe_allow_html=True)
        st.markdown('<h3 style="text-align: center; color: #666;">Management System</h3>', unsafe_allow_html=True)
        
        # Add a visible separator
        st.markdown("---")
        
        # Login form
        with st.form("login_form"):
            st.markdown("### 🔐 Please Login")
            username = st.text_input("Username", placeholder="Enter your username", key="login_username")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                login_button = st.form_submit_button("🚀 Login")
            
            if login_button:
                if username and password:  # Basic validation
                    if self._verify_password(username, password):
                        # Save session with cookies
                        if self.save_session(username, self.users[username]["role"]):
                            st.success(f"Welcome, {self.users[username]['name']}!")
                            time.sleep(1)  # Small delay to show success message
                            st.rerun()
                        else:
                            st.error("❌ Failed to create session. Please try again.")
                    else:
                        st.error("❌ Invalid username or password!")
                else:
                    st.warning("⚠️ Please enter both username and password!")
        
        # Demo credentials info - commented out for production
        # st.markdown('<div class="login-info">', unsafe_allow_html=True)
        # st.markdown("### 📋 Demo Credentials")
        # st.markdown("""
        # **Admin:** admin / admin123  
        # **Manager:** lab_manager / labmgr123  
        # **Technician:** technician / tech123
        # """)
        # st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
    
    def logout(self):
        """Handle user logout."""
        try:
            # Get current session token
            session_token = st.session_state.get('session_id')
            if session_token:
                # Clean up from all storage locations
                self._cleanup_session(session_token)
        except Exception as e:
            # Silent error handling for logout
            pass
        
        # Clear all session data
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_role = None
        st.session_state.login_time = None
        st.session_state.session_id = None
        st.session_state.session_persistent = False
        
        # Remove any additional session keys that might exist
        keys_to_remove = [key for key in st.session_state.keys() if key.startswith('login_') or key == '_persist']
        for key in keys_to_remove:
            del st.session_state[key]
        
        st.rerun()
    
    def _check_session_validity(self):
        """Check if the current session is still valid."""
        # Ensure session is initialized
        self._initialize_session()
        
        # Check if user is authenticated
        if not st.session_state.get('authenticated', False):
            return False
        
        # Check if required session data exists
        username = st.session_state.get('username')
        user_role = st.session_state.get('user_role')
        if not username or not user_role:
            return False
        
        # Check if login time exists and session hasn't expired (24 hours)
        login_time = st.session_state.get('login_time')
        if login_time:
            import time
            session_duration = time.time() - login_time
            # Session expires after 24 hours (86400 seconds)
            if session_duration > 86400:
                self.logout()
                return False
        
        # Verify user still exists in system
        if username not in self.users:
            self.logout()
            return False
        
        return True
    
    def get_user_permissions(self):
        """Get user permissions based on role with proper error handling."""
        permissions = {
            "admin": {
                "can_edit": True,
                "can_delete": True,
                "can_export": True,
                "can_manage_users": True,
                "can_view_all": True
            },
            "manager": {
                "can_edit": True,
                "can_delete": False,
                "can_export": True,
                "can_manage_users": False,
                "can_view_all": True
            },
            "technician": {
                "can_edit": True,
                "can_delete": False,
                "can_export": False,
                "can_manage_users": False,
                "can_view_all": True
            },
            "tech": {
                "can_edit": True,
                "can_delete": True,
                "can_export": True,
                "can_manage_users": True,
                "can_view_all": True
            },
            "user": {
                "can_edit": False,
                "can_delete": False,
                "can_export": False,
                "can_manage_users": False,
                "can_view_all": True
            }
        }
        
        # Get current user role
        current_role = st.session_state.get('user_role')
        current_username = st.session_state.get('username')
        
        # Check if role exists in permissions
        if current_role in permissions:
            return permissions[current_role]
        
        # Handle unknown role gracefully
        st.error(f"⚠️ Unknown user role: '{current_role}'. Please contact an administrator.")
        
        # Return minimal safe permissions for unknown roles
        return {
            "can_edit": False,
            "can_delete": False,
            "can_export": False,
            "can_manage_users": False,
            "can_view_all": True  # At least allow viewing
        }
        

    
    def display_header(self):
        """Display header with user info and logout."""
        # User info and logout in a container
        st.markdown('<div class="user-header">', unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1])
        
        with col1:
            user_info = self.users[st.session_state.username]
            # Calculate session duration
            if st.session_state.login_time:
                session_duration = time.time() - st.session_state.login_time
                hours = int(session_duration // 3600)
                minutes = int((session_duration % 3600) // 60)
                session_info = f" (Session: {hours}h {minutes}m)" if hours > 0 or minutes > 0 else " (Just logged in)"
            else:
                session_info = ""
            
            st.markdown(f"👤 **{user_info['name']}** ({user_info['role'].title()}){session_info}")
        
        with col2:
            if st.button("🚪 Logout", key="logout_btn"):
                self.logout()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Main title
        st.markdown(f'<h1 class="main-header">{self.main_page_titel}</h1>', unsafe_allow_html=True)


    def configure_page(self):
        """Configure Streamlit page settings and CSS styling."""
        # Page config is now set at module level, just add CSS
        # Custom CSS for better styling
        st.markdown("""
            <style>
                /* Hide Streamlit's default elements */
                #MainMenu {visibility: hidden;}
                .stDeployButton {display: none !important;}
                button[kind="header"] {display: none !important;}
                [data-testid="stToolbar"] {display: none !important;}
                .stAppDeployButton {display: none !important;}
                footer {visibility: hidden;}
                .stApp > header {visibility: hidden;}
                
                .block-container {
                    padding-top: 1rem;
                    padding-bottom: 2rem;
                }
                .stSelectbox > div > div > div > div {
                    background-color: #f0f2f6;
                }
                .main-header {
                    text-align: center;
                    color: #1f77b4;
                    font-size: 2.2rem;
                    font-weight: bold;
                    margin-bottom: 1rem;
                }
                
                /* Header styling for better visibility */
                .user-header {
                    background-color: #f8f9fa;
                    padding: 0.5rem 1rem;
                    border-radius: 8px;
                    margin-bottom: 1rem;
                    border: 1px solid #e0e0e0;
                }
                
                /* Ensure buttons are visible with white background */
                .stButton > button {
                    background-color: #ffffff !important;
                    color: #333333 !important;
                    border: 1px solid #dddddd !important;
                    border-radius: 5px;
                    padding: 0.4rem 1rem;
                    font-size: 0.9rem;
                }
                
                .stButton > button:hover {
                    background-color: #f8f9fa !important;
                    border-color: #aaaaaa !important;
                }
            </style>
        """, unsafe_allow_html=True)
    
    @st.cache_data
    def load_data(_self):
        """
        Load the CSV file and clean it.
        
        Returns:
            pandas.DataFrame: Cleaned DataFrame or empty DataFrame if error
        """
        csv_path = Path(_self.csv_filename)
        if not csv_path.exists():
            st.error(f"CSV file '{_self.csv_filename}' not found!")
            return pd.DataFrame()
        
        try:
            # Try different encodings to handle Unicode issues
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                st.error("Could not read CSV file with any supported encoding")
                return pd.DataFrame()
            
            return _self._clean_dataframe(df)
            
        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}")
            return pd.DataFrame()
    
    def _clean_dataframe(self, df):
        """
        Clean the DataFrame by removing empty columns and rows.
        
        Args:
            df (pandas.DataFrame): Raw DataFrame
            
        Returns:
            pandas.DataFrame: Cleaned DataFrame
        """
        # Get all actual columns from the CSV (not hardcoded)
        actual_columns = df.columns.tolist()
        
        # Remove columns that are mostly empty (more than 95% empty)
        non_empty_columns = []
        for col in actual_columns:
            non_empty_ratio = (df[col].notna() & (df[col] != '')).sum() / len(df)
            if non_empty_ratio > 0.05:  # Keep columns with more than 5% data
                non_empty_columns.append(col)
        
        # Keep only non-empty columns
        if non_empty_columns:
            df = df[non_empty_columns]
        
        # Clean the data
        df = df.replace('', np.nan)  # Replace empty strings with NaN
        df = df.dropna(how='all')  # Remove completely empty rows
        
        # Rename the first column for clarity if it has trailing space
        first_col = df.columns[0]
        if first_col.strip() != first_col:  # Has trailing/leading spaces
            df = df.rename(columns={first_col: first_col.strip() + '_ID'})
        
        return df
    
    def _identify_column_types(self):
        """Identify different types of columns based on their names."""
        # Check if self.df exists and is not None
        if self.df is None or self.df.empty:
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
        
        self.available_columns = self.df.columns.tolist()
        
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
    
    def _get_best_unique_identifier(self, row_data):
        """Get the best unique identifier for a row based on available columns and data."""
        if not hasattr(self, 'unique_id_cols') or not self.unique_id_cols:
            self._identify_column_types()
        
        # If still no unique_id_cols after identification, return None
        if not hasattr(self, 'unique_id_cols') or not self.unique_id_cols:
            return None, None
        
        # Try each unique identifier in order of preference
        for col in self.unique_id_cols:
            if col in row_data and pd.notna(row_data[col]) and str(row_data[col]).strip():
                return col, row_data[col]
        
        # If no unique identifier found, return None
        return None, None
    
    def _create_delete_query(self, row_data):
        """Create a MongoDB delete query for a row using the best available unique identifier."""
        id_col, id_value = self._get_best_unique_identifier(row_data)
        
        if id_col and id_value:
            return {id_col: id_value}
        else:
            # Fallback: use all non-null values as query
            return {k: v for k, v in row_data.items() if pd.notna(v) and str(v).strip()}
    
    def _get_values_for_deletion(self, selected_df, column_name):
        """Get list of values from a column for deletion, excluding null/empty values."""
        if column_name in selected_df.columns:
            return selected_df[column_name].dropna().tolist()
        return []
    
    def _should_have_dropdown(self, column_name):
        """Determine if a column should have dropdown options based on its type."""
        # Ensure column types are identified
        if not hasattr(self, 'category_cols'):
            self._identify_column_types()
        
        # Check if column is in any of the identified dropdown-eligible column lists
        dropdown_col_lists = [
            getattr(self, 'category_cols', []),
            getattr(self, 'vendor_cols', []), 
            getattr(self, 'location_cols', []),
            getattr(self, 'check_cols', []),
            getattr(self, 'serial_cols', [])
        ]
        
        for col_list in dropdown_col_lists:
            if col_list and column_name in col_list:
                return True
        
        # Additional pattern-based check for columns that might be missed
        col_lower = column_name.lower()
        dropdown_patterns = [
            'category', 'vendor', 'location', 'status', 'check', 
            'type', 'brand', 'manufacturer', 'department', 'room',
            'building', 'floor', 'section', 'area'
        ]
        
        return any(pattern in col_lower for pattern in dropdown_patterns)
    
    def _is_checkbox_column(self, column_name):
        """Determine if a column is a checkbox-type column that should be freely editable."""
        col_lower = column_name.lower()
        checkbox_patterns = [
            'check box', 'checkbox', 'check_box', 'check-box',
            'checked', 'active', 'enabled', 'disabled', 'status',
            'yes_no', 'yes/no', 'true_false', 'true/false',
            'pass_fail', 'pass/fail', 'ok_not_ok', 'ok/not_ok'
        ]
        
        return any(pattern in col_lower for pattern in checkbox_patterns)
    
    def create_sidebar_filters(self, prefix=""):
        """
        Create sidebar filters where each filter's options are dependent on previous filter selections.
        """
        def _key(name):
            return f"{prefix}_{name}" if prefix else name

        st.sidebar.header(f"🔍 {prefix}_Filters")
        filter_columns = {}

        # Start with full DataFrame
        filtered_df = self.df.copy()

        # Category filter
        if self.category_cols:
            category_col = self.category_cols[0]
            categories = ['All'] + sorted([cat for cat in filtered_df[category_col].dropna().unique() if str(cat).strip() != ''])
            selected_category = st.sidebar.selectbox(f"Filter by {category_col}", categories, key=_key('category'))
            filter_columns['category'] = selected_category
            if selected_category != 'All':
                filtered_df = filtered_df[filtered_df[category_col] == selected_category]

        # Vendor filter
        if self.vendor_cols:
            vendor_col = self.vendor_cols[0]
            vendors = ['All'] + sorted([vendor for vendor in filtered_df[vendor_col].dropna().unique() if str(vendor).strip() != ''])
            selected_vendor = st.sidebar.selectbox(f"Filter by {vendor_col}", vendors, key=_key('vendor'))
            filter_columns['vendor'] = selected_vendor
            if selected_vendor != 'All':
                filtered_df = filtered_df[filtered_df[vendor_col] == selected_vendor]

        # Location filter
        if self.location_cols:
            location_col = self.location_cols[0]
            locations = ['All'] + sorted([loc for loc in filtered_df[location_col].dropna().unique() if str(loc).strip() != ''])
            selected_location = st.sidebar.selectbox(f"Filter by {location_col}", locations, key=_key('location'))
            filter_columns['location'] = selected_location
            if selected_location != 'All':
                filtered_df = filtered_df[filtered_df[location_col] == selected_location]

        # Check status filter
        if self.check_cols:
            check_col = self.check_cols[0]
            check_statuses = ['All'] + sorted([str(check) for check in filtered_df[check_col].dropna().unique()])
            selected_check = st.sidebar.selectbox(f"Filter by {check_col}", check_statuses, key=_key('check'))
            filter_columns['check'] = selected_check
            if selected_check != 'All':
                filtered_df = filtered_df[filtered_df[check_col].astype(str) == selected_check]

        # Serial filter
        if self.serial_cols:
            serial_col = self.serial_cols[0]
            serials = ['All'] + sorted([str(serial) for serial in filtered_df[serial_col].dropna().unique() if str(serial).strip() != ''])
            selected_serial = st.sidebar.selectbox(f"Filter by {serial_col}", serials, key=_key('serial'))
            filter_columns['serial'] = selected_serial
            if selected_serial != 'All':
                filtered_df = filtered_df[filtered_df[serial_col] == selected_serial]

        # Text search
        search_text = st.sidebar.text_input(f"🔍 Search in: {', '.join(self.search_cols[:3])}", key=_key('search'))

        return filter_columns, search_text
    
    def apply_filters(self, filter_columns, search_text):
        """
        Apply filters to the DataFrame, making each filter dependent on previous selections.
        Args:
            filter_columns (dict): Dictionary of filter selections
            search_text (str): Text to search for
        """
        self.filtered_df = self.df.copy()

        # Apply filters in order, each time narrowing the DataFrame for subsequent filters
        if self.category_cols and 'category' in filter_columns and filter_columns['category'] != 'All':
            self.filtered_df = self.filtered_df[self.filtered_df[self.category_cols[0]] == filter_columns['category']]

        if self.vendor_cols and 'vendor' in filter_columns and filter_columns['vendor'] != 'All':
            self.filtered_df = self.filtered_df[self.filtered_df[self.vendor_cols[0]] == filter_columns['vendor']]

        if self.location_cols and 'location' in filter_columns and filter_columns['location'] != 'All':
            self.filtered_df = self.filtered_df[self.filtered_df[self.location_cols[0]] == filter_columns['location']]

        if self.check_cols and 'check' in filter_columns and filter_columns['check'] != 'All':
            self.filtered_df = self.filtered_df[self.filtered_df[self.check_cols[0]].astype(str) == filter_columns['check']]

        if self.serial_cols and 'serial' in filter_columns and filter_columns['serial'] != 'All':
            self.filtered_df = self.filtered_df[self.filtered_df[self.serial_cols[0]] == filter_columns['serial']]

        # Apply text search last
        if search_text and self.search_cols:
            mask = pd.Series([False] * len(self.filtered_df))
            for col in self.search_cols:
                if col in self.filtered_df.columns:
                    mask |= self.filtered_df[col].astype(str).str.contains(search_text, case=False, na=False)
            self.filtered_df = self.filtered_df[mask]
    
    # def configure_aggrid(self):
    #     """
    #     Configure AgGrid with dynamic column settings.
        
    #     Returns:
    #         dict: Grid options for AgGrid
    #     """
    #     gb = GridOptionsBuilder.from_dataframe(self.filtered_df)
        
    #     # Get user permissions
    #     permissions = self.get_user_permissions()
        
    #     # Enable editing based on permissions
    #     gb.configure_default_column(
    #         editable=permissions["can_edit"], 
    #         groupable=True, 
    #         resizable=True, 
    #         sortable=True, 
    #         filter=True
    #     )
        
    #     # Configure specific columns based on what exists with flexible widths
    #     for col in self.filtered_df.columns:
    #         col_lower = col.lower()
            
    #         # Calculate dynamic width based on column name length and content
    #         col_name_length = len(col)
    #         min_width = max(80, col_name_length * 8)  # Minimum width based on column name
            
    #         # ID columns - make read-only with smaller width
    #         if any(term in col_lower for term in ['id', '_id']):
    #             gb.configure_column(col, editable=False, width=min_width, minWidth=60, maxWidth=120)
            
    #         # Short text columns
    #         elif any(term in col_lower for term in ['category', 'vendor', 'location', 'check', 'etag']):
    #             gb.configure_column(col, width=max(min_width, 150), minWidth=100, maxWidth=200, wrapText=True, autoHeight=True)
            
    #         # Medium text columns
    #         elif any(term in col_lower for term in ['model', 'serial']):
    #             gb.configure_column(col, width=max(min_width, 180), minWidth=120, maxWidth=250, wrapText=True, autoHeight=True)
            
    #         # Long text columns with tooltips
    #         elif any(term in col_lower for term in ['description', 'comments']):
    #             gb.configure_column(col, width=max(min_width, 250), minWidth=150, maxWidth=400, tooltipField=col, wrapText=True, autoHeight=True)
            
    #         # Date columns
    #         elif any(term in col_lower for term in ['date', 'cal']):
    #             gb.configure_column(col, width=max(min_width, 130), minWidth=100, maxWidth=160)
            
    #         # Numeric columns
    #         elif any(term in col_lower for term in ['value', 'price', 'cost', 'year']):
    #             gb.configure_column(col, width=max(min_width, 120), minWidth=80, maxWidth=150)
            
    #         # Default for other columns
    #         else:
    #             gb.configure_column(col, width=max(min_width, 160), minWidth=100, maxWidth=300, wrapText=True, autoHeight=True)
        
    #     # Enable selection
    #     gb.configure_selection(selection_mode="multiple", use_checkbox=True)
        
    #     # Enable pagination
    #     gb.configure_pagination(enabled=True, paginationPageSize=20)
        
    #     # Enable filtering and sorting with better column management
    #     gb.configure_side_bar(filters_panel=True, defaultToolPanel='filters')
        
    #     # Configure grid options for better responsiveness
    #     gb.configure_grid_options(
    #         suppressColumnVirtualisation=False,
    #         suppressRowVirtualisation=False,
    #         enableRangeSelection=True,
    #         rowSelection='multiple',
    #         animateRows=True,
    #         suppressMovableColumns=False,
    #         enableCellTextSelection=True
    #     )
        
    #     return gb.build()
    
    # def display_data_grid(self):
    #     """Display the main data grid using AgGrid."""
    #     grid_options = self.configure_aggrid()
        
    #     # Display the grid
    #     st.subheader("📊 Equipment Data Grid")
    #     st.caption("💡 You can edit cells directly, resize columns, use filters, sort columns, and select multiple rows")
        
    #     grid_response = AgGrid(
    #         self.filtered_df,
    #         gridOptions=grid_options,
    #         data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    #         update_mode=GridUpdateMode.MODEL_CHANGED,
    #         allow_unsafe_jscode=True,
    #         fit_columns_on_grid_load=False,
    #         height=600,
    #         theme='streamlit',
    #         enable_enterprise_modules=False,
    #         reload_data=False
    #     )
        
    #     return grid_response
    
    def handle_data_updates(self, grid_response):
        """Handle data updates and save functionality."""
        updated_df = grid_response['data']
        
        # Check if data has been modified
        if not updated_df.equals(self.filtered_df):
            st.success("✅ Data has been modified in the grid!")
            
            # Option to save changes
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("💾 Save Changes to CSV"):
                    try:
                        updated_df.to_csv(self.csv_filename, index=False, encoding='utf-8')
                        st.success("✅ Changes saved successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error saving file: {str(e)}")
    
    def display_selected_items(self, grid_response):
        """Display selected items in an expandable format."""
        selected_rows = grid_response['selected_rows']
        if not selected_rows:
            return
        
        st.subheader(f"📋 Selected Items ({len(selected_rows)})")
        selected_df = pd.DataFrame(selected_rows)
        
        # Display selected items in a more readable format
        for idx, row in selected_df.iterrows():
            # Create a dynamic title using available columns
            title_parts = []
            if self.category_cols:
                title_parts.append(f"{row.get(self.category_cols[0], 'Unknown')}")
            
            model_cols = [col for col in self.available_columns if 'model' in col.lower()]
            if model_cols:
                title_parts.append(f"{row.get(model_cols[0], 'Unknown Model')}")
            
            serial_cols = [col for col in self.available_columns if 'serial' in col.lower()]
            if serial_cols:
                title_parts.append(f"(Serial: {row.get(serial_cols[0], 'N/A')})")
            
            title = "🔧 " + " - ".join(title_parts) if title_parts else f"🔧 Item {idx + 1}"
            
            with st.expander(title):
                col1, col2 = st.columns(2)
                
                # Dynamically display all available fields
                all_cols = list(row.index)
                mid_point = len(all_cols) // 2
                
                with col1:
                    for col in all_cols[:mid_point]:
                        if pd.notna(row[col]) and str(row[col]).strip():
                            st.write(f"**{col}:** {row[col]}")
                
                with col2:
                    for col in all_cols[mid_point:]:
                        if pd.notna(row[col]) and str(row[col]).strip():
                            st.write(f"**{col}:** {row[col]}")
        
        self.display_bulk_operations(selected_df)
    
    def display_bulk_operations(self, selected_df):
        """Display bulk operations for selected items."""
        permissions = self.get_user_permissions()
        
        st.subheader("🔄 Bulk Operations")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if permissions["can_export"]:
                if st.button("📤 Export Selected to CSV"):
                    csv = selected_df.to_csv(index=False)
                    st.download_button(
                        label="Download Selected Items",
                        data=csv,
                        file_name="selected_equipment.csv",
                        mime="text/csv"
                    )
            else:
                st.info("🚫 Export not allowed for your role")
        
        with col2:
            if permissions["can_edit"] and self.location_cols:
                new_location = st.selectbox("Update Location for Selected", 
                                          [''] + [loc for loc in self.df[self.location_cols[0]].dropna().unique() if str(loc).strip()])
                if st.button("📍 Update Location") and new_location:
                    st.warning("Note: This would update the location in a real implementation")
            else:
                if not permissions["can_edit"]:
                    st.info("🚫 Edit not allowed for your role")
                else:
                    st.info("No location column found")
        
        with col3:
            if permissions["can_delete"]:
                if st.button("🗑️ Mark as Retired"):
                    st.warning("Note: This would mark items as retired in a real implementation")
            else:
                st.info("🚫 Delete not allowed for your role")
    
    def display_footer(self):
        """Display the application footer."""
        st.markdown("---")
        
        st.markdown("**📋 ACT Lab Equipment Management System**")
    def _set_dropdown_columns(self, column_config):
        """
        Set dropdown options for category, vendor, location, check/status, and serial columns in column_config.
        """
        # Always use the latest Equipment Select Options for category
        self.Equipment_select_options_csv = self.Equipment_select_options_db_df.copy()
        # Helper to get options from Equipment Select Options DB
        def get_options(col):
            if (
                self.Equipment_select_options_csv is not None
                and col in self.Equipment_select_options_csv.columns
            ):
                # Use only unique, non-empty, sorted values from Equipment Select Options
                return sorted([
                    str(x)
                    for x in self.Equipment_select_options_csv[col].dropna().unique()
                    if str(x).strip()
                ])
            else:
                return []

        # Category
        if self.category_cols:
            col = self.category_cols[0]
            # Always update options from Equipment Select Options
            options = get_options(col)
            column_config[col]["options"] = options
            column_config[col]["editable"] = True
            column_config[col]["type"] = "categorical"
        # Vendor
        if self.vendor_cols:
            col = self.vendor_cols[0]
            options = get_options(col)
            column_config[col]["type"] = "categorical"
            column_config[col]["options"] = options
            column_config[col]["editable"] = True
        # Location
        if self.location_cols:
            col = self.location_cols[0]
            options = get_options(col)
            column_config[col]["type"] = "categorical"
            column_config[col]["options"] = options
            column_config[col]["editable"] = True
        # Check/Status
        if self.check_cols:
            col = self.check_cols[0]
            options = get_options(col)
            column_config[col]["type"] = "categorical"
            column_config[col]["options"] = options
            column_config[col]["editable"] = True
        # Serial (optional, usually unique, but can restrict to existing)
        if self.serial_cols:
            col = self.serial_cols[0]
            options = get_options(col)
            column_config[col]["options"] = options
            column_config[col]["editable"] = True

        for col in [c for c in [self.category_cols, self.vendor_cols, self.location_cols] if c]:
            colname = col[0]
            opts = column_config.get(colname, {}).get("options", None)
            if opts:
                self.display_df[colname] = pd.Categorical(self.display_df[colname], categories=opts)

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
                    if st.button("🗑️ Delete Column", key="delete_col_btn", type="primary"):
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
                        if st.button("✅ Yes, Delete", key="confirm_delete_btn", type="primary"):
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

        # Show download button only for admin
        if st.session_state.get("user_role") == "admin":
            st.markdown("### Admin Downloads")
            col1, col2 = st.columns(2)
            
            with col1:
                csv = self.display_df.to_csv(index=False)
                st.download_button(
                    label="📤 Download All Records",
                    data=csv,
                    file_name="equipment_records.csv",
                    mime="text/csv"
                )
            
            st.markdown("### Web Management")
            
            # Column and Filter Order Management under Admin Downloads
            self.save_column_order_ui()
            self.save_filter_order_ui()
        
    def save_column_order_ui(self):
        """UI for admin to save the current Equipment column order"""
        if st.session_state.user_role == "admin":
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
                    
                    if st.button("💾 Save Equipment Column Order", key="save_equipment_order_btn"):
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

    def save_select_options_column_order_ui(self):
        """UI for admin to save the current Select Options column order"""
        if st.session_state.user_role == "admin":
            with st.expander("💾 Save Select Options Column Order"):
                st.info("💡 Configure your preferred Select Options column order below and save it.")
                
                # Show current saved orders for Select Options only
                select_options_default = list(self.Equipment_select_options_db_df.columns) if hasattr(self, 'Equipment_select_options_db_df') and not self.Equipment_select_options_db_df.empty else []
                select_options_order = self._load_column_order('select_options', select_options_default)
                
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
                            self._save_column_order('select_options', new_order)
                            st.success("✅ Select Options columns order saved successfully!")
                            st.rerun()
                        else:
                            self._save_column_order('select_options', new_order)
                            st.success("✅ Select Options columns order saved successfully!")
                            st.rerun()
                else:
                    st.info("No Select Options data available")
                
                st.markdown("📋 **Instructions:** Edit the column order in the text area above (one column name per line), then click Save.")

    def _save_filter_order(self, filter_order):
        """
        Save filter order preference to a JSON file.
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
            
            preferences['equipment_filters'] = filter_order
            
            with open(filter_order_file, 'w') as f:
                json.dump(preferences, f, indent=2)
            
            return True
        except Exception as e:
            st.error(f"Error saving filter order: {str(e)}")
            return False
    
    def _load_filter_order(self, default_filters):
        """
        Load saved filter order preference.
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
                
                if 'equipment_filters' in preferences:
                    saved_order = preferences['equipment_filters']
                    # Ensure all current filters are included (in case new filters were added)
                    missing_filters = [f for f in default_filters if f not in saved_order]
                    # Add any missing filters at the end
                    return saved_order + missing_filters
            
            # Return default order if no saved preference
            return default_filters
        except Exception as e:
            # Return default order if there's an error loading preferences
            return default_filters

    def _load_excluded_filter_columns(self, default_excluded):
        """
        Load saved excluded filter columns preference.
        Args:
            default_excluded (list): Default excluded columns to use if no saved preference
        Returns:
            list: List of column names to exclude from filters
        """
        try:
            excluded_cols_file = Path("excluded_filter_columns.json")
            
            if excluded_cols_file.exists():
                with open(excluded_cols_file, 'r') as f:
                    preferences = json.load(f)
                
                if 'excluded_columns' in preferences:
                    return preferences['excluded_columns']
            
            # Return default excluded columns if no saved preference
            return default_excluded
        except Exception as e:
            # Return default excluded columns if there's an error loading preferences
            return default_excluded

    def save_filter_order_ui(self):
        """UI for admin to save the current Equipment Filter order"""
        if st.session_state.user_role == "admin":
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
                    
                    if st.button("💾 Save Equipment Filter Order", key="save_equipment_filter_order_btn"):
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

    def Add_New_Column_to_Equipment_records_DB(self):
        # Check if user has admin permissions - only show UI if they do
        permissions = self.get_user_permissions()
        if not permissions.get("can_manage_users", False):
            # Don't show anything for non-admin users
            return
        
        # Button to add a new column to the DB (must be after Equipment_collection and self.df are set)
        with st.expander("➕ Add New Column to Equipment DB"):
            new_col_name = st.text_input("New Column Name", key="new_col_name")
            new_col_default = st.text_input("Default Value (optional)", key="new_col_default")
            if st.button("➕ Add Column to All Records", key="add_col_btn"):
                if new_col_name and new_col_name.strip():
                    # Check if column already exists
                    if new_col_name.strip() in self.df.columns:
                        st.error(f"❌ Column '{new_col_name.strip()}' already exists. Please choose a different name.")
                    else:
                        modified_count = self.add_column_to_db(new_col_name, new_col_default if new_col_default else None)
                        st.success(f"✅ Added column '{new_col_name}' to {modified_count} records.")
                        st.info("🔄 Page will refresh to show the updated column.")
                        st.rerun()
                else:
                    st.warning("⚠️ Please enter a column name.")

    def rename_column_in_equipment_records_db(self):
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
                        if st.button("✏️ Rename Column", key="rename_col_btn", type="primary"):
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

    def add_new_column_to_select_options_db(self):
        # Button to add a new column to the Equipment Select Options DB
        with st.expander("➕ Add New Column to Equipment Select Options DB"):
            new_col_name = st.text_input("New Column Name", key="new_select_col_name")
            new_col_default = st.text_input("Default Value (optional)", key="new_select_col_default")
            if st.button("➕ Add Column to All Records", key="add_select_col_btn"):
                if new_col_name and new_col_name.strip():
                    try:
                        modified_count = self.add_column_to_select_options_db(new_col_name, new_col_default if new_col_default else None)
                        st.success(f"Added column '{new_col_name}' to {modified_count} select option records.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error adding column: {str(e)}")

    def delete_column_from_select_options_db_ui(self):
        # Button to delete a column from the Equipment Select Options DB
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
                    
                    if st.button("🗑️ Delete Column", key="delete_select_col_btn", type="primary"):
                        if col_to_delete:
                            try:
                                modified_count = self.delete_column_from_select_options_db(col_to_delete)
                                st.success(f"✅ Successfully deleted column '{col_to_delete}' from {modified_count} select option records.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error deleting column: {str(e)}")
                else:
                    st.info("No columns available for deletion")
            else:
                st.info("No select options data available")

    def rename_column_in_select_options_db_ui(self):
        # Button to rename a column in the Equipment Select Options DB
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

    def Equipment_select_options_Filters(self):
        # --- Inline filter column (not sidebar) ---
        # Print the current filter state
        st.markdown('**🔍Equipment_select_options Filters:**')
        filter_columns = {}
        filtered_select_options_df = self.Equipment_select_options_db_df.copy()
        filter_widgets = []
        
        # Build filter columns dynamically from all identified filterable column types
        filter_cols = []
        filterable_col_lists = [
            self.category_cols,
            self.vendor_cols,
            self.location_cols,
            # self.check_cols,  # Commented out as per original
            self.serial_cols
        ]
        
        for col_list in filterable_col_lists:
            if col_list:
                for col in col_list:
                    if col in filtered_select_options_df.columns and col not in filter_cols:
                        filter_cols.append(col)

        left_col, right_col = st.columns([1, 4])
        with left_col:
            for col_name in filter_cols:
                options = ['All'] + sorted([str(val) for val in filtered_select_options_df[col_name].dropna().unique() if str(val).strip() != ''])
                selected = st.selectbox(f"{col_name}", options, key=f'select_options_{col_name}')
                filter_columns[col_name] = selected
                if selected != 'All':
                    filtered_select_options_df = filtered_select_options_df[filtered_select_options_df[col_name] == selected]
            search_text = st.text_input('🔍 Search', key='select_options_search')
            if search_text:
                mask = pd.Series([False] * len(filtered_select_options_df))
                for col in self.search_cols:
                    if col in filtered_select_options_df.columns:
                        mask |= filtered_select_options_df[col].astype(str).str.contains(search_text, case=False, na=False)
                filtered_select_options_df = filtered_select_options_df[mask]

        with right_col:
            column_order = list(filtered_select_options_df.columns)
            column_config = {col: {"editable": True} for col in filtered_select_options_df.columns}
            # Make 'index' column non-editable
            if 'index' in column_config:
                column_config['index']['editable'] = False
            self.edited_select_options_df = st.data_editor(
                filtered_select_options_df,
                num_rows="dynamic",
                use_container_width=True,
                key="Equipment_select_options",
                column_order=column_order,
                column_config=column_config
            )
        #########################################
    def Equipment_Filters(self):
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
            
            st.subheader("📊 Equipment Records")
            
            # Add custom Select All / Clear Selection buttons at the top
            col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
            with col1:
                if st.button("☑️ Select All Visible", key="select_all_btn", help="Select all rows currently visible (after all filtering) - selection will be maintained when filtering"):
                    # Store only the currently visible/filtered rows in session state
                    st.session_state['select_all_rows'] = self.display_df.to_dict('records')
                    # Also store the visible data as our working dataset when in select all mode
                    st.session_state['select_all_active'] = True
                    # Force grid reload and increment key to force visual update
                    st.session_state['force_grid_reload'] = True
                    st.session_state['grid_key'] = st.session_state.get('grid_key', 0) + 1
                    st.rerun()
            
            with col2:
                if st.button("⬜ Clear Selection", key="clear_selection_btn", help="Clear all selected rows"):
                    # Clear the selection by removing from session state
                    if 'select_all_rows' in st.session_state:
                        del st.session_state['select_all_rows']
                    if 'select_all_active' in st.session_state:
                        del st.session_state['select_all_active']
                    # Force grid reload and increment key to force visual update
                    st.session_state['force_grid_reload'] = True
                    st.session_state['grid_key'] = st.session_state.get('grid_key', 0) + 1
                    st.rerun()
            
            with col3:
                # Add refresh button for when user finishes AgGrid filtering
                if st.button("🔄 Refresh Selection", key="refresh_selection_btn", help="Update selection to match current AgGrid filters"):
                    if 'select_all_rows' in st.session_state:
                        # Update select all to include only currently visible rows (will be corrected after grid renders)
                        st.session_state['refresh_selection_requested'] = True
                        st.success("🔄 Selection will be updated after grid renders!")
                        st.rerun()
                    # st.info("💡 Click 'Select All Visible' first to enable selection tracking")
            
            # Get dropdown options from Equipment Select Options DB
            def get_dropdown_options(col):
                if (hasattr(self, 'Equipment_select_options_db_df') and 
                    self.Equipment_select_options_db_df is not None and
                    col in self.Equipment_select_options_db_df.columns):
                    return sorted([
                        str(x) for x in self.Equipment_select_options_db_df[col].dropna().unique()
                        if str(x).strip()
                    ])
                else:
                    # Fallback to unique values from current data
                    return sorted([
                        str(x) for x in self.display_df[col].dropna().unique()
                        if str(x).strip()
                    ])
            
            # Get user permissions
            permissions = self.get_user_permissions()
            # Print permissions for debugging
            # st.write("User Permissions:", permissions)

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
                    suppressRowClickSelection=False
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
            
            # Display the AgGrid
            grid_response = AgGrid(
                grid_data,
                gridOptions=gb.build(),
                data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                update_mode=GridUpdateMode.MODEL_CHANGED,
                allow_unsafe_jscode=True,
                fit_columns_on_grid_load=False,
                height=600,
                theme='streamlit',
                enable_enterprise_modules=False,
                reload_data=force_reload,
                key=f"equipment_grid_{st.session_state.get('grid_key', 0)}"
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
            
            # Save Changes button (only for users with edit permissions)
            if permissions.get("can_edit", False):
                if st.button("💾 Save Changes to Database", key="save_changes_btn"):
                    self.Save_Equipment_Records_Changes_to_Database()
            
            # Add row management below the grid (only for users with edit permissions)
            if permissions["can_edit"]:
                col1, col2, col3 = st.columns([1, 1, 2])
                
                with col1:
                    if st.button("➕ Add New Row", key="add_row_btn"):
                        # Create a new empty row with default values
                        new_row = {}
                        for col in self.display_df.columns:
                            col_lower = col.lower()
                            
                            # Check if this is any kind of ID column
                            if any(term in col_lower for term in ['id', '_id']):
                                # Handle different ID types dynamically
                                if (col_lower == 'id' or col_lower.endswith('_id') or col_lower.startswith('id_')) and 'uuid' not in col_lower and 'serial' not in col_lower:
                                    # Auto-increment for id type columns (but not uuid or serial)
                                    max_id = self.display_df[col].max() if not self.display_df[col].empty else 0
                                    new_row[col] = max_id + 1 if pd.notna(max_id) else 1
                                elif any(pattern in col_lower for pattern in ['uuid', 'unique_id', 'unique id']):
                                    # Generate new UUID for uuid type columns
                                    import uuid
                                    new_row[col] = str(uuid.uuid4())
                                elif any(pattern in col_lower for pattern in ['serial', 'ser_num', 'serial_number']):
                                    # For serial numbers, leave empty (user will fill)
                                    new_row[col] = None
                                else:
                                    # Other ID columns get empty string or None
                                    new_row[col] = None
                            else:
                                # All non-ID columns default to None (will display as empty)
                                new_row[col] = None
                        
                        # Add the new row at the BEGINNING of display_df for immediate visibility on current page
                        new_row_df = pd.DataFrame([new_row])
                        self.display_df = pd.concat([new_row_df, self.display_df], ignore_index=True)
                        # Apply admin-saved column order
                        self.display_df = self._apply_column_order(self.display_df, 'equipment')
                        
                        # Also add to main dataframes for persistence (at the end for consistency)
                        self.df = pd.concat([self.df, new_row_df], ignore_index=True)
                        self.db_df = pd.concat([self.db_df, new_row_df], ignore_index=True)
                        # Apply admin-saved column order
                        self.df = self._apply_column_order(self.df, 'equipment')
                        self.db_df = self._apply_column_order(self.db_df, 'equipment')
                        
                        # Store in session state to persist through filters (insert at beginning)
                        if 'newly_added_rows' not in st.session_state:
                            st.session_state.newly_added_rows = []
                        st.session_state.newly_added_rows.insert(0, new_row)  # Insert at beginning
                        
                        # Check if any serial columns exist to show relevant message
                        serial_columns = [col for col in self.display_df.columns if any(term in col.lower() for term in ['serial', 'ser_num', 'serial_number'])]
                        
                        if serial_columns:
                            st.success("✅ New row added! It appears at the top of the current page.")
                            st.info(f"ℹ️ **Note**: Please ensure any serial numbers ({', '.join(serial_columns)}) are unique before saving to the database.")
                        else:
                            st.success("✅ New row added! It appears at the top of the current page.")
                        st.rerun()
                
                with col2:
                    if st.button("🗑️ Remove Selected", type="primary", key="delete_selected_btn"):
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

                
                # Add column management functions here
                self.Add_New_Column_to_Equipment_records_DB()
                self.rename_column_in_equipment_records_db()
                if st.session_state.user_role == "admin": 
                    self.delete_column_from_equeipment_records_db()
        #########################################

    def _validate_serials_in_realtime(self):
        """
        Validate serial numbers in real-time and provide immediate feedback.
        Returns a tuple: (is_valid, error_messages, duplicate_serials)
        """
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
            serials = self.edited_df[serial_col].dropna()  # Remove NaN/None values
            serials = serials[serials != '']  # Remove empty strings
            
            if len(serials) != len(serials.unique()):
                # Find duplicate values
                duplicates = serials[serials.duplicated()].unique()
                for dup in duplicates:
                    duplicate_serials.append(f"{serial_col}: {dup}")
                error_messages.append(f"❌ **{serial_col}**: Duplicate values found: {', '.join([str(d) for d in duplicates])}")
        
        is_valid = len(error_messages) == 0
        return is_valid, error_messages, duplicate_serials

    def _validate_unique_serials(self, df_to_check):
        """
        Validate that serial numbers are unique in the DataFrame.
        Args:
            df_to_check (pandas.DataFrame): DataFrame to validate
        Returns:
            tuple: (is_valid, duplicate_serials, error_message)
        """
        if not self.serial_cols:
            # No serial columns identified, skip validation
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
        """
        Validate that serial numbers don't already exist in the database.
        Args:
            df_to_check (pandas.DataFrame): DataFrame to validate
            exclude_current (bool): Whether to exclude current records when checking
        Returns:
            tuple: (is_valid, existing_serials, error_message)
        """
        if not self.serial_cols:
            return True, [], None
        
        serial_col = self.serial_cols[0]
        
        if serial_col not in df_to_check.columns:
            return True, [], None
        
        # Get non-empty serial numbers from the DataFrame to check
        serials_to_check = df_to_check[serial_col].dropna()
        serials_to_check = serials_to_check[serials_to_check.astype(str).str.strip() != '']
        
        if serials_to_check.empty:
            return True, [], None
        
        # Get current serials from database
        try:
            existing_records = list(self.Equipment_collection.find({serial_col: {"$exists": True, "$ne": None}}, {serial_col: 1}))
            existing_serials = [str(record[serial_col]).strip() for record in existing_records 
                             if record.get(serial_col) and str(record.get(serial_col)).strip()]
            
            if exclude_current and hasattr(self, 'display_df') and not self.display_df.empty:
                # Exclude serials that are already in our current display DataFrame
                current_serials = self.display_df[serial_col].dropna()
                current_serials = [str(s).strip() for s in current_serials if str(s).strip()]
                existing_serials = [s for s in existing_serials if s not in current_serials]
            
            # Check for conflicts
            conflicts = []
            for serial in serials_to_check:
                serial_str = str(serial).strip()
                if serial_str in existing_serials:
                    conflicts.append(serial_str)
            
            if conflicts:
                error_msg = f"❌ Serial numbers already exist in database: {', '.join(conflicts)}"
                return False, conflicts, error_msg
            
        except Exception as e:
            st.warning(f"Could not validate against database: {str(e)}")
            return True, [], None
        
        return True, [], None

    def Save_Equipment_Records_Changes_to_Database(self):
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
        
        st.success(f"Saved {len(changed_df)} changed records to the database.")






    def run(self):
        """Main method to run the application."""

        try:
            client = MongoClient("mongodb://ascy00075.sc.altera.com:27017/mongo?readPreference=primary&ssl=false")
            client.admin.command("ping")
        except ConnectionFailure as e:
            st.error(f"MongoDB connection failed: {e}")
            st.stop()


        db = client["Equipment_DB"]
        self.Equipment_collection = db["Equipment"]
        self.Equipment_select_options = db["Equipment_select_options"]

        # Initialize self.display_df from CSV before using it in init_db_Equipment_select_options
    
        # self.init_db_Equipment_select_options()  # COMMENTED OUT: Prevent re-import after deletion

        #############################################################
        # Always work with the data in the db (initialize self.df before any DB-dependent UI)
        # db_records = list(self.Equipment_collection.find({}, {'_id': 0}))
        # self.db_df = pd.DataFrame(db_records)
        # # Sort by 'act_id' if present
        # if 'act_id' in self.db_df.columns:
        #     self.db_df = self.db_df.sort_values(by='act_id', ascending=True, na_position='last').reset_index(drop=True)
        # self.df = self.db_df  # Ensure self.df is set for downstream code

        # Initialize session state and try to load from cookies
        self._initialize_session()


        # CRITICAL DEBUG: Track what happens in the authentication check
        auth_check_result = (st.session_state.get('authenticated', False) and 
                           bool(st.session_state.get('username')) and 
                           bool(st.session_state.get('session_id')))
        

        # Check if user is authenticated
        if auth_check_result:
            # User is authenticated, show main app
            self.configure_page()
            self.display_header()


            #############################################################
            self.Equipment_select_options_db_records = list(self.Equipment_select_options.find({}, {'_id': 0}))
            # Insert index as the first column for identification and deletion
            self.Equipment_select_options_db_df = pd.DataFrame(self.Equipment_select_options_db_records)

            # Tabs for Equipment and Equipment_select_options
            if st.session_state.user_role == "admin":
                tab1, tab2, tab3 = st.tabs(["Equipment Records", "Equipment Select Options", "🗂️ Backup & Restore"])
            else:
                tab1, tab2 = st.tabs(["Equipment Records", "Equipment Select Options"])
                #nth-child(2) => Equipment Select Options
                st.markdown("""
                    <style>
                    button[data-baseweb="tab"]:nth-child(2) {display: none;}
                    </style>
                """, unsafe_allow_html=True)
                
            
            with tab1:
                ##Equipment Records

                # Always work with the data in the db
                db_records = list(self.Equipment_collection.find({}, {'_id': 0}))
                self.db_df = pd.DataFrame(db_records)
                
                # Ensure self.df is always a DataFrame (even if empty)
                self.df = self.db_df.copy() if not self.db_df.empty else pd.DataFrame()
                
                # Sort by the best available ID column if present (only if not empty)
                if not self.df.empty:
                    self._identify_column_types()  # Identify columns first
                    
                    # Apply admin-saved column order
                    self.db_df = self._apply_column_order(self.db_df, 'equipment')
                    self.df = self._apply_column_order(self.df, 'equipment')
                    
                    if hasattr(self, 'unique_id_cols') and self.unique_id_cols:
                        # Use the first available unique identifier for sorting
                        for id_col in self.unique_id_cols:
                            if id_col in self.db_df.columns:
                                try:
                                    # Enhanced sorting logic to handle different ID types better
                                    if pd.api.types.is_numeric_dtype(self.db_df[id_col]):
                                        # Pure numeric column - sort numerically
                                        self.db_df = self.db_df.sort_values(by=id_col, ascending=True, na_position='last').reset_index(drop=True)
                                    else:
                                        # Mixed or string column - try to convert to numeric for sorting
                                        # This handles cases like "1", "2", "10" correctly (not alphabetically)
                                        self.db_df = self.db_df.sort_values(
                                            by=id_col, 
                                            ascending=True, 
                                            na_position='last', 
                                            key=lambda x: pd.to_numeric(x, errors='coerce').fillna(float('inf'))
                                        ).reset_index(drop=True)
                                    
                                    self.df = self.db_df.copy()  # Update self.df after sorting
                                    # Ensure column order is maintained after sorting
                                    self.db_df = self._apply_column_order(self.db_df, 'equipment')
                                    self.df = self._apply_column_order(self.df, 'equipment')
                                    break
                                except Exception as e:
                                    # If sorting fails, continue to next column
                                    continue
                    else:
                        # Fallback: if no unique_id_cols identified, look for any column with 'id' in name
                        id_columns = [col for col in self.df.columns if 'id' in col.lower() and col.lower() != '_id']
                        if id_columns:
                            id_col = id_columns[0]  # Use the first ID column found
                            try:
                                if pd.api.types.is_numeric_dtype(self.db_df[id_col]):
                                    self.db_df = self.db_df.sort_values(by=id_col, ascending=True, na_position='last').reset_index(drop=True)
                                else:
                                    self.db_df = self.db_df.sort_values(
                                        by=id_col, 
                                        ascending=True, 
                                        na_position='last', 
                                        key=lambda x: pd.to_numeric(x, errors='coerce').fillna(float('inf'))
                                    ).reset_index(drop=True)
                                
                                self.df = self.db_df.copy()
                                # Ensure column order is maintained after sorting
                                self.db_df = self._apply_column_order(self.db_df, 'equipment')
                                self.df = self._apply_column_order(self.df, 'equipment')
                            except Exception as e:
                                # If sorting fails, leave data unsorted
                                pass
                else:
                    # If DataFrame is empty, still initialize column types with empty lists
                    self._identify_column_types()

                # Ensure self.edited_df is always defined, just before calling Equipment_Filters
                # self.edited_df = None
                # Use the new Equipment_Filters function instead of sidebar filters
                self.Equipment_Filters()#self.edited_df in Equipment_Filters function

            ############################################################### tab2
            #only admin can see 
            if st.session_state.user_role == "admin":      
                
                with tab2:
                    st.session_state.current_tab = "Equipment Select Options"
                    ##Equipment_select_options
                    ########################################################################
                    ###

                    # Use MongoDB's _id as a persistent unique index
                    if '_id' in self.Equipment_select_options_db_df.columns:
                        self.Equipment_select_options_db_df.rename(columns={'_id': 'id'}, inplace=True)
                    # Ensure 'index' column is present for deletion logic
                    if 'index' not in self.Equipment_select_options_db_df.columns:
                        self.Equipment_select_options_db_df['index'] = self.Equipment_select_options_db_df.index
                    
                    # Apply admin-saved column order (this will handle positioning of all columns including id and index)
                    self.Equipment_select_options_db_df = self._apply_column_order(self.Equipment_select_options_db_df, 'select_options')

                    self.Equipment_select_options_Filters() 

                    # Column management for Equipment Select Options
                    self.save_select_options_column_order_ui()
                    self.add_new_column_to_select_options_db()
                    self.rename_column_in_select_options_db_ui()
                    self.delete_column_from_select_options_db_ui()

                    # st.dataframe(
                    #     self.Equipment_select_options_db_df,
                    #     use_container_width=True
                    # )
                    # Only show Save button for users with edit permissions
                    permissions = self.get_user_permissions()
                    if permissions.get("can_edit", False):
                        if st.button("💾 Save Changes to Database", key="save_changes_btn_select_options"):

                            # Prevent accidental deletion if DataFrame is empty
                            if self.edited_select_options_df is None or self.edited_select_options_df.empty:
                                st.error("Cannot save: No data to save. The table is empty.")
                                return

                            # Assign persistent index to new rows if missing
                            import uuid
                        self.edited_select_options_df = self.edited_select_options_df.copy()
                        if 'index' not in self.edited_select_options_df.columns:
                            self.edited_select_options_df['index'] = None
                        # Build set of used indices from DB (not from edited DataFrame)
                        used_indices = set(self.Equipment_select_options_db_df['index']) if 'index' in self.Equipment_select_options_db_df.columns else set()
                        # Assign UUID only to rows with missing index or index not present in DB
                        for i, row in self.edited_select_options_df.iterrows():
                            idx_val = row['index']
                            # If missing or is an integer (not a persistent UUID)
                            if pd.isna(idx_val) or (isinstance(idx_val, (int, float)) and not pd.isna(idx_val)):
                                new_index = str(uuid.uuid4())
                                self.edited_select_options_df.at[i, 'index'] = new_index
                                used_indices.add(new_index)

                        # Only update or upsert the visible/edited records in Equipment_select_options
                        select_options_columns = list(self.edited_select_options_df.columns) if self.edited_select_options_df is not None else []
                        select_unique_key = 'index' if 'index' in select_options_columns else (select_options_columns[0] if select_options_columns else None)

                        # Defensive: Ensure unique key exists in DataFrame columns and is not None
                        if not select_unique_key or select_unique_key not in self.edited_select_options_df.columns:
                            st.error("Unique key column not found in the data.")
                            return

                        try:
                            # Ensure all index values are strings and unique
                            self.edited_select_options_df['index'] = self.edited_select_options_df['index'].astype(str)
                            for idx, row in self.edited_select_options_df.iterrows():
                                key_value = str(row.get(select_unique_key)).strip() if pd.notna(row.get(select_unique_key)) else str(idx)
                                # Use only 'index' as the unique filter to prevent duplication
                                filter_query = {"index": key_value}
                                update_query = {"$set": row.to_dict()}
                                self.Equipment_select_options.update_one(filter_query, update_query, upsert=True)
                            # # Save the updated Equipment_select_options to CSV for dropdowns (once, after all updates)
                            # try:
                            #     edited_select_options_df.to_csv("Equipment_select_options.csv", index=False, encoding='utf-8')
                            #     st.success("Equipment_select_options.csv has been updated and downloaded.")
                            # except Exception as e:
                            #     st.warning(f"Could not save Equipment_select_options to CSV: {e}")
                        except Exception as e:
                            st.error(f"Error updating database: {e}")
                            return

                        # Allow deletion even for filtered views
                        if select_unique_key and select_unique_key in self.Equipment_select_options_db_df.columns:
                            try:
                                edited_indices = set(self.edited_select_options_df['index'])
                                db_indices = set(self.Equipment_select_options_db_df['index'])
                                indices_to_delete = db_indices - edited_indices
                                if indices_to_delete:
                                    deleted_count = 0
                                    for idx in indices_to_delete:
                                        records = self.Equipment_select_options_db_df[self.Equipment_select_options_db_df['index'] == idx].to_dict(orient='records')
                                        if records:
                                            # Use only 'index' for deletion filter to avoid accidental deletion of duplicates
                                            filter_query = {"index": idx}
                                            self.Equipment_select_options.delete_one(filter_query)
                                            deleted_count += 1
                                    st.success(f"Changes saved to the database. {deleted_count} records deleted.")
                                    self.Equipment_select_options_db_records = list(self.Equipment_select_options.find({}, {'_id': 0}))
                                    self.Equipment_select_options_db_df = pd.DataFrame(self.Equipment_select_options_db_records)
                                    if 'index' not in self.Equipment_select_options_db_df.columns:
                                        self.Equipment_select_options_db_df['index'] = self.Equipment_select_options_db_df.index
                                    # Apply admin-saved column order after data reload
                                    self.Equipment_select_options_db_df = self._apply_column_order(self.Equipment_select_options_db_df, 'select_options')
                                    # Removed st.rerun() to prevent endless loop
                                else:
                                    st.success("Changes saved to the database.")
                                    # Removed st.rerun() to prevent endless loop
                            except Exception as e:
                                st.error(f"Error deleting records: {e}")
                                return
                        else:
                            st.success("Changes saved to the database. No records deleted (no unique key).")
                            # Removed st.rerun() to prevent endless loop
                    # ...existing code...
                    #######################################################

            # Backup and Restore tab (only for admin users)
            if st.session_state.user_role == "admin":
                with tab3:
                    st.session_state.current_tab = "Backup & Restore"
                    
                    # Show backup notifications if any
                    if st.session_state.get("backup_notification"):
                        st.success(st.session_state["backup_notification"])
                        del st.session_state["backup_notification"]
                    
                    if st.session_state.get("backup_error"):
                        st.error(st.session_state["backup_error"])
                        del st.session_state["backup_error"]
                    
                    # Integrate automatic backup check
                    if integrate_auto_backup_into_main_app:
                        integrate_auto_backup_into_main_app(self, backup_interval_hours=1)
                    
                    # Display backup and restore UI
                    if backup_restore_ui:
                        backup_restore_ui(self)
                    else:
                        st.error("❌ Backup system not available. Please ensure backup_csv_for_db_restore.py is accessible.")



            
        else:
            # User not authenticated, show login page
            self.login_page()

# Main execution
if __name__ == "__main__":
    # Configure page settings once at the module level to avoid conflicts
    try:
        st.set_page_config(
            page_title="ACT Lab Equipment",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    except st.errors.StreamlitAPIException:
        # Page config already set, continue
        pass
    
    # Create and run the application
    csv_filename = "ACT-LAB-Equipment-List.csv"
    app = EquipmentManagementApp(csv_filename)
    app.run()
