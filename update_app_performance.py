#!/usr/bin/env python3
"""
Script to update app.py with performance-optimized anti-fading JavaScript
"""

import re

def update_app_performance():
    """Update app.py with performance-optimized anti-fading JavaScript"""
    
    # Read the current app.py file
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Performance-optimized JavaScript
    performance_js = '''
            <script>
            // Performance-Optimized Anti-Fading JavaScript for Complex Streamlit Applications
            
            // Performance-optimized function to prevent fading during rerun
            function performanceOptimizedAntiFade() {
                // Use requestAnimationFrame for better performance
                requestAnimationFrame(function() {
                    // Immediately force all critical elements
                    document.body.style.backgroundColor = '#ffffff';
                    document.body.style.transition = 'none';
                    document.body.style.opacity = '1';
                    document.body.style.animation = 'none';
                    
                    // Force Streamlit app container first (most important)
                    const appContainer = document.querySelector('.stApp');
                    if (appContainer) {
                        appContainer.style.backgroundColor = '#ffffff';
                        appContainer.style.transition = 'none';
                        appContainer.style.opacity = '1';
                        appContainer.style.animation = 'none';
                    }
                    
                    // Force all Streamlit decoration elements
                    const decorationElements = document.querySelectorAll('[data-testid="stDecoration"]');
                    for (let i = 0; i < decorationElements.length; i++) {
                        const element = decorationElements[i];
                        element.style.backgroundColor = '#ffffff';
                        element.style.opacity = '1';
                        element.style.transition = 'none';
                        element.style.animation = 'none';
                    }
                    
                    // Force critical Streamlit components only (performance optimization)
                    const criticalElements = document.querySelectorAll('.stButton, .stSelectbox, .stTextInput, .stDataFrame');
                    for (let i = 0; i < criticalElements.length; i++) {
                        const element = criticalElements[i];
                        element.style.transition = 'none';
                        element.style.animation = 'none';
                        element.style.opacity = '1';
                    }
                });
            }
            
            // Ultra-fast monitoring with performance optimization
            function performanceOptimizedMonitoring() {
                // Use a more efficient MutationObserver
                const observer = new MutationObserver(function(mutations) {
                    let needsFix = false;
                    
                    // Process mutations in batches for better performance
                    for (let i = 0; i < mutations.length; i++) {
                        const mutation = mutations[i];
                        if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                            const target = mutation.target;
                            if (target.style.opacity && target.style.opacity !== '1') {
                                target.style.opacity = '1';
                                target.style.transition = 'none';
                                needsFix = true;
                            }
                            if (target.style.backgroundColor && 
                                target.style.backgroundColor !== '#ffffff' && 
                                target.style.backgroundColor !== 'rgb(255, 255, 255)') {
                                target.style.backgroundColor = '#ffffff';
                                needsFix = true;
                            }
                        }
                    }
                    
                    // If any changes were made, run the optimized fix
                    if (needsFix) {
                        performanceOptimizedAntiFade();
                    }
                });
                
                // Observe everything immediately
                observer.observe(document.body, {
                    attributes: true,
                    attributeFilter: ['style'],
                    subtree: true,
                    childList: true
                });
            }
            
            // Performance-optimized event handlers
            function setupPerformanceOptimizedHandlers() {
                // Handle visibility changes (rerun indicator)
                document.addEventListener('visibilitychange', function() {
                    if (!document.hidden) {
                        // Run immediately when page becomes visible
                        performanceOptimizedAntiFade();
                    }
                });
                
                // Handle focus events
                window.addEventListener('focus', function() {
                    performanceOptimizedAntiFade();
                });
                
                // Handle click events with minimal delay
                document.addEventListener('click', function() {
                    // Run immediately after click
                    setTimeout(performanceOptimizedAntiFade, 5);
                });
                
                // Handle any mouse events that might trigger rerun
                document.addEventListener('mousedown', function() {
                    setTimeout(performanceOptimizedAntiFade, 2);
                });
                
                document.addEventListener('mouseup', function() {
                    setTimeout(performanceOptimizedAntiFade, 2);
                });
            }
            
            // Performance-optimized initialization
            function performanceOptimizedInit() {
                // Run immediately
                performanceOptimizedAntiFade();
                
                // Set up monitoring
                performanceOptimizedMonitoring();
                
                // Set up event handlers
                setupPerformanceOptimizedHandlers();
                
                // Run periodic checks less frequently for better performance
                setInterval(performanceOptimizedAntiFade, 1000);
                
                // Additional immediate checks with shorter intervals
                setTimeout(performanceOptimizedAntiFade, 50);
                setTimeout(performanceOptimizedAntiFade, 150);
                setTimeout(performanceOptimizedAntiFade, 300);
            }
            
            // Performance optimization: Debounce function to prevent excessive calls
            function debounce(func, wait) {
                let timeout;
                return function executedFunction(...args) {
                    const later = () => {
                        clearTimeout(timeout);
                        func(...args);
                    };
                    clearTimeout(timeout);
                    timeout = setTimeout(later, wait);
                };
            }
            
            // Debounced version of anti-fade function
            const debouncedAntiFade = debounce(performanceOptimizedAntiFade, 10);
            
            // Initialize as soon as possible
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', performanceOptimizedInit);
            } else {
                performanceOptimizedInit();
            }
            
            // Also run on window load
            window.addEventListener('load', performanceOptimizedAntiFade);
            
            // Run immediately
            performanceOptimizedAntiFade();
            
            // Performance-optimized safety: run every 200ms for the first 1 second
            let safetyCounter = 0;
            const safetyInterval = setInterval(function() {
                debouncedAntiFade();
                safetyCounter++;
                if (safetyCounter >= 5) { // 1 second
                    clearInterval(safetyInterval);
                }
            }, 200);
            
            // Additional performance optimizations
            // Prevent excessive DOM queries
            let lastAntiFadeTime = 0;
            const antiFadeThrottle = 50; // ms
            
            function throttledAntiFade() {
                const now = Date.now();
                if (now - lastAntiFadeTime > antiFadeThrottle) {
                    performanceOptimizedAntiFade();
                    lastAntiFadeTime = now;
                }
            }
            
            // Use throttled version for frequent events
            document.addEventListener('scroll', throttledAntiFade);
            document.addEventListener('resize', throttledAntiFade);
            </script>
'''
    
    # Pattern to match the old JavaScript (both instances)
    old_js_pattern = r'<script>\s*// Ultra-Fast Anti-Fading JavaScript for Complex Streamlit Applications.*?</script>'
    
    # Replace all instances
    updated_content = re.sub(old_js_pattern, performance_js.strip(), content, flags=re.DOTALL)
    
    # Write the updated content back to the file
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("✅ Successfully updated app.py with performance-optimized anti-fading JavaScript!")
    print("🔄 The main app should now have faster refresh times.")
    print("📝 Restart the app with: streamlit run app.py")

if __name__ == "__main__":
    update_app_performance()
