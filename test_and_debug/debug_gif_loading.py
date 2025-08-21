"""
Debug GIF Loading Performance
"""

import streamlit as st
import time
from pathlib import Path
from thinking_gif_component import thinking_gif

def main():
    st.set_page_config(
        page_title="GIF Loading Debug",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 GIF Loading Debug")
    st.markdown("---")
    
    # Check file and cache status
    gif_path = Path("Processing Buffering GIF by Mashable.gif")
    
    if gif_path.exists():
        st.success(f"✅ GIF file found: {gif_path}")
        st.info(f"📄 File size: {gif_path.stat().st_size:,} bytes")
    else:
        st.error(f"❌ GIF file not found: {gif_path}")
    
    # Check cache status
    st.subheader("Cache Status")
    cache_status = thinking_gif.get_gif_status()
    st.json(cache_status)
    
    st.markdown("---")
    
    # Test 1: CSS Spinner (should be instant)
    st.subheader("Test 1: CSS Spinner (Instant)")
    
    col1, col2 = st.columns([1, 0.3])
    
    with col1:
        if st.button("Test CSS Spinner", key="css_debug"):
            start_time = time.time()
            st.success("CSS spinner should appear instantly!")
            end_time = time.time()
            st.info(f"CSS spinner time: {end_time - start_time:.3f} seconds")
    
    with col2:
        css_container = st.container()
        if st.button("Show CSS Spinner", key="css_show_debug"):
            start_time = time.time()
            thinking_gif.show_simple_thinking(css_container, "css_debug")
            end_time = time.time()
            st.info(f"CSS display time: {end_time - start_time:.3f} seconds")
    
    st.markdown("---")
    
    # Test 2: GIF Display with timing
    st.subheader("Test 2: GIF Display (Timed)")
    
    col1, col2 = st.columns([1, 0.3])
    
    with col1:
        if st.button("Test GIF Display", key="gif_debug"):
            start_time = time.time()
            st.success("GIF should appear below!")
            end_time = time.time()
            st.info(f"Button click time: {end_time - start_time:.3f} seconds")
    
    with col2:
        gif_container = st.container()
        if st.button("Show GIF", key="gif_show_debug"):
            start_time = time.time()
            thinking_gif.show_thinking_gif(gif_container, "gif_debug")
            end_time = time.time()
            st.info(f"GIF display time: {end_time - start_time:.3f} seconds")
    
    st.markdown("---")
    
    # Test 3: Direct base64 encoding timing
    st.subheader("Test 3: Base64 Encoding Performance")
    
    if gif_path.exists():
        if st.button("Test Base64 Encoding", key="base64_test"):
            start_time = time.time()
            try:
                import base64
                with open(gif_path, "rb") as f:
                    gif_data = f.read()
                    encoded = base64.b64encode(gif_data).decode()
                    data_url = f"data:image/gif;base64,{encoded}"
                
                st.markdown(
                    f"""
                    <img src="{data_url}" 
                         alt="Base64 GIF" 
                         style="width: 100px; height: 100px; border: 1px solid #ccc;">
                    """,
                    unsafe_allow_html=True
                )
                end_time = time.time()
                st.success(f"✅ Base64 encoding and display: {end_time - start_time:.3f} seconds")
            except Exception as e:
                st.error(f"❌ Base64 encoding failed: {str(e)}")
    
    st.markdown("---")
    
    # Test 4: Session state cache check
    st.subheader("Test 4: Session State Cache")
    
    if 'thinking_gif_cache' in st.session_state:
        st.success("✅ GIF cache found in session state")
        cache_size = len(st.session_state.thinking_gif_cache)
        st.info(f"📄 Cache size: {cache_size:,} characters")
        
        if st.button("Show Cached GIF", key="cached_gif"):
            start_time = time.time()
            st.markdown(
                f"""
                <img src="{st.session_state.thinking_gif_cache}" 
                     alt="Cached GIF" 
                     style="width: 100px; height: 100px; border: 1px solid #ccc;">
                """,
                unsafe_allow_html=True
            )
            end_time = time.time()
            st.success(f"✅ Cached GIF display: {end_time - start_time:.3f} seconds")
    else:
        st.error("❌ No GIF cache in session state")
        
        if st.button("Force Cache GIF", key="force_cache"):
            thinking_gif._preload_gif()
            st.rerun()
    
    st.markdown("---")
    
    # Test 5: Button integration with timing
    st.subheader("Test 5: Button Integration (Timed)")
    
    def test_operation():
        """Test operation that takes time."""
        time.sleep(1)
        return "Operation completed!"
    
    start_time = time.time()
    success = thinking_gif.button_with_thinking_gif(
        button_text="Test Button with GIF (Timed)",
        operation_func=test_operation,
        button_key="test_btn_debug",
        use_simple_indicator=False  # Use GIF
    )
    end_time = time.time()
    
    if success:
        st.success(f"✅ Button operation completed in {end_time - start_time:.3f} seconds")

if __name__ == "__main__":
    main()
