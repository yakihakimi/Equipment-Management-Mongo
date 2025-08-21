// Ultra-Aggressive Anti-Fading JavaScript for Maximum Speed

// Ultra-fast function with minimal overhead
function ultraFastFix() {
    // Immediate execution without requestAnimationFrame for speed
    document.body.style.backgroundColor = '#ffffff';
    document.body.style.transition = 'none';
    document.body.style.opacity = '1';
    document.body.style.animation = 'none';
    
    // Force critical elements immediately
    const appContainer = document.querySelector('.stApp');
    if (appContainer) {
        appContainer.style.backgroundColor = '#ffffff';
        appContainer.style.transition = 'none';
        appContainer.style.opacity = '1';
        appContainer.style.animation = 'none';
    }
    
    // Force all divs immediately (aggressive approach)
    const allDivs = document.querySelectorAll('div');
    for (let i = 0; i < allDivs.length; i++) {
        const div = allDivs[i];
        div.style.transition = 'none';
        div.style.animation = 'none';
        div.style.opacity = '1';
        div.style.backgroundColor = '#ffffff';
    }
    
    // Force all Streamlit elements
    const stElements = document.querySelectorAll('.stButton, .stSelectbox, .stTextInput, .stDataFrame, .stForm, [data-testid="stDecoration"]');
    for (let i = 0; i < stElements.length; i++) {
        const element = stElements[i];
        element.style.transition = 'none';
        element.style.animation = 'none';
        element.style.opacity = '1';
        element.style.backgroundColor = '#ffffff';
    }
}

// Ultra-fast monitoring with minimal overhead
function ultraFastMonitoring() {
    // Simple observer without complex logic
    const observer = new MutationObserver(function() {
        ultraFastFix();
    });
    
    // Observe everything
    observer.observe(document.body, {
        attributes: true,
        subtree: true,
        childList: true
    });
}

// Ultra-fast event handlers
function setupUltraFastHandlers() {
    // Handle all events with immediate response
    document.addEventListener('click', ultraFastFix);
    document.addEventListener('mousedown', ultraFastFix);
    document.addEventListener('mouseup', ultraFastFix);
    document.addEventListener('visibilitychange', ultraFastFix);
    window.addEventListener('focus', ultraFastFix);
    window.addEventListener('load', ultraFastFix);
}

// Ultra-fast initialization
function ultraFastInit() {
    // Run immediately
    ultraFastFix();
    
    // Set up monitoring
    ultraFastMonitoring();
    
    // Set up event handlers
    setupUltraFastHandlers();
    
    // Run very frequently for maximum responsiveness
    setInterval(ultraFastFix, 100);
    
    // Additional immediate checks
    setTimeout(ultraFastFix, 10);
    setTimeout(ultraFastFix, 50);
    setTimeout(ultraFastFix, 100);
}

// Initialize immediately
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ultraFastInit);
} else {
    ultraFastInit();
}

// Run immediately
ultraFastFix();

// Safety: run every 50ms for the first 5 seconds
let safetyCounter = 0;
const safetyInterval = setInterval(function() {
    ultraFastFix();
    safetyCounter++;
    if (safetyCounter >= 100) { // 5 seconds
        clearInterval(safetyInterval);
    }
}, 50);

// Additional safety: run every 100ms indefinitely
setInterval(ultraFastFix, 100);
