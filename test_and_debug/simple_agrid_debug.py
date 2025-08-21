import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode

def simple_agrid_test():
    """
    Simple AgGrid test to isolate the data insertion and refresh issue
    """
    st.title("🔧 Simple AgGrid Debug - Equipment Select Options")
    st.markdown("**Minimal test to identify the refresh and data insertion issue**")
    
    # Initialize data ONCE in session state
    if 'test_data' not in st.session_state:
        st.session_state.test_data = pd.DataFrame({
            'ID': [1, 2, 3],
            'Option_Type': ['Category', 'Status', 'Location'],
            'Option_Value': ['Electronics', 'Active', 'Lab A'],
            'Description': ['Electronic equipment', 'Active status', 'Laboratory A']
        })
    
    st.subheader("Current Data in Session State")
    st.dataframe(st.session_state.test_data)
    
    st.subheader("AgGrid Test - MODEL_CHANGED Mode")
    
    # Create GridOptions
    gb = GridOptionsBuilder.from_dataframe(st.session_state.test_data)
    
    # Configure for editing
    gb.configure_default_column(
        editable=True,
        resizable=True,
        sortable=True,
        filter=True
    )
    
    # Configure selection
    gb.configure_selection(
        selection_mode='multiple',
        use_checkbox=True
    )
    
    # Enhanced editing configuration
    gb.configure_grid_options(
        suppressClickEdit=False,
        enterMovesDownAfterEdit=True,
        enterMovesDown=True,
        tabToNextCell=True,
        singleClickEdit=True,
        stopEditingWhenCellsLoseFocus=True,
        undoRedoCellEditing=True,
        rowSelection='multiple',
        checkboxSelection=True,
        headerCheckboxSelection=True
    )
    
    # Display AgGrid - CRITICAL: Use session state data directly
    grid_response = AgGrid(
        st.session_state.test_data,  # Use session state data directly
        gridOptions=gb.build(),
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        height=400,
        theme='streamlit',
        key="simple_debug_grid"  # Fixed key
    )
    
    # Handle the response
    st.subheader("Grid Response Analysis")
    
    # Get current data from grid
    current_data = grid_response['data']
    selected_rows = grid_response['selected_rows']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Data returned from AgGrid:**")
        if current_data is not None:
            current_df = pd.DataFrame(current_data)
            st.dataframe(current_df)
            
            # CRITICAL: Update session state ONLY if data actually changed
            if not current_df.equals(st.session_state.test_data):
                st.session_state.test_data = current_df.copy()
                st.success("✅ Session state updated with grid changes!")
                
                # Show what changed
                st.write("**Change detected:**")
                st.write(f"- Original rows: {len(st.session_state.test_data)}")
                st.write(f"- Current rows: {len(current_df)}")
        else:
            st.error("❌ No data returned from AgGrid!")
    
    with col2:
        st.write("**Selected Rows:**")
        if selected_rows is not None and len(selected_rows) > 0:
            st.dataframe(pd.DataFrame(selected_rows))
            st.info(f"✅ {len(selected_rows)} rows selected")
        else:
            st.info("No rows selected")
    
    # Debug information
    st.subheader("🔍 Debug Info")
    debug_info = {
        "Session state data rows": len(st.session_state.test_data),
        "Grid returned data": current_data is not None,
        "Grid data rows": len(current_data) if current_data is not None else 0,
        "Selected rows": len(selected_rows) if selected_rows else 0,
        "Data types match": type(current_data).__name__ if current_data is not None else "None"
    }
    st.json(debug_info)
    
    # Manual add row test
    st.subheader("📝 Add Row Test")
    with st.form("add_row_test"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            new_id = st.number_input("ID", value=len(st.session_state.test_data) + 1)
        with col2:
            new_type = st.text_input("Type", value="New")
        with col3:
            new_value = st.text_input("Value", value="New Value")
        with col4:
            new_desc = st.text_input("Description", value="New Description")
        
        if st.form_submit_button("Add Row"):
            new_row = pd.DataFrame([{
                'ID': new_id,
                'Option_Type': new_type,
                'Option_Value': new_value,
                'Description': new_desc
            }])
            
            # Add to session state
            st.session_state.test_data = pd.concat([st.session_state.test_data, new_row], ignore_index=True)
            st.success("Row added to session state!")
            st.rerun()
    
    # Reset button
    if st.button("🔄 Reset Data"):
        st.session_state.test_data = pd.DataFrame({
            'ID': [1, 2, 3],
            'Option_Type': ['Category', 'Status', 'Location'],
            'Option_Value': ['Electronics', 'Active', 'Lab A'],
            'Description': ['Electronic equipment', 'Active status', 'Laboratory A']
        })
        st.success("Data reset!")
        st.rerun()

def main():
    st.set_page_config(
        page_title="Simple AgGrid Debug",
        page_icon="🔧",
        layout="wide"
    )
    
    simple_agrid_test()

if __name__ == "__main__":
    main()

# Test Instructions:
# 1. Run: streamlit run simple_agrid_debug.py
# 2. Click on a cell and edit it, then press Enter
# 3. Check if the page refreshes and data is lost
# 4. Try selecting rows and check if indicators work
# 5. Use the "Add Row Test" form to add data
# 6. Observe the debug information for data flow issues
