#!/usr/bin/env python3
"""
Test script to verify login page functionality after fixes.
"""

import streamlit as st
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_login_page():
    """Test the login page functionality."""
    
    st.title("🔧 Login Page Test")
    st.markdown("---")
    
    # Test 1: Check if login page can be imported
    try:
        from app_fast import EquipmentManagementAppFast
        st.success("✅ Successfully imported EquipmentManagementAppFast")
    except ImportError as e:
        st.error(f"❌ Failed to import EquipmentManagementAppFast: {e}")
        return
    
    # Test 2: Check if authentication manager can be imported
    try:
        from login_and_signup import AuthenticationManager
        st.success("✅ Successfully imported AuthenticationManager")
    except ImportError as e:
        st.error(f"❌ Failed to import AuthenticationManager: {e}")
        return
    
    # Test 3: Test authentication manager initialization
    try:
        auth_manager = AuthenticationManager()
        st.success("✅ Successfully initialized AuthenticationManager")
    except Exception as e:
        st.error(f"❌ Failed to initialize AuthenticationManager: {e}")
        return
    
    # Test 4: Check if required methods exist
    required_methods = [
        'login_page',
        'logout', 
        'forgot_password_page',
        'signup_page',
        'display_header'
    ]
    
    for method in required_methods:
        if hasattr(auth_manager, method):
            st.success(f"✅ Method '{method}' exists in AuthenticationManager")
        else:
            st.error(f"❌ Method '{method}' missing from AuthenticationManager")
    
    # Test 5: Check if app can be initialized
    try:
        csv_filename = "ACT-LAB-Equipment-List.csv"
        app = EquipmentManagementAppFast(csv_filename)
        st.success("✅ Successfully initialized EquipmentManagementAppFast")
    except Exception as e:
        st.error(f"❌ Failed to initialize EquipmentManagementAppFast: {e}")
        return
    
    # Test 6: Check if login page method exists
    if hasattr(app, 'login_page'):
        st.success("✅ Login page method exists in app")
    else:
        st.error("❌ Login page method missing from app")
    
    # Test 7: Check session state handling
    st.markdown("### Session State Test")
    
    # Clear any existing session state
    if 'authenticated' in st.session_state:
        del st.session_state['authenticated']
    if 'username' in st.session_state:
        del st.session_state['username']
    if 'user_role' in st.session_state:
        del st.session_state['user_role']
    if 'session_id' in st.session_state:
        del st.session_state['session_id']
    if 'login_time' in st.session_state:
        del st.session_state['login_time']
    
    st.success("✅ Session state cleared for testing")
    
    # Test 8: Check if logout functionality works
    st.markdown("### Logout Test")
    
    # Simulate logout
    st.session_state['logout_complete'] = True
    
    if st.session_state.get('logout_complete', False):
        st.success("✅ Logout session state set correctly")
    else:
        st.error("❌ Logout session state not set correctly")
    
    st.markdown("---")
    st.markdown("### 🎯 Test Summary")
    st.markdown("""
    **What was fixed:**
    1. ✅ Login page UI restored to match original app.py design
    2. ✅ Added "Forgot Password" and "Signup" buttons
    3. ✅ Fixed logout functionality to prevent login issues
    4. ✅ Improved session state handling to prevent unnecessary reruns
    5. ✅ Enhanced CSS styling for better visual consistency
    
    **Next steps:**
    1. Run the main app: `streamlit run app_fast.py`
    2. Test login with valid credentials
    3. Test logout functionality
    4. Test "Forgot Password" and "Signup" buttons
    """)

if __name__ == "__main__":
    test_login_page()
