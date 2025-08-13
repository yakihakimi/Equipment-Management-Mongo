#!/usr/bin/env python3
"""
Test script for Intel SMTP email delivery.
Tests the exact implementation that worked in your other app.
"""

import smtplib
from email.mime.text import MIMEText
from datetime import datetime

def test_intel_smtp():
    """Test Intel SMTP server with the exact configuration that worked."""
    print("🔄 Testing Intel SMTP email delivery...")
    print("=" * 50)
    
    # Configuration from your working app
    smtp_server = "sc-out.intel.com"
    smtp_port = 25
    sender_email = "yakov.yosef.hakimi@intel.com"  # Intel format for SMTP
    recipient_email = "yakov.yosef.hakimi@altera.com"  # Your actual email
    
    print(f"📧 SMTP Server: {smtp_server}")
    print(f"📧 SMTP Port: {smtp_port}")
    print(f"📧 From: {sender_email}")
    print(f"📧 To: {recipient_email}")
    print()
    
    try:
        # Create test message (exactly like your working code)
        subject = "✅ Test Email from Equipment Management System"
        body = (
            f"Dear Admin,\n\n"
            f"This is a test email from the Equipment Management System.\n\n"
            f"🔧 System: Altera Lab Equipment Management\n"
            f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"📍 Server: Intel SMTP (sc-out.intel.com)\n\n"
            f"If you receive this email, the Intel SMTP configuration is working correctly!\n\n"
            f"Best,\nEquipment Management System"
        )
        
        # Create message (exactly like your working code)
        msg = MIMEText(body, _subtype="plain", _charset="utf-8")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = recipient_email
        
        print("📨 Sending email...")
        
        # Send email (exactly like your working code)
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.send_message(msg)
        
        print("✅ SUCCESS: Email sent successfully!")
        print(f"✅ Email should arrive at: {recipient_email}")
        print()
        print("🎯 Next steps:")
        print("1. Check your Altera email inbox")
        print("2. If email arrives, the configuration is working")
        print("3. Use this exact configuration in your Equipment Management app")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Email sending failed")
        print(f"❌ Error: {str(e)}")
        print()
        print("🔧 Troubleshooting:")
        print("1. Verify you're on the Intel/Altera network")
        print("2. Check if sc-out.intel.com is accessible")
        print("3. Ensure port 25 is not blocked")
        print("4. Try different sender email format if needed")
        
        return False

if __name__ == "__main__":
    print("🧪 Intel SMTP Test Script")
    print("Testing the exact configuration from your working app...")
    print()
    
    success = test_intel_smtp()
    
    print()
    print("=" * 50)
    if success:
        print("🎉 TEST PASSED: Ready to use in Equipment Management System!")
    else:
        print("💡 TEST FAILED: Check network and configuration")
