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

    async def highlight_specific_element(self, element_handle):
        """
        Highlight a specific element on the page.

        Args:
            element_handle: Playwright ElementHandle to highlight

        Returns:
            1 if successful, 0 if failed
        """
        if not element_handle:
            return 0

        return await self.page.evaluate("""
            (element) => {
                return window.elementHighlighter.highlightSpecificElement(element);
            }
        """, element_handle)

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

    async def highlight_element(self,
                                element: Union[ElementHandle, str],
                                color: str = "rgba(0, 255, 0, 0.5)",
                                duration: int = 1000) -> None:
        """
        Highlight a specific element with a colored box.

        Args:
            element: ElementHandle or CSS selector for the element to highlight
            color: CSS color for the highlight (rgba format recommended)
            duration: Duration of the highlight in milliseconds (0 for permanent)
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
            (box, color, duration) => {
                // Create a highlight element
                const highlight = document.createElement('div');
                highlight.style.position = 'absolute';
                highlight.style.top = (box.y + window.scrollY) + 'px';
                highlight.style.left = (box.x + window.scrollX) + 'px';
                highlight.style.width = box.width + 'px';
                highlight.style.height = box.height + 'px';
                highlight.style.border = '2px solid ' + color.replace(')', ', 1)').replace('rgba', 'rgb');
                highlight.style.backgroundColor = color;
                highlight.style.zIndex = '10000';
                highlight.style.pointerEvents = 'none';  // Don't interfere with clicks
                highlight.className = 'element-highlight';
                
                // Add the highlight to the page
                document.body.appendChild(highlight);
                
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
        """, box, color, duration)

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
