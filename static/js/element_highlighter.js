/**
 * Element Highlighter for Browser Automation
 * 
 * This script provides functionality to highlight elements in the browser
 * with colored bounding boxes in real-time during automation.
 */

window.elementHighlighter = {
    highlights: [],
    
    highlight: function(selector, options = {}) {
        const element = document.querySelector(selector);
        if (!element) return null;
        
        const defaults = {
            color: 'rgba(255, 105, 180, 0.5)',
            borderWidth: 3,
            fillOpacity: 0.2,
            duration: 1000,
            pulseEffect: true,
            zIndex: 10000,
            id: 'highlight-' + Math.random().toString(36).substr(2, 9)
        };
        
        const config = {...defaults, ...options};
        
        // Get element position
        const rect = element.getBoundingClientRect();
        
        // Create highlight overlay
        const highlight = document.createElement('div');
        highlight.id = config.id;
        highlight.style.position = 'fixed';
        highlight.style.left = rect.left + 'px';
        highlight.style.top = rect.top + 'px';
        highlight.style.width = rect.width + 'px';
        highlight.style.height = rect.height + 'px';
        highlight.style.border = `${config.borderWidth}px solid ${config.color}`;
        highlight.style.backgroundColor = config.color.replace(')', ', ' + config.fillOpacity + ')').replace('rgb', 'rgba');
        highlight.style.zIndex = config.zIndex;
        highlight.style.pointerEvents = 'none';
        highlight.style.boxSizing = 'border-box';
        
        if (config.pulseEffect) {
            highlight.style.animation = 'pulse-highlight 1.5s infinite';
            
            // Add the animation if it doesn't exist yet
            if (!document.getElementById('highlight-keyframes')) {
                const style = document.createElement('style');
                style.id = 'highlight-keyframes';
                style.innerHTML = `
                    @keyframes pulse-highlight {
                        0% { opacity: 1; }
                        50% { opacity: 0.6; }
                        100% { opacity: 1; }
                    }
                `;
                document.head.appendChild(style);
            }
        }
        
        document.body.appendChild(highlight);
        
        // Store the highlight
        this.highlights.push({
            id: config.id,
            element: highlight,
            selector: selector,
            timer: null
        });
        
        // Set up removal if duration is specified
        if (config.duration > 0) {
            const timer = setTimeout(() => {
                this.removeHighlight(config.id);
            }, config.duration);
            
            // Store the timer
            const highlightObj = this.highlights.find(h => h.id === config.id);
            if (highlightObj) {
                highlightObj.timer = timer;
            }
        }
        
        return config.id;
    },
    
    removeHighlight: function(id) {
        const index = this.highlights.findIndex(h => h.id === id);
        if (index !== -1) {
            const highlight = this.highlights[index];
            
            // Clear any pending timers
            if (highlight.timer) {
                clearTimeout(highlight.timer);
            }
            
            // Remove the element
            if (highlight.element && highlight.element.parentNode) {
                highlight.element.parentNode.removeChild(highlight.element);
            }
            
            // Remove from our array
            this.highlights.splice(index, 1);
            return true;
        }
        return false;
    },
    
    removeAllHighlights: function() {
        // Make a copy since we'll be modifying the array
        const highlightIds = this.highlights.map(h => h.id);
        
        // Remove each highlight
        highlightIds.forEach(id => {
            this.removeHighlight(id);
        });
        
        return highlightIds.length;
    },
    
    updateHighlightPosition: function(id) {
        const highlight = this.highlights.find(h => h.id === id);
        if (!highlight) return false;
        
        const element = document.querySelector(highlight.selector);
        if (!element) return false;
        
        const rect = element.getBoundingClientRect();
        
        highlight.element.style.left = rect.left + 'px';
        highlight.element.style.top = rect.top + 'px';
        highlight.element.style.width = rect.width + 'px';
        highlight.element.style.height = rect.height + 'px';
        
        return true;
    },
    
    updateAllHighlightPositions: function() {
        this.highlights.forEach(highlight => {
            this.updateHighlightPosition(highlight.id);
        });
        
        return this.highlights.length;
    }
};

// Set up a mutation observer to update highlight positions when DOM changes
const setupMutationObserver = function() {
    const observer = new MutationObserver(() => {
        window.elementHighlighter.updateAllHighlightPositions();
    });
    
    // Start observing the document with the configured parameters
    observer.observe(document.body, { 
        childList: true, 
        subtree: true,
        attributes: true,
        attributeFilter: ['style', 'class']
    });
};

// Initialize the mutation observer when the script loads
if (document.body) {
    setupMutationObserver();
} else {
    document.addEventListener('DOMContentLoaded', setupMutationObserver);
}
