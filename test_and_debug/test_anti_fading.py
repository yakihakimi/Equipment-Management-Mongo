import streamlit as st
import pandas as pd
import time

# Configure page
st.set_page_config(
    page_title="Anti-Fading Test",
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

st.title("🧪 Anti-Fading Test Page")
st.markdown("This page tests the anti-fading measures to ensure they work properly.")

# Create test data
test_data = pd.DataFrame({
    'ID': range(1, 11),
    'Name': [f'Item {i}' for i in range(1, 11)],
    'Value': [i * 10 for i in range(1, 11)],
    'Status': ['Active', 'Inactive', 'Active', 'Pending', 'Active', 'Inactive', 'Active', 'Pending', 'Active', 'Inactive']
})

st.markdown("### Test Interactions")

# Test buttons that might cause fading
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Test Rerun (should not fade)"):
        st.success("Button clicked! Page should not fade.")
        time.sleep(0.5)
        st.rerun()

with col2:
    if st.button("📊 Test DataFrame Interaction"):
        st.success("DataFrame interaction triggered!")
        st.dataframe(test_data)

with col3:
    if st.button("🎯 Test Navigation"):
        st.success("Navigation test completed!")
        st.info("If you see this message without fading, the anti-fading measures are working!")

# Test form interactions
st.markdown("### Test Form Interactions")
with st.form("test_form"):
    name = st.text_input("Enter your name:")
    age = st.number_input("Enter your age:", min_value=0, max_value=120)
    submit = st.form_submit_button("Submit Form")
    
    if submit:
        st.success(f"Form submitted: Name: {name}, Age: {age}")

# Test selectbox interactions
st.markdown("### Test Selectbox Interactions")
option = st.selectbox(
    "Choose an option:",
    ["Option 1", "Option 2", "Option 3", "Option 4"]
)
st.write(f"You selected: {option}")

# Test dataframe display
st.markdown("### Test DataFrame Display")
st.dataframe(test_data, use_container_width=True)

# Test sidebar interactions
st.sidebar.markdown("### Sidebar Test")
sidebar_option = st.sidebar.selectbox("Sidebar Option:", ["A", "B", "C"])
st.sidebar.write(f"Sidebar selection: {sidebar_option}")

# Status indicator
st.markdown("---")
st.markdown("### Status")
if st.button("🔄 Refresh Status"):
    st.success("✅ Anti-fading measures are active!")
    st.info("💡 Try clicking buttons, interacting with forms, or navigating to see if fading occurs.")
    st.warning("⚠️ If you see any fading, the measures need to be enhanced.")

st.markdown("""
### Instructions for Testing:
1. Click various buttons and observe if the page fades
2. Interact with the dataframe and form elements
3. Navigate between different sections
4. Check if the page maintains consistent appearance

If the page doesn't fade during these interactions, the anti-fading measures are working correctly!
""")
