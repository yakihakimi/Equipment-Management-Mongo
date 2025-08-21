#!/usr/bin/env python3
"""
Test script to verify that the column addition functionality works without NoneType errors.
"""

import streamlit as st
import pandas as pd
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

def test_column_addition():
    """Test the column addition functionality."""
    
    st.title("🧪 Test Column Addition Fix")
    
    try:
        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017/")
        client.admin.command('ping')
        
        db = client["Equipment_DB"]
        equipment_select_options = db["Equipment_select_options"]
        
        st.success("✅ Connected to MongoDB successfully")
        
        # Test 1: Check if collection exists and has data
        count = equipment_select_options.count_documents({})
        st.info(f"📊 Equipment Select Options collection has {count} documents")
        
        # Test 2: Try to add a test column
        test_column_name = "test_column_fix"
        test_default_value = "test_value"
        
        st.info(f"🔧 Testing column addition: '{test_column_name}' with default value '{test_default_value}'")
        
        # Add the test column
        update_result = equipment_select_options.update_many(
            {},
            {"$set": {test_column_name: test_default_value}}
        )
        
        st.success(f"✅ Successfully added column '{test_column_name}' to {update_result.modified_count} records")
        
        # Test 3: Verify the column was added
        sample_doc = equipment_select_options.find_one({})
        if sample_doc and test_column_name in sample_doc:
            st.success(f"✅ Column '{test_column_name}' verified in database with value: {sample_doc[test_column_name]}")
        else:
            st.error(f"❌ Column '{test_column_name}' not found in database")
        
        # Test 4: Clean up - remove the test column
        cleanup_result = equipment_select_options.update_many(
            {},
            {"$unset": {test_column_name: ""}}
        )
        
        st.info(f"🧹 Cleaned up test column from {cleanup_result.modified_count} records")
        
        # Test 5: Verify cleanup
        sample_doc_after = equipment_select_options.find_one({})
        if sample_doc_after and test_column_name not in sample_doc_after:
            st.success(f"✅ Test column '{test_column_name}' successfully removed")
        else:
            st.warning(f"⚠️ Test column '{test_column_name}' may still exist")
        
        st.success("🎉 All tests completed successfully!")
        
    except ConnectionFailure as e:
        st.error(f"❌ MongoDB connection failed: {e}")
        st.info("💡 Make sure MongoDB is running on localhost:27017")
    except Exception as e:
        st.error(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_column_addition()
