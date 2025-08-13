"""
Test script for the authentication system
"""

from login_and_signup import AuthenticationManager
from datetime import datetime

def test_auth_manager():
    """Test basic authentication manager functionality."""
    print("Testing Authentication Manager...")
    
    # Create auth manager
    auth_manager = AuthenticationManager("Test System")
    
    # Test MongoDB connection
    try:
        print("Testing MongoDB connection...")
        users = auth_manager.users
        print(f"✅ MongoDB connection successful. Users available: {len(users)}")
        
        # Print user info
        for username, user_info in list(users.items())[:3]:  # Show first 3 users
            print(f"  - {username}: {user_info.get('first_name', 'N/A')} {user_info.get('last_name', 'N/A')} ({user_info.get('role', 'N/A')})")
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False
    
    # Test user creation
    print("\nTesting user signup...")
    success, message = auth_manager.create_signup_request(
        username="testuser123",
        email="testuser123",  # Will be converted to testuser123@altera.com
        first_name="Test",
        last_name="User",
        wwid="TEST123",
        requested_role="user"
    )
    
    if success:
        print(f"✅ Signup test successful: {message}")
    else:
        print(f"ℹ️ Signup test result: {message}")
    
    # Test pending users
    print("\nTesting pending users retrieval...")
    pending = auth_manager.get_pending_users()
    print(f"✅ Found {len(pending)} pending users")
    
    # Test email validation
    print("\nTesting email validation...")
    valid, result = auth_manager._validate_email("testuser")
    print(f"✅ Email validation: {result} (valid: {valid})")
    
    print("\n🎉 All basic tests completed!")
    return True

if __name__ == "__main__":
    test_auth_manager()
