"""
Element Highlighter for Browser Automation

This module provides comprehensive functionality to detect and highlight
interactive elements in the browser with colored bounding boxes.
"""

from playwright.async_api import Page
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
        js_file_path = os.path.join(root_dir, "static", "js", "element_highlighter.js")
        
        # Read the JavaScript file
        with open(js_file_path, 'r') as file:
            js_code = file.read()
            
        # Inject the JavaScript into the page
        await self.page.add_init_script(js_code)
    
    async def find_and_highlight_interactive_elements(self, 
                                                     do_highlight: bool = True,
                                                     focus_highlight_index: int = -1,
                                                     viewport_expansion: int = 0) -> int:
        """
        Find and highlight all interactive elements on the page.
        
        Args:
            do_highlight: Whether to actually highlight elements or just detect them
            focus_highlight_index: If >= 0, only highlight the element with this index
            viewport_expansion: How much to expand the viewport when detecting elements
                               (0 = only elements in viewport, -1 = all elements)
            
        Returns:
            Number of interactive elements found
        """
        options = {
            "doHighlightElements": do_highlight,
            "focusHighlightIndex": focus_highlight_index,
            "viewportExpansion": viewport_expansion
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
