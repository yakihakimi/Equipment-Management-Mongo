# Email Configuration for Equipment Management System
# Copy this file to email_config.py and update with your actual settings

# SMTP Server Settings
SMTP_SERVER = "smtp.altera.com"  # Your company's SMTP server
SMTP_PORT = 25  # Usually 587 for TLS, 465 for SSL, 25 for non-encrypted

# Email Accounts
SYSTEM_EMAIL = "yakov.yosef.hakimi@altera.com"  # System sender email
SYSTEM_PASSWORD = ""    # App password or email password (leave empty for passwordless)
ADMIN_EMAIL = "yakov.yosef.hakimi@altera.com"  # Admin email for notifications

# System Settings
SYSTEM_URL = "http://10.13.64.134:8501"    # URL where the system is hosted
SYSTEM_NAME = "Altera Lab Equipment Management System"

# Notification Settings
USE_FILE_NOTIFICATIONS = False  # Set to True to use file-based notifications instead of real email
NOTIFICATIONS_DIR = "email_notifications"  # Directory for file-based notifications

# Email Templates
APPROVAL_REQUEST_SUBJECT = "New User Access Request - {username}"
APPROVAL_NOTIFICATION_SUBJECT = "Equipment Management System - Account Approved"

# Security Notes:
# 1. Never commit this file with real passwords to version control
# 2. Use app passwords instead of regular email passwords when possible
# 3. Consider using environment variables for sensitive information
# 4. Enable 2FA on the system email account

# Example for using environment variables instead:
# import os
# SYSTEM_PASSWORD = os.getenv('EQUIPMENT_SYSTEM_EMAIL_PASSWORD')
