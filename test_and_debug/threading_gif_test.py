"""
Test the threading-based thinking GIF component for immediate display and proper timeout
"""

import streamlit as st
import time
from thinking_gif_component import thinking_gif

def main():
    st.set_page_config(
        page_title="Threading GIF Test",
        page_icon="⚡",
        layout="wide"
    )
    
    st.title("⚡ Threading-Based Thinking GIF Test")
    st.markdown("---")
    
    st.info("This test uses threading to show GIF immediately and handle timeout properly.")
    
    # Test 1: Immediate GIF display with threading
    st.subheader("Test 1: Immediate GIF Display (Threading)")
    
    col1, col2 = st.columns([1, 0.3])
    
    with col1:
        if st.button("🚀 Test Immediate GIF", key="test_immediate_threading"):
            st.success("GIF should appear immediately!")
    
    with col2:
        gif_container = st.container()
        if st.button("Show GIF", key="show_gif_threading"):
            # This should show the GIF immediately using threading
            thinking_gif.show_thinking_gif(gif_container, "threading_test", timeout_seconds=15)
    
    st.markdown("---")
    
    # Test 2: Integrated button with threading
    st.subheader("Test 2: Integrated Button with Threading")
    
    def slow_operation():
        """Simulate a slow operation."""
        time.sleep(5)  # 5 second operation
        return "Operation completed!"
    
    success = thinking_gif.button_with_thinking_gif(
        button_text="⚡ Threading Button with GIF",
        operation_func=slow_operation,
        button_key="threading_btn",
        use_simple_indicator=False,  # Use GIF
        timeout_seconds=15
    )
    
    if success:
        st.success("✅ Threading operation completed!")
    
    st.markdown("---")
    
    # Test 3: CSS Spinner with threading
    st.subheader("Test 3: CSS Spinner with Threading")
    
    def quick_operation():
        """Quick operation."""
        time.sleep(2)
        return "Quick operation done!"
    
    success = thinking_gif.button_with_thinking_gif(
        button_text="⚡ CSS Spinner Threading",
        operation_func=quick_operation,
        button_key="css_threading_btn",
        use_simple_indicator=True,  # Use CSS spinner
        timeout_seconds=15
    )
    
    if success:
        st.success("✅ CSS spinner threading completed!")
    
    st.markdown("---")
    
    # Test 4: Manual integration with threading
    st.subheader("Test 4: Manual Integration with Threading")
    
    col1, col2 = st.columns([1, 0.3])
    
    with col1:
        if st.button("💾 Save Data (Threading)", key="save_data_threading"):
            st.info("Starting save operation with threading...")
    
    with col2:
        save_container = st.container()
        if st.button("Show Save GIF (Threading)", key="save_gif_threading"):
            # Show GIF immediately using threading
            thinking_gif.show_thinking_gif(save_container, "save_operation_threading", timeout_seconds=15)
            
            # Simulate save operation in background
            def save_operation():
                time.sleep(4)
                st.success("✅ Data saved successfully with threading!")
            
            # Execute in thread
            import threading
            save_thread = threading.Thread(target=save_operation, daemon=True)
            save_thread.start()
    
    st.markdown("---")
    
    # Test 5: Multiple operations with different timeouts
    st.subheader("Test 5: Multiple Operations with Threading")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        def short_operation():
            time.sleep(1)
            return "Short operation done!"
        
        success = thinking_gif.button_with_thinking_gif(
            button_text="⏱️ Short (5s timeout)",
            operation_func=short_operation,
            button_key="short_threading",
            timeout_seconds=5
        )
    
    with col2:
        def medium_operation():
            time.sleep(3)
            return "Medium operation done!"
        
        success = thinking_gif.button_with_thinking_gif(
            button_text="⏱️ Medium (10s timeout)",
            operation_func=medium_operation,
            button_key="medium_threading",
            timeout_seconds=10
        )
    
    with col3:
        def long_operation():
            time.sleep(5)
            return "Long operation done!"
        
        success = thinking_gif.button_with_thinking_gif(
            button_text="⏱️ Long (15s timeout)",
            operation_func=long_operation,
            button_key="long_threading",
            timeout_seconds=15
        )
    
    st.markdown("---")
    
    # Performance status
    st.subheader("🔍 Performance Status")
    status = thinking_gif.get_gif_status()
    st.json(status)
    
    st.markdown("---")
    
    # Instructions for app_fast.py
    st.subheader("📋 For app_fast.py Integration (Threading)")
    
    st.markdown("""
    **Add this import to app_fast.py:**
    ```python
    from thinking_gif_component import thinking_gif
    ```
    
    **Use in your buttons:**
    ```python
    # Method 1: Integrated button with threading
    success = thinking_gif.button_with_thinking_gif(
        button_text="Save Changes",
        operation_func=your_save_function,
        button_key="save_btn",
        timeout_seconds=15
    )
    
    # Method 2: Manual display with threading
    if st.button("Save"):
        thinking_gif.show_thinking_gif(container, "save_thinking", timeout_seconds=15)
        # Your operation will run in background thread
        your_save_function()
    ```
    
    **Key Benefits of Threading:**
    - ⚡ **Instant Display**: GIF shows immediately when button is clicked
    - ⏱️ **Reliable Timeout**: Threading-based timeout that actually works
    - 🚀 **Non-Blocking**: Operations run in background threads
    - 🛡️ **Thread-Safe**: Proper thread management and cleanup
    """)

if __name__ == "__main__":
    main()
