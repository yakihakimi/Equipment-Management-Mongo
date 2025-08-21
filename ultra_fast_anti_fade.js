// Ultra-Fast Anti-Fading JavaScript for Complex Streamlit Applications

// Ultra-fast function to prevent fading during rerun
function ultraFastAntiFade() {
    // Immediately force all critical elements
    document.body.style.backgroundColor = '#ffffff';
    document.body.style.transition = 'none';
    document.body.style.opacity = '1';
    document.body.style.animation = 'none';
    
    // Force all divs immediately
    const allDivs = document.querySelectorAll('div');
    for (let i = 0; i < allDivs.length; i++) {
        const div = allDivs[i];
        div.style.transition = 'none';
        div.style.animation = 'none';
        div.style.opacity = '1';
        div.style.backgroundColor = '#ffffff';
    }
    
    // Force Streamlit app container
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
    
    // Force all Streamlit components
    const stElements = document.querySelectorAll('.stButton, .stSelectbox, .stTextInput, .stDataFrame, .stForm');
    for (let i = 0; i < stElements.length; i++) {
        const element = stElements[i];
        element.style.transition = 'none';
        element.style.animation = 'none';
        element.style.opacity = '1';
    }
}

// Ultra-fast monitoring with immediate response
function ultraFastMonitoring() {
    // Use a more aggressive MutationObserver
    const observer = new MutationObserver(function(mutations) {
        let needsFix = false;
        
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
        
        // If any changes were made, run the full fix
        if (needsFix) {
            ultraFastAntiFade();
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

// Ultra-fast event handlers
function setupUltraFastHandlers() {
    // Handle visibility changes (rerun indicator)
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            // Run immediately when page becomes visible
            ultraFastAntiFade();
        }
    });
    
    // Handle focus events
    window.addEventListener('focus', function() {
        ultraFastAntiFade();
    });
    
    // Handle click events with minimal delay
    document.addEventListener('click', function() {
        // Run immediately after click
        setTimeout(ultraFastAntiFade, 10);
    });
    
    // Handle any mouse events that might trigger rerun
    document.addEventListener('mousedown', function() {
        setTimeout(ultraFastAntiFade, 5);
    });
    
    document.addEventListener('mouseup', function() {
        setTimeout(ultraFastAntiFade, 5);
    });
}

// Ultra-fast initialization
function ultraFastInit() {
    // Run immediately
    ultraFastAntiFade();
    
    // Set up monitoring
    ultraFastMonitoring();
    
    // Set up event handlers
    setupUltraFastHandlers();
    
    // Run periodic checks more frequently for complex apps
    setInterval(ultraFastAntiFade, 500);
    
    // Additional immediate checks
    setTimeout(ultraFastAntiFade, 100);
    setTimeout(ultraFastAntiFade, 200);
    setTimeout(ultraFastAntiFade, 500);
}

// Initialize as soon as possible
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ultraFastInit);
} else {
    ultraFastInit();
}

// Also run on window load
window.addEventListener('load', ultraFastAntiFade);

// Run immediately
ultraFastAntiFade();

// Additional safety: run every 100ms for the first 2 seconds
let safetyCounter = 0;
const safetyInterval = setInterval(function() {
    ultraFastAntiFade();
    safetyCounter++;
    if (safetyCounter >= 20) { // 2 seconds
        clearInterval(safetyInterval);
    }
}, 100);
