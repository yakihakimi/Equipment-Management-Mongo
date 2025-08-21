"""
Simple CSS Spinner Component for Equipment Management System
Provides a fast loading indicator that can be placed next to buttons during operations.
"""

import streamlit as st
import time
from typing import Optional, Callable, Any

class SimpleSpinnerComponent:
    """
    A simple, fast component that displays a CSS spinner next to buttons during operations.
    """
    
    def __init__(self):
        """Initialize the simple spinner component."""
        pass
    
    def show_spinner(self, container, key: str = "spinner", timeout_seconds: int = 5):
        """
        Display a simple CSS spinner in the specified container.
        
        Args:
            container: Streamlit container to display the spinner in
            key: Unique key for the spinner component
            timeout_seconds: Number of seconds before spinner disappears (default: 5)
        """
        # Initialize session state for this spinner
        spinner_active_key = f"spinner_active_{key}"
        spinner_start_time_key = f"spinner_start_time_{key}"
        
        # Set start time if not already set
        if spinner_start_time_key not in st.session_state:
            st.session_state[spinner_start_time_key] = time.time()
            st.session_state[spinner_active_key] = True
        
        # Check if timeout has elapsed
        elapsed_time = time.time() - st.session_state[spinner_start_time_key]
        if elapsed_time > timeout_seconds:
            # Timeout reached, hide the spinner
            st.session_state[spinner_active_key] = False
            return
        
        # Show the spinner if still active
        if st.session_state.get(spinner_active_key, False):
            with container:
                st.markdown(
                    """
                    <div style="display: flex; align-items: center; justify-content: center;">
                        <div style="width: 20px; height: 20px; border: 2px solid #f3f3f3; border-top: 2px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 5px;"></div>
                        <span style="font-size: 12px; color: #666;">Processing...</span>
                    </div>
                    <style>
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
    
    # Backward compatibility methods
    def show_thinking_gif(self, container, key: str = "thinking_gif", timeout_seconds: int = 5):
        """
        Backward compatibility method - same as show_spinner.
        """
        return self.show_spinner(container, key, timeout_seconds)
    
    def show_simple_thinking(self, container, key: str = "simple_thinking", timeout_seconds: int = 5):
        """
        Backward compatibility method - same as show_spinner.
        """
        return self.show_spinner(container, key, timeout_seconds)
    
    def button_with_spinner(self, 
                           button_text: str, 
                           operation_func: Callable[[], Any],
                           button_key: str,
                           container_key: str = None,
                           timeout_seconds: int = 5,
                           **button_kwargs) -> bool:
        """
        Create a button that shows a spinner immediately when clicked.
        
        Args:
            button_text: Text to display on the button
            operation_func: Function to execute when button is clicked
            button_key: Unique key for the button
            container_key: Unique key for the spinner container
            timeout_seconds: Number of seconds before spinner disappears (default: 5)
            **button_kwargs: Additional arguments to pass to st.button
            
        Returns:
            bool: True if operation completed successfully, False otherwise
        """
        if container_key is None:
            container_key = f"spinner_container_{button_key}"
        
        # Create columns for button and spinner
        col1, col2 = st.columns([1, 0.3])
        
        with col1:
            button_clicked = st.button(button_text, key=button_key, **button_kwargs)
        
        with col2:
            spinner_container = st.container()
        
        # Check if button was clicked in this session
        button_state_key = f"button_clicked_{button_key}"
        if button_clicked:
            # Set button state to show we need to display the spinner
            st.session_state[button_state_key] = True
            
            # Show spinner immediately
            self.show_spinner(spinner_container, container_key, timeout_seconds)
            
            # Execute the operation
            try:
                result = operation_func()
                
                # Clear the button state after operation completes
                st.session_state[button_state_key] = False
                
                return True
            except Exception as e:
                st.error(f"Operation failed: {str(e)}")
                st.session_state[button_state_key] = False
                return False
        
        return False
    
    # Backward compatibility methods
    def button_with_thinking_gif(self, 
                                button_text: str, 
                                operation_func: Callable[[], Any],
                                button_key: str,
                                container_key: str = None,
                                use_simple_indicator: bool = True,
                                timeout_seconds: int = 5,
                                **button_kwargs) -> bool:
        """
        Backward compatibility method - same as button_with_spinner.
        """
        return self.button_with_spinner(button_text, operation_func, button_key, container_key, timeout_seconds, **button_kwargs)
    
    def operation_with_spinner(self, 
                              operation_func: Callable[[], Any],
                              success_message: str = "Operation completed successfully!",
                              error_message: str = "Operation failed!",
                              container_key: str = "spinner_operation",
                              timeout_seconds: int = 5) -> bool:
        """
        Execute an operation with a spinner and success/error messages.
        
        Args:
            operation_func: Function to execute
            success_message: Message to show on success
            error_message: Message to show on error
            container_key: Unique key for the container
            timeout_seconds: Number of seconds before spinner disappears (default: 5)
            
        Returns:
            bool: True if operation completed successfully, False otherwise
        """
        # Create container for spinner
        spinner_container = st.container()
        
        # Show spinner immediately
        self.show_spinner(spinner_container, container_key, timeout_seconds)
        
        try:
            # Execute the operation
            result = operation_func()
            
            # Show success message
            st.success(success_message)
            return True
            
        except Exception as e:
            st.error(f"{error_message}: {str(e)}")
            return False
    
    # Backward compatibility method
    def operation_with_thinking_gif(self, 
                                   operation_func: Callable[[], Any],
                                   success_message: str = "Operation completed successfully!",
                                   error_message: str = "Operation failed!",
                                   container_key: str = "thinking_operation",
                                   use_simple_indicator: bool = True,
                                   timeout_seconds: int = 5) -> bool:
        """
        Backward compatibility method - same as operation_with_spinner.
        """
        return self.operation_with_spinner(operation_func, success_message, error_message, container_key, timeout_seconds)
    
    def kill_spinner(self, key: str):
        """
        Manually kill a specific spinner.
        
        Args:
            key: Unique key for the spinner component
        """
        spinner_active_key = f"spinner_active_{key}"
        if spinner_active_key in st.session_state:
            st.session_state[spinner_active_key] = False
    
    # Backward compatibility methods
    def kill_gif_process(self, key: str):
        """
        Backward compatibility method - same as kill_spinner.
        """
        return self.kill_spinner(key)
    
    def kill_spinner_process(self, key: str):
        """
        Backward compatibility method - same as kill_spinner.
        """
        return self.kill_spinner(key)
    
    def kill_all_spinners(self):
        """
        Kill all active spinners.
        """
        try:
            # Find all active spinner keys in session state
            for key in list(st.session_state.keys()):
                if key.startswith("spinner_active_"):
                    st.session_state[key] = False
            
        except Exception as e:
            st.warning(f"Error killing all spinners: {str(e)}")
    
    # Backward compatibility method
    def kill_all_processes(self):
        """
        Backward compatibility method - same as kill_all_spinners.
        """
        return self.kill_all_spinners()
    
    def get_status(self) -> dict:
        """
        Get the status of the spinner component.
        
        Returns:
            dict: Status information about the spinner component
        """
        # Count active spinners
        active_spinners = sum(1 for key in st.session_state.keys() if key.startswith("spinner_active_") and st.session_state[key])
        
        return {
            "component_type": "Simple CSS Spinner",
            "active_spinners": active_spinners,
            "timeout_default": "5 seconds",
            "performance": "Fast - No GIF loading delays"
        }
    
    # Backward compatibility method
    def get_gif_status(self) -> dict:
        """
        Backward compatibility method - same as get_status.
        """
        return self.get_status()
    
    # Backward compatibility method
    def set_custom_gif_path(self, gif_path: str) -> bool:
        """
        Backward compatibility method - no longer needed, always returns True.
        """
        st.info("GIF functionality has been removed. Using fast CSS spinner instead.")
        return True


def create_simple_spinner_component() -> SimpleSpinnerComponent:
    """
    Factory function to create a simple spinner component.
    
    Returns:
        SimpleSpinnerComponent: A new simple spinner component instance
    """
    return SimpleSpinnerComponent()


# Global instance for easy access
simple_spinner = create_simple_spinner_component()

# Backward compatibility - alias for existing code
thinking_gif = simple_spinner
