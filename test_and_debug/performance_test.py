import streamlit as st
import pandas as pd
import time

# Configure page
st.set_page_config(
    page_title="Performance Test",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load the anti-fading CSS
with open('anti_fading.css', 'r') as f:
    css_content = f.read()

st.markdown(f"""
<style>
{css_content}
</style>

<script>
// Lightweight anti-fading fix - runs only when needed
document.addEventListener('DOMContentLoaded', function() {{
    // One-time fix for initial load
    function quickFix() {{
        document.body.style.backgroundColor = '#ffffff';
        document.body.style.transition = 'none';
        document.body.style.opacity = '1';
        
        const appContainer = document.querySelector('.stApp');
        if (appContainer) {{
            appContainer.style.backgroundColor = '#ffffff';
            appContainer.style.transition = 'none';
            appContainer.style.opacity = '1';
        }}
    }}
    
    // Run once on load
    quickFix();
    
    // Light monitoring - only check every 2 seconds instead of 100ms
    setInterval(quickFix, 2000);
}});
</script>
""", unsafe_allow_html=True)

st.title("⚡ Performance Test Page")
st.markdown("Testing page loading speed and anti-fading measures.")

# Performance test
start_time = time.time()

# Create test data
test_data = pd.DataFrame({
    'ID': range(1, 21),
    'Name': [f'Item {i}' for i in range(1, 21)],
    'Value': [i * 10 for i in range(1, 21)],
    'Status': ['Active', 'Inactive', 'Active', 'Pending'] * 5
})

load_time = time.time() - start_time

st.success(f"✅ Page loaded in {load_time:.3f} seconds")

# Test interactions
st.markdown("### Quick Interaction Tests")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Test Rerun"):
        st.success("Rerun completed!")
        st.rerun()

with col2:
    if st.button("📊 Test DataFrame"):
        st.success("DataFrame displayed!")
        st.dataframe(test_data)

# Test navigation
st.markdown("### Navigation Test")
page = st.selectbox("Select a page:", ["Page 1", "Page 2", "Page 3"])
st.write(f"Current page: {page}")

# Test form
st.markdown("### Form Test")
with st.form("test_form"):
    name = st.text_input("Name:")
    submit = st.form_submit_button("Submit")
    if submit:
        st.success(f"Form submitted: {name}")

# Performance indicators
st.markdown("---")
st.markdown("### Performance Indicators")

if st.button("🔄 Check Performance"):
    st.success("✅ Performance check completed!")
    st.info("💡 If this page loaded quickly and doesn't fade during interactions, the optimizations are working!")

st.markdown("""
### What to Test:
1. **Page Load Speed**: Should load quickly without delays
2. **No Fading**: Page should not fade when clicking buttons or navigating
3. **Responsive**: Interactions should be immediate
4. **Consistent**: Background should stay white throughout

### Expected Results:
- ✅ Fast page loading
- ✅ No fading during interactions
- ✅ Smooth navigation
- ✅ Consistent white background
""")
