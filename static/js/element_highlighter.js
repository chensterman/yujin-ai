/**
 * Advanced Element Highlighter for Browser Automation
 * 
 * This script provides comprehensive functionality to detect and highlight 
 * interactive elements in the browser with colored bounding boxes.
 */

window.elementHighlighter = (function() {
  // Private variables
  const HIGHLIGHT_CONTAINER_ID = "playwright-highlight-container";
  let highlightIndex = 0;
  const DOM_HASH_MAP = {};
  let ID = { current: 0 };
  
  // Color palette for highlights
  const COLORS = [
    "#FF0000", "#00FF00", "#0000FF", "#FFA500", "#800080", 
    "#008080", "#FF69B4", "#4B0082", "#FF4500", "#2E8B57", 
    "#DC143C", "#4682B4"
  ];
  
  // DOM caching for performance
  const DOM_CACHE = {
    boundingRects: new WeakMap(),
    computedStyles: new WeakMap(),
    clearCache: function() {
      this.boundingRects = new WeakMap();
      this.computedStyles = new WeakMap();
    }
  };
  
  // Helper functions for DOM operations with caching
  function getCachedBoundingRect(element) {
    if (!element) return null;
    
    if (DOM_CACHE.boundingRects.has(element)) {
      return DOM_CACHE.boundingRects.get(element);
    }
    
    const rect = element.getBoundingClientRect();
    if (rect) {
      DOM_CACHE.boundingRects.set(element, rect);
    }
    return rect;
  }
  
  function getCachedComputedStyle(element) {
    if (!element) return null;
    
    if (DOM_CACHE.computedStyles.has(element)) {
      return DOM_CACHE.computedStyles.get(element);
    }
    
    const style = window.getComputedStyle(element);
    if (style) {
      DOM_CACHE.computedStyles.set(element, style);
    }
    return style;
  }
  
  // XPath helper for element identification
  function getXPathTree(element, stopAtBoundary = true) {
    const segments = [];
    let currentElement = element;
    
    while (currentElement && currentElement.nodeType === Node.ELEMENT_NODE) {
      // Stop if we hit a shadow root or iframe
      if (
        stopAtBoundary &&
        (currentElement.parentNode instanceof ShadowRoot ||
         currentElement.parentNode instanceof HTMLIFrameElement)
      ) {
        break;
      }
      
      let index = 0;
      let sibling = currentElement.previousSibling;
      while (sibling) {
        if (
          sibling.nodeType === Node.ELEMENT_NODE &&
          sibling.nodeName === currentElement.nodeName
        ) {
          index++;
        }
        sibling = sibling.previousSibling;
      }
      
      const tagName = currentElement.nodeName.toLowerCase();
      const xpathIndex = index > 0 ? `[${index + 1}]` : "";
      segments.unshift(`${tagName}${xpathIndex}`);
      
      currentElement = currentElement.parentNode;
    }
    
    return segments.join("/");
  }
  
  // Core highlighting function
  function highlightElement(element, index, parentIframe = null) {
    if (!element) return index;
    
    try {
      // Create or get highlight container
      let container = document.getElementById(HIGHLIGHT_CONTAINER_ID);
      if (!container) {
        container = document.createElement("div");
        container.id = HIGHLIGHT_CONTAINER_ID;
        container.style.position = "fixed";
        container.style.pointerEvents = "none";
        container.style.top = "0";
        container.style.left = "0";
        container.style.width = "100%";
        container.style.height = "100%";
        container.style.zIndex = "2147483647";
        document.body.appendChild(container);
      }
      
      // Get element position
      const rect = element.getBoundingClientRect();
      if (!rect) return index;
      
      // Generate a color based on the index
      const colorIndex = index % COLORS.length;
      const baseColor = COLORS[colorIndex];
      const backgroundColor = baseColor + "1A"; // 10% opacity version of the color
      
      // Create highlight overlay
      const overlay = document.createElement("div");
      overlay.style.position = "fixed";
      overlay.style.border = `2px solid ${baseColor}`;
      overlay.style.backgroundColor = backgroundColor;
      overlay.style.pointerEvents = "none";
      overlay.style.boxSizing = "border-box";
      
      // Get element position
      let iframeOffset = { x: 0, y: 0 };
      
      // If element is in an iframe, calculate iframe offset
      if (parentIframe) {
        const iframeRect = parentIframe.getBoundingClientRect();
        iframeOffset.x = iframeRect.left;
        iframeOffset.y = iframeRect.top;
      }
      
      // Calculate position
      const top = rect.top + iframeOffset.y;
      const left = rect.left + iframeOffset.x;
      
      overlay.style.top = `${top}px`;
      overlay.style.left = `${left}px`;
      overlay.style.width = `${rect.width}px`;
      overlay.style.height = `${rect.height}px`;
      
      // Create and position label
      const label = document.createElement("div");
      label.className = "playwright-highlight-label";
      label.style.position = "fixed";
      label.style.background = baseColor;
      label.style.color = "white";
      label.style.padding = "1px 4px";
      label.style.borderRadius = "4px";
      label.style.fontSize = `${Math.min(12, Math.max(8, rect.height / 2))}px`;
      label.textContent = index;
      
      const labelWidth = 20;
      const labelHeight = 16;
      
      let labelTop = top + 2;
      let labelLeft = left + rect.width - labelWidth - 2;
      
      if (rect.width < labelWidth + 4 || rect.height < labelHeight + 4) {
        labelTop = top - labelHeight - 2;
        labelLeft = left + rect.width - labelWidth;
      }
      
      label.style.top = `${labelTop}px`;
      label.style.left = `${labelLeft}px`;
      
      // Add to container
      container.appendChild(overlay);
      container.appendChild(label);
      
      // Update positions on scroll
      const updatePositions = () => {
        const newRect = element.getBoundingClientRect();
        let newIframeOffset = { x: 0, y: 0 };
        
        if (parentIframe) {
          const iframeRect = parentIframe.getBoundingClientRect();
          newIframeOffset.x = iframeRect.left;
          newIframeOffset.y = iframeRect.top;
        }
        
        const newTop = newRect.top + newIframeOffset.y;
        const newLeft = newRect.left + newIframeOffset.x;
        
        overlay.style.top = `${newTop}px`;
        overlay.style.left = `${newLeft}px`;
        overlay.style.width = `${newRect.width}px`;
        overlay.style.height = `${newRect.height}px`;
        
        let newLabelTop = newTop + 2;
        let newLabelLeft = newLeft + newRect.width - labelWidth - 2;
        
        if (newRect.width < labelWidth + 4 || newRect.height < labelHeight + 4) {
          newLabelTop = newTop - labelHeight - 2;
          newLabelLeft = newLeft + newRect.width - labelWidth;
        }
        
        label.style.top = `${newLabelTop}px`;
        label.style.left = `${newLabelLeft}px`;
      };
      
      window.addEventListener('scroll', updatePositions);
      window.addEventListener('resize', updatePositions);
      
      return index + 1;
    } catch (e) {
      console.error("Error highlighting element:", e);
      return index;
    }
  }
  
  // Element visibility check
  function isElementVisible(element) {
    const style = getCachedComputedStyle(element);
    return (
      element.offsetWidth > 0 &&
      element.offsetHeight > 0 &&
      style.visibility !== "hidden" &&
      style.display !== "none"
    );
  }
  
  // Check if element is the topmost at its position
  function isTopElement(element) {
    const rect = getCachedBoundingRect(element);
    
    // If element is not in viewport, consider it top
    const isInViewport = (
      rect.left < window.innerWidth &&
      rect.right > 0 &&
      rect.top < window.innerHeight &&
      rect.bottom > 0
    );
    
    if (!isInViewport) {
      return true;
    }
    
    // For elements in viewport, check if they're topmost
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    try {
      const topEl = document.elementFromPoint(centerX, centerY);
      if (!topEl) return false;
      
      let current = topEl;
      while (current && current !== document.documentElement) {
        if (current === element) return true;
        current = current.parentElement;
      }
      return false;
    } catch (e) {
      return true;
    }
  }
  
  // Interactive element detection
  function isInteractiveElement(element) {
    if (!element || element.nodeType !== Node.ELEMENT_NODE) {
      return false;
    }
    
    // Base interactive elements and roles
    const interactiveElements = new Set([
      "a", "button", "details", "embed", "input", "menu", "menuitem",
      "object", "select", "textarea", "canvas", "summary", "dialog"
    ]);
    
    const interactiveRoles = new Set([
      'button', 'link', 'checkbox', 'radio', 'tab', 'menu', 'menuitem',
      'slider', 'switch', 'textbox', 'combobox', 'listbox', 'option',
      'searchbox', 'spinbutton', 'scrollbar', 'tooltip', 'treeitem'
    ]);
    
    const tagName = element.tagName.toLowerCase();
    const role = element.getAttribute("role");
    const tabIndex = element.getAttribute("tabindex");
    
    // Basic role/attribute checks
    if (
      interactiveElements.has(tagName) ||
      (role && interactiveRoles.has(role.toLowerCase())) ||
      (tabIndex !== null && tabIndex !== "-1") ||
      element.onclick ||
      element.hasAttribute("onclick") ||
      element.hasAttribute("ng-click") ||
      element.hasAttribute("@click") ||
      element.hasAttribute("v-on:click") ||
      element.hasAttribute("aria-expanded") ||
      element.hasAttribute("aria-pressed") ||
      element.hasAttribute("aria-selected") ||
      element.hasAttribute("aria-checked") ||
      element.getAttribute("contenteditable") === "true" ||
      element.draggable ||
      element.getAttribute("draggable") === "true"
    ) {
      return true;
    }
    
    // Class-based checks for common interactive patterns
    if (element.classList) {
      for (const cls of element.classList) {
        const lowerCls = cls.toLowerCase();
        if (
          lowerCls.includes('button') ||
          lowerCls.includes('btn') ||
          lowerCls.includes('clickable') ||
          lowerCls.includes('interactive') ||
          lowerCls.includes('selectable') ||
          lowerCls.includes('dropdown')
        ) {
          return true;
        }
      }
    }
    
    return false;
  }
  
  // Helper function to check if element is accepted for processing
  function isElementAccepted(element) {
    if (!element || !element.tagName) return false;
    
    // Always accept body and common container elements
    const alwaysAccept = new Set([
      "body", "div", "main", "article", "section", "nav", "header", "footer"
    ]);
    const tagName = element.tagName.toLowerCase();
    
    if (alwaysAccept.has(tagName)) return true;
    
    const leafElementDenyList = new Set([
      "svg", "script", "style", "link", "meta", "noscript", "template"
    ]);
    
    return !leafElementDenyList.has(tagName);
  }
  
  // Main function to find and highlight all interactive elements
  function findAndHighlightInteractiveElements(options = {}) {
    // Default options
    const defaults = {
      doHighlightElements: true,
      focusHighlightIndex: -1,
      viewportExpansion: 0,
      parentSelector: null
    };
    
    const config = {...defaults, ...options};
    
    // Reset for new highlighting session
    highlightIndex = 0;
    ID.current = 0;
    DOM_CACHE.clearCache();
    
    // Remove any existing highlights
    removeAllHighlights();
    
    // If parentSelector is provided, use that as the starting point
    let startNode = document.body;
    if (config.parentSelector) {
      const parentElement = document.querySelector(config.parentSelector);
      if (parentElement) {
        console.log(`Starting highlight from parent selector: ${config.parentSelector}`);
        startNode = parentElement;
      } else {
        console.warn(`Parent selector not found: ${config.parentSelector}, using document.body`);
      }
    }
    
    // Start processing from the selected node
    buildDomTree(startNode);
    
    return highlightIndex;
  }
  
  // Process DOM tree to find interactive elements
  function buildDomTree(node, parentIframe = null) {
    if (!node || node.id === HIGHLIGHT_CONTAINER_ID) {
      return null;
    }
    
    // Early bailout for non-element nodes
    if (node.nodeType !== Node.ELEMENT_NODE) {
      return null;
    }
    
    // Quick checks for element nodes
    if (!isElementAccepted(node)) {
      return null;
    }
    
    // Process element node
    const nodeData = {
      tagName: node.tagName.toLowerCase(),
      xpath: getXPathTree(node, true),
      children: []
    };
    
    // Check visibility and interactivity
    if (node.nodeType === Node.ELEMENT_NODE) {
      nodeData.isVisible = isElementVisible(node);
      if (nodeData.isVisible) {
        nodeData.isTopElement = isTopElement(node);
        if (nodeData.isTopElement) {
          nodeData.isInteractive = isInteractiveElement(node);
          if (nodeData.isInteractive) {
            nodeData.highlightIndex = highlightIndex++;
            
            // Highlight the element
            highlightElement(node, nodeData.highlightIndex, parentIframe);
          }
        }
      }
    }
    
    // Process children, with special handling for iframes
    if (node.tagName) {
      const tagName = node.tagName.toLowerCase();
      
      // Handle iframes
      if (tagName === "iframe") {
        try {
          const iframeDoc = node.contentDocument || node.contentWindow?.document;
          if (iframeDoc && iframeDoc.body) {
            buildDomTree(iframeDoc.body, node);
          }
        } catch (e) {
          console.warn("Unable to access iframe:", e);
        }
      }
      // Handle shadow DOM
      else if (node.shadowRoot) {
        for (const child of node.shadowRoot.childNodes) {
          buildDomTree(child, parentIframe);
        }
      }
      // Handle regular elements
      else {
        for (const child of node.childNodes) {
          if (child.nodeType === Node.ELEMENT_NODE) {
            buildDomTree(child, parentIframe);
          }
        }
      }
    }
    
    const id = `${ID.current++}`;
    DOM_HASH_MAP[id] = nodeData;
    return id;
  }
  
  // Remove all highlights
  function removeAllHighlights() {
    const container = document.getElementById(HIGHLIGHT_CONTAINER_ID);
    if (container) {
      container.remove();
    }
  }
  
  // Function to highlight all text nodes within a parent element
  function highlightAllText(parentSelector) {
    // Remove any existing highlights
    removeAllHighlights();
    
    // Reset for new highlighting session
    highlightIndex = 0;
    ID.current = 0;
    DOM_CACHE.clearCache();
    
    // Find the parent element
    const parentElement = document.querySelector(parentSelector);
    if (!parentElement) {
      console.warn(`Parent selector not found: ${parentSelector}`);
      return 0;
    }
    
    console.log(`Highlighting all text within: ${parentSelector}`);
    
    // Create a container for highlights if it doesn't exist
    let container = document.getElementById(HIGHLIGHT_CONTAINER_ID);
    if (!container) {
      container = document.createElement("div");
      container.id = HIGHLIGHT_CONTAINER_ID;
      container.style.position = "fixed";
      container.style.pointerEvents = "none";
      container.style.top = "0";
      container.style.left = "0";
      container.style.width = "100%";
      container.style.height = "100%";
      container.style.zIndex = "2147483647";
      document.body.appendChild(container);
    }
    
    // Function to process text nodes
    function processTextNodes(node) {
      // Skip script and style elements
      if (node.nodeName === 'SCRIPT' || node.nodeName === 'STYLE') {
        return;
      }
      
      // If this is a text node with non-whitespace content
      if (node.nodeType === Node.TEXT_NODE && node.textContent.trim().length > 0) {
        // Get the parent element of the text node
        const parentElement = node.parentElement;
        if (parentElement) {
          // Create a range for the text node
          const range = document.createRange();
          range.selectNodeContents(node);
          
          // Get the bounding client rect
          const rects = range.getClientRects();
          
          // Highlight each rect
          for (let i = 0; i < rects.length; i++) {
            const rect = rects[i];
            if (rect.width > 0 && rect.height > 0) {
              // Generate a color based on the index
              const colorIndex = highlightIndex % COLORS.length;
              const baseColor = COLORS[colorIndex];
              const backgroundColor = baseColor + "1A"; // 10% opacity version of the color
              
              // Create a highlight element
              const highlight = document.createElement("div");
              highlight.style.position = "fixed";
              highlight.style.left = `${rect.left}px`;
              highlight.style.top = `${rect.top}px`;
              highlight.style.width = `${rect.width}px`;
              highlight.style.height = `${rect.height}px`;
              highlight.style.backgroundColor = backgroundColor;
              highlight.style.border = `2px solid ${baseColor}`;
              highlight.style.boxSizing = "border-box";
              highlight.style.pointerEvents = "none";
              highlight.style.zIndex = "10000";
              
              // Add the highlight to the container
              container.appendChild(highlight);
              highlightIndex++;
            }
          }
        }
      }
      
      // Process child nodes
      for (let i = 0; i < node.childNodes.length; i++) {
        processTextNodes(node.childNodes[i]);
      }
    }
    
    // Start processing from the parent element
    processTextNodes(parentElement);
    
    return highlightIndex;
  }

  // Public API
  return {
    findAndHighlightInteractiveElements: findAndHighlightInteractiveElements,
    removeAllHighlights: removeAllHighlights,
    isInteractiveElement: isInteractiveElement,
    highlightAllText: highlightAllText
  };
})();
