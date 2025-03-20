"""
Element Highlighter for Browser Automation

This module provides comprehensive functionality to detect and highlight
interactive elements in the browser with colored bounding boxes.
"""

from playwright.async_api import Page, ElementHandle
from typing import Dict, Any, Optional, List, Union
import os
import pathlib


class ElementHighlighter:
    """Handles advanced detection and highlighting of interactive elements in the browser."""

    def __init__(self, page: Page):
        """
        Initialize the advanced element highlighter.

        Args:
            page: Playwright page object to work with
        """
        self.page = page

    async def setup(self):
        """Set up the highlighter by injecting JavaScript."""
        await self._setup_highlighter()

    async def _setup_highlighter(self):
        """Inject the highlighting JavaScript into the page."""
        # Get the path to the JavaScript file
        root_dir = pathlib.Path(__file__).parent.parent.absolute()
        js_file_path = os.path.join(
            root_dir, "static", "js", "element_highlighter.js")

        # Read the JavaScript file
        with open(js_file_path, 'r') as file:
            js_code = file.read()

        # Inject the JavaScript into the page
        await self.page.add_init_script(js_code)
    
    async def find_and_highlight_interactive_elements(self, 
                                                     do_highlight: bool = True,
                                                     focus_highlight_index: int = -1,
                                                     viewport_expansion: int = 0,
                                                     parent_selector: str = None) -> int:
        """
        Find and highlight all interactive elements on the page.

        Args:
            do_highlight: Whether to actually highlight elements or just detect them
            focus_highlight_index: If >= 0, only highlight the element with this index
            viewport_expansion: How much to expand the viewport when detecting elements
                               (0 = only elements in viewport, -1 = all elements)
            parent_selector: CSS selector for a parent element to limit the search scope
                            (if provided, only elements within this parent will be highlighted)
            
        Returns:
            Number of interactive elements found
        """
        options = {
            "doHighlightElements": do_highlight,
            "focusHighlightIndex": focus_highlight_index,
            "viewportExpansion": viewport_expansion,
            "parentSelector": parent_selector
        }

        return await self.page.evaluate("""
            (options) => {
                return window.elementHighlighter.findAndHighlightInteractiveElements(options);
            }
        """, options)

    async def remove_all_highlights(self) -> None:
        """Remove all highlights from the page."""
        await self.page.evaluate("""
            () => {
                return window.elementHighlighter.removeAllHighlights();
            }
        """)

    async def is_element_interactive(self, selector: str) -> bool:
        """
        Check if an element is interactive.

        Args:
            selector: CSS selector for the element to check

        Returns:
            True if the element is interactive, False otherwise
        """
        return await self.page.evaluate("""
            (selector) => {
                const element = document.querySelector(selector);
                if (!element) return false;
                return window.elementHighlighter.isInteractiveElement(element);
            }
        """, selector)

    async def highlight_element(self, 
                               element: Union[ElementHandle, str], 
                               color: str = "rgba(0, 255, 0, 0.5)", 
                               duration: int = 2000) -> None:
        """
        Highlight an element with a colored overlay.
        
        Args:
            element: ElementHandle or CSS selector for the element to highlight
            color: CSS color for the highlight
            duration: Duration to show the highlight in ms (0 for indefinite)
        """
        # If element is a string (selector), get the element handle
        if isinstance(element, str):
            element_handle = await self.page.query_selector(element)
            if not element_handle:
                return  # Element not found
        else:
            element_handle = element

        # Get the bounding box of the element
        box = await element_handle.bounding_box()
        if not box:
            return  # Element not visible

        # Create a highlight for the element
        await self.page.evaluate("""
            function(params) {
                const box = params.box;
                const color = params.color;
                const duration = params.duration;
                
                // Create or get highlight container
                let container = document.getElementById('highlight-container');
                if (!container) {
                    container = document.createElement("div");
                    container.id = 'highlight-container';
                    container.style.position = "fixed";
                    container.style.pointerEvents = "none";
                    container.style.top = "0";
                    container.style.left = "0";
                    container.style.width = "100%";
                    container.style.height = "100%";
                    container.style.zIndex = "2147483647";
                    document.body.appendChild(container);
                }
                
                // Generate a color based on the index
                const COLORS = ["#FF5733", "#33FF57", "#3357FF", "#F3FF33", "#FF33F3", "#33FFF3"];
                const colorIndex = 0; // Use first color for single element
                const baseColor = COLORS[colorIndex];
                const backgroundColor = baseColor + "1A"; // 10% opacity version of the color
                
                // Create a highlight element
                const highlight = document.createElement("div");
                highlight.style.position = "fixed";
                highlight.style.left = `${box.x}px`;
                highlight.style.top = `${box.y}px`;
                highlight.style.width = `${box.width}px`;
                highlight.style.height = `${box.height}px`;
                highlight.style.backgroundColor = backgroundColor;
                highlight.style.border = `2px solid ${baseColor}`;
                highlight.style.boxSizing = "border-box";
                highlight.style.pointerEvents = "none";
                highlight.style.zIndex = "10000";
                highlight.className = 'element-highlight';
                
                // Add the highlight to the container
                container.appendChild(highlight);
                
                // Remove the highlight after the specified duration
                if (duration > 0) {
                    setTimeout(() => {
                        if (highlight.parentNode) {
                            highlight.parentNode.removeChild(highlight);
                        }
                    }, duration);
                }
                
                return true;
            }
        """, {"box": box, "color": color, "duration": duration})
        
    async def highlight_and_click(self, 
                                 selector: str, 
                                 color: str = "rgba(0, 255, 0, 0.5)",
                                 pre_click_delay: int = 500,
                                 post_click_delay: int = 500) -> bool:
        """
        Highlight an element, then click it.

        Args:
            selector: CSS selector for the element to highlight and click
            color: CSS color for the highlight
            pre_click_delay: Delay before clicking (ms)
            post_click_delay: Delay after clicking (ms)

        Returns:
            True if the element was found and clicked, False otherwise
        """
        element = await self.page.query_selector(selector)
        if not element:
            return False

        # Highlight the element
        await self.highlight_element(element, color, pre_click_delay)

        # Wait before clicking
        if pre_click_delay > 0:
            await self.page.wait_for_timeout(pre_click_delay)

        # Click the element
        await element.click()

        # Highlight again after clicking with a different color
        if post_click_delay > 0:
            await self.highlight_element(element, "rgba(255, 165, 0, 0.5)", post_click_delay)
            await self.page.wait_for_timeout(post_click_delay)

        return True

    async def highlight_all_text(self, parent_selector: str) -> int:
        """
        Highlight all text nodes within a parent element.
        
        Args:
            parent_selector: CSS selector for the parent element
            
        Returns:
            Number of text nodes highlighted
        """
        return await self.page.evaluate("""
            (parentSelector) => {
                return window.elementHighlighter.highlightAllText(parentSelector);
            }
        """, parent_selector)
