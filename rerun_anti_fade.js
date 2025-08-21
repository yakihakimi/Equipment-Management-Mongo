// Anti-Fading JavaScript for Streamlit Rerun Operations

// Function to prevent fading during rerun
function preventRerunFading() {
    // Force all elements to maintain their appearance
    document.body.style.backgroundColor = '#ffffff';
    document.body.style.transition = 'none';
    document.body.style.opacity = '1';
    
    // Fix Streamlit app container
    const appContainer = document.querySelector('.stApp');
    if (appContainer) {
        appContainer.style.backgroundColor = '#ffffff';
        appContainer.style.transition = 'none';
        appContainer.style.opacity = '1';
    }
    
    // Fix all div elements that might fade during rerun
    const allDivs = document.querySelectorAll('div');
    allDivs.forEach(function(div) {
        div.style.transition = 'none';
        div.style.animation = 'none';
        div.style.opacity = '1';
    });
    
    // Specifically target Streamlit decoration elements
    const decorationElements = document.querySelectorAll('[data-testid="stDecoration"]');
    decorationElements.forEach(function(element) {
        element.style.backgroundColor = '#ffffff';
        element.style.opacity = '1';
        element.style.transition = 'none';
        element.style.animation = 'none';
    });
    
    // Fix any loading overlays
    const overlays = document.querySelectorAll('[data-testid="stDecoration"]::before, [data-testid="stDecoration"]::after');
    overlays.forEach(function(overlay) {
        overlay.style.display = 'none';
        overlay.style.opacity = '0';
    });
}

// Function to monitor for rerun events
function monitorForRerun() {
    // Check if page is about to rerun (when elements start fading)
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                const target = mutation.target;
                // If any element starts fading (opacity changes), immediately fix it
                if (target.style.opacity && target.style.opacity !== '1') {
                    target.style.opacity = '1';
                    target.style.transition = 'none';
                }
                // If background color changes, fix it
                if (target.style.backgroundColor && 
                    target.style.backgroundColor !== '#ffffff' && 
                    target.style.backgroundColor !== 'rgb(255, 255, 255)') {
                    target.style.backgroundColor = '#ffffff';
                }
            }
        });
    });
    
    // Observe all style changes
    observer.observe(document.body, {
        attributes: true,
        attributeFilter: ['style'],
        subtree: true
    });
}

// Function to handle page visibility changes (rerun indicator)
function handleVisibilityChange() {
    if (!document.hidden) {
        // Page became visible again (after rerun), fix any fading
        setTimeout(preventRerunFading, 10);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Run initial fix
    preventRerunFading();
    
    // Set up monitoring
    monitorForRerun();
    
    // Monitor for page visibility changes (rerun indicator)
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // Also monitor for any focus events (another rerun indicator)
    window.addEventListener('focus', function() {
        setTimeout(preventRerunFading, 10);
    });
    
    // Monitor for any click events that might trigger rerun
    document.addEventListener('click', function() {
        // Small delay to catch any fading that occurs after click
        setTimeout(preventRerunFading, 50);
    });
    
    // Periodic check to ensure no fading occurs
    setInterval(preventRerunFading, 1000);
});

// Also run when window loads
window.addEventListener('load', function() {
    preventRerunFading();
});

// Run immediately if DOM is already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', preventRerunFading);
} else {
    preventRerunFading();
}
