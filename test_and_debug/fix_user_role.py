#!/usr/bin/env python3
"""
Fix user role script - Update yaki user to tech role
"""

from pymongo import MongoClient
from datetime import datetime

def fix_user_role():
    """Update yaki user to have tech role."""
    try:
        # Connect to MongoDB
        mongo_connection_string = "mongodb://ascy00075.sc.altera.com:27017/mongo?readPreference=primary&ssl=false"
        client = MongoClient(mongo_connection_string)
        db = client["Equipment_DB"]
        users_collection = db["users"]
        
        print("🔄 Connecting to database...")
        
        # Find the yaki user
        user = users_collection.find_one({"username": "yaki"})
        if not user:
            print("❌ User 'yaki' not found")
            return False
        
        print(f"📋 Found user: {user['username']}")
        print(f"📋 Current role: {user.get('role', 'None')}")
        print(f"📋 Requested role: {user.get('requested_role', 'None')}")
        print(f"📋 Status: {user.get('status', 'None')}")
        
        # Update role to tech
        result = users_collection.update_one(
            {"username": "yaki"},
            {
                "$set": {
                    "role": "tech",
                    "role_changed_at": datetime.now(),
                    "role_changed_by": "admin_fix"
                }
            }
        )
        
        if result.modified_count > 0:
            print("✅ Successfully updated yaki's role to 'tech'")
            
            # Verify the change
            updated_user = users_collection.find_one({"username": "yaki"})
            print(f"✅ Verified - New role: {updated_user.get('role')}")
            print()
            print("🎯 Now yaki should have tech permissions!")
            print("🔄 Try logging out and back in to refresh permissions.")
            return True
        else:
            print("❌ Failed to update user role")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 User Role Fix Script")
    print("Updating yaki user to tech role...")
    print("=" * 40)
    
    success = fix_user_role()
    
    print("=" * 40)
    if success:
        print("🎉 SUCCESS: Role updated!")
        print("💡 Log out and back in to see the tech permissions.")
    else:
        print("💡 FAILED: Check the error message above.")
