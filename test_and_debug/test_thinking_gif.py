"""
Test script for the Thinking GIF Component
"""

import streamlit as st
import time
from thinking_gif_component import thinking_gif

def main():
    st.set_page_config(
        page_title="Thinking GIF Test",
        page_icon="🧠",
        layout="wide"
    )
    
    st.title("🧠 Thinking GIF Component Test")
    st.markdown("---")
    
    st.info("This page tests the thinking GIF component functionality. The component now shows immediate CSS spinner feedback while GIF loads in background.")
    
    # Test 0: GIF Status and Management
    st.subheader("Test 0: GIF Status and Management")
    
    # Show GIF status
    status = thinking_gif.get_gif_status()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**GIF Status:**")
        st.json(status)
    
    with col2:
        st.markdown("**GIF Management:**")
        
        # Custom path input
        custom_path = st.text_input(
            "Set Custom GIF Path:",
            value="Processing Buffering GIF by Mashable.gif",
            help="Enter the path to your GIF file"
        )
        
        if st.button("🔧 Set Custom Path", key="set_path_btn"):
            if thinking_gif.set_custom_gif_path(custom_path):
                st.rerun()
        
        if st.button("📊 Refresh Status", key="refresh_status_btn"):
            st.rerun()
    
    st.markdown("---")
    
    # Test 1: Simple CSS spinner (fastest)
    st.subheader("Test 1: Simple CSS Spinner (Fastest)")
    col1, col2 = st.columns([1, 0.3])
    
    with col1:
        if st.button("Show CSS Spinner", key="test1_btn"):
            st.success("Button clicked! Check the spinner on the right.")
    
    with col2:
        thinking_container = st.container()
        if st.button("Show CSS Spinner", key="test1_btn"):
            thinking_gif.show_simple_thinking(thinking_container, "test1_thinking")
    
    st.markdown("---")
    
    # Test 2: Button with simple spinner (default)
    st.subheader("Test 2: Button with Simple Spinner (Default)")
    
    def test_operation():
        """Test operation that takes some time."""
        time.sleep(2)  # Simulate processing time
        return "Operation completed!"
    
    success = thinking_gif.button_with_thinking_gif(
        button_text="Test Operation (2s delay) - Simple Spinner",
        operation_func=test_operation,
        button_key="test2_btn",
        use_simple_indicator=True  # Use CSS spinner
    )
    
    if success:
        st.success("Operation completed successfully!")
    
    st.markdown("---")
    
    # Test 3: Button with GIF indicator
    st.subheader("Test 3: Button with GIF Indicator")
    
    def test_operation_gif():
        """Test operation that takes some time."""
        time.sleep(2)  # Simulate processing time
        return "Operation completed!"
    
    success = thinking_gif.button_with_thinking_gif(
        button_text="Test Operation (2s delay) - GIF",
        operation_func=test_operation_gif,
        button_key="test3_btn",
        use_simple_indicator=False  # Use GIF
    )
    
    if success:
        st.success("Operation completed successfully!")
    
    st.markdown("---")
    
    # Test 4: Operation with thinking indicator
    st.subheader("Test 4: Operation with Thinking Indicator")
    
    if st.button("Run Test Operation", key="test4_btn"):
        def long_operation():
            """Long operation that takes time."""
            time.sleep(3)  # Simulate processing time
            return "Long operation completed!"
        
        success = thinking_gif.operation_with_thinking_gif(
            operation_func=long_operation,
            success_message="Long operation completed successfully!",
            error_message="Long operation failed!",
            container_key="test4_thinking",
            use_simple_indicator=True  # Use CSS spinner
        )
    
    st.markdown("---")
    
    # Test 5: Multiple buttons with different indicators
    st.subheader("Test 5: Multiple Buttons with Different Indicators")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        btn1_col1, btn1_col2 = st.columns([1, 0.3])
        with btn1_col1:
            btn1_clicked = st.button("Quick - CSS", key="test5_btn1")
        with btn1_col2:
            btn1_thinking = st.container()
        
        if btn1_clicked:
            thinking_gif.show_simple_thinking(btn1_thinking, "test5_thinking1")
            time.sleep(1)
            st.success("Quick operation done!")
    
    with col2:
        btn2_col1, btn2_col2 = st.columns([1, 0.3])
        with btn2_col1:
            btn2_clicked = st.button("Medium - GIF", key="test5_btn2")
        with btn2_col2:
            btn2_thinking = st.container()
        
        if btn2_clicked:
            thinking_gif.show_thinking_gif(btn2_thinking, "test5_thinking2")
            time.sleep(2)
            st.success("Medium operation done!")
    
    with col3:
        btn3_col1, btn3_col2 = st.columns([1, 0.3])
        with btn3_col1:
            btn3_clicked = st.button("Long - CSS", key="test5_btn3")
        with btn3_col2:
            btn3_thinking = st.container()
        
        if btn3_clicked:
            thinking_gif.show_simple_thinking(btn3_thinking, "test5_thinking3")
            time.sleep(3)
            st.success("Long operation done!")
    
    st.markdown("---")
    
    # Test 6: Performance comparison
    st.subheader("Test 6: Performance Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**CSS Spinner Performance:**")
        if st.button("Test CSS Spinner Speed", key="css_speed_btn"):
            start_time = time.time()
            thinking_gif.show_simple_thinking(st.container(), "css_speed_test")
            end_time = time.time()
            st.success(f"CSS spinner loaded in {end_time - start_time:.3f} seconds")
    
    with col2:
        st.markdown("**GIF Performance:**")
        if st.button("Test GIF Speed", key="gif_speed_btn"):
            start_time = time.time()
            # Check if we're using local or URL
            gif_source = thinking_gif._get_gif_source()
            if "Processing Buffering GIF" in gif_source:
                st.info("✅ Using local GIF")
            else:
                st.info("🌐 Using URL fallback")
            
            thinking_gif.show_thinking_gif(st.container(), "gif_speed_test")
            end_time = time.time()
            st.success(f"GIF loaded in {end_time - start_time:.3f} seconds")
    
    st.markdown("---")
    
    # Test 7: File information
    st.subheader("Test 7: File Information")
    
    from pathlib import Path
    
    gif_path = Path("Processing Buffering GIF by Mashable.gif")
    
    if gif_path.exists():
        st.success(f"✅ Local GIF file found: {gif_path.absolute()}")
        size = gif_path.stat().st_size
        st.info(f"📄 File size: {size:,} bytes")
        st.info(f"📄 File name: {gif_path.name}")
    else:
        st.error(f"❌ Local GIF file not found: {gif_path}")
        st.info("The component will use URL fallback.")
    
    st.markdown("---")
    
    # Test 8: Usage recommendations
    st.subheader("Test 8: Usage Recommendations")
    
    st.markdown("""
    **Recommended Usage:**
    
    - **CSS Spinner (Default)**: Use for most operations - instant feedback, no loading delay
    - **GIF Indicator**: Use when you want the animated GIF - shows CSS spinner first, then GIF loads
    - **Quick Operations**: Always use CSS spinner for operations < 1 second
    - **Long Operations**: Either option works, CSS spinner is faster to display
    """)

if __name__ == "__main__":
    main()
