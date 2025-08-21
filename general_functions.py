import streamlit as st
import json
from pathlib import Path
import pandas as pd


def is_admin(auth_manager=None):
    """Check if current user is admin (case-insensitive)."""
    if auth_manager:
        username = st.session_state.get('username')
        if username:
            return auth_manager.is_admin_user(username)
    # Fallback check using session state
    user_role = str(st.session_state.get('user_role', '')).lower()
    username = str(st.session_state.get('username', '')).lower()
    return user_role == "admin" or username == "admin"


def apply_column_order(df, data_type):
    """Apply saved column order to DataFrame."""
    try:
        with open('column_order_preferences.json', 'r') as f:
            column_order = json.load(f)
            saved_order = column_order.get(data_type, [])
            if saved_order:
                # Filter to only include columns that exist in the DataFrame
                existing_cols = [col for col in saved_order if col in df.columns]
                # Add any missing columns at the end
                missing_cols = [col for col in df.columns if col not in existing_cols]
                final_order = existing_cols + missing_cols
                return df.reindex(columns=final_order)
    except (FileNotFoundError, Exception):
        pass
    return df


def load_column_order(table_type, default_columns):
    """Load saved column order preference for a specific table type."""
    try:
        column_order_file = Path("column_order_preferences.json")
        
        if column_order_file.exists():
            with open(column_order_file, 'r') as f:
                preferences = json.load(f)
            
            if table_type in preferences:
                saved_order = preferences[table_type]
                # Ensure all current columns are included (in case new columns were added)
                missing_columns = [col for col in default_columns if col not in saved_order]
                # Add any missing columns at the end
                return saved_order + missing_columns
        
        # Return default order if no saved preference
        return default_columns
    except Exception as e:
        # Return default order if there's an error loading preferences
        return default_columns


def save_column_order(table_type, column_order):
    """Save column order preference for a specific table type."""
    try:
        column_order_file = Path("column_order_preferences.json")
        
        # Load existing preferences if file exists
        preferences = {}
        if column_order_file.exists():
            try:
                with open(column_order_file, 'r') as f:
                    preferences = json.load(f)
            except:
                preferences = {}
        
        # Update preferences for this table type
        preferences[table_type] = column_order
        
        # Save back to file
        with open(column_order_file, 'w') as f:
            json.dump(preferences, f, indent=2)
        
        return True
    except Exception as e:
        st.error(f"Error saving column order: {str(e)}")
        return False


def save_filter_order(filter_order):
    """Save filter order preference to a JSON file."""
    try:
        filter_order_file = Path("filter_order_preferences.json")
        
        preferences = {}
        if filter_order_file.exists():
            with open(filter_order_file, 'r') as f:
                preferences = json.load(f)
        
        preferences['equipment_filters'] = filter_order
        
        with open(filter_order_file, 'w') as f:
            json.dump(preferences, f, indent=2)
        
        return True
    except Exception as e:
        st.error(f"Error saving filter order: {str(e)}")
        return False

        # with right_col:
        #     # Use filtered data directly since new rows are now saved immediately to database
        #     self.display_select_options_df = filtered_select_options_df.copy()
            
        #     # Sort display_df by ID column consistently (or fall back to index)
        #     if not self.display_select_options_df.empty:
        #         if 'ID' in self.display_select_options_df.columns:
        #             try:
        #                 # Sort by ID column in ascending order
        #                 if pd.api.types.is_numeric_dtype(self.display_select_options_df['ID']):
        #                     self.display_select_options_df = self.display_select_options_df.sort_values(
        #                         by='ID', ascending=True, na_position='last'
        #                     ).reset_index(drop=True)
        #                 else:
        #                     # Handle mixed/string ID column
        #                     self.display_select_options_df = self.display_select_options_df.sort_values(
        #                         by='ID', 
        #                         ascending=True, 
        #                         na_position='last', 
        #                         key=lambda x: pd.to_numeric(x, errors='coerce').fillna(float('inf'))
        #                     ).reset_index(drop=True)
        #             except Exception:
        #                 # If ID sorting fails, fall back to index sorting
        #                 if 'index' in self.display_select_options_df.columns:
        #                     try:
        #                         self.display_select_options_df = self.display_select_options_df.sort_values(by='index', ascending=True, na_position='last').reset_index(drop=True)
        #                     except Exception:
        #                         pass
        #         elif 'index' in self.display_select_options_df.columns:
        #             try:
        #                 self.display_select_options_df = self.display_select_options_df.sort_values(by='index', ascending=True, na_position='last').reset_index(drop=True)
        #             except Exception:
        #                 # If sorting fails, leave data unsorted
        #                 pass
            
        #     # Check if we need to reapply select all after filtering
        #     if 'reapply_select_all_select_options' in st.session_state and st.session_state['reapply_select_all_select_options']:
        #         # Update the select all rows with the new filtered data
        #         st.session_state['select_all_select_options_rows'] = self.display_select_options_df.to_dict('records')
        #         st.session_state['reapply_select_all_select_options'] = False
        #         # Force grid reload to show the new selection
        #         st.session_state['force_select_options_grid_reload'] = True
        #         st.session_state['select_options_grid_key'] = st.session_state.get('select_options_grid_key', 0) + 1
            
        #     st.subheader("📊 Equipment Select Options")
            
        #     # Add custom Select All / Clear Selection buttons at the top
        #     col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
        #     with col1:
        #         if st.button("☑️ Select All Visible", key="select_all_select_options_btn", help="Select all rows currently visible (after all filtering) - selection will be maintained when filtering"):
        #             # Store the selection data
        #             st.session_state['select_all_select_options_rows'] = self.display_select_options_df.to_dict('records')
        #             st.session_state['select_all_select_options_active'] = True
        #             st.session_state['force_select_options_grid_reload'] = True
        #             st.session_state['select_options_grid_key'] = st.session_state.get('select_options_grid_key', 0) + 1
        #             # Ensure we stay on the current page after rerun
        #             st.session_state['current_page'] = "Equipment Select Options"
            
        #     with col2:
        #         if st.button("⬜ Clear Selection", key="clear_selection_select_options_btn", help="Clear all selected rows"):
        #             # Clear the selection by removing from session state
        #             if 'select_all_select_options_rows' in st.session_state:
        #                 del st.session_state['select_all_select_options_rows']
        #             if 'select_all_select_options_active' in st.session_state:
        #                 del st.session_state['select_all_select_options_active']
        #             # Force grid reload and increment key to force visual update
        #             st.session_state['force_select_options_grid_reload'] = True
        #             st.session_state['select_options_grid_key'] = st.session_state.get('select_options_grid_key', 0) + 1
        #             # Force grid reload and increment key to force visual update
        #             st.session_state['force_select_options_grid_reload'] = True
        #             st.session_state['select_options_grid_key'] = st.session_state.get('select_options_grid_key', 0) + 1
        #             # st.rerun()
            
        #     with col3:
        #         if st.button("🔄 Refresh Selection", key="refresh_selection_select_options_btn", help="Refresh the current selection based on filters"):
        #             # Reapply select all to current filtered data if select all was active
        #             if st.session_state.get('select_all_select_options_active', False):
        #                 st.session_state['select_all_select_options_rows'] = self.display_select_options_df.to_dict('records')
        #                 st.session_state['force_select_options_grid_reload'] = True
        #                 st.session_state['select_options_grid_key'] = st.session_state.get('select_options_grid_key', 0) + 1
        #             st.rerun()
            
        #     # Get user permissions
        #     permissions = self.auth_manager.get_user_permissions()

        #     # Configure AgGrid for Select Options
        #     gb = GridOptionsBuilder.from_dataframe(self.display_select_options_df)
            
        #     # Enable editing based on permissions
        #     gb.configure_default_column(
        #         editable=permissions["can_edit"], 
        #         groupable=True, 
        #         resizable=True, 
        #         sortable=True, 
        #         filter=True,
        #         flex=1,  # Enable flexible column sizing
        #         minWidth=80,  # Set minimum width for all columns
        #         singleClickEdit=True,  # Enable single-click editing for better responsiveness
        #         stopEditingWhenCellsLoseFocus=True  # Save edits when cell loses focus
        #     )
            
        #     # Configure specific columns with flexible sizing
        #     for col in self.display_select_options_df.columns:
        #         col_lower = col.lower()
                
        #         if col == 'index':
        #             # Make index column non-editable and fixed narrow width (not pinned to allow checkboxes on the left)
        #             gb.configure_column(col, editable=False, width=100, flex=0)
        #         elif any(term in col_lower for term in ['id', '_id']):
        #             # ID columns - make read-only with small flex ratio
        #             gb.configure_column(col, editable=False, flex=0.5, minWidth=60, maxWidth=120)
        #         elif any(term in col_lower for term in ['serial', 'ser_num', 'serial_number']):
        #             # Serial number columns - medium flex ratio with validation styling
        #             gb.configure_column(
        #                 col, 
        #                 editable=permissions["can_edit"],
        #                 flex=1, 
        #                 minWidth=120, 
        #                 maxWidth=250,
        #                 cellStyle={'backgroundColor': '#fff3cd', 'border': '1px solid #ffeaa7'},  # Light yellow background
        #                 headerTooltip=f"Serial numbers should be unique for better organization."
        #             )
        #         elif any(term in col_lower for term in ['description', 'comments']):
        #             # Description columns - large text editor with higher flex ratio
        #             gb.configure_column(
        #                 col, 
        #                 editable=permissions["can_edit"], 
        #                 cellEditor='agLargeTextCellEditor', 
        #                 cellEditorPopup=True,
        #                 flex=2,  # Give more space to description columns
        #                 minWidth=150
        #             )
        #         elif any(term in col_lower for term in ['date', 'cal']):
        #             # Date columns - smaller flex ratio
        #             gb.configure_column(
        #                 col, 
        #                 editable=permissions["can_edit"], 
        #                 type=["dateColumnFilter", "customDateTimeFormat"], 
        #                 custom_format_string='yyyy-MM-dd',
        #                 flex=0.8,
        #                 minWidth=100
        #             )
        #         elif any(term in col_lower for term in ['value', 'price', 'cost', 'year']):
        #             # Numeric columns - smaller flex ratio
        #             gb.configure_column(
        #                 col, 
        #                 editable=permissions["can_edit"], 
        #                 type=["numericColumn", "numberColumnFilter", "customNumericFormat"], 
        #                 precision=2,
        #                 flex=0.7,
        #                 minWidth=80
        #             )
        #         else:
        #             # Default columns - standard flex ratio
        #             gb.configure_column(col, editable=permissions["can_edit"], flex=1, minWidth=100)
            
        #     # Enable selection (with checkboxes for row selection on the left)
        #     gb.configure_selection(
        #         selection_mode="multiple", 
        #         use_checkbox=True
        #     )
            
        #     # Enable pagination
        #     gb.configure_pagination(enabled=True, paginationPageSize=20)
            
        #     # Configure grid options for better checkbox functionality and left-side checkboxes
        #     gb.configure_grid_options(
        #         suppressColumnVirtualisation=False,
        #         suppressRowVirtualisation=False,
        #         enableRangeSelection=True,
        #         rowSelection='multiple',
        #         rowMultiSelectWithClick=True,  # Enable multi-select
        #         suppressRowDeselection=False,  # Allow deselection
        #         animateRows=True,
        #         suppressMovableColumns=False,
        #         enableCellTextSelection=True,
        #         headerHeight=40,  # Ensure header is tall enough for checkbox
        #         checkboxSelection=True,  # Enable checkbox selection on the left
        #         headerCheckboxSelection=True,  # Enable header checkbox for select all
        #         suppressRowClickSelection=False  # Allow row click selection
        #     )
            
        #     # Pre-select rows if we're in "select all" mode
        #     if 'select_all_select_options_rows' in st.session_state:
        #         # Add JavaScript to select all visible rows on grid ready
        #         pre_select_js = """
        #         function onGridReady(params) {
        #             setTimeout(function() {
        #                 params.api.selectAll();
        #             }, 100);
        #         }
        #         """
                
        #         # Custom JS for cell editing that doesn't trigger page refresh
        #         cell_edit_js = """
        #         function(event) {
        #             console.log('Cell value changed:', event);
        #             // Don't trigger Streamlit rerun on cell change
        #             // Let VALUE_CHANGED mode handle the updates
        #             return false;
        #         }
        #         """
                
        #         # Custom JS for better row selection feedback
        #         selection_changed_js = """
        #         function(event) {
        #             console.log('Selection changed:', event.api.getSelectedRows().length + ' rows selected');
        #             // Update selection indicator without full rerun
        #             const selectedRows = event.api.getSelectedRows();
        #             if (selectedRows.length > 0) {
        #                 console.log('Selected rows:', selectedRows);
        #             }
        #             return true;
        #         }
        #         """
                
        #         # Enhanced cell editing JS to prevent unnecessary refreshes
        #         cell_edit_js = """
        #         function(event) {
        #             console.log('Cell value changed - Select All Mode:', event.oldValue, '->', event.newValue);
        #             // Minimal processing to prevent refresh
        #             return false;
        #         }
        #         """
                
        #         # Enhanced selection JS for better feedback
        #         selection_changed_js = """
        #         function(event) {
        #             const rowCount = event.api.getSelectedRows().length;
        #             console.log('Selection changed - Select All Mode:', rowCount + ' rows selected');
        #             // Update visual indicators without triggering Streamlit refresh
        #             return true;
        #         }
        #         """
                
        #         gb.configure_grid_options(
        #             onGridReady=JsCode(pre_select_js),
        #             onCellValueChanged=JsCode(cell_edit_js),
        #             onSelectionChanged=JsCode(selection_changed_js)
        #         )
        #     else:
        #         # Optimized JS for normal mode - prevents refresh on first edit
        #         cell_edit_optimized_js = """
        #         function(event) {
        #             console.log('Cell edit (Normal Mode):', event.colDef.field, ':', event.oldValue, '->', event.newValue);
        #             // Let AgGrid handle the edit without triggering immediate Streamlit refresh
        #             // This prevents the "first edit refresh" issue
        #             return false;
        #         }
        #         """
                
        #         # Selection handling for normal mode
        #         selection_optimized_js = """
        #         function(event) {
        #             const selectedRows = event.api.getSelectedRows();
        #             console.log('Row selection (Normal Mode):', selectedRows.length + ' rows selected');
        #             // Ensure selection indicators are reliable
        #             if (selectedRows.length > 0) {
        #                 console.log('Selected row IDs:', selectedRows.map(row => row.ID || row.id || 'no-id'));
        #             }
        #             return true;
        #         }
        #         """
                
        #         gb.configure_grid_options(
        #             onCellValueChanged=JsCode(cell_edit_optimized_js),
        #             onSelectionChanged=JsCode(selection_optimized_js)
        #         )
            
        #     # Enable adding new rows (only for users with edit permissions)
        #     if permissions["can_edit"]:
        #         gb.configure_grid_options(
        #             enableRangeSelection=True,
        #             rowSelection='multiple',
        #             suppressRowClickSelection=False,
        #             suppressCellSelection=False,  # Allow cell selection without triggering rerun
        #             suppressRowDeselection=False,
        #             suppressMultiRangeSelection=False,
        #             stopEditingWhenCellsLoseFocus=True,  # Auto-save when losing focus
        #             undoRedoCellEditing=True,  # Enable undo/redo for better UX
        #             undoRedoCellEditingLimit=20,  # Limit undo history
        #             # Additional options for better cell editing
        #             suppressClickEdit=False,  # Allow click to edit
        #             enterMovesDownAfterEdit=True,  # Enter moves to next row after edit
        #             enterMovesDown=True,  # Enter moves down in general
        #             tabToNextCell=True,  # Tab moves to next cell
        #             tabToNextRow=True,  # Tab moves to next row when at end
        #             singleClickEdit=True,  # Enable single click to edit
        #             suppressNavigationWithArrowKeys=False,  # Allow arrow key navigation
        #             # Prevent unnecessary refreshes
        #             deltaSort=False,
        #             deltaColumnMode=False,
        #             immutableData=False
        #         )
            
        #     # Check for select all mode and force grid reload if needed
        #     force_reload = 'force_select_options_grid_reload' in st.session_state and st.session_state['force_select_options_grid_reload']
        #     if force_reload:
        #         st.session_state['force_select_options_grid_reload'] = False
            
        #     # Initialize stable grid key to prevent unnecessary reloads
        #     if 'select_options_grid_key' not in st.session_state:
        #         st.session_state['select_options_grid_key'] = 0
            
        #     # Add New Row functionality will be moved AFTER AgGrid for better UX
            
        #     # Determine what data to display in AgGrid
        #     grid_data = self.display_select_options_df
        #     if (st.session_state.get('select_all_select_options_active', False) and 
        #         'select_all_select_options_rows' in st.session_state and
        #         len(st.session_state['select_all_select_options_rows']) < len(self.display_select_options_df)):
        #         # We're in select all mode with filtered data - create DataFrame from selected rows
        #         grid_data = pd.DataFrame(st.session_state['select_all_select_options_rows'])
        #         # Ensure it has the same column order as display_select_options_df
        #         if not grid_data.empty:
        #             grid_data = grid_data.reindex(columns=self.display_select_options_df.columns, fill_value='')
            
        #     # Display the AgGrid with optimized settings
        #     grid_response = AgGrid(
        #         grid_data,
        #         gridOptions=gb.build(),
        #         data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        #         update_mode=GridUpdateMode.MODEL_CHANGED,  # Use MODEL_CHANGED as requested
        #         allow_unsafe_jscode=True,
        #         fit_columns_on_grid_load=True,  # Enable auto-fitting columns to content
        #         height=600,
        #         theme='streamlit',
        #         enable_enterprise_modules=False,
        #         reload_data=force_reload,
        #         key=f"select_options_grid_{st.session_state.get('select_options_grid_key', 0)}"
        #     )
            
        #     # Get the selected rows for use in row management below
        #     selected_rows = grid_response['selected_rows']
            
        #     # Get the currently visible/filtered data from AgGrid (after internal filtering)
        #     visible_data = grid_response['data']  # This contains only the rows visible after AgGrid filtering
            
        #     # Handle refresh selection request with actual visible data
        #     if st.session_state.get('refresh_select_options_selection_requested', False):
        #         if 'select_all_select_options_rows' in st.session_state:
        #             # Convert visible_data to the correct format if it's a DataFrame
        #             if isinstance(visible_data, pd.DataFrame):
        #                 st.session_state['select_all_select_options_rows'] = visible_data.to_dict('records')
        #             else:
        #                 st.session_state['select_all_select_options_rows'] = visible_data
        #             st.session_state['selection_auto_updated'] = True
        #         st.session_state['refresh_select_options_selection_requested'] = False  # Clear the flag
            
        #     # Check if AgGrid filtering resulted in empty data and we should show a message
        #     if len(visible_data) == 0 and len(grid_data) > 0:
        #         st.session_state['show_empty_filter_message'] = True
            
        #     # Track AgGrid internal filtering changes more conservatively
        #     current_visible_count = len(visible_data)
            
        #     # Create a more stable signature that doesn't change on every interaction
        #     if current_visible_count > 0:
        #         visible_signature = f"count_{current_visible_count}"
        #     else:
        #         visible_signature = "empty"
            
        #     # Initialize tracking if not exists
        #     if 'previous_visible_select_options_signature' not in st.session_state:
        #         st.session_state['previous_visible_select_options_signature'] = visible_signature
        #         st.session_state['select_options_signature_stable_count'] = 0
            
        #     # Only update selection if we're in select all mode - simplified logic
        #     if 'select_all_select_options_rows' in st.session_state and st.session_state['previous_visible_select_options_signature'] != visible_signature:
        #         # Only update if we have visible data (not empty)
        #         if current_visible_count > 0:
        #             # Convert visible_data to the correct format if it's a DataFrame
        #             if isinstance(visible_data, pd.DataFrame):
        #                 st.session_state['select_all_select_options_rows'] = visible_data.to_dict('records')
        #             else:
        #                 st.session_state['select_all_select_options_rows'] = visible_data
        #             st.session_state['selection_auto_updated'] = True
        #         else:
        #             st.session_state['show_empty_filter_message'] = True
            
        #     # Update the tracked signature
        #     st.session_state['previous_visible_select_options_signature'] = visible_signature
            
        #     # Check if we're in "select all" mode and override selected_rows
        #     if 'select_all_select_options_rows' in st.session_state:
        #         selected_rows = st.session_state['select_all_select_options_rows']
            
        #     # Show notification if selection was automatically updated due to filtering (reduce noise)
        #     if st.session_state.get('selection_auto_updated', False) and st.session_state.get('show_selection_messages', True):
        #         st.success("🔄 **Selection automatically updated** to match filtered results!")
        #         st.session_state['selection_auto_updated'] = False  # Clear the flag
            
        #     # Show notification if showing all data due to empty AgGrid filters (reduce noise)  
        #     if st.session_state.get('show_empty_filter_message', False) and st.session_state.get('show_selection_messages', True):
        #         st.info("📄 **Showing all data** - AgGrid filters resulted in no matches, displaying complete dataset")
        #         st.session_state['show_empty_filter_message'] = False  # Clear the flag
            
        #     # Display selection help
        #     if selected_rows is not None and len(selected_rows) > 0:
        #         if 'select_all_select_options_rows' in st.session_state:
        #             st.info(f"✅ **ALL {len(selected_rows)} row(s) selected** (Select All mode - automatically adapts to sidebar filters, use 'Refresh Selection' after AgGrid column filtering) - Use the buttons below for bulk operations")
        #         else:
        #             st.info(f"✅ **{len(selected_rows)} row(s) selected** ")
            
        #     # Get edited data from AgGrid
        #     self.edited_select_options_df = grid_response['data']
            
        #     # Add New Row functionality AFTER AgGrid (only for users with edit permissions)
        #     if permissions["can_edit"]:
        #         st.markdown("---")  # Add separator
        #         self._render_add_new_row_section_select_options()
        #         st.markdown("---")  # Add separator
            
        #     # Save Changes to Database button moved to row management section for better UX
            
        #     # For non-edit users, show a read-only message and revert any changes
        #     if not permissions["can_edit"]:
        #         # Check if any changes were made by comparing with original data
        #         if not self.edited_select_options_df.equals(self.display_select_options_df):
        #             st.info("ℹ️ **Read-Only Mode**: You can view dropdown options but cannot make changes. Contact an admin to modify data.")
        #             # Revert changes to prevent unauthorized modifications
        #             self.edited_select_options_df = self.display_select_options_df.copy()
        #         else:
        #             st.info("👀 **Read-only mode** - You can view data but cannot make changes.")
            
        #     # Add row management below the grid (only for users with edit permissions)
        #     if permissions["can_edit"]:
        #         col1, col2, col3 = st.columns([1, 1, 2])
                
        #         # Note: The "Add New Row" button is now positioned below the grid for better user experience
        #         # via the form-based implementation below the grid
                
        #         with col1:
        #             if st.button("💾 Save Changes to Database", key="save_changes_btn_select_options"):
        #                 self._save_select_options_changes_to_database()
                
        #         with col2:
        #             if st.button("🗑️ Remove Selected", type="primary", key="delete_select_options_selected_btn"):
        #                 if selected_rows is not None and len(selected_rows) > 0:
        #                     if permissions.get("can_delete", True):  # Default to True for select options if not specified
        #                         try:
        #                             # Handle different selected_rows formats
        #                             if isinstance(selected_rows, pd.DataFrame):
        #                                 # Convert DataFrame to list of dictionaries
        #                                 selected_rows = selected_rows.to_dict('records')
        #                             elif not isinstance(selected_rows, (list, tuple)):
        #                                 st.error(f"❌ Invalid selected_rows type: {type(selected_rows)}")
        #                                 return
                                    
        #                             # Delete from database
        #                             delete_count = 0
        #                             errors = []
                                    
        #                             for i, selected_row in enumerate(selected_rows):
        #                                 try:
        #                                     # Handle both dict and non-dict selected rows
        #                                     if isinstance(selected_row, dict) and 'index' in selected_row:
        #                                         result = self.Equipment_select_options.delete_one({"index": selected_row['index']})
        #                                         if result.deleted_count > 0:
        #                                             delete_count += 1
        #                                         else:
        #                                             errors.append(f"Row {i+1}: No document found with index {selected_row['index']}")
        #                                     elif hasattr(selected_row, 'get') and selected_row.get('index'):
        #                                         result = self.Equipment_select_options.delete_one({"index": selected_row['index']})
        #                                         if result.deleted_count > 0:
        #                                             delete_count += 1
        #                                         else:
        #                                             errors.append(f"Row {i+1}: No document found with index {selected_row.get('index')}")
        #                                     else:
        #                                         errors.append(f"Row {i+1}: Missing or invalid 'index' field - type: {type(selected_row)}, data: {selected_row}")
        #                                 except Exception as e:
        #                                     errors.append(f"Row {i+1}: Error - {str(e)}")
                                    
        #                             if delete_count > 0:
        #                                 st.success(f"🗑️ Deleted {delete_count} selected rows from the database.")
        #                                 if errors:
        #                                     st.warning(f"⚠️ {len(errors)} row(s) had issues: {'; '.join(errors[:3])}{'...' if len(errors) > 3 else ''}")
                                        
        #                                 # Reload data
        #                                 self.Equipment_select_options_db_records = list(self.Equipment_select_options.find({}, {'_id': 0}))
        #                                 self.Equipment_select_options_db_df = pd.DataFrame(self.Equipment_select_options_db_records)
        #                                 if 'index' not in self.Equipment_select_options_db_df.columns:
        #                                     self.Equipment_select_options_db_df['index'] = self.Equipment_select_options_db_df.index
                                        
        #                                 # Reassign sequential IDs after deletion to maintain continuity
        #                                 if not self.Equipment_select_options_db_df.empty:
        #                                     self.Equipment_select_options_db_df['ID'] = [int(i) for i in range(1, len(self.Equipment_select_options_db_df) + 1)]
        #                                     # Update IDs in database
        #                                     for idx, row in self.Equipment_select_options_db_df.iterrows():
        #                                         if 'index' in row and pd.notna(row['index']):
        #                                             self.Equipment_select_options.update_one(
        #                                                 {"index": row['index']},
        #                                                 {"$set": {"ID": row['ID']}}
        #                                             )
                                            
        #                                     # Sort by ID after reassignment
        #                                     try:
        #                                         self.Equipment_select_options_db_df = self.Equipment_select_options_db_df.sort_values(
        #                                             by='ID', ascending=True, na_position='last'
        #                                         ).reset_index(drop=True)
        #                                     except Exception:
        #                                         pass
                                        
        #                                 # Apply admin-saved column order after data reload
        #                                 self.Equipment_select_options_db_df = self._apply_column_order(self.Equipment_select_options_db_df, 'select_options')
                                        
        #                                 # Clear selection and force grid reload
        #                                 if 'select_all_select_options_rows' in st.session_state:
        #                                     del st.session_state['select_all_select_options_rows']
        #                                 st.session_state['select_all_select_options_active'] = False
        #                                 st.session_state['force_select_options_grid_reload'] = True
        #                                 st.session_state['select_options_grid_key'] = st.session_state.get('select_options_grid_key', 0) + 1
        #                                 # No st.rerun() needed - grid reload mechanism will handle the refresh
        #                             else:
        #                                 error_msg = f"❌ Failed to delete selected rows. Errors: {'; '.join(errors[:5])}{'...' if len(errors) > 5 else ''}"
        #                                 st.error(error_msg)
        #                         except Exception as e:
        #                             st.error(f"❌ Error during deletion: {str(e)}")
        #                     else:
        #                         st.error("🚫 You don't have permission to delete rows.")
        #                 else:
        #                     st.warning("⚠️ Please select rows first in order to delete them.")
                
        #         with col3:
        #             # Add download selected option for admin (always show button)
        #             if st.session_state.get("user_role") == "admin":
        #                 if selected_rows is not None and len(selected_rows) > 0:
        #                     selected_df = pd.DataFrame(selected_rows)
        #                     selected_csv = selected_df.to_csv(index=False)
        #                     st.download_button(
        #                         label=f"📤 Download Selected ({len(selected_rows)} rows)",
        #                         data=selected_csv,
        #                         file_name="selected_select_options.csv",
        #                         mime="text/csv",
        #                         key="download_select_options_selected_btn"
        #                     )
        #                 else:
        #                     st.button(
        #                         "📤 Download Selected (0 rows)", 
        #                         disabled=True, 
        #                         key="download_select_options_selected_disabled_btn",
        #                         help="Select rows first to enable download"
        #                     )
        # #########################################