"""
Simple test script to verify GIF loading functionality
"""

import streamlit as st
import time
from pathlib import Path
from thinking_gif_component import thinking_gif

def main():
    st.set_page_config(
        page_title="GIF Loading Test",
        page_icon="🔄",
        layout="wide"
    )
    
    st.title("🔄 GIF Loading Test")
    st.markdown("---")
    
    # Check if GIF file exists
    gif_path = Path("Processing Buffering GIF by Mashable.gif")
    
    if gif_path.exists():
        st.success(f"✅ GIF file found: {gif_path}")
        size = gif_path.stat().st_size
        st.info(f"📄 File size: {size:,} bytes")
    else:
        st.error(f"❌ GIF file not found: {gif_path}")
        st.info("The component will use URL fallback.")
    
    st.markdown("---")
    
    # Test 1: Simple CSS Spinner
    st.subheader("Test 1: CSS Spinner (Should work instantly)")
    
    col1, col2 = st.columns([1, 0.3])
    
    with col1:
        if st.button("Test CSS Spinner", key="css_test_btn"):
            st.success("CSS spinner should appear instantly!")
    
    with col2:
        css_container = st.container()
        if st.button("Show CSS Spinner", key="css_show_btn"):
            thinking_gif.show_simple_thinking(css_container, "css_demo")
    
    st.markdown("---")
    
    # Test 2: GIF Display
    st.subheader("Test 2: GIF Display (Should show GIF)")
    
    col1, col2 = st.columns([1, 0.3])
    
    with col1:
        if st.button("Test GIF Display", key="gif_test_btn"):
            st.success("GIF should appear below the CSS spinner!")
    
    with col2:
        gif_container = st.container()
        if st.button("Show GIF", key="gif_show_btn"):
            thinking_gif.show_thinking_gif(gif_container, "gif_demo")
    
    st.markdown("---")
    
    # Test 3: Direct Streamlit Image
    st.subheader("Test 3: Direct Streamlit Image (For comparison)")
    
    if gif_path.exists():
        try:
            st.image(str(gif_path), width=100, caption="Direct Streamlit Image")
            st.success("✅ Direct image display works!")
        except Exception as e:
            st.error(f"❌ Direct image display failed: {str(e)}")
    else:
        st.warning("⚠️ No GIF file to test direct display")
    
    st.markdown("---")
    
    # Test 4: Button Integration
    st.subheader("Test 4: Button Integration")
    
    def test_operation():
        """Test operation that takes time."""
        time.sleep(2)
        return "Operation completed!"
    
    success = thinking_gif.button_with_thinking_gif(
        button_text="Test Button with GIF",
        operation_func=test_operation,
        button_key="test_btn",
        use_simple_indicator=False  # Use GIF
    )
    
    if success:
        st.success("✅ Button operation completed!")
    
    st.markdown("---")
    
    # Debug information
    st.subheader("🔍 Debug Information")
    
    status = thinking_gif.get_gif_status()
    st.json(status)
    
    # Test file reading
    if gif_path.exists():
        try:
            with open(gif_path, "rb") as f:
                data = f.read(100)  # Read first 100 bytes
                st.info(f"✅ File can be read. First 100 bytes: {len(data)} bytes")
        except Exception as e:
            st.error(f"❌ File cannot be read: {str(e)}")

if __name__ == "__main__":
    main()
