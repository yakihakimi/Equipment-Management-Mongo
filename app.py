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

# Import backup and restore functionality
try:
    from backup_csv_for_db_restore import backup_restore_ui, integrate_auto_backup_into_main_app, run_automatic_backup_check
except ImportError:
    st.warning("⚠️ Backup system not available. Please ensure backup_csv_for_db_restore.py is in the same directory.")
    backup_restore_ui = None
    integrate_auto_backup_into_main_app = None
    run_automatic_backup_check = None

# Ultra-aggressive anti-fading CSS and JavaScript
ULTRA_AGGRESSIVE_CSS = """
<style>
/* Ultra-Aggressive Anti-Fading CSS for Maximum Speed */

/* CRITICAL: Force ALL elements to stay visible */
* {
    transition: none !important;
    animation: none !important;
    animation-duration: 0s !important;
    animation-delay: 0s !important;
    transition-duration: 0s !important;
    transition-delay: 0s !important;
    opacity: 1 !important;
    background-color: #ffffff !important;
}

/* Force Streamlit app container */
.stApp {
    background-color: #ffffff !important;
    background-image: none !important;
    opacity: 1 !important;
    transition: none !important;
    animation: none !important;
}

/* Force main container */
.main .block-container {
    background-color: #ffffff !important;
    background-image: none !important;
    transition: none !important;
    opacity: 1 !important;
    animation: none !important;
}

/* Force ALL divs */
.stApp > div,
.main > div,
.block-container > div,
[data-testid="stAppViewContainer"] > div,
[data-testid="stDecoration"] > div,
div {
    background-color: #ffffff !important;
    opacity: 1 !important;
    transition: none !important;
    animation: none !important;
}

/* Force ALL Streamlit elements */
.stButton,
.stSelectbox,
.stTextInput,
.stTextArea,
.stDataFrame,
.stForm,
.stCheckbox,
.stRadio,
.stMarkdown,
.stCode,
.stText {
    background-color: #ffffff !important;
    opacity: 1 !important;
    transition: none !important;
    animation: none !important;
}

/* Force ALL Streamlit elements and their children */
.stButton *,
.stSelectbox *,
.stTextInput *,
.stTextArea *,
.stDataFrame *,
.stForm *,
.stCheckbox *,
.stRadio *,
.stMarkdown *,
.stCode *,
.stText * {
    background-color: #ffffff !important;
    opacity: 1 !important;
    transition: none !important;
    animation: none !important;
}

/* Force ALL elements in Streamlit app */
.stApp * {
    background-color: #ffffff !important;
    opacity: 1 !important;
    transition: none !important;
    animation: none !important;
}

/* Prevent any loading states */
[data-testid="stDecoration"]::before,
[data-testid="stDecoration"]::after,
.stApp > div::before,
.stApp > div::after {
    display: none !important;
    opacity: 0 !important;
}

/* Force all text to stay visible */
* {
    color: inherit !important;
    opacity: 1 !important;
}

/* Override any existing animations */
@keyframes none {
    from { opacity: 1; background-color: #ffffff; }
    to { opacity: 1; background-color: #ffffff; }
}

/* Force all elements to maintain appearance */
* {
    animation-duration: 0s !important;
    animation-delay: 0s !important;
    transition-duration: 0s !important;
    transition-delay: 0s !important;
    opacity: 1 !important;
    background-color: #ffffff !important;
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

/* Hide Streamlit's default elements */
#MainMenu {visibility: hidden;}
.stDeployButton {display: none !important;}
button[kind="header"] {display: none !important;}
[data-testid="stToolbar"] {display: none !important;}
.stAppDeployButton {display: none !important;}
footer {visibility: hidden;}
.stApp > header {visibility: hidden;}

/* Container styling */
.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
}

/* Selectbox styling */
.stSelectbox > div > div > div > div {
    background-color: #f0f2f6;
}

/* Main header styling */
.main-header {
    text-align: center;
    color: #1f77b4;
    font-size: 2.2rem;
    font-weight: bold;
    margin-bottom: 1rem;
}

/* User header styling */
.user-header {
    background-color: #f8f9fa;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    border: 1px solid #e0e0e0;
}

/* Login page specific styles */
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

/* Login page buttons - Blue style */
.login-container .stButton > button {
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

.login-container .stButton > button:hover {
    background-color: #1565c0 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

/* Main app buttons - White style (same as original app.py) */
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

/* Make form visible */
.stForm {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
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
    width: 100% !important;
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
}

/* Force compact form elements */
.stForm [data-testid="stVerticalBlock"] > div {
    gap: 0.3rem !important;
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
"""

ULTRA_AGGRESSIVE_JS = """
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
"""

class EquipmentManagementAppFast:
    """
    A class-based Streamlit application for managing equipment data from CSV files.
    Optimized version with ultra-aggressive anti-fading implementation.
    """
    
    def __init__(self, csv_filename="ACT-LAB-Equipment-List.csv"):
        """
        Initialize the Equipment Management App.
        
        Args:
            csv_filename (str): Name of the CSV file to load
        """
        # Initialize cookie controller FIRST, before any other session state modifications
        try:
            from streamlit_cookies_controller import CookieController
            self.cookie_controller = CookieController()
        except ImportError:
            st.warning("⚠️ Cookie controller not available. Session persistence may not work properly.")
            self.cookie_controller = None
        
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
        
        # Initialize session storage file
        self.sessions_file = Path("sessions_storage.json")
        
        # Initialize session storage in session state
        if 'sessions_storage' not in st.session_state:
            st.session_state.sessions_storage = self._load_sessions_from_file()
        
        # Also store sessions in a more persistent way using multiple session state keys
        if 'persistent_sessions' not in st.session_state:
            st.session_state.persistent_sessions = st.session_state.sessions_storage.copy()
        
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
        if not self.cookie_controller:
            st.warning("⚠️ Cookie controller not available. Session persistence may not work properly.")
            return False
            
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
        if not self.cookie_controller:
            return False
            
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
            if self.cookie_controller:
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
        """Display the login page with ultra-aggressive anti-fading."""
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
            
            /* Remove any unwanted white boxes or containers */
            .stApp > div:not([data-testid="stAppViewContainer"]):not([data-testid="stDecoration"]) {
                background: transparent !important;
                box-shadow: none !important;
                border: none !important;
            }
            
            /* Ensure clean background */
            .stApp {
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
                background-image: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
            }
            
            .main .block-container {
                background: transparent !important;
                padding-top: 1rem !important;
                padding-bottom: 1rem !important;
            }
            
            /* Login form styling without container */
            .login-header {
                text-align: center;
                color: #1f77b4 !important;
                font-size: 2.2rem;
                font-weight: bold;
                margin-bottom: 1rem;
                text-shadow: none;
                background: transparent !important;
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
                max-width: 200px;
            }
            
            /* Center buttons */
            .stButton {
                display: flex;
                justify-content: center;
                width: 100%;
            }
            
            .stButton > button:hover {
            background-color: #1565c0 !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }
            
            /* Make form visible and centered */
            .stForm {
                background: transparent !important;
                border: none !important;
                padding: 0 !important;
                display: flex;
                flex-direction: column;
                align-items: center;
                max-width: 400px;
                margin: 0 auto;
            }
            
            /* Center all form elements */
            .stForm > div {
                display: flex;
                flex-direction: column;
                align-items: center;
                width: 100%;
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
        
        # Display login form with proper styling
        st.markdown(f'<h1 class="login-header">🔬 {self.login}</h1>', unsafe_allow_html=True)
        st.markdown('<h3 style="text-align: center; color: #666;">Management System</h3>', unsafe_allow_html=True)
        
        # Add a visible separator
        st.markdown("---")
        
        # Check if signup should be shown
        if st.session_state.get('show_signup', False):
            self.auth_manager.signup_page()
            return
        
        # Check if forgot password should be shown
        if st.session_state.get('show_forgot_password', False):
            self.auth_manager.forgot_password_page()
            return
        
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
                            # Force rerun to show main application
                            st.rerun()
                        else:
                            st.error("❌ Failed to create session. Please try again.")
                    else:
                        st.error("❌ Invalid username or password!")
                else:
                    st.warning("⚠️ Please enter both username and password!")
        
        # Add Forgot Password and Signup buttons
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔑 Forgot Password?", key="forgot_password_btn"):
                st.session_state.show_forgot_password = True
                st.rerun()
        
        with col2:
            if st.button("📝 Sign Up", key="signup_btn"):
                st.session_state.show_signup = True
                st.rerun()
        
        # Demo credentials info - commented out for production
        # st.markdown('<div class="login-info">', unsafe_allow_html=True)
        # st.markdown("### 📋 Demo Credentials")
        # st.markdown("""
        # **Admin:** admin / admin123  
        # **Manager:** lab_manager / labmgr123  
        # **Technician:** technician / tech123
        # """)
        # st.markdown('</div>', unsafe_allow_html=True)
    
    def configure_page(self):
        """Configure page settings with ultra-aggressive anti-fading."""
        # Inject ultra-aggressive anti-fading CSS and JavaScript
        st.markdown(ULTRA_AGGRESSIVE_CSS + ULTRA_AGGRESSIVE_JS, unsafe_allow_html=True)
    
    def run(self):
        """Main method to run the application with ultra-aggressive anti-fading."""
        
        # No need to handle logout completion since we use rerun directly

        try:
            client = MongoClient("mongodb://ascy00075.sc.altera.com:27017/mongo?readPreference=primary&ssl=false")
            client.admin.command("ping")
        except ConnectionFailure as e:
            st.error(f"MongoDB connection failed: {e}")
            st.stop()

        db = client["Equipment_DB"]
        self.Equipment_collection = db["Equipment"]
        self.Equipment_select_options = db["Equipment_select_options"]

        # Initialize session state and authentication
        self.auth_manager._initialize_session()

        # Check if user is authenticated
        if self.auth_manager.is_authenticated():
            # User is authenticated, show main app
            self.configure_page()
            self.auth_manager.display_header(self.main_page_titel)
            
            # Run automatic backup check for admin users
            if run_automatic_backup_check:
                try:
                    backup_created, backup_message = run_automatic_backup_check(backup_interval_hours=0.1)
                    if backup_created:
                        st.session_state["backup_notification"] = f"✅ Automatic backup created: {backup_message}"
                except Exception as e:
                    # Silent error handling for automatic backups
                    st.session_state["backup_error"] = f"Backup system error: {str(e)}"
            
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
                            from backup_csv_for_db_restore import backup_restore_ui
                        except ImportError:
                            backup_restore_ui = None
                        
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
                # For non-admin users, show Equipment Records
                with tab1:
                    # Check if user needs password change first
                    if self.auth_manager.user_needs_password_change(st.session_state.username):
                        st.warning("⚠️ You must change your password before accessing the system.")
                        self.auth_manager.password_change_page()
                        return

                    # Import and use the standalone Equipment Records system for non-admin users
                    try:
                        from Equipment_Records_Page import EquipmentRecordsSystem
                        equipment_records = EquipmentRecordsSystem()
                        equipment_records.equipment_records_page()
                    except ImportError:
                        st.error("❌ Equipment Records system not available. Please ensure Equipment_Records_Page.py is accessible.")
                        st.info("💡 Please contact an administrator to resolve this issue.")
        else:
            # User not authenticated, show login page
            self.login_page()

# Main execution
if __name__ == "__main__":
    # Configure page settings once at the module level to avoid conflicts
    try:
        st.set_page_config(
            page_title="ACT Lab Equipment - Fast",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    except st.errors.StreamlitAPIException:
        # Page config already set, continue
        pass
    
    # Create and run the application
    csv_filename = "ACT-LAB-Equipment-List.csv"
    app = EquipmentManagementAppFast(csv_filename)
    app.run()
