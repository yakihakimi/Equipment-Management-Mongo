#!/usr/bin/env python3
"""
Test script for Equipment Management System approval emails.
Tests both signup request and approval emails using Intel SMTP.
"""

import smtplib
from email.mime.text import MIMEText
from datetime import datetime

def test_signup_request_email():
    """Test the signup request notification email."""
    print("🔄 Testing signup request notification...")
    
    # Configuration
    smtp_server = "sc-out.intel.com"
    smtp_port = 25
    sender_email = "yakov.yosef.hakimi@intel.com"
    admin_email = "yakov.yosef.hakimi@altera.com"
    
    # Sample user data
    user_data = {
        'username': 'test_user',
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@altera.com',
        'wwid': 'TEST123',
        'requested_role': 'technician',
        'created_at': datetime.now()
    }
    
    try:
        # Email body (same as in the app)
        body = f"""
A new user has requested access to the Altera Lab Equipment Management System:

Name: {user_data['first_name']} {user_data['last_name']}
Username: {user_data['username']}
Email: {user_data['email']}
WWID: {user_data['wwid']}
Requested Role: {user_data['requested_role']}
Request Date: {user_data['created_at'].strftime('%Y-%m-%d %H:%M:%S')}

Please log into the Altera Lab Equipment Management System to approve or reject this request.

System URL: http://localhost:8501

This is an automated message from the Altera Lab Equipment Management System.
        """
        
        # Create message
        subject = f"New User Access Request - {user_data['username']}"
        msg = MIMEText(body, _subtype="plain", _charset="utf-8")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = admin_email
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.send_message(msg)
        
        print("✅ Signup request email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Signup request email failed: {str(e)}")
        return False

def test_approval_email():
    """Test the user approval email."""
    print("🔄 Testing user approval email...")
    
    # Configuration
    smtp_server = "sc-out.intel.com"
    smtp_port = 25
    sender_email = "yakov.yosef.hakimi@intel.com"
    user_email = "yakov.yosef.hakimi@altera.com"  # Your email for testing
    
    # Sample approval data
    username = "test_user"
    password = "abc123"
    
    try:
        # Email body (same format as in your working app)
        subject = "✅ Access Approved"
        body = (
            f"Dear {username},\n\n"
            f"Your access request for the Altera Lab Equipment Management System has been approved.\n\n"
            f"👤 Username: {username}\n"
            f"🔑 Password: {password} (please change it after logging in)\n\n"
            f"System URL: http://localhost:8501\n\n"
            f"IMPORTANT: You will be required to change your password on first login.\n\n"
            f"Best,\nAdmin"
        )
        
        # Create message
        msg = MIMEText(body, _subtype="plain", _charset="utf-8")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = user_email
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.send_message(msg)
        
        print("✅ Approval email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Approval email failed: {str(e)}")
        return False

def test_email_test_function():
    """Test the email test functionality."""
    print("🔄 Testing email test function...")
    
    # Configuration
    smtp_server = "sc-out.intel.com"
    smtp_port = 25
    sender_email = "yakov.yosef.hakimi@intel.com"
    admin_email = "yakov.yosef.hakimi@altera.com"
    
    try:
        # Email body
        subject = "Test Email from Altera Lab Equipment Management System"
        body = (
            f"This is a test email from the Altera Lab Equipment Management System.\n\n"
            f"Email configuration test successful!\n\n"
            f"Test Details:\n"
            f"- SMTP Server: {smtp_server}\n"
            f"- SMTP Port: {smtp_port}\n"
            f"- System Email: {sender_email}\n"
            f"- Admin Email: {admin_email}\n"
            f"- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"If you receive this email, the email configuration is working correctly.\n\n"
            f"This is an automated test message from the Altera Lab Equipment Management System."
        )
        
        # Create message
        msg = MIMEText(body, _subtype="plain", _charset="utf-8")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = admin_email
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.send_message(msg)
        
        print("✅ Test email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test email failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Equipment Management Email System Test")
    print("Testing all email functions with Intel SMTP...")
    print("=" * 60)
    
    results = []
    
    # Test all email functions
    print("1️⃣ Testing signup request notification...")
    results.append(test_signup_request_email())
    print()
    
    print("2️⃣ Testing user approval email...")
    results.append(test_approval_email())
    print()
    
    print("3️⃣ Testing email test function...")
    results.append(test_email_test_function())
    print()
    
    # Summary
    print("=" * 60)
    print("📊 TEST RESULTS:")
    print(f"✅ Passed: {sum(results)}/3")
    print(f"❌ Failed: {3 - sum(results)}/3")
    
    if all(results):
        print()
        print("🎉 ALL TESTS PASSED!")
        print("🎯 Your Equipment Management System is ready for email notifications!")
        print("📧 Check your email inbox for the test messages.")
    else:
        print()
        print("⚠️ Some tests failed. Check the error messages above.")
        print("💡 Ensure you're on the Intel/Altera network and email settings are correct.")
