import streamlit as st
import pandas as pd
import time

# Configure page
st.set_page_config(
    page_title="Rerun Anti-Fading Test",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load the anti-fading CSS
with open('anti_fading.css', 'r') as f:
    css_content = f.read()

# Load the rerun anti-fade JavaScript
with open('rerun_anti_fade.js', 'r') as f:
    js_content = f.read()

st.markdown(f"""
<style>
{css_content}
</style>

<script>
{js_content}
</script>
""", unsafe_allow_html=True)

st.title("🔄 Rerun Anti-Fading Test")
st.markdown("This page specifically tests the anti-fading measures during rerun operations.")

# Create test data
test_data = pd.DataFrame({
    'ID': range(1, 6),
    'Name': [f'Item {i}' for i in range(1, 6)],
    'Value': [i * 10 for i in range(1, 6)],
    'Status': ['Active', 'Inactive', 'Active', 'Pending', 'Active']
})

st.markdown("### Test Rerun Operations")

# Test buttons that trigger rerun
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Force Rerun"):
        st.success("Rerun triggered! Page should not fade.")
        time.sleep(0.5)
        st.rerun()

with col2:
    if st.button("📊 DataFrame + Rerun"):
        st.success("DataFrame interaction + rerun!")
        st.dataframe(test_data)
        time.sleep(0.5)
        st.rerun()

with col3:
    if st.button("🎯 Navigation + Rerun"):
        st.success("Navigation + rerun completed!")
        st.info("If you see this without fading, the anti-fading measures are working!")
        time.sleep(0.5)
        st.rerun()

# Test form with rerun
st.markdown("### Test Form with Rerun")
with st.form("rerun_form"):
    name = st.text_input("Enter your name:")
    submit = st.form_submit_button("Submit & Rerun")
    
    if submit:
        st.success(f"Form submitted: {name}")
        st.info("Form submitted successfully! Rerun should not cause fading.")
        time.sleep(1)
        st.rerun()

# Test selectbox with rerun
st.markdown("### Test Selectbox with Rerun")
option = st.selectbox("Choose an option:", ["Option 1", "Option 2", "Option 3"])
st.write(f"You selected: {option}")

if st.button("🔄 Rerun after Selection"):
    st.success(f"Selection: {option} - Rerun should not fade!")
    time.sleep(0.5)
    st.rerun()

# Test dataframe display with rerun
st.markdown("### Test DataFrame with Rerun")
st.dataframe(test_data, use_container_width=True)

if st.button("🔄 Rerun after DataFrame"):
    st.success("DataFrame displayed! Rerun should not fade.")
    time.sleep(0.5)
    st.rerun()

# Status indicator
st.markdown("---")
st.markdown("### Rerun Status")
if st.button("🔄 Test Rerun Status"):
    st.success("✅ Rerun anti-fading measures are active!")
    st.info("💡 Try clicking the rerun buttons above to see if fading occurs.")
    st.warning("⚠️ If you see any fading during rerun, the measures need to be enhanced.")
    time.sleep(1)
    st.rerun()

st.markdown("""
### Instructions for Testing Rerun Anti-Fading:
1. Click any of the rerun buttons above
2. Observe if the page fades during the rerun operation
3. Check if the page maintains consistent white background
4. Verify that no opacity changes occur during rerun

### Expected Results:
- ✅ No fading during rerun operations
- ✅ Consistent white background throughout
- ✅ No opacity changes during page refresh
- ✅ Smooth rerun experience

If the page doesn't fade during rerun operations, the anti-fading measures are working correctly!
""")
