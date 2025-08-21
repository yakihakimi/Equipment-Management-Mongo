"""
Demo script for Improved Thinking Component
"""

import streamlit as st
import time
from thinking_gif_component import thinking_gif

def main():
    st.set_page_config(
        page_title="Thinking Component Demo",
        page_icon="⚡",
        layout="wide"
    )
    
    st.title("⚡ Improved Thinking Component Demo")
    st.markdown("---")
    
    st.success("🎉 **NEW**: The component now shows immediate CSS spinner feedback while GIF loads in background!")
    
    st.info("This demo shows the improved thinking component with instant visual feedback and better performance.")
    
    # Show initial status
    st.subheader("🔍 Component Status")
    status = thinking_gif.get_gif_status()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Current Status:**")
        st.json(status)
    
    with col2:
        st.markdown("**Actions:**")
        
        # Custom path input
        custom_path = st.text_input(
            "Set Custom GIF Path:",
            value="Processing Buffering GIF by Mashable.gif",
            help="Enter the path to your GIF file"
        )
        
        if st.button("🔧 Set Custom Path", key="set_path_btn"):
            if thinking_gif.set_custom_gif_path(custom_path):
                time.sleep(1)
                st.rerun()
        
        if st.button("📊 Refresh Status", key="refresh"):
            st.rerun()
    
    st.markdown("---")
    
    # Performance comparison
    st.subheader("⚡ Performance Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**CSS Spinner (Instant):**")
        if st.button("Test CSS Spinner", key="css_test"):
            start_time = time.time()
            thinking_gif.show_simple_thinking(st.container(), "css_demo")
            end_time = time.time()
            st.success(f"⏱️ CSS spinner loaded in {end_time - start_time:.3f} seconds")
            st.info("✅ Instant feedback - no loading delay!")
    
    with col2:
        st.markdown("**GIF with CSS Fallback:**")
        if st.button("Test GIF with CSS", key="gif_test"):
            # Check if we're using local or URL
            gif_source = thinking_gif._get_gif_source()
            if "Processing Buffering GIF" in gif_source:
                st.info("✅ Using local GIF")
            else:
                st.info("🌐 Using URL fallback")
            
            start_time = time.time()
            thinking_gif.show_thinking_gif(st.container(), "gif_demo")
            end_time = time.time()
            st.success(f"⏱️ GIF loaded in {end_time - start_time:.3f} seconds")
            st.info("✅ Shows CSS spinner first, then GIF loads!")
    
    st.markdown("---")
    
    # File information
    st.subheader("📁 File Information")
    
    import os
    from pathlib import Path
    
    gif_path = Path("Processing Buffering GIF by Mashable.gif")
    
    if gif_path.exists():
        st.success(f"✅ Local GIF file found: {gif_path.absolute()}")
        size = gif_path.stat().st_size
        st.info(f"📄 File name: {gif_path.name}")
        st.info(f"📄 File size: {size:,} bytes")
        st.info(f"📄 File path: {gif_path}")
    else:
        st.error(f"❌ Local GIF file not found: {gif_path}")
        st.info("The component will use URL fallback.")
    
    st.markdown("---")
    
    # Benefits explanation
    st.subheader("🎯 Key Improvements")
    
    benefits = [
        "⚡ **Instant Feedback**: CSS spinner shows immediately - no waiting for GIF to load",
        "🔄 **Dual Display**: Shows CSS spinner first, then GIF loads in background",
        "🚀 **Better Performance**: No delay in user feedback",
        "📶 **Offline Support**: CSS spinner works without internet",
        "💾 **Local Storage**: Uses local GIF file when available",
        "🛡️ **Fallback Support**: Automatic URL fallback if local file missing"
    ]
    
    for benefit in benefits:
        st.markdown(benefit)
    
    st.markdown("---")
    
    # Usage examples
    st.subheader("💡 Usage Examples")
    
    st.code("""
# Fastest option - CSS spinner only
thinking_gif.show_simple_thinking(container, "demo")

# Dual display - CSS spinner + GIF
thinking_gif.show_thinking_gif(container, "demo")

# Button with CSS spinner (default)
thinking_gif.button_with_thinking_gif(
    button_text="Save",
    operation_func=save_operation,
    button_key="save_btn",
    use_simple_indicator=True  # CSS spinner
)

# Button with GIF
thinking_gif.button_with_thinking_gif(
    button_text="Save",
    operation_func=save_operation,
    button_key="save_btn",
    use_simple_indicator=False  # GIF
)
    """, language="python")
    
    st.markdown("---")
    
    # Live tests
    st.subheader("🧪 Live Tests")
    
    # Test 1: CSS Spinner
    st.markdown("**Test 1: CSS Spinner (Instant)**")
    test1_col1, test1_col2 = st.columns([1, 0.3])
    
    with test1_col1:
        if st.button("Test CSS Spinner", key="live_css_test"):
            st.success("Button clicked! Check the instant spinner on the right.")
    
    with test1_col2:
        test1_container = st.container()
        if st.button("Test CSS Spinner", key="live_css_test"):
            thinking_gif.show_simple_thinking(test1_container, "live_css_demo")
    
    st.markdown("---")
    
    # Test 2: GIF with CSS
    st.markdown("**Test 2: GIF with CSS Fallback**")
    test2_col1, test2_col2 = st.columns([1, 0.3])
    
    with test2_col1:
        if st.button("Test GIF with CSS", key="live_gif_test"):
            st.success("Button clicked! Check the dual display on the right.")
    
    with test2_col2:
        test2_container = st.container()
        if st.button("Test GIF with CSS", key="live_gif_test"):
            thinking_gif.show_thinking_gif(test2_container, "live_gif_demo")
    
    st.markdown("---")
    
    # Test 3: Button integration
    st.markdown("**Test 3: Button Integration**")
    
    def demo_operation():
        """Demo operation that takes time."""
        time.sleep(2)
        return "Operation completed!"
    
    success = thinking_gif.button_with_thinking_gif(
        button_text="Demo Operation (2s delay)",
        operation_func=demo_operation,
        button_key="demo_btn",
        use_simple_indicator=True  # Use CSS spinner for instant feedback
    )
    
    if success:
        st.success("✅ Demo operation completed successfully!")

if __name__ == "__main__":
    main()
