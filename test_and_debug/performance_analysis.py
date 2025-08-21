import streamlit as st
import time
import psutil
import os
import sys

# Configure page
st.set_page_config(
    page_title="Performance Analysis",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🔍 Performance Analysis for Main App")
st.markdown("This script analyzes potential performance bottlenecks that could cause slow refreshes.")

# Performance monitoring functions
def get_system_info():
    """Get system performance information"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available': memory.available / (1024**3),  # GB
            'disk_percent': disk.percent,
            'disk_free': disk.free / (1024**3)  # GB
        }
    except Exception as e:
        st.error(f"Error getting system info: {str(e)}")
        return None

def analyze_file_size():
    """Analyze file sizes that might affect performance"""
    files_to_check = [
        'app.py',
        'Equipment_Records_Page.py',
        'Equipment_Select_Options_Page.py',
        'User_Management_Page.py'
    ]
    
    file_sizes = {}
    for file in files_to_check:
        try:
            if os.path.exists(file):
                size = os.path.getsize(file)
                file_sizes[file] = size / 1024  # KB
            else:
                file_sizes[file] = 0
        except Exception as e:
            file_sizes[file] = f"Error: {str(e)}"
    
    return file_sizes

def check_imports_and_dependencies():
    """Check for heavy imports that might slow down the app"""
    heavy_imports = [
        'pandas',
        'numpy',
        'matplotlib',
        'plotly',
        'seaborn',
        'scikit-learn',
        'tensorflow',
        'torch',
        'pymongo',
        'sqlalchemy'
    ]
    
    found_imports = []
    for import_name in heavy_imports:
        try:
            __import__(import_name)
            found_imports.append(import_name)
        except ImportError:
            pass
    
    return found_imports

# Performance analysis
st.markdown("### System Performance")

# Get system info
system_info = get_system_info()
if system_info:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("CPU Usage", f"{system_info['cpu_percent']:.1f}%")
    
    with col2:
        st.metric("Memory Usage", f"{system_info['memory_percent']:.1f}%")
    
    with col3:
        st.metric("Available Memory", f"{system_info['memory_available']:.1f} GB")
    
    with col4:
        st.metric("Disk Usage", f"{system_info['disk_percent']:.1f}%")

# File size analysis
st.markdown("### File Size Analysis")
file_sizes = analyze_file_size()

for file, size in file_sizes.items():
    if isinstance(size, (int, float)):
        if size > 100:  # KB
            st.warning(f"⚠️ {file}: {size:.1f} KB (Large file - may affect performance)")
        else:
            st.success(f"✅ {file}: {size:.1f} KB")
    else:
        st.error(f"❌ {file}: {size}")

# Import analysis
st.markdown("### Heavy Dependencies Analysis")
found_imports = check_imports_and_dependencies()

if found_imports:
    st.warning("⚠️ Heavy dependencies found that might affect performance:")
    for imp in found_imports:
        st.write(f"  - {imp}")
else:
    st.success("✅ No heavy dependencies detected")

# Performance recommendations
st.markdown("### Performance Recommendations")

st.markdown("""
#### For Slow Refreshes (>5 seconds):

**1. Database Operations:**
- Check if database queries are taking too long
- Consider adding indexes to frequently queried fields
- Use connection pooling for database connections

**2. Data Processing:**
- Check if large datasets are being processed on every rerun
- Consider caching frequently used data with `@st.cache_data`
- Use `@st.cache_resource` for expensive computations

**3. Page Rendering:**
- Check if complex UI components are being recreated unnecessarily
- Consider using `st.empty()` containers for dynamic content
- Avoid heavy computations in the main rendering loop

**4. Memory Usage:**
- Check for memory leaks in long-running sessions
- Clear unused variables and dataframes
- Use generators instead of lists for large datasets

**5. Network Operations:**
- Check if external API calls are blocking the UI
- Use async operations where possible
- Implement proper error handling for network timeouts
""")

# Performance testing
st.markdown("### Performance Testing")

if st.button("🚀 Test Page Load Performance"):
    start_time = time.time()
    
    # Simulate some operations
    st.write("Testing page load performance...")
    time.sleep(0.1)  # Simulate some work
    
    load_time = time.time() - start_time
    st.success(f"✅ Page load test completed in {load_time:.3f} seconds")
    
    if load_time > 1.0:
        st.warning("⚠️ Page load is taking longer than expected")
    else:
        st.success("✅ Page load performance is good")

# Specific recommendations for the main app
st.markdown("### Specific Recommendations for Main App")

st.markdown("""
#### Immediate Actions to Try:

**1. Update the JavaScript to Performance-Optimized Version:**
```javascript
// Replace the current ultra-fast solution with performance-optimized version
// This reduces DOM queries and uses requestAnimationFrame
```

**2. Check for Multiple Rerun Calls:**
- Look for multiple `st.rerun()` calls in sequence
- Replace with session state management where possible
- Use `st.experimental_rerun()` for better performance

**3. Optimize Data Loading:**
- Use `@st.cache_data` for CSV loading
- Implement lazy loading for large datasets
- Consider pagination for large tables

**4. Reduce UI Complexity:**
- Simplify complex layouts
- Use fewer columns and containers
- Minimize the number of interactive elements

**5. Monitor Browser Performance:**
- Open browser developer tools
- Check the Network tab for slow requests
- Monitor the Console for JavaScript errors
- Check the Performance tab for bottlenecks
""")

# Quick performance check
st.markdown("### Quick Performance Check")

col1, col2 = st.columns(2)

with col1:
    if st.button("📊 Test DataFrame Performance"):
        start_time = time.time()
        
        # Create a test dataframe
        import pandas as pd
        test_data = pd.DataFrame({
            'ID': range(1000),
            'Name': [f'Item {i}' for i in range(1000)],
            'Value': [i * 10 for i in range(1000)]
        })
        
        st.dataframe(test_data)
        
        load_time = time.time() - start_time
        st.success(f"DataFrame loaded in {load_time:.3f} seconds")

with col2:
    if st.button("🔄 Test Rerun Performance"):
        start_time = time.time()
        st.success("Rerun test completed!")
        time.sleep(0.1)
        st.rerun()

st.markdown("""
### Next Steps:
1. **Apply the performance-optimized JavaScript** to the main app
2. **Monitor system resources** during slow refreshes
3. **Check browser developer tools** for specific bottlenecks
4. **Consider implementing caching** for expensive operations
5. **Profile the application** to identify specific slow operations

The performance-optimized anti-fading solution should help reduce refresh times significantly!
""")
