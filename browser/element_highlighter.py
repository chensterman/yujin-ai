"""
Element Highlighter for Browser Automation

This module provides functionality to highlight elements in the browser
with colored bounding boxes in real-time during automation.
"""

from playwright.async_api import Page
from typing import Dict, Any, Optional, List, Union
import os
import pathlib


class ElementHighlighter:
    """Handles highlighting of elements in the browser."""
    
    def __init__(self, page: Page):
        """
        Initialize the element highlighter.
        
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
    
    async def highlight(self, 
                        selector: str, 
                        color: str = "rgba(255, 105, 180, 0.5)", 
                        duration: int = 2000,
                        border_width: int = 3,
                        fill_opacity: float = 0.2,
                        pulse_effect: bool = True) -> Optional[str]:
        """
        Highlight an element on the page.
        
        Args:
            selector: CSS selector for the element to highlight
            color: RGB or RGBA color string for the highlight
            duration: How long the highlight should remain (ms), 0 for permanent
            border_width: Width of the highlight border in pixels
            fill_opacity: Opacity of the highlight fill (0-1)
            pulse_effect: Whether to add a pulsing animation
            
        Returns:
            Highlight ID if successful, None if element not found
        """
        options = {
            "color": color,
            "duration": duration,
            "borderWidth": border_width,
            "fillOpacity": fill_opacity,
            "pulseEffect": pulse_effect
        }
        
        # Combine the selector and options into a single argument object
        args = {"selector": selector, "options": options}
        
        return await self.page.evaluate("""
            (args) => {
                const { selector, options } = args;
                return window.elementHighlighter.highlight(selector, options);
            }
        """, args)
    
    async def remove_highlight(self, highlight_id: str) -> bool:
        """
        Remove a specific highlight.
        
        Args:
            highlight_id: ID of the highlight to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        return await self.page.evaluate("""
            (id) => {
                return window.elementHighlighter.removeHighlight(id);
            }
        """, highlight_id)
    
    async def remove_all_highlights(self) -> int:
        """
        Remove all highlights from the page.
        
        Returns:
            Number of highlights removed
        """
        return await self.page.evaluate("""
            () => {
                return window.elementHighlighter.removeAllHighlights();
            }
        """)
    
    async def update_highlight_positions(self) -> int:
        """
        Update positions of all highlights to match their elements.
        
        Returns:
            Number of highlights updated
        """
        return await self.page.evaluate("""
            () => {
                return window.elementHighlighter.updateAllHighlightPositions();
            }
        """)
        
    async def highlight_and_click(self, 
                                 selector: str, 
                                 color: str = "rgba(0, 255, 0, 0.5)",
                                 pre_click_delay: int = 500,
                                 post_click_delay: int = 0) -> bool:
        """
        Highlight an element, then click it.
        
        Args:
            selector: CSS selector for the element
            color: Color for the highlight
            pre_click_delay: Delay before clicking (ms)
            post_click_delay: Delay after clicking (ms)
            
        Returns:
            True if successful, False otherwise
        """
        # First check if element exists
        element = await self.page.query_selector(selector)
        if not element:
            return False
            
        # Highlight the element
        await self.highlight(selector, color=color, duration=pre_click_delay + post_click_delay + 1000)
        
        # Wait before clicking
        if pre_click_delay > 0:
            await self.page.wait_for_timeout(pre_click_delay)
            
        # Click the element
        await element.click()
        
        # Wait after clicking if needed
        if post_click_delay > 0:
            await self.page.wait_for_timeout(post_click_delay)
            
        return True
