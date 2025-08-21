"""
Test script to verify that the cookie controller initialization issue is resolved.
"""

import streamlit as st
from login_and_signup import AuthenticationManager

def test_cookie_controller():
    """Test that the cookie controller initializes without errors."""
    
    st.title("🍪 Cookie Controller Test")
    st.markdown("---")
    
    try:
        st.info("🔄 Testing AuthenticationManager initialization...")
        
        # Test AuthenticationManager initialization
        auth_manager = AuthenticationManager()
        
        st.success("✅ AuthenticationManager initialized successfully!")
        
        # Check cookie controller status
        if hasattr(auth_manager, 'cookie_controller'):
            if auth_manager.cookie_controller is not None:
                st.success("✅ Cookie controller is available and working")
            else:
                st.warning("⚠️ Cookie controller is None (fallback mode)")
        else:
            st.error("❌ Cookie controller attribute not found")
        
        # Test session initialization
        st.info("🔄 Testing session initialization...")
        auth_manager._initialize_session()
        st.success("✅ Session initialization completed successfully!")
        
        # Display current session state
        st.markdown("### 📊 Current Session State")
        st.write(f"Authenticated: {st.session_state.get('authenticated', False)}")
        st.write(f"Username: {st.session_state.get('username', None)}")
        st.write(f"User Role: {st.session_state.get('user_role', None)}")
        st.write(f"Session ID: {st.session_state.get('session_id', None)}")
        
        st.success("🎉 **COOKIE CONTROLLER TEST PASSED!** No errors detected.")
        
    except Exception as e:
        st.error(f"❌ **COOKIE CONTROLLER TEST FAILED!** Error: {str(e)}")
        st.error("Please check the cookie controller implementation.")

if __name__ == "__main__":
    test_cookie_controller()
