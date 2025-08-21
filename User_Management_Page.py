"""
User Management Page for Equipment Management System
Extracted from login_and_signup.py to provide standalone user management functionality.
"""

import streamlit as st
import hashlib
import json
import time
import uuid
import re
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path
from pymongo import MongoClient

# Try to import email configuration
try:
    from email_config import (
        SMTP_SERVER, SMTP_PORT, SYSTEM_EMAIL, SYSTEM_PASSWORD, 
        ADMIN_EMAIL, SYSTEM_URL, SYSTEM_NAME
    )
    EMAIL_CONFIGURED = True
    
    # Check if file notifications are preferred
    try:
        from email_config import USE_FILE_NOTIFICATIONS, NOTIFICATIONS_DIR
        if USE_FILE_NOTIFICATIONS:
            from file_email_notifier import FileEmailNotifier
            FILE_NOTIFIER = FileEmailNotifier(NOTIFICATIONS_DIR)
        else:
            FILE_NOTIFIER = None
    except ImportError:
        FILE_NOTIFIER = None
except ImportError as e:
    # Fallback values if no email configuration file
    SMTP_SERVER = "smtp.intel.com"
    SMTP_PORT = 587
    SYSTEM_EMAIL = "equipment-system@altera.com"
    SYSTEM_PASSWORD = "your-password-here"
    ADMIN_EMAIL = "yakov.yosef.hakimi@altera.com"
    SYSTEM_URL = "http://localhost:8501"
    SYSTEM_NAME = "Altera Lab Equipment Management System"
    EMAIL_CONFIGURED = False
    FILE_NOTIFIER = None
    print(f"⚠️ Email configuration not found: {e}. Using fallback values.")


class UserManagementSystem:
    """
    Standalone User Management System for admin operations.
    Extracted from AuthenticationManager to provide focused user management functionality.
    """
    
    # Centralized role definitions
    VALID_ROLES = ["admin", "tech", "user"]
    LEGACY_ROLES = ["manager", "technician"]  # For backward compatibility in existing data
    
    def __init__(self, mongo_connection_string="mongodb://ascy00075.sc.altera.com:27017/mongo?readPreference=primary&ssl=false"):
        """
        Initialize the User Management System.
        
        Args:
            mongo_connection_string (str): MongoDB connection string
        """
        self.mongo_connection_string = mongo_connection_string
        
        # Initialize MongoDB connection
        self._connect_to_database()
    
    def _connect_to_database(self):
        """Connect to MongoDB database."""
        try:
            self.client = MongoClient(self.mongo_connection_string)
            self.client.admin.command("ping")
            self.db = self.client["Equipment_DB"]
            self.users_collection = self.db["users"]
            return True
        except Exception as e:
            st.error(f"MongoDB connection failed: {e}")
            return False
    
    def _hash_password(self, password):
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_password(self, length=6):
        """Generate a random password."""
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))
    
    def _send_approval_email(self, recipient_email, username, password):
        """Send approval email with login credentials."""
        try:
            # Use file notifier if configured
            if FILE_NOTIFIER:
                FILE_NOTIFIER.send_approval_notification(recipient_email, username, password)
                return True
            
            # Otherwise use real email if configured
            if not EMAIL_CONFIGURED:
                st.warning("⚠️ Email not configured. Cannot send approval email.")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = SYSTEM_EMAIL
            msg['To'] = recipient_email
            msg['Subject'] = f"Account Approved - {SYSTEM_NAME}"
            
            body = f"""
            Dear User,

            Your account request has been approved! You can now access the {SYSTEM_NAME}.

            Your login credentials:
            Username: {username}
            Password: {password}

            Please log in at: {SYSTEM_URL}

            For security reasons, you may be required to change your password upon first login.

            Best regards,
            {SYSTEM_NAME} Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SYSTEM_EMAIL, SYSTEM_PASSWORD)
            text = msg.as_string()
            server.sendmail(SYSTEM_EMAIL, recipient_email, text)
            server.quit()
            
            return True
        except Exception as e:
            st.error(f"Failed to send email: {str(e)}")
            return False
    
    def _send_password_reset_email(self, recipient_email, username, new_password):
        """Send password reset email."""
        try:
            # Use file notifier if configured
            if FILE_NOTIFIER:
                FILE_NOTIFIER.send_password_reset_notification(recipient_email, username, new_password)
                return True
            
            # Otherwise use real email if configured
            if not EMAIL_CONFIGURED:
                st.warning("⚠️ Email not configured. Cannot send password reset email.")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = SYSTEM_EMAIL
            msg['To'] = recipient_email
            msg['Subject'] = f"Password Reset - {SYSTEM_NAME}"
            
            body = f"""
            Dear User,

            Your password has been reset for the {SYSTEM_NAME}.

            Your new login credentials:
            Username: {username}
            New Password: {new_password}

            Please log in at: {SYSTEM_URL}

            For security reasons, please change your password after logging in.

            Best regards,
            {SYSTEM_NAME} Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SYSTEM_EMAIL, SYSTEM_PASSWORD)
            text = msg.as_string()
            server.sendmail(SYSTEM_EMAIL, recipient_email, text)
            server.quit()
            
            return True
        except Exception as e:
            st.error(f"Failed to send password reset email: {str(e)}")
            return False
    
    def create_user_directly(self, username, email_prefix, first_name, last_name, wwid, role, 
                           manual_password=None, password_change_required=True, created_by="admin", 
                           send_email=True):
        """
        Create a user directly (admin function).
        
        Args:
            username (str): Username
            email_prefix (str): Email prefix (will add @altera.com)
            first_name (str): First name
            last_name (str): Last name
            wwid (str): Work Week ID
            role (str): User role
            manual_password (str, optional): Manual password, if not provided will generate random
            password_change_required (bool): Whether user must change password on first login
            created_by (str): Who created this user
            send_email (bool): Whether to send approval email
        
        Returns:
            tuple: (success, message, password_used)
        """
        try:
            # Validate role
            if role not in self.VALID_ROLES:
                return False, f"Invalid role. Valid roles are: {', '.join(self.VALID_ROLES)}", None
            
            # Check if username already exists
            if self.users_collection.find_one({"username": username}):
                return False, "Username already exists", None
            
            # Construct email
            email = f"{email_prefix}@altera.com" if not email_prefix.endswith("@altera.com") else email_prefix
            
            # Check if email already exists
            if self.users_collection.find_one({"email": email}):
                return False, "Email already exists", None
            
            # Generate or use provided password
            password = manual_password if manual_password else self._generate_password(6)
            
            # Create user document
            user_doc = {
                "uuid": str(uuid.uuid4()),
                "username": username,
                "email": email,
                "password": self._hash_password(password),
                "role": role,
                "first_name": first_name,
                "last_name": last_name,
                "wwid": wwid,
                "status": "approved",  # Direct creation means approved
                "created_at": datetime.now(),
                "approved_at": datetime.now(),
                "approved_by": created_by,
                "password_change_required": password_change_required
            }
            
            # Insert user
            result = self.users_collection.insert_one(user_doc)
            
            if result.inserted_id:
                # Send email if requested
                if send_email:
                    self._send_approval_email(email, username, password)
                
                return True, f"User {username} created successfully", password
            else:
                return False, "Failed to create user", None
                
        except Exception as e:
            return False, f"Error creating user: {str(e)}", None
    
    def change_user_password(self, admin_username, new_password, is_admin=False, target_username=None):
        """
        Change user password.
        
        Args:
            admin_username (str): Username of admin performing the change
            new_password (str): New password
            is_admin (bool): Whether the requester is admin
            target_username (str): Target user (for admin use)
        
        Returns:
            tuple: (success, message)
        """
        try:
            if is_admin and target_username:
                # Admin changing another user's password
                username_to_change = target_username
                message_suffix = f" for user {target_username}"
            else:
                # User changing their own password or admin changing their own
                username_to_change = admin_username
                message_suffix = ""
            
            # Update password in database
            result = self.users_collection.update_one(
                {"username": username_to_change, "status": "approved"},
                {
                    "$set": {
                        "password": self._hash_password(new_password),
                        "password_change_required": False,
                        "password_changed_at": datetime.now(),
                        "password_changed_by": admin_username
                    }
                }
            )
            
            if result.modified_count > 0:
                return True, f"Password changed successfully{message_suffix}"
            else:
                return False, f"Failed to change password{message_suffix} or user not found"
                
        except Exception as e:
            return False, f"Error changing password: {str(e)}"
    
    def change_user_role(self, target_username, new_role, admin_username):
        """Change role for a user (admin only)."""
        try:
            # Allow current valid roles + legacy roles for backward compatibility
            all_valid_roles = self.VALID_ROLES + self.LEGACY_ROLES
            if new_role not in all_valid_roles:
                return False, f"Invalid role. Valid roles are: {', '.join(self.VALID_ROLES)}"
            
            result = self.users_collection.update_one(
                {"username": target_username, "status": "approved"},
                {
                    "$set": {
                        "role": new_role,
                        "role_changed_at": datetime.now(),
                        "role_changed_by": admin_username
                    }
                }
            )
            
            if result.modified_count > 0:
                return True, f"Role changed to {new_role} successfully"
            else:
                return False, "Failed to change role or user not found"
                
        except Exception as e:
            return False, f"Error changing role: {str(e)}"
    
    def get_user_role(self, username):
        """Get user role from database."""
        user = self.users_collection.find_one({"username": username, "status": "approved"})
        return user["role"] if user else None
    
    def is_admin_user(self, username):
        """Check if user is admin."""
        role = self.get_user_role(username)
        return role == "admin"
    
    def get_user_info(self, username):
        """Get full user information from database."""
        return self.users_collection.find_one({"username": username, "status": "approved"})
    
    def user_needs_password_change(self, username):
        """Check if user needs to change password."""
        user = self.get_user_info(username)
        return user.get("password_change_required", False) if user else False
    
    def approve_pending_user(self, user_id, approved_by):
        """Approve a pending user and send credentials."""
        try:
            # Get user information
            user = self.users_collection.find_one({"_id": user_id, "status": "pending"})
            if not user:
                return False, "User not found or already processed"
            
            # Generate random password
            password = self._generate_password(6)
            
            # Update user status and add password
            result = self.users_collection.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "status": "approved",
                        "password": self._hash_password(password),
                        "approved_at": datetime.now(),
                        "approved_by": approved_by,
                        "password_change_required": True
                    }
                }
            )
            
            if result.modified_count > 0:
                # Send approval email
                if self._send_approval_email(user["email"], user["username"], password):
                    return True, f"User approved and email sent with password: {password}"
                else:
                    return True, f"User approved but email failed. Password: {password}"
            else:
                return False, "Failed to approve user"
                
        except Exception as e:
            return False, f"Error approving user: {str(e)}"
    
    def reject_pending_user(self, user_id):
        """Reject a pending user."""
        try:
            result = self.users_collection.update_one(
                {"_id": user_id, "status": "pending"},
                {"$set": {"status": "rejected", "rejected_at": datetime.now()}}
            )
            
            if result.modified_count > 0:
                return True, "User rejected successfully"
            else:
                return False, "Failed to reject user or user not found"
                
        except Exception as e:
            return False, f"Error rejecting user: {str(e)}"
    
    def user_management_page(self):
        """Display user management page for admins."""
        # Note: This assumes current user is already verified as admin
        st.markdown("## 👥 User Management")
        st.markdown("---")
        
        tab1, tab2, tab3, tab4 = st.tabs(["👤 All Users", "⏳ Pending Approval", "🔐 Password Reset", "➕ Create User"])
        
        with tab1:
            # Get all approved users
            all_users = list(self.users_collection.find({"status": "approved"}).sort("first_name", 1))
            
            if all_users:
                for user in all_users:
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.markdown(f"""
                            **{user['first_name']} {user['last_name']}**  
                            Username: `{user['username']}`  
                            Email: {user['email']}  
                            WWID: {user['wwid']}  
                            Role: **{user['role']}**  
                            Status: {user['status']}
                            """)
                        
                        with col2:
                            # Use valid roles for new assignments, but handle legacy roles in display
                            user_role = user['role']
                            if user_role in self.VALID_ROLES:
                                role_index = self.VALID_ROLES.index(user_role)
                            else:
                                # For legacy roles, default to 'user'
                                role_index = self.VALID_ROLES.index('user')
                            
                            new_role = st.selectbox(
                                "Change Role", 
                                self.VALID_ROLES,
                                index=role_index,
                                key=f"role_{user['_id']}"
                            )
                            
                            if st.button(f"Update Role", key=f"update_role_{user['_id']}"):
                                if new_role != user['role']:
                                    success, message = self.change_user_role(
                                        user['username'], new_role, st.session_state.username
                                    )
                                    if success:
                                        st.success(message)
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(message)
                        
                        with col3:
                            # Check if we're showing confirmation for this user
                            confirm_key = f"confirm_reset_{user['_id']}"
                            
                            if st.session_state.get(confirm_key, False):
                                # Show warning popup
                                st.warning(f"⚠️ **Reset Password for {user['username']}?**")
                                st.write(f"This will generate a new password for **{user['first_name']} {user['last_name']}** and send it via email.")
                                
                                col_yes, col_no = st.columns(2)
                                with col_yes:
                                    if st.button("✅ Yes, Reset", key=f"confirm_yes_{user['_id']}"):
                                        new_pwd = self._generate_password(4)
                                        success, message = self.change_user_password(
                                            st.session_state.username, new_pwd, True, user['username']
                                        )
                                        if success:
                                            st.success(f"New password: **{new_pwd}**")
                                            # Send email with new password
                                            self._send_password_reset_email(user['email'], user['username'], new_pwd)
                                        else:
                                            st.error(message)
                                        # Clear confirmation state
                                        st.session_state[confirm_key] = False
                                        st.rerun()
                                
                                with col_no:
                                    if st.button("❌ Cancel", key=f"confirm_no_{user['_id']}"):
                                        # Clear confirmation state
                                        st.session_state[confirm_key] = False
                                        st.rerun()
                            else:
                                # Show initial reset button
                                if st.button(f"Reset Password", key=f"reset_pwd_{user['_id']}"):
                                    # Set confirmation state
                                    st.session_state[confirm_key] = True
                                    st.rerun()
                        
                        st.markdown("---")
            else:
                st.info("No users found.")
        
        with tab2:
            # Get pending users
            pending_users = list(self.users_collection.find({"status": "pending"}).sort("created_at", -1))
            
            if pending_users:
                st.info(f"📋 **{len(pending_users)} user(s) waiting for approval**")
                
                for user in pending_users:
                    with st.container():
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.markdown(f"""
                            **{user['first_name']} {user['last_name']}**  
                            Username: `{user['username']}`  
                            Email: {user['email']}  
                            WWID: {user['wwid']}  
                            Requested Role: **{user['role']}**  
                            Submitted: {user['created_at'].strftime('%Y-%m-%d %H:%M')}
                            """)
                        
                        with col2:
                            col_approve, col_reject = st.columns(2)
                            
                            with col_approve:
                                if st.button("✅ Approve", key=f"approve_{user['_id']}"):
                                    success, message = self.approve_pending_user(
                                        user['_id'], st.session_state.username
                                    )
                                    if success:
                                        st.success(message)
                                        time.sleep(2)
                                        st.rerun()
                                    else:
                                        st.error(message)
                            
                            with col_reject:
                                if st.button("❌ Reject", key=f"reject_{user['_id']}"):
                                    success, message = self.reject_pending_user(user['_id'])
                                    if success:
                                        st.success(message)
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(message)
                        
                        st.markdown("---")
            else:
                st.info("📭 No pending user requests.")
        
        with tab3:
            # Password reset functionality
            st.markdown("### 🔐 Reset User Password")
            st.markdown("Generate a new random password for any user and optionally send it via email.")
            
            # Get all approved users for selection
            all_users = list(self.users_collection.find({"status": "approved"}).sort("username", 1))
            user_options = [f"{user['username']} ({user['first_name']} {user['last_name']})" for user in all_users]
            
            if user_options:
                selected_user_display = st.selectbox("Select User", user_options)
                selected_username = selected_user_display.split(" (")[0]
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    send_email_option = st.checkbox("Send new password via email", value=True)
                
                with col2:
                    if st.button("🔄 Generate New Password", type="primary"):
                        new_password = self._generate_password(6)
                        success, message = self.change_user_password(
                            st.session_state.username, new_password, True, selected_username
                        )
                        
                        if success:
                            st.success(f"✅ New password for **{selected_username}**: `{new_password}`")
                            
                            if send_email_option:
                                # Get user email
                                user_info = self.get_user_info(selected_username)
                                if user_info:
                                    email_success = self._send_password_reset_email(
                                        user_info['email'], selected_username, new_password
                                    )
                                    if email_success:
                                        st.success("📧 Password sent via email!")
                                    else:
                                        st.warning("⚠️ Password reset successful but email failed to send.")
                        else:
                            st.error(f"❌ {message}")
            else:
                st.info("No users found.")
        
        with tab4:
            # Create user functionality
            st.markdown("### ➕ Create New User")
            st.markdown("Create a new user account directly (bypassing the signup process).")
            
            with st.form("create_user_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_username = st.text_input("Username*", placeholder="e.g., john.doe")
                    new_first_name = st.text_input("First Name*", placeholder="John")
                    new_last_name = st.text_input("Last Name*", placeholder="Doe")
                    new_email_prefix = st.text_input("Email Prefix*", placeholder="john.doe (will become john.doe@altera.com)")
                
                with col2:
                    new_wwid = st.text_input("WWID*", placeholder="e.g., 12345678")
                    new_role = st.selectbox("Role*", self.VALID_ROLES, index=2)  # Default to 'user'
                    new_password = st.text_input("Password (leave empty for auto-generate)", type="password", placeholder="Optional: custom password")
                    send_email = st.checkbox("Send credentials via email", value=True)
                
                password_change_required = st.checkbox("Require password change on first login", value=True)
                
                submit_create = st.form_submit_button("➕ Create User", type="primary")
                
                if submit_create:
                    # Validate required fields
                    if not all([new_username, new_first_name, new_last_name, new_email_prefix, new_wwid]):
                        st.error("❌ Please fill in all required fields marked with *")
                    else:
                        # Create user
                        success, message, password = self.create_user_directly(
                            username=new_username.strip(),
                            email_prefix=new_email_prefix.strip(),
                            first_name=new_first_name.strip(),
                            last_name=new_last_name.strip(),
                            wwid=new_wwid.strip(),
                            role=new_role,
                            manual_password=new_password.strip() if new_password.strip() else None,
                            password_change_required=password_change_required,
                            created_by=st.session_state.username,
                            send_email=send_email
                        )
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.info(f"🔑 **Password:** `{password}`")
                            if send_email:
                                st.info("📧 Login credentials sent via email!")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
    
    def password_change_page(self):
        """Display password change page."""
        st.markdown("## 🔐 Change Password")
        st.markdown("---")
        
        user_info = self.get_user_info(st.session_state.username)
        if user_info and user_info.get("password_change_required", False):
            st.warning("⚠️ You must change your password before accessing the system.")
        
        with st.form("password_change_form"):
            if self.is_admin_user(st.session_state.username):
                st.markdown("### Admin: Change Any User Password")
                target_user = st.text_input("Target Username (leave empty for yourself)", 
                                           placeholder="Enter username to change password for")
            else:
                target_user = None
            
            new_password = st.text_input("New Password", type="password", 
                                       placeholder="Enter new password")
            confirm_password = st.text_input("Confirm Password", type="password", 
                                           placeholder="Confirm new password")
            
            submit_button = st.form_submit_button("🔄 Change Password")
            
            if submit_button:
                if not new_password or not confirm_password:
                    st.error("❌ Please fill in all fields!")
                    return
                
                if new_password != confirm_password:
                    st.error("❌ Passwords do not match!")
                    return
                
                if len(new_password) < 3:
                    st.error("❌ Password must be at least 3 characters long!")
                    return
                
                # Change password
                is_admin = self.is_admin_user(st.session_state.username)
                success, message = self.change_user_password(
                    st.session_state.username, new_password, 
                    is_admin, target_user
                )
                
                if success:
                    st.success(f"✅ {message}")
                    st.session_state.password_change_success = True
                    # Don't rerun immediately, let user see the message
                else:
                    st.error(f"❌ {message}")


def main():
    """
    Main function to run the User Management Page as a standalone application.
    """
    st.set_page_config(
        page_title="User Management System",
        page_icon="👥",
        layout="wide"
    )
    
    # Initialize the user management system
    user_mgmt = UserManagementSystem()
    
    # Check if user is authenticated (this would need to be implemented)
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    # Simple authentication check (in real implementation, this would be more robust)
    if not st.session_state.authenticated:
        st.markdown("## 🔐 User Management Access")
        st.warning("⚠️ This is a demo. In production, proper authentication would be required.")
        
        username = st.text_input("Enter admin username for demo:")
        if st.button("Access User Management") and username:
            # In real implementation, verify admin credentials
            st.session_state.authenticated = True
            st.session_state.username = username
            st.rerun()
    else:
        # Show user management interface
        st.title("👥 User Management System")
        st.markdown(f"**Logged in as:** {st.session_state.username}")
        
        # Display the user management page
        user_mgmt.user_management_page()
        
        # Add logout button
        if st.sidebar.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.rerun()


if __name__ == "__main__":
    main()
