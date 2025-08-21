import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode, JsCode
import json
from pathlib import Path

def create_debug_agrid():
    """
    Debug version of Equipment Select Options AgGrid to test and fix insertion issues
    """
    st.title("🔧 Equipment Select Options - Debug Mode")
    st.markdown("This is a simplified version to debug AgGrid data insertion and row selection issues.")
    
    # Sample data for testing
    if 'debug_select_options_data' not in st.session_state:
        st.session_state.debug_select_options_data = pd.DataFrame({
            'ID': [1, 2, 3],
            'Option_Type': ['Category', 'Status', 'Location'],
            'Option_Value': ['Electronics', 'Active', 'Lab A'],
            'Description': ['Electronic equipment category', 'Active status', 'Laboratory A location']
        })
    
    # Display current data
    st.subheader("Current Data")
    st.dataframe(st.session_state.debug_select_options_data)
    
    # AgGrid Configuration
    st.subheader("AgGrid with Fixed Configuration")
    
    # Create GridOptionsBuilder
    gb = GridOptionsBuilder.from_dataframe(st.session_state.debug_select_options_data)
    
    # Configure columns
    gb.configure_default_column(
        editable=True,
        resizable=True,
        sortable=True,
        filter=True,
        minWidth=100
    )
    
    # Configure selection
    gb.configure_selection(
        selection_mode='multiple',
        use_checkbox=True,
        pre_selected_rows=[]
    )
    
    # Configure grid options for better data insertion
    gb.configure_grid_options(
        enableRangeSelection=True,
        rowSelection='multiple',
        suppressRowClickSelection=False,
        suppressCellSelection=False,
        stopEditingWhenCellsLoseFocus=True,
        undoRedoCellEditing=True,
        undoRedoCellEditingLimit=20,
        # Key fixes for insertion issues
        suppressClickEdit=False,  # Allow click to edit
        enterMovesDownAfterEdit=True,  # Enter moves to next row
        enterMovesDown=True,
        tabToNextCell=True,
        tabToNextRow=True,
        # Prevent unnecessary refreshes
        deltaSort=False,
        deltaColumnMode=False,
        immutableData=False
    )
    
    # Custom JS to handle cell editing better
    cellvalue_changed_js = JsCode("""
    function(event) {
        console.log('Cell value changed:', event);
        // Don't trigger Streamlit rerun on every cell change
        return false;
    }
    """)
    
    # JS for row selection
    selection_changed_js = JsCode("""
    function(event) {
        console.log('Selection changed:', event);
        // Update selection without triggering full rerun
        return true;
    }
    """)
    
    gb.configure_grid_options(
        onCellValueChanged=cellvalue_changed_js,
        onSelectionChanged=selection_changed_js
    )
    
    # Display AgGrid with optimized settings
    grid_response = AgGrid(
        st.session_state.debug_select_options_data,
        gridOptions=gb.build(),
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.VALUE_CHANGED,  # Changed from MODEL_CHANGED
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        height=400,
        theme='streamlit',
        enable_enterprise_modules=False,
        reload_data=False,  # Prevent unnecessary reloads
        key="debug_select_options_grid"
    )
    
    # Handle data changes
    if grid_response['data'] is not None:
        updated_df = pd.DataFrame(grid_response['data'])
        
        # Only update session state if data actually changed
        if not updated_df.equals(st.session_state.debug_select_options_data):
            st.session_state.debug_select_options_data = updated_df
            st.success("Data updated successfully!")
    
    # Display selected rows
    selected_rows = grid_response['selected_rows']
    if selected_rows:
        st.subheader("Selected Rows")
        st.dataframe(pd.DataFrame(selected_rows))
        st.info(f"Number of selected rows: {len(selected_rows)}")
    
    # Add new row functionality
    st.subheader("Add New Row")
    with st.form("add_new_row"):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            new_id = st.number_input("ID", min_value=1, value=len(st.session_state.debug_select_options_data) + 1)
        
        with col2:
            new_option_type = st.text_input("Option Type")
        
        with col3:
            new_option_value = st.text_input("Option Value")
        
        with col4:
            new_description = st.text_input("Description")
        
        if st.form_submit_button("Add Row"):
            new_row = {
                'ID': new_id,
                'Option_Type': new_option_type,
                'Option_Value': new_option_value,
                'Description': new_description
            }
            
            # Add new row to dataframe
            new_df = pd.concat([st.session_state.debug_select_options_data, pd.DataFrame([new_row])], ignore_index=True)
            st.session_state.debug_select_options_data = new_df
            st.success("New row added successfully!")
            st.rerun()
    
    # Debug information
    st.subheader("Debug Information")
    st.json({
        "Total rows": len(st.session_state.debug_select_options_data),
        "Selected rows count": len(selected_rows) if selected_rows else 0,
        "Grid update mode": "VALUE_CHANGED",
        "Data return mode": "FILTERED_AND_SORTED"
    })
    
    # Reset data button
    if st.button("Reset Data"):
        del st.session_state.debug_select_options_data
        st.rerun()

def main():
    """Main function to run the debug application"""
    st.set_page_config(
        page_title="Equipment Select Options Debug",
        page_icon="🔧",
        layout="wide"
    )
    
    create_debug_agrid()

if __name__ == "__main__":
    main()

# Instructions for running this debug file:
# 1. Save this file as 'equipment_select_options_debug.py'
# 2. Run in terminal: streamlit run equipment_select_options_debug.py
# 3. Test data insertion by:
#    - Clicking on cells to edit them
#    - Pressing Enter to move to next row
#    - Using Tab to move to next cell
#    - Adding new rows using the form at the bottom
# 4. Test row selection by:
#    - Clicking checkboxes to select rows
#    - Checking the console logs for selection feedback
#    - Observing the selected rows display below the grid
