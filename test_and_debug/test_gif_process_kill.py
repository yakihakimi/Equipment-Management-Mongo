"""
Test the GIF process killing functionality after timeout
"""

import streamlit as st
import time
from thinking_gif_component import thinking_gif

def main():
    st.set_page_config(
        page_title="GIF Process Kill Test",
        page_icon="💀",
        layout="wide"
    )
    
    st.title("💀 GIF Process Kill Test")
    st.markdown("---")
    
    st.info("This test demonstrates how the GIF process is killed after timeout.")
    
    # Test 1: GIF with process killing after timeout
    st.subheader("Test 1: GIF Process Kill After Timeout")
    
    col1, col2 = st.columns([1, 0.3])
    
    with col1:
        if st.button("🚀 Test GIF Process Kill", key="test_gif_kill"):
            st.success("GIF should appear and be killed after timeout!")
    
    with col2:
        gif_container = st.container()
        if st.button("Show GIF (Will be killed)", key="show_gif_kill"):
            # This should show the GIF and kill it after 5 seconds
            thinking_gif.show_thinking_gif(gif_container, "gif_kill_test", timeout_seconds=5)
    
    st.markdown("---")
    
    # Test 2: CSS Spinner with process killing
    st.subheader("Test 2: CSS Spinner Process Kill")
    
    col1, col2 = st.columns([1, 0.3])
    
    with col1:
        if st.button("⚡ Test Spinner Process Kill", key="test_spinner_kill"):
            st.success("Spinner should appear and be killed after timeout!")
    
    with col2:
        spinner_container = st.container()
        if st.button("Show Spinner (Will be killed)", key="show_spinner_kill"):
            # This should show the spinner and kill it after 3 seconds
            thinking_gif.show_simple_thinking(spinner_container, "spinner_kill_test", timeout_seconds=3)
    
    st.markdown("---")
    
    # Test 3: Multiple GIFs with different timeouts
    st.subheader("Test 3: Multiple GIFs with Different Kill Times")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        gif1_container = st.container()
        if st.button("GIF 1 (3s kill)", key="gif1_kill"):
            thinking_gif.show_thinking_gif(gif1_container, "gif1_kill", timeout_seconds=3)
    
    with col2:
        gif2_container = st.container()
        if st.button("GIF 2 (5s kill)", key="gif2_kill"):
            thinking_gif.show_thinking_gif(gif2_container, "gif2_kill", timeout_seconds=5)
    
    with col3:
        gif3_container = st.container()
        if st.button("GIF 3 (10s kill)", key="gif3_kill"):
            thinking_gif.show_thinking_gif(gif3_container, "gif3_kill", timeout_seconds=10)
    
    st.markdown("---")
    
    # Test 4: Manual process killing
    st.subheader("Test 4: Manual Process Killing")
    
    col1, col2 = st.columns([1, 0.3])
    
    with col1:
        if st.button("💀 Kill All Processes", key="kill_all"):
            thinking_gif.kill_all_processes()
            st.success("All GIF and spinner processes killed!")
    
    with col2:
        manual_gif_container = st.container()
        if st.button("Show Manual GIF", key="manual_gif"):
            thinking_gif.show_thinking_gif(manual_gif_container, "manual_gif_kill", timeout_seconds=15)
    
    st.markdown("---")
    
    # Test 5: Button integration with process killing
    st.subheader("Test 5: Button Integration with Process Killing")
    
    def long_operation():
        """Simulate a long operation."""
        time.sleep(8)  # 8 second operation
        return "Long operation completed!"
    
    success = thinking_gif.button_with_thinking_gif(
        button_text="⚡ Long Operation (GIF killed after 5s)",
        operation_func=long_operation,
        button_key="long_op_kill",
        use_simple_indicator=False,  # Use GIF
        timeout_seconds=5  # GIF will be killed after 5 seconds
    )
    
    if success:
        st.success("✅ Long operation completed!")
    
    st.markdown("---")
    
    # Performance status
    st.subheader("🔍 Process Status")
    status = thinking_gif.get_gif_status()
    st.json(status)
    
    st.markdown("---")
    
    # Instructions for app_fast.py
    st.subheader("📋 For app_fast.py Integration (Process Killing)")
    
    st.markdown("""
    **Add this import to app_fast.py:**
    ```python
    from thinking_gif_component import thinking_gif
    ```
    
    **Use in your buttons:**
    ```python
    # Method 1: Integrated button with process killing
    success = thinking_gif.button_with_thinking_gif(
        button_text="Save Changes",
        operation_func=your_save_function,
        button_key="save_btn",
        timeout_seconds=15  # GIF will be killed after 15 seconds
    )
    
    # Method 2: Manual display with process killing
    if st.button("Save"):
        thinking_gif.show_thinking_gif(container, "save_thinking", timeout_seconds=15)
        # GIF will be automatically killed after 15 seconds
        your_save_function()
    
    # Method 3: Manual process killing
    if st.button("Kill All"):
        thinking_gif.kill_all_processes()  # Kill all active GIFs/spinners
    ```
    
    **Key Features of Process Killing:**
    - ⚡ **Instant Display**: GIF shows immediately when button is clicked
    - 💀 **Process Killing**: GIF/spinner is completely removed after timeout
    - 🧹 **Memory Cleanup**: Containers and threads are properly cleaned up
    - 🛡️ **Error Handling**: Safe process killing with error handling
    - 🔄 **UI Update**: Automatic UI refresh after process killing
    """)

if __name__ == "__main__":
    main()
