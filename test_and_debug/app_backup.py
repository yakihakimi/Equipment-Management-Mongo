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
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import sys

# Import authentication functionality
from login_and_signup import AuthenticationManager

# Import general utility functions
from general_functions import is_admin, apply_column_order, load_column_order, save_column_order, save_filter_order

# Import Equipment Select Options functionality
try:
    from Equipment_Select_Options_Page import EquipmentSelectOptionsSystem
except ImportError:
    st.warning("⚠️ Equipment Select Options system not available. Please ensure Equipment_Select_Options_Page.py is accessible.")
    EquipmentSelectOptionsSystem = None



# Note: User Management functionality has been extracted to User_Management_Page.py
# The main app now imports and uses UserManagementSystem from that module when needed

# Note: Equipment Records functionality has been extracted to Equipment_Records_Page.py
# The main app now imports and uses EquipmentRecordsSystem from that module when needed

# Note: Equipment Select Options functionality has been extracted to Equipment_Select_Options_Page.py
# The main app now imports and uses EquipmentSelectOptionsSystem from that module when needed

# Import backup and restore functionality
try:
    from backup_csv_for_db_restore import backup_restore_ui, integrate_auto_backup_into_main_app
except ImportError:
    st.warning("⚠️ Backup system not available. Please ensure backup_csv_for_db_restore.py is in the same directory.")
    backup_restore_ui = None
    integrate_auto_backup_into_main_app = None

class EquipmentManagementApp:
    # Equipment Records add_column_to_db function has been moved to Equipment_Records_Page.py
    
    # Equipment Records delete_column_from_db function has been moved to Equipment_Records_Page.py
    
    # Equipment Records _save_column_order function has been moved to Equipment_Records_Page.py
    
    # Equipment Records _load_column_order function has been moved to Equipment_Records_Page.py
    
    # Equipment Records _apply_column_order function has been moved to Equipment_Records_Page.py
    
    def _apply_column_order(self, df, data_type):
        """Apply saved column order to DataFrame."""
        return apply_column_order(df, data_type)
    
    # Equipment Records rename_column_in_db function has been moved to Equipment_Records_Page.py
    
    # Equipment Select Options functions have been moved to Equipment_Select_Options_Page.py
    

    

    # def init_db_from_csv(self, unique_key=None):
    #     """
    #     Initialize the Equipment collection from CSV, inserting only unique rows based on a unique key.
    #     Args:
    #         unique_key (str or list): Column(s) to use as unique key. If None, use all columns.
    #     """
    #     # Load and clean data
    #     df = self.load_data()
    #     if df.empty:
    #         return
    #     # Remove duplicates in DataFrame
    #     if unique_key:
    #         df = df.drop_duplicates(subset=unique_key)
    #     else:
    #         df = df.drop_duplicates()

    #     records = df.to_dict(orient='records')
    #     # Insert only unique records not already in DB
    #     for record in records:
    #         # Build filter for uniqueness
    #         if unique_key:
    #             if isinstance(unique_key, list):
    #                 filter_query = {k: record.get(k) for k in unique_key}
    #             else:
    #                 filter_query = {unique_key: record.get(unique_key)}
    #         else:
    #             filter_query = record.copy()
    #         if not self.Equipment_collection.find_one(filter_query):
    #             self.Equipment_collection.insert_one(record)
    """
    A class-based Streamlit application for managing equipment data from CSV files.
    """





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

        # Initialize authentication manager
        self.auth_manager = AuthenticationManager(login_title=self.login)
        
        # Initialize Equipment Select Options system
        if EquipmentSelectOptionsSystem:
            self.select_options_system = EquipmentSelectOptionsSystem()
        else:
            self.select_options_system = None
    
    def _verify_password(self, username, password):
        """Verify username and password."""
        return self.auth_manager._verify_password(username, password)
    
    def _is_admin(self):
        """Check if current user is admin (case-insensitive)."""
        return is_admin(self.auth_manager if hasattr(self, 'auth_manager') else None)
    
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
            # Use session state instead of rerun to prevent fading
            st.session_state['redirect_to_main'] = True
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
            /* Ultra-Fast Anti-Fading CSS for Complex Streamlit Applications */
            
            /* CRITICAL: Prevent ALL transitions and animations immediately */
            * {
                transition: none !important;
                animation: none !important;
                animation-duration: 0s !important;
                animation-delay: 0s !important;
                transition-duration: 0s !important;
                transition-delay: 0s !important;
                opacity: 1 !important;
            }
            
            /* Force consistent background during ALL states */
            .stApp {
                background-color: #ffffff !important;
                background-image: none !important;
                opacity: 1 !important;
                transition: none !important;
                animation: none !important;
            }
            
            .main .block-container {
                background-color: #ffffff !important;
                background-image: none !important;
                transition: none !important;
                opacity: 1 !important;
                animation: none !important;
                padding-top: 2rem;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            
            /* Target ALL Streamlit elements that might fade */
            .stApp > div,
            .main > div,
            .block-container > div,
            [data-testid="stAppViewContainer"] > div,
            [data-testid="stDecoration"] > div {
                background-color: #ffffff !important;
                opacity: 1 !important;
                transition: none !important;
                animation: none !important;
            }
            
            /* Target Streamlit's loading and decoration elements */
            .stApp > div[data-testid="stDecoration"] {
                background-color: #ffffff !important;
                background-image: none !important;
                opacity: 1 !important;
                transition: none !important;
                animation: none !important;
            }
            
            /* Prevent opacity changes during loading */
            .stApp > div,
            .main > div,
            .block-container > div {
                opacity: 1 !important;
                background-color: #ffffff !important;
                transition: none !important;
                animation: none !important;
            }
            
            /* Override any Streamlit loading states */
            [data-testid="stAppViewContainer"] {
                background-color: #ffffff !important;
                opacity: 1 !important;
                transition: none !important;
                animation: none !important;
            }
            
            /* Prevent any fade effects from Streamlit's internal CSS */
            .stApp > div[data-testid="stDecoration"]::before,
            .stApp > div[data-testid="stDecoration"]::after,
            .stApp > div::before,
            .stApp > div::after {
                display: none !important;
                opacity: 0 !important;
            }
            
            /* Force ALL elements to maintain their appearance */
            .stApp * {
                transition: none !important;
                animation: none !important;
                opacity: 1 !important;
            }
            
            /* CRITICAL: Prevent fading during rerun operations */
            .stApp > div[data-testid="stDecoration"] {
                background-color: #ffffff !important;
                opacity: 1 !important;
                transition: none !important;
                animation: none !important;
            }
            
            /* Prevent any loading states during rerun */
            .stApp > div[data-testid="stDecoration"]::before,
            .stApp > div[data-testid="stDecoration"]::after {
                display: none !important;
                opacity: 0 !important;
            }
            
            /* Force all elements to stay visible during rerun */
            .stApp > div,
            .main > div,
            .block-container > div,
            [data-testid="stAppViewContainer"] > div {
                opacity: 1 !important;
                background-color: #ffffff !important;
                transition: none !important;
                animation: none !important;
            }
            
            /* Prevent any Streamlit internal loading animations */
            .stApp * {
                animation-duration: 0s !important;
                animation-delay: 0s !important;
                transition-duration: 0s !important;
                transition-delay: 0s !important;
                opacity: 1 !important;
            }
            
            /* Hide Streamlit's default elements */
            #MainMenu {visibility: hidden;}
            .stDeployButton {display: none !important;}
            footer {visibility: hidden;}
            .stApp > header {visibility: hidden;}
            
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
            
            /* Additional fixes for Streamlit's internal elements that cause fading */
            .stApp > div[data-testid="stDecoration"] {
                background-color: #ffffff !important;
                background-image: none !important;
            }
            
            /* Prevent any loading overlays */
            .stApp > div[data-testid="stDecoration"]::before,
            .stApp > div[data-testid="stDecoration"]::after {
                display: none !important;
            }
            
            /* Force all Streamlit elements to maintain appearance */
            .stApp * {
                transition: none !important;
                animation: none !important;
            }
            
            /* Specific fixes for AgGrid and dataframe interactions */
            .ag-root-wrapper,
            .ag-root,
            .ag-body-viewport,
            .ag-body-viewport-wrapper,
            .ag-theme-streamlit {
                background-color: #ffffff !important;
                transition: none !important;
                opacity: 1 !important;
            }
            
            /* Prevent any loading overlays or fade effects */
            .stApp > div[data-testid="stDecoration"]::before,
            .stApp > div[data-testid="stDecoration"]::after,
            .stApp > div::before,
            .stApp > div::after {
                display: none !important;
                opacity: 0 !important;
            }
            
            /* Force all interactive elements to maintain appearance */
            .stButton > button,
            .stSelectbox > div,
            .stTextInput > div,
            .stTextArea > div,
            .stDataFrame > div,
            .stForm > div {
                transition: none !important;
                animation: none !important;
                opacity: 1 !important;
                background-color: #ffffff !important;
            }
            
            /* Prevent any hover effects that might cause fading */
            .stButton > button:hover,
            .stSelectbox > div:hover,
            .stTextInput > div:hover,
            .stTextArea > div:hover,
            .stDataFrame > div:hover,
            .stForm > div:hover {
                background-color: #ffffff !important;
                transition: none !important;
                opacity: 1 !important;
                animation: none !important;
            }
            
            /* CRITICAL: Additional ultra-fast fixes for complex apps */
            /* Force all elements to maintain opacity */
            .stApp *,
            .main *,
            .block-container *,
            [data-testid="stAppViewContainer"] * {
                opacity: 1 !important;
                transition: none !important;
                animation: none !important;
            }
            
            /* Prevent any CSS animations or transitions */
            @keyframes none {
                from { opacity: 1; }
                to { opacity: 1; }
            }
            
            /* Override any existing animations */
            * {
                animation-duration: 0s !important;
                animation-delay: 0s !important;
                transition-duration: 0s !important;
                transition-delay: 0s !important;
                opacity: 1 !important;
            }
            </style>
            
            <script>
            // Ultra-Aggressive Anti-Fading JavaScript for Maximum Speed
            
            // Ultra-fast function with minimal overhead
            function ultraFastFix() {
                // Immediate execution without requestAnimationFrame for speed
                document.body.style.backgroundColor = '#ffffff';
                document.body.style.transition = 'none';
                document.body.style.opacity = '1';
                document.body.style.animation = 'none';
                
                // Force critical elements immediately
                const appContainer = document.querySelector('.stApp');
                if (appContainer) {
                    appContainer.style.backgroundColor = '#ffffff';
                    appContainer.style.transition = 'none';
                    appContainer.style.opacity = '1';
                    appContainer.style.animation = 'none';
                }
                
                // Force all divs immediately (aggressive approach)
                const allDivs = document.querySelectorAll('div');
                for (let i = 0; i < allDivs.length; i++) {
                    const div = allDivs[i];
                    div.style.transition = 'none';
                    div.style.animation = 'none';
                    div.style.opacity = '1';
                    div.style.backgroundColor = '#ffffff';
                }
                
                // Force all Streamlit elements
                const stElements = document.querySelectorAll('.stButton, .stSelectbox, .stTextInput, .stDataFrame, .stForm, [data-testid="stDecoration"]');
                for (let i = 0; i < stElements.length; i++) {
                    const element = stElements[i];
                    element.style.transition = 'none';
                    element.style.animation = 'none';
                    element.style.opacity = '1';
                    element.style.backgroundColor = '#ffffff';
                }
            }
            
            // Ultra-fast monitoring with minimal overhead
            function ultraFastMonitoring() {
                // Simple observer without complex logic
                const observer = new MutationObserver(function() {
                    ultraFastFix();
                });
                
                // Observe everything
                observer.observe(document.body, {
                    attributes: true,
                    subtree: true,
                    childList: true
                });
            }
            
            // Ultra-fast event handlers
            function setupUltraFastHandlers() {
                // Handle all events with immediate response
                document.addEventListener('click', ultraFastFix);
                document.addEventListener('mousedown', ultraFastFix);
                document.addEventListener('mouseup', ultraFastFix);
                document.addEventListener('visibilitychange', ultraFastFix);
                window.addEventListener('focus', ultraFastFix);
                window.addEventListener('load', ultraFastFix);
            }
            
            // Ultra-fast initialization
            function ultraFastInit() {
                // Run immediately
                ultraFastFix();
                
                // Set up monitoring
                ultraFastMonitoring();
                
                // Set up event handlers
                setupUltraFastHandlers();
                
                // Run very frequently for maximum responsiveness
                setInterval(ultraFastFix, 100);
                
                // Additional immediate checks
                setTimeout(ultraFastFix, 10);
                setTimeout(ultraFastFix, 50);
                setTimeout(ultraFastFix, 100);
            }
            
            // Initialize immediately
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', ultraFastInit);
            } else {
                ultraFastInit();
            }
            
            // Run immediately
            ultraFastFix();
            
            // Safety: run every 50ms for the first 5 seconds
            let safetyCounter = 0;
            const safetyInterval = setInterval(function() {
                ultraFastFix();
                safetyCounter++;
                if (safetyCounter >= 100) { // 5 seconds
                    clearInterval(safetyInterval);
                }
            }, 50);
            
            // Additional safety: run every 100ms indefinitely
            setInterval(ultraFastFix, 100);
            </script>
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
                        users = self.auth_manager.users
                        if self.save_session(username, users[username]["role"]):
                            st.success(f"Welcome, {users[username]['name']}!")
                            time.sleep(1)  # Small delay to show success message
                            # Use session state instead of rerun to prevent fading
                            st.session_state['login_successful'] = True
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
        
        # Use session state instead of rerun to prevent fading
        st.session_state['logout_complete'] = True
    
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
        users = self.auth_manager.users
        if username not in users:
            self.logout()
            return False
        
        return True
    
    def display_header(self):
        """Display header with user info and logout."""
        # User info and logout in a container
        st.markdown('<div class="user-header">', unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1])
        
        with col1:
            users = self.auth_manager.users
            user_info = users[st.session_state.username]
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
                self.auth_manager.logout()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Main title
        st.markdown(f'<h1 class="main-header">{self.main_page_titel}</h1>', unsafe_allow_html=True)


    def configure_page(self):
        """Configure Streamlit page settings and CSS styling."""
        st.markdown("""
            <style>
                /* Comprehensive fix for page fading during refresh */
                
                /* Prevent all transitions and animations */
                * {
                    transition: none !important;
                    animation: none !important;
                }
                
                /* Force consistent background during all states */
                .stApp {
                    background-color: #ffffff !important;
                    background-image: none !important;
                }
                
                .main .block-container {
                    background-color: #ffffff !important;
                    background-image: none !important;
                    transition: none !important;
                }
                
                /* Target Streamlit's loading and decoration elements */
                .stApp > div[data-testid="stDecoration"] {
                    background-color: #ffffff !important;
                    background-image: none !important;
                }
                
                /* Prevent opacity changes during loading */
                .stApp > div,
                .main > div,
                .block-container > div {
                    opacity: 1 !important;
                    background-color: #ffffff !important;
                }
                
                /* Override any Streamlit loading states */
                [data-testid="stAppViewContainer"] {
                    background-color: #ffffff !important;
                    opacity: 1 !important;
                }
                
                /* Ensure consistent styling during page transitions */
                .stApp > div[data-testid="stDecoration"] {
                    background-color: #ffffff !important;
                }
                
                /* Prevent any fade effects from Streamlit's internal CSS */
                .stApp > div[data-testid="stDecoration"]::before,
                .stApp > div[data-testid="stDecoration"]::after {
                    display: none !important;
                }
                
                /* Force all elements to maintain their appearance */
                .stApp * {
                    transition: none !important;
                    animation: none !important;
                }
                
                /* Specific fixes for AgGrid and dataframe interactions */
                .ag-root-wrapper,
                .ag-root,
                .ag-body-viewport,
                .ag-body-viewport-wrapper,
                .ag-theme-streamlit {
                    background-color: #ffffff !important;
                    transition: none !important;
                    opacity: 1 !important;
                }
                
                /* Prevent any loading overlays or fade effects */
                .stApp > div[data-testid="stDecoration"]::before,
                .stApp > div[data-testid="stDecoration"]::after,
                .stApp > div::before,
                .stApp > div::after {
                    display: none !important;
                }
                
                /* Force all interactive elements to maintain appearance */
                .stButton > button,
                .stSelectbox > div,
                .stTextInput > div,
                .stTextArea > div {
                    transition: none !important;
                    animation: none !important;
                }
                
                /* Prevent any hover effects that might cause fading */
                .stButton > button:hover,
                .stSelectbox > div:hover,
                .stTextInput > div:hover {
                    background-color: inherit !important;
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
                
                /* Prevent AgGrid from causing page fading */
                .ag-theme-streamlit {
                    background-color: #ffffff !important;
                    transition: none !important;
                }
                
                /* Fix for page navigation fading */
                .stSelectbox,
                .stSelectbox > div,
                .stSelectbox > div > div {
                    background-color: #ffffff !important;
                    transition: none !important;
                }
                
                /* Prevent any loading overlays */
                .stApp > div[data-testid="stDecoration"]::before,
                .stApp > div[data-testid="stDecoration"]::after {
                    display: none !important;
                }
                
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
            
            <script>
            // Ultra-Aggressive Anti-Fading JavaScript for Maximum Speed
            
            // Ultra-fast function with minimal overhead
            function ultraFastFix() {
                // Immediate execution without requestAnimationFrame for speed
                document.body.style.backgroundColor = '#ffffff';
                document.body.style.transition = 'none';
                document.body.style.opacity = '1';
                document.body.style.animation = 'none';
                
                // Force critical elements immediately
                const appContainer = document.querySelector('.stApp');
                if (appContainer) {
                    appContainer.style.backgroundColor = '#ffffff';
                    appContainer.style.transition = 'none';
                    appContainer.style.opacity = '1';
                    appContainer.style.animation = 'none';
                }
                
                // Force all divs immediately (aggressive approach)
                const allDivs = document.querySelectorAll('div');
                for (let i = 0; i < allDivs.length; i++) {
                    const div = allDivs[i];
                    div.style.transition = 'none';
                    div.style.animation = 'none';
                    div.style.opacity = '1';
                    div.style.backgroundColor = '#ffffff';
                }
                
                // Force all Streamlit elements
                const stElements = document.querySelectorAll('.stButton, .stSelectbox, .stTextInput, .stDataFrame, .stForm, [data-testid="stDecoration"]');
                for (let i = 0; i < stElements.length; i++) {
                    const element = stElements[i];
                    element.style.transition = 'none';
                    element.style.animation = 'none';
                    element.style.opacity = '1';
                    element.style.backgroundColor = '#ffffff';
                }
            }
            
            // Ultra-fast monitoring with minimal overhead
            function ultraFastMonitoring() {
                // Simple observer without complex logic
                const observer = new MutationObserver(function() {
                    ultraFastFix();
                });
                
                // Observe everything
                observer.observe(document.body, {
                    attributes: true,
                    subtree: true,
                    childList: true
                });
            }
            
            // Ultra-fast event handlers
            function setupUltraFastHandlers() {
                // Handle all events with immediate response
                document.addEventListener('click', ultraFastFix);
                document.addEventListener('mousedown', ultraFastFix);
                document.addEventListener('mouseup', ultraFastFix);
                document.addEventListener('visibilitychange', ultraFastFix);
                window.addEventListener('focus', ultraFastFix);
                window.addEventListener('load', ultraFastFix);
            }
            
            // Ultra-fast initialization
            function ultraFastInit() {
                // Run immediately
                ultraFastFix();
                
                // Set up monitoring
                ultraFastMonitoring();
                
                // Set up event handlers
                setupUltraFastHandlers();
                
                // Run very frequently for maximum responsiveness
                setInterval(ultraFastFix, 100);
                
                // Additional immediate checks
                setTimeout(ultraFastFix, 10);
                setTimeout(ultraFastFix, 50);
                setTimeout(ultraFastFix, 100);
            }
            
            // Initialize immediately
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', ultraFastInit);
            } else {
                ultraFastInit();
            }
            
            // Run immediately
            ultraFastFix();
            
            // Safety: run every 50ms for the first 5 seconds
            let safetyCounter = 0;
            const safetyInterval = setInterval(function() {
                ultraFastFix();
                safetyCounter++;
                if (safetyCounter >= 100) { // 5 seconds
                    clearInterval(safetyInterval);
                }
            }, 50);
            
            // Additional safety: run every 100ms indefinitely
            setInterval(ultraFastFix, 100);
            </script>
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
        
        # Check if column exists in Equipment Select Options (this makes any column with select options a dropdown)
        if (hasattr(self, 'Equipment_select_options_db_df') and 
            self.Equipment_select_options_db_df is not None and
            column_name in self.Equipment_select_options_db_df.columns):
            # Check if there are actually options available for this column
            options = self.Equipment_select_options_db_df[column_name].dropna().unique()
            if len(options) > 0 and any(str(opt).strip() for opt in options):
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
    

    
    # def refresh_equipment_data(self):
    #     """Force refresh of equipment data from database."""
    #     # Equipment Records data refresh is now handled by EquipmentRecordsSystem
    #     st.info("🔄 Equipment Records data refresh is handled by the Equipment Records page.")
    #     st.info("💡 Please refresh the Equipment Records page to reload data.")



    # def _load_and_sync_data_on_startup(self):
    #     """
    #     Load Equipment Records data and auto-sync columns with Equipment Select Options on startup.
    #     This ensures dropdown consistency without showing UI messages during startup.
    #     """
    #     # Load Equipment Records data
    #     db_records = list(self.Equipment_collection.find({}, {'_id': 0}))
    #     self.df = pd.DataFrame(db_records)
    #     
    #     # Auto-sync columns between Equipment Records and Equipment Select Options on startup
    #     # This ensures dropdown consistency without showing UI messages during startup
    #     try:
    #         if (hasattr(self, 'df') and self.df is not None and not self.df.empty and 
    #             hasattr(self, 'Equipment_select_options_db_df') and 
    #             self.Equipment_select_options_db_df is not None and not self.Equipment_select_options_db_df.empty):
    #         # Find common columns (excluding system columns)
    #         equipment_columns = set(self.df.columns)
    #         select_options_columns = set(self.Equipment_select_options_db_df.columns)
    #         common_columns = equipment_columns.intersection(select_options_columns)
    #         system_columns = {'_id', 'uuid', 'index'}
    #         common_columns = common_columns - system_columns
    #         
    #         # Silently sync without UI messages during startup
    #         for col_name in common_columns:
    #             if (col_name in self.Equipment_select_options_db_df.columns):
    #                 valid_options = set(
    #                     str(x) for x in self.Equipment_select_options_db_df[col_name].dropna().unique()
    #                     if str(x).strip()
    #                 )
    #                 if valid_options:
    #                     current_values = self.df[col_name].dropna().unique()
    #                     invalid_values = [
    #                         str(val) for val in current_values 
    #                         if str(val).strip() and str(val) not in valid_options
    #                     ]
    #                     if invalid_values:
    #                         first_valid_option = sorted(list(valid_options))[0]
    #                         mask = self.df[col_name].isin(invalid_values)
    #                         if mask.any():
    #                             self.df.loc[mask, col_name] = first_valid_option
    #                         # Update database silently
    #                         for invalid_value in invalid_values:
    #                             self.Equipment_collection.update_many(
    #                                 {col_name: invalid_value},
    #                                 {"$set": {col_name: first_valid_option}}
    #                             )
    #     except Exception:
    #         # Silent error handling during startup
    #         pass
    
    
    
    # def create_sidebar_filters(self, prefix=""):
    #     """
    #     Create sidebar filters where each filter's options are dependent on previous filter selections.
    #     """
    #     def _key(name):
    #         return f"{prefix}_{name}" if prefix else name

    #     st.sidebar.header(f"🔍 {prefix}_Filters")
    #     filter_columns = {}

    #     # Start with full DataFrame
    #     filtered_df = self.df.copy()

    #     # Category filter
    #     if self.category_cols:
    #         category_col = self.category_cols[0]
    #         categories = ['All'] + sorted([cat for cat in filtered_df[category_col].dropna().unique() if str(cat).strip() != ''])
    #         selected_category = st.sidebar.selectbox(f"Filter by {category_col}", categories, key=_key('category'))
    #         filter_columns['category'] = selected_category
    #         if selected_category != 'All':
    #             filtered_df = filtered_df[filtered_df[category_col] == selected_category]

    #     # Vendor filter
    #     if self.vendor_cols:
    #         vendor_col = self.vendor_cols[0]
    #         vendors = ['All'] + sorted([vendor for vendor in filtered_df[vendor_col].dropna().unique() if str(vendor).strip() != ''])
    #         selected_vendor = st.sidebar.selectbox(f"Filter by {vendor_col}", vendors, key=_key('vendor'))
    #         filter_columns['vendor'] = selected_vendor
    #         if selected_vendor != 'All':
    #             filtered_df = filtered_df[filtered_df[vendor_col] == selected_vendor]

    #     # Location filter
    #     if self.location_cols:
    #         location_col = self.location_cols[0]
    #         locations = ['All'] + sorted([loc for loc in filtered_df[location_col].dropna().unique() if str(loc).strip() != ''])
    #         selected_location = st.sidebar.selectbox(f"Filter by {location_col}", locations, key=_key('location'))
    #         filter_columns['location'] = selected_location
    #         if selected_location != 'All':
    #             filtered_df = filtered_df[filtered_df[location_col] == selected_location]

    #     # Check status filter
    #     if self.check_cols:
    #         check_col = self.check_cols[0]
    #         check_statuses = ['All'] + sorted([str(check) for check in filtered_df[check_col].dropna().unique()])
    #         selected_check = st.sidebar.selectbox(f"Filter by {check_col}", check_statuses, key=_key('check'))
    #         filter_columns['check'] = selected_check
    #         if selected_check != 'All':
    #             filtered_df = filtered_df[filtered_df[check_col].astype(str) == selected_check]

    #     # Serial filter
    #     if self.serial_cols:
    #         serial_col = self.serial_cols[0]
    #         serials = ['All'] + sorted([str(serial) for serial in filtered_df[serial_col].dropna().unique() if str(serial).strip() != ''])
    #         selected_serial = st.sidebar.selectbox(f"Filter by {serial_col}", serials, key=_key('serial'))
    #         filter_columns['serial'] = selected_serial
    #         if selected_serial != 'All':
    #             filtered_df = filtered_df[filtered_df[serial_col] == selected_serial]

    #     # Text search
    #     search_text = st.sidebar.text_input(f"🔍 Search in: {', '.join(self.search_cols[:3])}", key=_key('search'))

    #     return filter_columns, search_text
    
    # def apply_filters(self, filter_columns, search_text):
    #     """
    #     Apply filters to the DataFrame, making each filter dependent on previous selections.
    #     Args:
    #         filter_columns (dict): Dictionary of filter selections
    #         search_text (str): Text to search for
    #     """
    #     self.filtered_df = self.df.copy()

    #     # Apply filters in order, each time narrowing the DataFrame for subsequent filters
    #     if self.category_cols and 'category' in filter_columns and filter_columns['category'] != 'All':
    #         self.filtered_df = self.filtered_df[self.filtered_df[self.category_cols[0]] == filter_columns['category']]

    #     if self.vendor_cols and 'vendor' in filter_columns and filter_columns['vendor'] != 'All':
    #         self.filtered_df = self.filtered_df[self.filtered_df[self.vendor_cols[0]] == filter_columns['vendor']]

    #     if self.location_cols and 'location' in filter_columns and filter_columns['location'] != 'All':
    #         self.filtered_df = self.filtered_df[self.filtered_df[self.location_cols[0]] == filter_columns['location']]

    #     if self.check_cols and 'check' in filter_columns and filter_columns['check'] != 'All':
    #         self.filtered_df = self.filtered_df[self.filtered_df[self.check_cols[0]].astype(str) == filter_columns['check']]

    #     if self.serial_cols and 'serial' in filter_columns and filter_columns['serial'] != 'All':
    #         self.filtered_df = self.filtered_df[self.filtered_df[self.serial_cols[0]] == filter_columns['serial']]

    #     # Apply text search last
    #     if search_text and self.search_cols:
    #         mask = pd.Series([False] * len(self.filtered_df))
    #         for col in self.search_cols:
    #             if col in self.filtered_df.columns:
    #                 mask |= self.filtered_df[col].astype(str).str.contains(search_text, case=False, na=False)
    #         self.filtered_df = self.filtered_df[mask]
    
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
    
    # def handle_data_updates(self, grid_response):
    #     """Handle data updates and save functionality."""
    #     updated_df = grid_response['data']
    #     
    #     # Check if data has been modified
    #     if not updated_df.equals(self.filtered_df):
    #         st.success("✅ Data has been modified in the grid!")
    #         
    #         # Option to save changes
    #         col1, col2 = st.columns([1, 4])
    #         with col1:
    #         if st.button("💾 Save Changes to CSV"):
    #             try:
    #                 updated_df.to_csv(self.csv_filename, index=False, encoding='utf-8')
    #                 st.success("✅ Changes saved successfully!")
    #                 st.rerun()
    #             except Exception as e:
    #                 st.error(f"❌ Error saving file: {str(e)}")
    
    # def display_selected_items(self, grid_response):
    #     """Display selected items in an expandable format."""
    #     selected_rows = grid_response['selected_rows']
    #     if not selected_rows:
    #         return
    #     
    #     st.subheader(f"📋 Selected Items ({len(selected_rows)})")
    #     selected_df = pd.DataFrame(selected_rows)
    #     
    #     # Display selected items in a more readable format
    #     for idx, row in selected_df.iterrows():
    #         # Create a dynamic title using available columns
    #         title_parts = []
    #         if self.category_cols:
    #         title_parts.append(f"{row.get(self.category_cols[0], 'Unknown')}")
    #         
    #         model_cols = [col for col in self.available_columns if 'model' in col.lower()]
    #         if model_cols:
    #         title_parts.append(f"{row.get(model_cols[0], 'Unknown Model')}")
    #         
    #         serial_cols = [col for col in self.available_columns if 'serial' in col.lower()]
    #         if serial_cols:
    #         title_parts.append(f"(Serial: {row.get(serial_cols[0], 'N/A')})")
    #         
    #         title = "🔧 " + " - ".join(title_parts) if title_parts else f"🔧 Item {idx + 1}"
    #         
    #         with st.expander(title):
    #         col1, col2 = st.columns(2)
    #         
    #         # Dynamically display all available fields
    #         all_cols = list(row.index)
    #         mid_point = len(all_cols) // 2
    #         
    #         with col1:
    #         for col in all_cols[:mid_point]:
    #         if pd.notna(row[col]) and str(row[col]).strip():
    #         st.write(f"**{col}:** {row[col]}")
    #         
    #         with col2:
    #         for col in all_cols[mid_point:]:
    #         if pd.notna(row[col]) and str(row[col]).strip():
    #         st.write(f"**{col}:** {row[col]}")
    #     
    #     self.display_bulk_operations(selected_df)
    
    # def display_bulk_operations(self, selected_df):
    #     """Display bulk operations for selected items."""
    #     permissions = self.auth_manager.get_user_permissions()
    #     
    #     st.subheader("🔄 Bulk Operations")
    #     col1, col2, col3 = st.columns(3)
    #     
    #     with col1:
    #     if permissions["can_export"]:
    #         if st.button("📤 Export Selected to CSV"):
    #             csv = selected_df.to_csv(index=False)
    #             st.download_button(
    #                 label="Download Selected Items",
    #                 data=csv,
    #                 file_name="selected_equipment.csv",
    #                 mime="text/csv"
    #             )
    #     else:
    #         st.info("🚫 Export not allowed for your role")
    #     
    #     with col2:
    #     if permissions["can_edit"] and self.location_cols:
    #         new_location = st.selectbox("Update Location for Selected", 
    #                                   [''] + [loc for loc in self.df[self.location_cols[0]].dropna().unique() if str(loc).strip()])
    #         if st.button("📍 Update Location") and new_location:
    #             st.warning("Note: This would update the location in a real implementation")
    #     else:
    #         if not permissions["can_edit"]:
    #             st.info("🚫 Edit not allowed for your role")
    #         else:
    #             st.info("No location column found")
    #     
    #     with col3:
    #     if permissions["can_delete"]:
    #         if st.button("🗑️ Mark as Retired"):
    #             st.warning("Note: This would mark items as retired in a real implementation")
    #     else:
    #         st.info("🚫 Delete not allowed for your role")
    
    # def display_footer(self):
    #     """Display the application footer."""
    #     st.markdown("---")
    #     
    #     st.markdown("**📋 ACT Lab Equipment Management System**")
    # def _set_dropdown_columns(self, column_config):
    #     """
    #     Set dropdown options for category, vendor, location, check/status, and serial columns in column_config.
    #     """
    #     # Always use the latest Equipment Select Options for category
    #     self.Equipment_select_options_csv = self.Equipment_select_options_db_df.copy()
    #     # Helper to get options from Equipment Select Options DB
    #     def get_options(col):
    #         if (
    #             self.Equipment_select_options_csv is not None
    #             and col in self.Equipment_select_options_csv.columns
    #         ):
    #             # Use only unique, non-empty, sorted values from Equipment Select Options
    #             return sorted([
    #                 str(x)
    #                 for x in self.Equipment_select_options_csv[col].dropna().unique()
    #                 if str(x).strip()
    #             ])
    #         else:
    #             return []

    #     # Category
    #     if self.category_cols:
    #         col = self.category_cols[0]
    #         # Always update options from Equipment Select Options
    #         options = get_options(col)
    #         column_config[col]["options"] = options
    #         column_config[col]["editable"] = True
    #         column_config[col]["type"] = "categorical"
    #     # Vendor
    #     if self.vendor_cols:
    #         col = self.vendor_cols[0]
    #         options = get_options(col)
    #         column_config[col]["type"] = "categorical"
    #         column_config[col]["options"] = options
    #         column_config[col]["editable"] = True
    #     # Location
    #     if self.location_cols:
    #         col = self.location_cols[0]
    #         options = get_options(col)
    #         column_config[col]["type"] = "categorical"
    #         column_config[col]["options"] = options
    #         column_config[col]["editable"] = True
    #     # Check/Status
    #     if self.check_cols:
    #         col = self.check_cols[0]
    #         options = get_options(col)
    #         column_config[col]["type"] = "categorical"
    #         column_config[col]["options"] = options
    #         column_config[col]["editable"] = True
    #     # Serial (optional, usually unique, but can restrict to existing)
    #     if self.serial_cols:
    #         col = self.serial_cols[0]
    #         options = get_options(col)
    #         column_config[col]["options"] = options
    #         column_config[col]["editable"] = True

    #     for col in [c for c in [self.category_cols, self.vendor_cols, self.location_cols] if c]:
    #         colname = col[0]
    #         opts = column_config.get(colname, {}).get("options", None)
    #         if opts:
    #             self.display_df[colname] = pd.Categorical(self.display_df[colname], categories=opts)

    # Equipment Records delete column function has been moved to Equipment_Records_Page.py
        
    # Equipment Records save_column_order_ui function has been moved to Equipment_Records_Page.py



    # def _save_filter_order(self, filter_order):
    #     """
    #     Save filter order preference to a JSON file.
    #     Args:
    #         filter_order (list): List of filter column names in desired order
    #     Returns:
    #         bool: Success status
    #     """
    #     return save_filter_order(filter_order)

    
    # Equipment Select Options functions have been moved to Equipment_Select_Options_Page.py



    def run(self):
        """Main method to run the application."""
        
        # Handle session state changes to prevent unnecessary reruns
        if st.session_state.get('redirect_to_main', False):
            del st.session_state['redirect_to_main']
            # Continue to main app without rerun
        
        if st.session_state.get('login_successful', False):
            del st.session_state['login_successful']
            # Continue to main app without rerun
            
        if st.session_state.get('logout_complete', False):
            del st.session_state['logout_complete']
            # Continue to login page without rerun

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

        # Initialize session state and authentication
        self.auth_manager._initialize_session()

        # Check if user is authenticated
        if self.auth_manager.is_authenticated():
            # User is authenticated, show main app
            self.configure_page()
            self.auth_manager.display_header(self.main_page_titel)

            # Equipment Records data is now handled by EquipmentRecordsSystem
            # No need to initialize equipment data here as it's handled in the Equipment Records page
            
            # Load Equipment Select Options data when accessing that tab
            if self.select_options_system:
                self.select_options_system._initialize_select_options_data()

            # Initialize current page in session state if not exists
            if 'current_page' not in st.session_state:
                st.session_state.current_page = "Equipment Records"

            # Page navigation using selectbox - only for admin users
            if self._is_admin():
                page_options = ["Equipment Records", "Equipment Select Options", "🗂️ Backup & Restore", "👥 User Management"]
                
                # Callback function to handle page changes immediately
                def on_page_change():
                    st.session_state.current_page = st.session_state.page_selector
                
                # Use selectbox for page selection with immediate callback
                selected_page = st.selectbox(
                    "📋 Navigate to:",
                    options=page_options,
                    index=page_options.index(st.session_state.current_page) if st.session_state.current_page in page_options else 0,
                    key="page_selector",
                    on_change=on_page_change
                )
                
                st.markdown("---")  # Add a separator line
            else:
                # For non-admin users, use simple tabs for Equipment Records only
                tab1 = st.tabs(["Equipment Records"])[0]
            
            # Display the selected page content for admin users
            if self._is_admin():
                if st.session_state.current_page == "Equipment Records":
                    # Import and use the standalone Equipment Records system
                    try:
                        from Equipment_Records_Page import EquipmentRecordsSystem
                        equipment_records = EquipmentRecordsSystem()
                        equipment_records.equipment_records_page()
                    except ImportError:
                        st.error("❌ Equipment Records system not available. Please ensure Equipment_Records_Page.py is accessible.")
                        st.info("💡 Fallback: Using built-in equipment records functions.")
                        
                        # Check if user needs password change first
                        if self.auth_manager.user_needs_password_change(st.session_state.username):
                            st.warning("⚠️ You must change your password before accessing the system.")
                            self.auth_manager.password_change_page()
                            return

                        # Fallback: Equipment Records functions are no longer available in main app
                        st.error("❌ Equipment Records functionality is not available in fallback mode.")
                        st.info("💡 Please ensure Equipment_Records_Page.py is accessible and properly configured.")
                        return
                    
                elif st.session_state.current_page == "Equipment Select Options":
                    # Only admin can see Equipment Select Options
                    if self._is_admin():
                        if self.select_options_system:
                            # Use the Equipment Select Options system
                            self.select_options_system.equipment_select_options_page()
                        else:
                            st.error("❌ Equipment Select Options system not available. Please ensure Equipment_Select_Options_Page.py is accessible.")
                            st.info("💡 Please ensure Equipment_Select_Options_Page.py is accessible and properly configured.")
                
                elif st.session_state.current_page == "🗂️ Backup & Restore":
                    # Backup and Restore page (only for admin users)
                    if self._is_admin():
                        st.session_state.current_tab = "Backup & Restore"
                        
                        # Show backup notifications if any
                        if st.session_state.get("backup_notification"):
                            st.success(st.session_state["backup_notification"])
                            del st.session_state["backup_notification"]
                        
                        if st.session_state.get("backup_error"):
                            st.error(st.session_state["backup_error"])
                            del st.session_state["backup_error"]
                        
                        # Import and use the backup system
                        try:
                            from backup_csv_for_db_restore import backup_restore_ui, integrate_auto_backup_into_main_app
                        except ImportError:
                            backup_restore_ui = None
                            integrate_auto_backup_into_main_app = None
                        
                        # Integrate automatic backup check
                        if integrate_auto_backup_into_main_app:
                            integrate_auto_backup_into_main_app(self, backup_interval_hours=1)
                        
                        # Display backup and restore UI
                        if backup_restore_ui:
                            backup_restore_ui(self)
                        else:
                            st.error("❌ Backup system not available. Please ensure backup_csv_for_db_restore.py is accessible.")
                        
                elif st.session_state.current_page == "👥 User Management":
                    # User Management page (only for admin users)
                    if self._is_admin():
                        st.session_state.current_tab = "User Management"
                        
                        # Check if user needs password change first
                        if self.auth_manager.user_needs_password_change(st.session_state.username):
                            st.warning("⚠️ Please change your password before accessing other features.")
                            self.auth_manager.password_change_page()
                        else:
                            # Import and use the standalone User Management system
                            try:
                                from User_Management_Page import UserManagementSystem
                                user_mgmt = UserManagementSystem()
                                user_mgmt.user_management_page()
                            except ImportError:
                                st.error("❌ User Management system not available. Please ensure User_Management_Page.py is accessible.")
                                st.info("💡 Fallback: Using built-in user management functions.")
                                self.auth_manager.user_management_page()
            else:
                # For non-admin users, use tabs for Equipment Records and Equipment Select Options
                with tab1:
                    ##Equipment Records
                    
                    # Check if user needs password change first
                    if self.auth_manager.user_needs_password_change(st.session_state.username):
                        st.warning("⚠️ You must change your password before accessing the system.")
                        self.auth_manager.password_change_page()
                        return

                    # Equipment Records functionality is now handled by EquipmentRecordsSystem
                    # For non-admin users, redirect to Equipment Records page
                    st.info("📊 Equipment Records functionality is now available through the Equipment Records page.")
                    st.info("💡 Please contact an administrator to access Equipment Records.")



            
        else:
            # User not authenticated, show login page
            self.auth_manager.login_page()

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
