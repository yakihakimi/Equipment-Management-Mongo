"""
Example of how to integrate thinking GIF component into app_fast.py
"""

import streamlit as st
import time
from thinking_gif_component import thinking_gif

def main():
    st.set_page_config(
        page_title="Thinking GIF Integration Example",
        page_icon="⚡",
        layout="wide"
    )
    
    st.title("⚡ Thinking GIF Integration Example for app_fast.py")
    st.markdown("---")
    
    st.info("This shows how to integrate the optimized thinking GIF component into your main app with 15-second timeout.")
    
    # Example 1: Simple button with thinking GIF
    st.subheader("Example 1: Button with Thinking GIF (15s timeout)")
    
    def sample_operation():
        """Sample operation that takes time."""
        time.sleep(3)  # Simulate processing
        return "Operation completed!"
    
    success = thinking_gif.button_with_thinking_gif(
        button_text="🚀 Fast Operation with GIF",
        operation_func=sample_operation,
        button_key="fast_operation",
        use_simple_indicator=False,  # Use GIF
        timeout_seconds=15  # 15 second timeout
    )
    
    if success:
        st.success("✅ Operation completed!")
    
    st.markdown("---")
    
    # Example 2: Button with CSS spinner (faster)
    st.subheader("Example 2: Button with CSS Spinner (Faster, 15s timeout)")
    
    def quick_operation():
        """Quick operation."""
        time.sleep(2)
        return "Quick operation done!"
    
    success = thinking_gif.button_with_thinking_gif(
        button_text="⚡ Quick Operation with CSS Spinner",
        operation_func=quick_operation,
        button_key="quick_operation",
        use_simple_indicator=True,  # Use CSS spinner (faster)
        timeout_seconds=15
    )
    
    if success:
        st.success("✅ Quick operation completed!")
    
    st.markdown("---")
    
    # Example 3: Manual integration (like in app_fast.py)
    st.subheader("Example 3: Manual Integration (Like in app_fast.py)")
    
    col1, col2 = st.columns([1, 0.3])
    
    with col1:
        if st.button("💾 Save Changes", key="save_btn"):
            # Show thinking GIF immediately
            with col2:
                thinking_container = st.container()
                thinking_gif.show_thinking_gif(thinking_container, "save_thinking", timeout_seconds=15)
            
            # Execute operation
            time.sleep(4)  # Simulate save operation
            st.success("✅ Changes saved successfully!")
    
    st.markdown("---")
    
    # Example 4: Multiple operations with different timeouts
    st.subheader("Example 4: Different Timeouts")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        def short_operation():
            time.sleep(1)
            return "Short operation done!"
        
        success = thinking_gif.button_with_thinking_gif(
            button_text="⏱️ Short (5s timeout)",
            operation_func=short_operation,
            button_key="short_op",
            timeout_seconds=5
        )
    
    with col2:
        def medium_operation():
            time.sleep(3)
            return "Medium operation done!"
        
        success = thinking_gif.button_with_thinking_gif(
            button_text="⏱️ Medium (10s timeout)",
            operation_func=medium_operation,
            button_key="medium_op",
            timeout_seconds=10
        )
    
    with col3:
        def long_operation():
            time.sleep(5)
            return "Long operation done!"
        
        success = thinking_gif.button_with_thinking_gif(
            button_text="⏱️ Long (15s timeout)",
            operation_func=long_operation,
            button_key="long_op",
            timeout_seconds=15
        )
    
    st.markdown("---")
    
    # Integration instructions
    st.subheader("📋 Integration Instructions for app_fast.py")
    
    st.markdown("""
    **Step 1: Import the component**
    ```python
    from thinking_gif_component import thinking_gif
    ```
    
    **Step 2: Use in your buttons**
    ```python
    # For save operations
    if st.button("💾 Save Changes"):
        thinking_gif.show_thinking_gif(container, "save_thinking", timeout_seconds=15)
        # Your save operation here
        save_operation()
    
    # For button integration
    success = thinking_gif.button_with_thinking_gif(
        button_text="Save",
        operation_func=save_operation,
        button_key="save_btn",
        timeout_seconds=15
    )
    ```
    
    **Step 3: Performance tips**
    - Use `use_simple_indicator=True` for fastest response
    - Use `timeout_seconds=15` to auto-hide after 15 seconds
    - GIF is pre-cached for instant display
    """)
    
    st.markdown("---")
    
    # Performance status
    st.subheader("🔍 Performance Status")
    status = thinking_gif.get_gif_status()
    st.json(status)

if __name__ == "__main__":
    main()
