#!/usr/bin/env python3
"""
Test the hybrid email system (real email + file notification)
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Load configuration
try:
    from email_config import (
        SMTP_SERVER, SMTP_PORT, SYSTEM_EMAIL, ADMIN_EMAIL, SYSTEM_NAME,
        SMTP_USE_TLS, SMTP_USE_AUTH, USE_FILE_NOTIFICATIONS, NOTIFICATIONS_DIR
    )
    from file_email_notifier import FileEmailNotifier
    print("✅ Hybrid configuration loaded")
    print(f"   Real Email: SMTP {SMTP_SERVER}:{SMTP_PORT}")
    print(f"   File Notifications: {'Enabled' if USE_FILE_NOTIFICATIONS else 'Disabled'}")
except ImportError as e:
    print(f"❌ Failed to load configuration: {e}")
    exit(1)

def test_hybrid_email():
    """Test both real email and file notification."""
    subject = f"HYBRID TEST from {SYSTEM_NAME}"
    body = f"""
Hello Yakov,

This is a HYBRID test from the Equipment Management System.

Test Details:
- Sent via: BOTH real email AND file notification
- Sent from: {SYSTEM_EMAIL}
- Sent to: {ADMIN_EMAIL}
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Purpose: Ensure you get notifications even if email delivery has issues

If you see this in either your email OR the file notifications, the system is working!

Check:
1. Your Altera email inbox (may take 15-30 minutes)
2. Spam/junk folder
3. Admin panel → Email Test tab for file notifications

Best regards,
Equipment Management System
    """
    
    email_success = False
    file_success = False
    
    # Test real email
    try:
        print("📧 Sending real email...")
        msg = MIMEMultipart()
        msg['From'] = SYSTEM_EMAIL
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        if SMTP_USE_TLS:
            server.starttls()
        if SMTP_USE_AUTH:
            print("⚠️ Auth needed but no credentials provided")
        
        server.sendmail(SYSTEM_EMAIL, ADMIN_EMAIL, msg.as_string())
        server.quit()
        
        print("✅ Real email sent successfully!")
        email_success = True
        
    except Exception as e:
        print(f"❌ Real email failed: {e}")
    
    # Test file notification
    try:
        print("📁 Saving file notification...")
        notifier = FileEmailNotifier(NOTIFICATIONS_DIR)
        success, message = notifier.send_email(
            to_email=ADMIN_EMAIL,
            subject=subject,
            body=body,
            from_email=SYSTEM_EMAIL
        )
        
        if success:
            print("✅ File notification saved successfully!")
            file_success = True
        else:
            print(f"❌ File notification failed: {message}")
            
    except Exception as e:
        print(f"❌ File notification error: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 HYBRID TEST RESULTS:")
    print(f"📧 Real Email: {'✅ SUCCESS' if email_success else '❌ FAILED'}")
    print(f"📁 File Notification: {'✅ SUCCESS' if file_success else '❌ FAILED'}")
    
    if email_success and file_success:
        print("🎉 BOTH methods working - you'll get notified either way!")
    elif email_success:
        print("📧 Only real email working - check your inbox in 15-30 minutes")
    elif file_success:
        print("📁 Only file notifications working - check Admin panel for notifications")
    else:
        print("❌ Both methods failed - check configuration")
    
    print("=" * 50)

if __name__ == "__main__":
    test_hybrid_email()
