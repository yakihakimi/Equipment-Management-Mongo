"""
Simple GIF Display Test
"""

import streamlit as st
from pathlib import Path

def main():
    st.set_page_config(
        page_title="Simple GIF Test",
        page_icon="🖼️",
        layout="wide"
    )
    
    st.title("🖼️ Simple GIF Display Test")
    st.markdown("---")
    
    # Check file
    gif_path = Path("Processing Buffering GIF by Mashable.gif")
    
    if gif_path.exists():
        st.success(f"✅ GIF file found: {gif_path}")
        st.info(f"📄 File size: {gif_path.stat().st_size:,} bytes")
        
        # Test 1: Direct Streamlit image
        st.subheader("Test 1: Direct Streamlit Image")
        try:
            st.image(str(gif_path), width=150, caption="Direct Streamlit Image")
            st.success("✅ Direct image display works!")
        except Exception as e:
            st.error(f"❌ Direct image failed: {str(e)}")
        
        # Test 2: HTML img tag
        st.subheader("Test 2: HTML img tag")
        st.markdown(
            f"""
            <img src="{gif_path}" 
                 alt="GIF Test" 
                 style="width: 150px; height: 150px; border: 1px solid #ccc;">
            """,
            unsafe_allow_html=True
        )
        st.info("Above should show GIF via HTML img tag")
        
        # Test 3: Base64 encoded
        st.subheader("Test 3: Base64 Encoded")
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
                     style="width: 150px; height: 150px; border: 1px solid #ccc;">
                """,
                unsafe_allow_html=True
            )
            st.success("✅ Base64 encoded GIF should work!")
        except Exception as e:
            st.error(f"❌ Base64 encoding failed: {str(e)}")
        
    else:
        st.error(f"❌ GIF file not found: {gif_path}")
    
    st.markdown("---")
    
    # Test thinking component
    st.subheader("Test 4: Thinking Component")
    from thinking_gif_component import thinking_gif
    
    if st.button("Test Thinking GIF", key="test_thinking"):
        thinking_gif.show_thinking_gif(st.container(), "test")

if __name__ == "__main__":
    main()
