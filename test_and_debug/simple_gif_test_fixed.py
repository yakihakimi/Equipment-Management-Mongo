"""
Simple test for the fixed thinking GIF component
"""

import streamlit as st
import time
from thinking_gif_component import thinking_gif

def main():
    st.set_page_config(
        page_title="Fixed GIF Test",
        page_icon="⚡",
        layout="wide"
    )
    
    st.title("⚡ Fixed Thinking GIF Test")
    st.markdown("---")
    
    st.info("Testing the fixed GIF component with immediate display and proper timeout.")
    
    # Test 1: Simple button with immediate GIF display
    st.subheader("Test 1: Immediate GIF Display")
    
    col1, col2 = st.columns([1, 0.3])
    
    with col1:
        if st.button("🚀 Test Button", key="test_btn"):
            st.success("Button clicked! GIF should appear immediately.")
    
    with col2:
        gif_container = st.container()
        if st.button("Show GIF", key="show_gif_btn"):
            # This should show the GIF immediately
            thinking_gif.show_thinking_gif(gif_container, "test_gif", timeout_seconds=15)
    
    st.markdown("---")
    
    # Test 2: Integrated button with operation
    st.subheader("Test 2: Integrated Button with Operation")
    
    def test_operation():
        """Test operation that takes time."""
        time.sleep(3)  # 3 second operation
        return "Operation completed!"
    
    success = thinking_gif.button_with_thinking_gif(
        button_text="⚡ Integrated Button",
        operation_func=test_operation,
        button_key="integrated_btn",
        use_simple_indicator=False,  # Use GIF
        timeout_seconds=15
    )
    
    if success:
        st.success("✅ Operation completed!")
    
    st.markdown("---")
    
    # Test 3: CSS Spinner (faster alternative)
    st.subheader("Test 3: CSS Spinner (Faster)")
    
    def quick_operation():
        """Quick operation."""
        time.sleep(2)
        return "Quick operation done!"
    
    success = thinking_gif.button_with_thinking_gif(
        button_text="⚡ CSS Spinner",
        operation_func=quick_operation,
        button_key="css_btn",
        use_simple_indicator=True,  # Use CSS spinner
        timeout_seconds=15
    )
    
    if success:
        st.success("✅ CSS spinner operation completed!")
    
    st.markdown("---")
    
    # Test 4: Manual integration (like in app_fast.py)
    st.subheader("Test 4: Manual Integration (Like app_fast.py)")
    
    col1, col2 = st.columns([1, 0.3])
    
    with col1:
        if st.button("💾 Save Changes", key="save_btn"):
            st.info("Starting save operation...")
    
    with col2:
        save_container = st.container()
        if st.button("Show Save GIF", key="save_gif_btn"):
            # Show GIF immediately
            thinking_gif.show_thinking_gif(save_container, "save_operation", timeout_seconds=15)
            
            # Simulate save operation
            time.sleep(4)
            st.success("✅ Changes saved successfully!")
    
    st.markdown("---")
    
    # Performance status
    st.subheader("🔍 Performance Status")
    status = thinking_gif.get_gif_status()
    st.json(status)
    
    st.markdown("---")
    
    # Instructions for app_fast.py
    st.subheader("📋 For app_fast.py Integration")
    
    st.markdown("""
    **Add this import to app_fast.py:**
    ```python
    from thinking_gif_component import thinking_gif
    ```
    
    **Use in your buttons:**
    ```python
    # Method 1: Integrated button
    success = thinking_gif.button_with_thinking_gif(
        button_text="Save Changes",
        operation_func=your_save_function,
        button_key="save_btn",
        timeout_seconds=15
    )
    
    # Method 2: Manual display
    if st.button("Save"):
        thinking_gif.show_thinking_gif(container, "save_thinking", timeout_seconds=15)
        your_save_function()
    ```
    """)

if __name__ == "__main__":
    main()
