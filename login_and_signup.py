"""
Login and Signup functionality for Equipment Management System
Handles user authentication, session management, cookie operations, and user registration.
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
from streamlit_cookies_controller import CookieController
from pymongo import MongoClient

# Try to import email configuration
try:
    from email_config import (
        SMTP_SERVER, SMTP_PORT, SYSTEM_EMAIL, SYSTEM_PASSWORD, 
        ADMIN_EMAIL, SYSTEM_URL, SYSTEM_NAME
    )
    EMAIL_CONFIGURED = True
    
    # Check if file notifications are preferred (now set to False for real email)
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
    ADMIN_EMAIL = "yakov.yosef.hakimi@altera.com"  # Updated to your email
    SYSTEM_URL = "http://localhost:8501"
    SYSTEM_NAME = "Altera Lab Equipment Management System"
    EMAIL_CONFIGURED = False
    FILE_NOTIFIER = None
    print(f"⚠️ Email configuration not found: {e}. Using fallback values.")


class AuthenticationManager:
    """
    Manages user authentication, sessions, cookies, and user registration for the Equipment Management System.
    """
    
    # Centralized role definitions
    VALID_ROLES = ["admin", "tech", "user"]
    LEGACY_ROLES = ["manager", "technician"]  # For backward compatibility in existing data
    
    def __init__(self, login_title="Altera Lab Equipment", mongo_connection_string="mongodb://ascy00075.sc.altera.com:27017/mongo?readPreference=primary&ssl=false"):
        """
        Initialize the Authentication Manager.
        
        Args:
            login_title (str): Title to display on login page
            mongo_connection_string (str): MongoDB connection string
        """
        # Initialize cookie controller with error handling to avoid session state conflicts
        try:
            self.cookie_controller = CookieController()
        except Exception as e:
            # st.warning(f"⚠️ Cookie controller initialization failed: {str(e)}")
            # st.info("Session persistence may be limited. Continuing without cookie controller.")
            self.cookie_controller = None
        
        self.login_title = login_title
        self.mongo_connection_string = mongo_connection_string
        
        # Initialize MongoDB connection
        self._connect_to_database()
        
        # Session storage file
        self.sessions_file = Path("sessions_storage.json")
        
        # Initialize session storage
        if 'sessions_storage' not in st.session_state:
            st.session_state.sessions_storage = self._load_sessions_from_file()
        
        # Also store sessions in a more persistent way using multiple session state keys
        if 'persistent_sessions' not in st.session_state:
            st.session_state.persistent_sessions = st.session_state.sessions_storage.copy()

        # Initialize default admin user if no users exist in database
        self._initialize_default_users()
    
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
    
    def _initialize_default_users(self):
        """Initialize default users if none exist in database."""
        try:
            # Check if any users exist
            if self.users_collection.count_documents({}) == 0:
                # Create default admin user
                default_admin = {
                    "uuid": str(uuid.uuid4()),
                    "username": "admin",
                    "email": "admin@altera.com",
                    "password": self._hash_password("admin123"),
                    "role": "admin",
                    "first_name": "System",
                    "last_name": "Administrator",
                    "wwid": "ADMIN001",
                    "status": "approved",
                    "created_at": datetime.now(),
                    "approved_at": datetime.now(),
                    "approved_by": "system",
                    "password_change_required": False
                }
                self.users_collection.insert_one(default_admin)
                
                # Create some additional default users for testing
                default_users = [
                    {
                        "uuid": str(uuid.uuid4()),
                        "username": "lab_manager",
                        "email": "lab_manager@altera.com",
                        "password": self._hash_password("labmgr123"),
                        "role": "manager",
                        "first_name": "Lab",
                        "last_name": "Manager",
                        "wwid": "LAB001",
                        "status": "approved",
                        "created_at": datetime.now(),
                        "approved_at": datetime.now(),
                        "approved_by": "admin",
                        "password_change_required": False
                    },
                    {
                        "uuid": str(uuid.uuid4()),
                        "username": "technician",
                        "email": "technician@altera.com",
                        "password": self._hash_password("tech123"),
                        "role": "technician",
                        "first_name": "Lab",
                        "last_name": "Technician",
                        "wwid": "TECH001",
                        "status": "approved",
                        "created_at": datetime.now(),
                        "approved_at": datetime.now(),
                        "approved_by": "admin",
                        "password_change_required": False
                    }
                ]
                
                for user in default_users:
                    self.users_collection.insert_one(user)
                
        except Exception as e:
            st.error(f"Error initializing default users: {e}")
    
    @property
    def users(self):
        """Get users from database in the format expected by existing code."""
        try:
            users_dict = {}
            db_users = list(self.users_collection.find({"status": "approved"}))
            for user in db_users:
                users_dict[user["username"]] = {
                    "password": user["password"],
                    "role": user["role"],
                    "name": f"{user['first_name']} {user['last_name']}",
                    "email": user["email"],
                    "uuid": user["uuid"],
                    "wwid": user["wwid"],
                    "password_change_required": user.get("password_change_required", False)
                }
            return users_dict
        except Exception as e:
            st.error(f"Error loading users: {e}")
            return {}
    
    def _hash_password(self, password):
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, username, password):
        """Verify username and password."""
        user = self.users_collection.find_one({"username": username, "status": "approved"})
        if user:
            hashed_password = self._hash_password(password)
            return user["password"] == hashed_password
        return False
    
    def _generate_password(self, length=4):
        """Generate a random password of specified length."""
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))
    
    def _validate_email(self, email):
        """Validate email format and ensure it's @altera.com."""
        # Extract username part before @ if @ exists
        if '@' in email:
            username_part = email.split('@')[0]
        else:
            username_part = email
        
        # Validate username part (basic email validation)
        if not re.match(r'^[a-zA-Z0-9._-]+$', username_part):
            return False, "Invalid email format"
        
        # Always append @altera.com
        final_email = f"{username_part}@altera.com"
        
        return True, final_email
    
    def test_email_connection(self):
        """Test email connection and send a test email."""
        if not EMAIL_CONFIGURED:
            st.error("❌ Email not configured. Please check email_config.py")
            return False
            
        try:
            st.info("🔄 Testing email connection...")
            
            # Create test message using Intel SMTP approach
            subject = f"Test Email from {SYSTEM_NAME}"
            body = (
                f"This is a test email from the {SYSTEM_NAME}.\n\n"
                f"Email configuration test successful!\n\n"
                f"Test Details:\n"
                f"- SMTP Server: {SMTP_SERVER}\n"
                f"- SMTP Port: {SMTP_PORT}\n"
                f"- System Email: {SYSTEM_EMAIL}\n"
                f"- Admin Email: {ADMIN_EMAIL}\n"
                f"- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"If you receive this email, the email configuration is working correctly.\n\n"
                f"This is an automated test message from the {SYSTEM_NAME}."
            )
            
            msg = MIMEText(body, _subtype="plain", _charset="utf-8")
            msg["Subject"] = subject
            msg["From"] = SYSTEM_EMAIL
            msg["To"] = ADMIN_EMAIL
            
            # Send email using Intel SMTP (simple and proven)
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.send_message(msg)
            
            st.success(f"✅ Test email sent successfully to {ADMIN_EMAIL}!")
            st.toast(f"📧 Test email sent to {ADMIN_EMAIL}", icon="📨")
            return True
            
        except Exception as e:
            st.error(f"❌ Email test failed: {str(e)}")
            st.info("💡 Please check your email configuration in email_config.py")
            return False
    
    def _send_approval_request_email(self, user_data):
        """Send approval request email to admin via real email AND file notification."""
        # Always show UI notification regardless of email configuration
        st.info(f"📧 Admin notification: New request from {user_data['username']} ({user_data['email']})")
        
        # Email body
        body = f"""
        A new user has requested access to the {SYSTEM_NAME}:
        
        Name: {user_data['first_name']} {user_data['last_name']}
        Username: {user_data['username']}
        Email: {user_data['email']}
        WWID: {user_data['wwid']}
        Requested Role: {user_data['requested_role']}
        Password: {'✅ User provided their own password' if user_data.get('user_provided_password', False) else '🔄 System will generate password'}
        Request Date: {user_data['created_at'].strftime('%Y-%m-%d %H:%M:%S')}
        
        Please log into the {SYSTEM_NAME} to approve or reject this request.
        
        System URL: {SYSTEM_URL}
        
        This is an automated message from the {SYSTEM_NAME}.
        """
        
        email_success = False
        file_success = False
        
        # Try real email first (if configured)
        if EMAIL_CONFIGURED:
            try:
                # Create message using the Intel SMTP approach
                subject = f"New User Access Request - {user_data['username']}"
                msg = MIMEText(body, _subtype="plain", _charset="utf-8")
                msg["Subject"] = subject
                msg["From"] = SYSTEM_EMAIL
                msg["To"] = ADMIN_EMAIL
                
                # Send email using Intel SMTP (simple and proven)
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.send_message(msg)
                
                st.success(f"📧 Real email sent to {ADMIN_EMAIL}!")
                email_success = True
                
            except Exception as e:
                st.warning(f"📧 Real email failed: {str(e)}")
        
        # Also save to file (for backup and immediate viewing)
        if FILE_NOTIFIER:
            try:
                success, message = FILE_NOTIFIER.send_email(
                    to_email=ADMIN_EMAIL,
                    subject=f"New User Access Request - {user_data['username']}",
                    body=body,
                    from_email=SYSTEM_EMAIL
                )
                if success:
                    st.success(f"📁 Notification saved to file (backup)!")
                    file_success = True
                else:
                    st.warning(f"� File notification failed: {message}")
            except Exception as e:
                st.warning(f"📁 File notification error: {str(e)}")
        
        # Show results
        if email_success and file_success:
            st.info("✅ Notification sent via both email and file backup!")
        elif email_success:
            st.info("✅ Email sent successfully!")
        elif file_success:
            st.info("✅ File notification saved successfully!")
        else:
            st.warning("⚠️ Both email and file notifications had issues, but request was still saved.")
        
        return True  # Always return True so signup process continues
    
    def _send_approval_email_no_password(self, user_email, username):
        """Send approval email without password (user already provided one during signup)."""
        if not EMAIL_CONFIGURED:
            st.info("📧 Email not configured. Please notify the user that their account has been approved.")
            return True  # Return True so the process continues
            
        try:
            # Email body without password
            subject = "✅ Access Approved"
            body = (
                f"Dear {username},\n\n"
                f"Your access request for the {SYSTEM_NAME} has been approved.\n\n"
                f"👤 Username: {username}\n"
                f"🔑 Password: Use the password you provided during signup\n\n"
                f"System URL: {SYSTEM_URL}\n\n"
                f"You can now log in using the credentials you provided during registration.\n"
                f"Since you set your own password, no password change is required.\n\n"
                f"Best,\nAdmin"
            )
            
            # Create message using Intel SMTP approach
            msg = MIMEText(body, _subtype="plain", _charset="utf-8")
            msg["Subject"] = subject
            msg["From"] = SYSTEM_EMAIL
            msg["To"] = user_email
            
            # Send email using Intel SMTP (simple and proven)
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.send_message(msg)
            
            st.success(f"📧 Email sent successfully to {user_email}")
            st.toast(f"📧 Approval email sent to {user_email}", icon="📨")
            return True
            
        except Exception as e:
            # Don't fail the approval process if email fails
            st.warning(f"📧 Email sending failed: {str(e)}")
            st.info("💡 User was still approved successfully - please notify them manually.")
            return True

    def _send_approval_email(self, user_email, username, password):
        """Send approval email with generated password to user."""
        # Always show the password in UI for admin
        st.success(f"✅ User approved! Password: **{password}**")
        
        if not EMAIL_CONFIGURED:
            st.info("📧 Email not configured. Please share the password manually with the user.")
            return True  # Return True so the process continues
            
        try:
            # Email body with improved formatting like your working example
            subject = "✅ Access Approved"
            body = (
                f"Dear {username},\n\n"
                f"Your access request for the {SYSTEM_NAME} has been approved.\n\n"
                f"👤 Username: {username}\n"
                f"🔑 Password: {password} (please change it after logging in)\n\n"
                f"System URL: {SYSTEM_URL}\n\n"
                f"IMPORTANT: You will be required to change your password on first login.\n\n"
                f"Best,\nAdmin"
            )
            
            # Create message using Intel SMTP approach
            msg = MIMEText(body, _subtype="plain", _charset="utf-8")
            msg["Subject"] = subject
            msg["From"] = SYSTEM_EMAIL
            msg["To"] = user_email
            
            # Send email using Intel SMTP (simple and proven)
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.send_message(msg)
            
            st.success(f"📧 Email sent successfully to {user_email}")
            st.toast(f"📧 Approval email sent to {user_email}", icon="📨")
            return True
            
        except Exception as e:
            # Don't fail the approval process if email fails
            st.warning(f"📧 Email sending failed: {str(e)}")
            st.info("💡 User was still approved successfully - please share the password manually.")
            return True
    
    def create_signup_request(self, username, email, first_name, last_name, wwid, requested_role, user_password=None):
        """Create a new signup request in the database."""
        try:
            # Validate email
            is_valid, final_email = self._validate_email(email)
            if not is_valid:
                return False, final_email
            
            # Check if username already exists
            if self.users_collection.find_one({"username": username}):
                return False, "Username already exists"
            
            # Check if email already exists
            if self.users_collection.find_one({"email": final_email}):
                return False, "Email already registered"
            
            # Check if WWID already exists
            if self.users_collection.find_one({"wwid": wwid}):
                return False, "WWID already registered"
            
            # Hash password if provided by user
            hashed_password = None
            if user_password:
                hashed_password = self._hash_password(user_password)
            
            # Create new user request
            user_data = {
                "uuid": str(uuid.uuid4()),
                "username": username.lower().strip(),
                "email": final_email,
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "wwid": wwid.strip().upper(),
                "requested_role": requested_role,
                "status": "pending",
                "created_at": datetime.now(),
                "password": hashed_password,  # Will be None if user didn't provide password
                "user_provided_password": bool(user_password),  # Track if user provided password
                "approved_at": None,
                "approved_by": None,
                "password_change_required": not bool(user_password)  # No need to change if user set it
            }
            
            # Insert into database
            result = self.users_collection.insert_one(user_data)
            
            if result.inserted_id:
                # Send approval request email to admin
                self._send_approval_request_email(user_data)
                if user_password:
                    return True, "Signup request submitted successfully with your password. You will receive an email when approved."
                else:
                    return True, "Signup request submitted successfully. You will receive an email with your login credentials when approved."
            else:
                return False, "Failed to create signup request"
                
        except Exception as e:
            return False, f"Error creating signup request: {str(e)}"
    
    def get_pending_users(self):
        """Get all pending user requests (admin only)."""
        try:
            return list(self.users_collection.find({"status": "pending"}).sort("created_at", 1))
        except Exception as e:
            st.error(f"Error fetching pending users: {e}")
            return []
    
    def approve_user(self, user_id, approver_username, assigned_role=None):
        """Approve a pending user and generate password if needed."""
        try:
            # Get the user's requested role first
            pending_user = self.users_collection.find_one({"_id": user_id, "status": "pending"})
            if not pending_user:
                return False, "Pending user not found"
            
            # Use assigned role if provided, otherwise use requested role
            if assigned_role:
                final_role = assigned_role
            else:
                final_role = pending_user.get("requested_role", "user")
            
            # Check if user already provided a password
            user_provided_password = pending_user.get("user_provided_password", False)
            
            if user_provided_password and pending_user.get("password"):
                # User already set their password during signup
                generated_password = None
                hashed_password = pending_user["password"]  # Use existing hashed password
                password_change_required = False  # User already set their preferred password
                approval_message = f"User approved successfully with '{final_role}' role using their provided password."
            else:
                # Generate password for user
                generated_password = self._generate_password(4)
                hashed_password = self._hash_password(generated_password)
                password_change_required = True
                approval_message = f"User approved successfully with '{final_role}' role. Password: {generated_password}"
            
            # Update user status
            result = self.users_collection.update_one(
                {"_id": user_id, "status": "pending"},
                {
                    "$set": {
                        "status": "approved",
                        "password": hashed_password,
                        "approved_at": datetime.now(),
                        "approved_by": approver_username,
                        "role": final_role,
                        "password_change_required": password_change_required
                    }
                }
            )
            
            if result.modified_count > 0:
                # Get user details for email
                user = self.users_collection.find_one({"_id": user_id})
                if user:
                    # Send approval email
                    if user_provided_password:
                        # Send email without password (user already knows it)
                        self._send_approval_email_no_password(user["email"], user["username"])
                    else:
                        # Send email with generated password
                        self._send_approval_email(user["email"], user["username"], generated_password)
                    
                    return True, approval_message
                else:
                    return False, "User not found"
            else:
                return False, "Failed to approve user"
                
        except Exception as e:
            return False, f"Error approving user: {str(e)}"
    
    def reject_user(self, user_id, approver_username):
        """Reject a pending user request."""
        try:
            result = self.users_collection.update_one(
                {"_id": user_id, "status": "pending"},
                {
                    "$set": {
                        "status": "rejected",
                        "approved_at": datetime.now(),
                        "approved_by": approver_username
                    }
                }
            )
            
            if result.modified_count > 0:
                return True, "User request rejected successfully"
            else:
                return False, "Failed to reject user request"
                
        except Exception as e:
            return False, f"Error rejecting user: {str(e)}"
    
    def ignore_user(self, user_id, approver_username):
        """Ignore a pending user request (mark as ignored for later review)."""
        try:
            result = self.users_collection.update_one(
                {"_id": user_id, "status": "pending"},
                {
                    "$set": {
                        "status": "ignored",
                        "ignored_at": datetime.now(),
                        "ignored_by": approver_username
                    }
                }
            )
            
            if result.modified_count > 0:
                return True, "User request ignored successfully"
            else:
                return False, "Failed to ignore user request"
                
        except Exception as e:
            return False, f"Error ignoring user: {str(e)}"
    
    def create_user_directly(self, username, email_prefix, first_name, last_name, wwid, role, 
                           manual_password=None, password_change_required=True, created_by="admin", 
                           send_email=True):
        """Create a user directly without approval process (admin only)."""
        try:
            # Validate email
            is_valid, final_email = self._validate_email(email_prefix)
            if not is_valid:
                return False, final_email
            
            # Check if username already exists
            if self.users_collection.find_one({"username": username}):
                return False, "Username already exists"
            
            # Check if email already exists
            if self.users_collection.find_one({"email": final_email}):
                return False, "Email already registered"
            
            # Check if WWID already exists
            if self.users_collection.find_one({"wwid": wwid}):
                return False, "WWID already registered"
            
            # Generate or use provided password
            if manual_password:
                password = manual_password
            else:
                password = self._generate_password(4)
            
            hashed_password = self._hash_password(password)
            
            # Create new user directly as approved
            user_data = {
                "uuid": str(uuid.uuid4()),
                "username": username,
                "email": final_email,
                "first_name": first_name,
                "last_name": last_name,
                "wwid": wwid,
                "role": role,
                "status": "approved",
                "password": hashed_password,
                "created_at": datetime.now(),
                "approved_at": datetime.now(),
                "approved_by": created_by,
                "password_change_required": password_change_required,
                "created_manually": True
            }
            
            # Insert into database
            result = self.users_collection.insert_one(user_data)
            
            if result.inserted_id:
                # Try to send welcome email if requested
                if send_email:
                    try:
                        self._send_approval_email(final_email, username, password)
                    except:
                        pass  # Don't fail user creation if email fails
                
                return True, f"User created successfully! Username: {username}, Password: {password}"
            else:
                return False, "Failed to create user"
                
        except Exception as e:
            return False, f"Error creating user: {str(e)}"
    
    def change_user_password(self, username, new_password, is_admin=False, target_username=None):
        """Change password for a user."""
        try:
            # If admin is changing another user's password
            if is_admin and target_username:
                username_to_update = target_username
            else:
                username_to_update = username
            
            hashed_password = self._hash_password(new_password)
            
            result = self.users_collection.update_one(
                {"username": username_to_update},
                {
                    "$set": {
                        "password": hashed_password,
                        "password_change_required": False,
                        "password_changed_at": datetime.now(),
                        "password_changed_by": username
                    }
                }
            )
            
            if result.modified_count > 0:
                return True, "Password changed successfully"
            else:
                return False, "Failed to change password"
                
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
    
    def is_manager_user(self, username):
        """Check if user is manager or admin."""
        role = self.get_user_role(username)
        return role in ["admin", "manager"]
    
    def is_tech_user(self, username):
        """Check if user is technician, tech, manager, or admin."""
        role = self.get_user_role(username)
        return role in ["admin", "manager", "technician", "tech"]
    
    def get_user_info(self, username):
        """Get full user information from database."""
        return self.users_collection.find_one({"username": username, "status": "approved"})
    
    def user_needs_password_change(self, username):
        """Check if user needs to change password."""
        user = self.get_user_info(username)
        return user.get("password_change_required", False) if user else False
    
    def signup_page(self):
        """Display the signup page."""
        st.markdown("## 📝 Sign Up for Account Access")
        st.markdown("---")
        
        # Check if signup was just completed
        if st.session_state.get('signup_completed', False):
            st.success("✅ Signup request submitted successfully!")
            st.info("🔄 Please wait for admin approval. You will receive an email with your login credentials once approved.")
            st.info("💡 Your request has been sent to the system administrator.")
            st.info("📧 You can close this page or refresh to return to the login screen.")
            
            # Add return to login button
            if st.button("🔙 Return to Login"):
                st.session_state.signup_completed = False
                st.session_state.show_signup = False
                st.rerun()
            return
        
        with st.form("signup_form"):
            st.markdown("### User Information")
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input("First Name *", placeholder="Enter your first name")
                email_prefix = st.text_input("Email (Username) *", 
                                           placeholder="Enter username part (before @altera.com)")
            
            with col2:
                last_name = st.text_input("Last Name *", placeholder="Enter your last name")
                wwid = st.text_input("WWID *", placeholder="Enter your WWID")
            
            username = st.text_input("System Username *", 
                                   placeholder="Enter preferred system username")
            
            requested_role = st.selectbox("Requested Role", 
                                        self.VALID_ROLES,
                                        help="Select the role you are requesting. Admin approval required.")
            
            st.markdown("### Password (Optional)")
            st.info("💡 You can set your own password now, or let the admin generate one for you after approval.")
            
            col3, col4 = st.columns(2)
            with col3:
                user_password = st.text_input("Password (Optional)", 
                                            type="password",
                                            placeholder="Enter your preferred password",
                                            help="Leave empty to have admin generate a password for you")
            with col4:
                confirm_password = st.text_input("Confirm Password", 
                                                type="password",
                                                placeholder="Confirm your password",
                                                help="Only needed if you entered a password above")
            
            submit_button = st.form_submit_button("📤 Submit Request")
            
            if submit_button:
                # Validate required fields
                if not all([first_name, last_name, username, email_prefix, wwid]):
                    st.error("❌ Please fill in all required fields!")
                    return
                
                # Validate password if provided
                if user_password and not confirm_password:
                    st.error("❌ Please confirm your password!")
                    return
                
                if user_password and user_password != confirm_password:
                    st.error("❌ Passwords do not match!")
                    return
                
                if user_password and len(user_password.strip()) < 3:
                    st.error("❌ Password must be at least 3 characters long!")
                    return
                
                # Clean inputs
                first_name = first_name.strip()
                last_name = last_name.strip()
                username = username.strip().lower()
                email_prefix = email_prefix.strip().lower()
                wwid = wwid.strip().upper()
                clean_password = user_password.strip() if user_password else None
                
                # Create signup request
                success, message = self.create_signup_request(
                    username, email_prefix, first_name, last_name, wwid, requested_role, clean_password
                )
                
                if success:
                    st.session_state.signup_completed = True
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
        
        # Back to login
        if st.button("🔙 Back to Login"):
            st.session_state.show_signup = False
            st.session_state.signup_completed = False
            st.rerun()
    
    def forgot_password_page(self):
        """Display forgot password page."""
        st.markdown("## 🔑 Reset Your Password")
        st.markdown("---")
        
        # Check if password reset request was just completed
        if st.session_state.get('password_reset_requested', False):
            st.success("✅ Password reset request submitted!")
            st.info("� Please check your email for a password reset link.")
            st.info("💡 Click the link in the email to receive your temporary password.")
            st.info("⏰ The reset link will expire in 24 hours for security.")
            
            # Add return to login button
            if st.button("🔙 Return to Login"):
                st.session_state.password_reset_requested = False
                st.session_state.show_forgot_password = False
                st.rerun()
            return
        
        with st.form("forgot_password_form"):
            st.markdown("### Reset Password Information")
            st.info("📋 Please provide either your username or email address to reset your password.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                username_input = st.text_input("Username", placeholder="Enter your username")
            
            with col2:
                email_input = st.text_input("Email", placeholder="Enter your email (username@altera.com)")
            
            submit_button = st.form_submit_button("🔄 Reset Password")
            
            if submit_button:
                # Validate at least one field is provided
                if not username_input and not email_input:
                    st.error("❌ Please provide either username or email!")
                    return
                
                # Clean inputs
                clean_username = username_input.strip().lower() if username_input else None
                clean_email = email_input.strip().lower() if email_input else None
                
                # Try to find user
                user = None
                if clean_username:
                    user = self.users_collection.find_one({"username": clean_username, "status": "approved"})
                
                if not user and clean_email:
                    # Validate and format email
                    if '@' not in clean_email:
                        clean_email = f"{clean_email}@altera.com"
                    user = self.users_collection.find_one({"email": clean_email, "status": "approved"})
                
                if user:
                    # Create password reset request (don't reset password yet)
                    success, message = self._create_password_reset_request(user['username'], user['email'])
                    if success:
                        st.session_state.password_reset_requested = True
                        st.rerun()
                    else:
                        st.error("❌ Failed to send password reset email. Please try again or contact admin.")
                else:
                    st.error("❌ User not found! Please check your username or email.")
        
        # Back to login
        if st.button("🔙 Back to Login"):
            st.session_state.show_forgot_password = False
            st.rerun()
    
    def admin_approval_page(self):
        """Display admin approval page for pending users."""
        if not self.is_admin_user(st.session_state.username):
            st.error("❌ Access denied. Admin privileges required.")
            return
        
        st.markdown("## 👥 User Management - Pending Approvals")
        st.markdown("---")
        
        # Show persistent messages
        if st.session_state.get('approval_message'):
            st.success(st.session_state.approval_message)
            st.balloons()
            # Clear the message after showing it
            del st.session_state.approval_message
        
        if st.session_state.get('rejection_message'):
            st.success(st.session_state.rejection_message)
            # Clear the message after showing it
            del st.session_state.rejection_message
        
        if st.session_state.get('ignore_message'):
            st.info(st.session_state.ignore_message)
            # Clear the message after showing it
            del st.session_state.ignore_message
        
        # Get pending users
        pending_users = self.get_pending_users()
        
        if not pending_users:
            st.info("✅ No pending user requests.")
            return
        
        for user in pending_users:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    # Check if user provided their own password
                    password_status = "✅ Own password" if user.get('user_provided_password', False) else "🔄 Will generate"
                    
                    st.markdown(f"""
                    **{user['first_name']} {user['last_name']}**  
                    Username: `{user['username']}`  
                    Email: {user['email']}  
                    WWID: {user['wwid']}  
                    Requested Role: **{user['requested_role']}**  
                    Password: {password_status}  
                    Requested: {user['created_at'].strftime('%Y-%m-%d %H:%M')}
                    """)
                
                with col2:
                    # Role selection dropdown with requested role as default
                    role_options = self.VALID_ROLES
                    requested_role = user.get('requested_role', 'user')
                    try:
                        default_index = role_options.index(requested_role)
                    except ValueError:
                        default_index = 2  # Default to 'user' if requested role not found
                    
                    selected_role = st.selectbox(
                        "Assign Role",
                        role_options,
                        index=default_index,
                        key=f"role_select_{user['_id']}",
                        help="Choose the role to assign to this user"
                    )
                    
                    if st.button(f"✅ Approve", key=f"approve_{user['_id']}"):
                        success, message = self.approve_user(user['_id'], st.session_state.username, selected_role)
                        if success:
                            st.success(message)
                            st.balloons()  # Add celebration animation
                            # Store success message to show after rerun
                            st.session_state.approval_message = f"✅ {message}"
                            time.sleep(2)  # Give time to see the balloons
                            st.rerun()
                        else:
                            st.error(message)
                
                with col3:
                    if st.button(f"❌ Reject", key=f"reject_{user['_id']}"):
                        success, message = self.reject_user(user['_id'], st.session_state.username)
                        if success:
                            st.success(message)
                            st.session_state.rejection_message = f"✅ {message}"
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
                
                with col4:
                    if st.button(f"⏸️ Ignore", key=f"ignore_{user['_id']}"):
                        success, message = self.ignore_user(user['_id'], st.session_state.username)
                        if success:
                            st.info(message)
                            st.session_state.ignore_message = f"ℹ️ {message}"
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
                
                st.markdown("---")
    
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
        
        # Show success message if password was just changed
        if st.session_state.get('password_change_success'):
            st.info("💡 Password changed successfully! You can now use your new password.")
            # Clear the flag after a few seconds or on next interaction
            if st.button("🔄 Continue"):
                st.session_state.password_change_success = False
                st.rerun()
    
    def user_management_page(self):
        """Display user management page for admins."""
        if not self.is_admin_user(st.session_state.username):
            st.error("❌ Access denied. Admin privileges required.")
            return
        
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
                                            self._send_approval_email(user['email'], user['username'], new_pwd)
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
            self.admin_approval_page()
        
        with tab3:
            self.password_change_page()
        
        with tab4:
            # Create User Tab
            st.markdown("### ➕ Create User Manually")
            st.markdown("---")
            
            with st.form("create_user_form"):
                st.markdown("#### User Information")
                col1, col2 = st.columns(2)
                
                with col1:
                    first_name = st.text_input("First Name *", placeholder="Enter first name")
                    email_prefix = st.text_input("Email (Username Part) *", 
                                               placeholder="Enter username part (before @altera.com)")
                    wwid = st.text_input("WWID *", placeholder="Enter WWID")
                
                with col2:
                    last_name = st.text_input("Last Name *", placeholder="Enter last name")
                    username = st.text_input("System Username *", placeholder="Enter system username")
                    role = st.selectbox("Role *", 
                                      self.VALID_ROLES,
                                      help="Select the user's role")
                
                st.markdown("#### Password Settings")
                col3, col4 = st.columns(2)
                
                with col3:
                    password_option = st.radio("Password Option", 
                                             ["Generate automatically", "Set manually"])
                
                with col4:
                    manual_password = st.text_input("Password", 
                                                   placeholder="Enter password (leave empty for auto-generation)",
                                                   help="Enter a password or leave empty to auto-generate")
                
                st.markdown("#### Notification Settings")
                col5, col6 = st.columns(2)
                
                with col5:
                    password_change_required = st.checkbox("Require password change on first login", 
                                                          value=True)
                
                with col6:
                    send_email_notification = st.checkbox("Send email notification to user", 
                                                         value=True,
                                                         help="Send welcome email with login credentials to the user")
                
                create_button = st.form_submit_button("👤 Create User")
                
                if create_button:
                    # Validate required fields
                    if not all([first_name, last_name, username, email_prefix, wwid]):
                        st.error("❌ Please fill in all required fields!")
                    elif password_option == "Set manually" and not manual_password:
                        st.error("❌ Please enter a password!")
                    else:
                        # Clean password input by removing leading and trailing whitespace
                        cleaned_password = manual_password.strip() if manual_password else None
                        
                        # Create user directly (bypass approval process)
                        success, message = self.create_user_directly(
                            username=username.strip().lower(),
                            email_prefix=email_prefix.strip().lower(),
                            first_name=first_name.strip(),
                            last_name=last_name.strip(),
                            wwid=wwid.strip().upper(),
                            role=role,
                            manual_password=cleaned_password,
                            password_change_required=password_change_required,
                            created_by=st.session_state.username,
                            send_email=send_email_notification
                        )
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.balloons()
                        else:
                            st.error(f"❌ {message}")
            
            st.markdown("---")
            st.markdown("**💡 User Creation Notes:**")
            st.info("""
            - Users created manually are automatically approved and active
            - Generated passwords are 4 characters long (letters and numbers)
            - Users will receive email notifications if email is configured
            - All fields marked with * are required
            - Email will be automatically formatted as @altera.com
            """)
    
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
            if not self.cookie_controller:
                st.warning("⚠️ Cookie controller not available. Using session state only.")
                return True  # Return True to continue without cookies
            
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
            
            # Save to file for true persistence
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
        """Load session from cookies."""
        try:
            if not self.cookie_controller:
                # If cookie controller is not available, try to load from session state only
                if hasattr(st.session_state, 'session_id') and st.session_state.session_id:
                    # Session already loaded in session state
                    return True
                return False
            
            session_token = self.cookie_controller.get("session_token")
            if session_token:
                # First reload sessions from file to get latest state
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
                    # No session found but we have a cookie - clean up the orphaned cookie
                    try:
                        if self.cookie_controller:
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
            
            # Remove from file storage
            self._save_sessions_to_file()
            
            # Remove cookie
            try:
                if self.cookie_controller:
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
        
        # Check for password reset token in URL parameters
        query_params = st.query_params
        if "reset_token" in query_params:
            reset_token = query_params["reset_token"]
            if reset_token:
                success, message = self.process_password_reset_token(reset_token)
                if success:
                    st.success(f"✅ {message}")
                    st.info("💡 Please check your email for the temporary password.")
                    # Clear the reset token from URL
                    st.query_params.clear()
                else:
                    st.error(f"❌ {message}")
        
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
        
        st.markdown(f'<h1 class="login-header">🔬 {self.login_title}</h1>', unsafe_allow_html=True)
        st.markdown('<h3 style="text-align: center; color: #666;">Management System</h3>', unsafe_allow_html=True)
        
        # Add a visible separator
        st.markdown("---")
        
        # Check if signup should be shown
        if st.session_state.get('show_signup', False):
            self.signup_page()
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
                    # Trim whitespace from username and password
                    clean_username = username.strip()
                    clean_password = password.strip()
                    
                    if self._verify_password(clean_username, clean_password):
                        user_info = self.get_user_info(clean_username)
                        if user_info:
                            # Save session with cookies
                            if self.save_session(clean_username, user_info["role"]):
                                display_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
                                if not display_name:
                                    display_name = clean_username
                                st.success(f"Welcome, {display_name}!")
                                time.sleep(1)  # Small delay to show success message
                                st.rerun()
                            else:
                                st.error("❌ Failed to create session. Please try again.")
                        else:
                            st.error("❌ User not found or not approved!")
                    else:
                        st.error("❌ Invalid username or password!")
                else:
                    st.warning("⚠️ Please enter both username and password!")
        
        # Signup option and Forgot Password
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("� Request Account Access"):
                st.session_state.show_signup = True
                st.rerun()
        
        # Forgot Password button below signup
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("� Forgot Password"):
                st.session_state.show_forgot_password = True
                st.rerun()
        
        # Check if forgot password should be shown
        if st.session_state.get('show_forgot_password', False):
            self.forgot_password_page()
            return
        
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
        
        # Force rerun to redirect to login page
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
            session_duration = time.time() - login_time
            # Session expires after 24 hours (86400 seconds)
            if session_duration > 86400:
                # Clear session and force rerun
                st.session_state.authenticated = False
                st.session_state.username = None
                st.session_state.user_role = None
                st.session_state.login_time = None
                st.session_state.session_id = None
                st.session_state.session_persistent = False
                st.rerun()
                return False
        
        # Verify user still exists in system
        user_info = self.get_user_info(username)
        if not user_info:
            # Clear session and force rerun
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.user_role = None
            st.session_state.login_time = None
            st.session_state.session_id = None
            st.session_state.session_persistent = False
            st.rerun()
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
    
    def display_header(self, main_page_title="🔬 Equipment Management System"):
        """Display header with user info and logout."""
        # User info and logout in a container
        st.markdown('<div class="user-header">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            user_info = self.get_user_info(st.session_state.username)
            if user_info:
                display_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
                if not display_name:
                    display_name = st.session_state.username
                # Calculate session duration
                if st.session_state.login_time:
                    session_duration = time.time() - st.session_state.login_time
                    hours = int(session_duration // 3600)
                    minutes = int((session_duration % 3600) // 60)
                    session_info = f" (Session: {hours}h {minutes}m)" if hours > 0 or minutes > 0 else " (Just logged in)"
                else:
                    session_info = ""
                
                st.markdown(f"👤 **{display_name}** ({user_info['role'].title()}){session_info}")
            else:
                st.markdown(f"👤 **{st.session_state.username}** (Unknown Role)")
        
        with col2:
            if st.button("🔐 Change Password", key="change_password_btn"):
                st.session_state.show_password_change = True
                st.rerun()
        
        with col3:
            if st.button("🚪 Logout", key="logout_btn"):
                self.logout()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Show password change modal if requested
        if st.session_state.get('show_password_change', False):
            self._display_password_change_modal()
        
        # Main title
        st.markdown(f'<h1 class="main-header">{main_page_title}</h1>', unsafe_allow_html=True)
    
    def _display_password_change_modal(self):
        """Display a modal for changing password."""
        st.markdown("---")
        st.markdown("## 🔐 Change Your Password")
        
        with st.form("user_password_change_form"):
            st.markdown("### Update Your Password")
            
            col1, col2 = st.columns(2)
            with col1:
                current_password = st.text_input("Current Password", type="password", 
                                               placeholder="Enter your current password")
            with col2:
                new_password = st.text_input("New Password", type="password", 
                                           placeholder="Enter new password")
            
            confirm_password = st.text_input("Confirm New Password", type="password", 
                                           placeholder="Confirm new password")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                change_button = st.form_submit_button("🔄 Change Password")
            with col2:
                cancel_button = st.form_submit_button("❌ Cancel")
            
            if cancel_button:
                st.session_state.show_password_change = False
                st.rerun()
            
            if change_button:
                # Validate inputs
                if not all([current_password, new_password, confirm_password]):
                    st.error("❌ Please fill in all fields!")
                elif new_password != confirm_password:
                    st.error("❌ New passwords do not match!")
                elif len(new_password) < 3:
                    st.error("❌ New password must be at least 3 characters long!")
                elif current_password.strip() == new_password.strip():
                    st.error("❌ New password must be different from current password!")
                else:
                    # Verify current password first
                    clean_current = current_password.strip()
                    clean_new = new_password.strip()
                    
                    if self._verify_password(st.session_state.username, clean_current):
                        # Change password
                        success, message = self.change_user_password(
                            st.session_state.username, clean_new, False, None
                        )
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.session_state.show_password_change = False
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.error("❌ Current password is incorrect!")
        
        st.markdown("---")
    
    def _create_password_reset_request(self, username, user_email):
        """Create a password reset request and send email with reset link."""
        try:
            # Generate reset token
            reset_token = str(uuid.uuid4())
            reset_expiry = datetime.now() + timedelta(hours=24)  # 24 hour expiry
            
            # Store reset request in database
            result = self.users_collection.update_one(
                {"username": username, "status": "approved"},
                {
                    "$set": {
                        "password_reset_token": reset_token,
                        "password_reset_expiry": reset_expiry,
                        "password_reset_requested_at": datetime.now()
                    }
                }
            )
            
            if result.modified_count > 0:
                # Send reset email with link
                self._send_password_reset_request_email(user_email, username, reset_token)
                return True, "Reset email sent successfully"
            else:
                return False, "Failed to create reset request"
                
        except Exception as e:
            return False, f"Error creating reset request: {str(e)}"
    
    def _send_password_reset_request_email(self, user_email, username, reset_token):
        """Send password reset request email with clickable link."""
        if not EMAIL_CONFIGURED:
            return  # Skip email if not configured
            
        try:
            # Create reset link (you can customize this URL to your system)
            reset_link = f"{SYSTEM_URL}?reset_token={reset_token}"
            
            # Email body
            subject = "🔑 Password Reset Request - Equipment Management System"
            body = (
                f"Dear {username},\n\n"
                f"You have requested a password reset for the Equipment Management System.\n\n"
                f"To reset your password, please click the following link:\n"
                f"{reset_link}\n\n"
                f"This link will:\n"
                f"- Generate a temporary password for you\n"
                f"- Allow you to log in and set a new permanent password\n"
                f"- Expire in 24 hours for security\n\n"
                f"If you did not request this password reset, please ignore this email.\n"
                f"Your current password will remain unchanged.\n\n"
                f"For security reasons:\n"
                f"- Do not share this link with anyone\n"
                f"- The link can only be used once\n"
                f"- Change your password immediately after logging in\n\n"
                f"If you have any issues, please contact your system administrator.\n\n"
                f"Best regards,\n"
                f"Equipment Management System"
            )
            
            # Create message using Intel SMTP approach
            msg = MIMEText(body, _subtype="plain", _charset="utf-8")
            msg["Subject"] = subject
            msg["From"] = SYSTEM_EMAIL
            msg["To"] = user_email
            
            # Send email using Intel SMTP (simple and proven)
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.send_message(msg)
                
        except Exception as e:
            # Don't fail the reset process if email fails
            pass

    def process_password_reset_token(self, reset_token):
        """Process password reset token when user clicks the email link."""
        try:
            # Find user with valid reset token
            user = self.users_collection.find_one({
                "password_reset_token": reset_token,
                "password_reset_expiry": {"$gt": datetime.now()},
                "status": "approved"
            })
            
            if user:
                # Generate temporary password
                temp_password = self._generate_password(6)
                hashed_password = self._hash_password(temp_password)
                
                # Update user with temporary password and clear reset token
                result = self.users_collection.update_one(
                    {"_id": user["_id"]},
                    {
                        "$set": {
                            "password": hashed_password,
                            "password_change_required": True,
                            "password_reset_completed_at": datetime.now(),
                            "temp_password_issued": True
                        },
                        "$unset": {
                            "password_reset_token": "",
                            "password_reset_expiry": ""
                        }
                    }
                )
                
                if result.modified_count > 0:
                    # Send email with temporary password
                    self._send_temporary_password_email(user["email"], user["username"], temp_password)
                    return True, f"Temporary password sent to {user['email']}"
                else:
                    return False, "Failed to reset password"
            else:
                return False, "Invalid or expired reset token"
                
        except Exception as e:
            return False, f"Error processing reset token: {str(e)}"
    
    def _send_temporary_password_email(self, user_email, username, temp_password):
        """Send temporary password email to user."""
        if not EMAIL_CONFIGURED:
            return  # Skip email if not configured
            
        try:
            # Email body
            subject = "🔑 Temporary Password - Equipment Management System"
            body = (
                f"Dear {username},\n\n"
                f"Your password reset request has been processed.\n\n"
                f"👤 Username: {username}\n"
                f"🔑 Temporary Password: {temp_password}\n\n"
                f"IMPORTANT SECURITY INSTRUCTIONS:\n"
                f"1. Log in using this temporary password\n"
                f"2. Change your password IMMEDIATELY after logging in\n"
                f"3. This temporary password will expire after first use\n"
                f"4. Do not share this password with anyone\n\n"
                f"System URL: {SYSTEM_URL}\n\n"
                f"If you did not request this password reset, please contact your administrator immediately.\n\n"
                f"Best regards,\n"
                f"Equipment Management System"
            )
            
            # Create message using Intel SMTP approach
            msg = MIMEText(body, _subtype="plain", _charset="utf-8")
            msg["Subject"] = subject
            msg["From"] = SYSTEM_EMAIL
            msg["To"] = user_email
            
            # Send email using Intel SMTP (simple and proven)
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.send_message(msg)
                
        except Exception as e:
            # Don't fail the reset process if email fails
            pass

    def _reset_user_password(self, username):
        """Reset user password and return new password."""
        try:
            # Generate new password
            new_password = self._generate_password(6)  # Slightly longer for security
            hashed_password = self._hash_password(new_password)
            
            # Update password in database
            result = self.users_collection.update_one(
                {"username": username, "status": "approved"},
                {
                    "$set": {
                        "password": hashed_password,
                        "password_change_required": True,  # Force user to change on next login
                        "password_reset_at": datetime.now(),
                        "password_reset_by": "forgot_password_system"
                    }
                }
            )
            
            if result.modified_count > 0:
                # Get user info for email notification
                user_info = self.get_user_info(username)
                if user_info:
                    # Try to send email notification if configured
                    try:
                        self._send_password_reset_email(user_info['email'], username, new_password)
                    except:
                        pass  # Don't fail the reset if email fails
                
                return True, new_password
            else:
                return False, None
                
        except Exception as e:
            return False, None
    
    def _send_password_reset_email(self, user_email, username, new_password):
        """Send password reset email to user."""
        if not EMAIL_CONFIGURED:
            return  # Skip email if not configured
            
        try:
            # Email body
            subject = "🔑 Password Reset - Equipment Management System"
            body = (
                f"Dear {username},\n\n"
                f"Your password has been reset for the Equipment Management System.\n\n"
                f"👤 Username: {username}\n"
                f"🔑 New Password: {new_password}\n\n"
                f"IMPORTANT: \n"
                f"- Please change this password immediately after logging in\n"
                f"- This password was generated automatically for security\n"
                f"- Do not share this password with anyone\n\n"
                f"System URL: {SYSTEM_URL}\n\n"
                f"If you did not request this password reset, please contact your administrator immediately.\n\n"
                f"Best regards,\n"
                f"Equipment Management System"
            )
            
            # Create message using Intel SMTP approach
            msg = MIMEText(body, _subtype="plain", _charset="utf-8")
            msg["Subject"] = subject
            msg["From"] = SYSTEM_EMAIL
            msg["To"] = user_email
            
            # Send email using Intel SMTP (simple and proven)
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.send_message(msg)
                
        except Exception as e:
            # Don't fail the reset process if email fails
            pass
    
    def is_authenticated(self):
        """Check if user is currently authenticated."""
        return st.session_state.get('authenticated', False)
    
    def get_current_user(self):
        """Get current user information."""
        username = st.session_state.get('username')
        if username:
            return self.get_user_info(username)
        return None


# Convenience functions for backward compatibility
def create_auth_manager(login_title="Altera Lab Equipment"):
    """Create and return an AuthenticationManager instance."""
    return AuthenticationManager(login_title)


# Example usage if run directly
if __name__ == "__main__":
    st.set_page_config(
        page_title="Login - Equipment Management",
        page_icon="🔐",
        layout="centered"
    )
    
    auth_manager = AuthenticationManager()
    
    if not auth_manager.is_authenticated():
        auth_manager.login_page()
    else:
        auth_manager.display_header()
        st.success("You are logged in!")
        st.write("This is a demo of the authentication system.")
