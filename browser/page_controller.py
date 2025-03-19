"""
Page Controller for Browser Automation

This module provides higher-level page interaction utilities
built on top of Playwright's Page API.
"""

import asyncio
from playwright.async_api import Page, ElementHandle, TimeoutError
from typing import Optional, List, Dict, Any, Union, Callable
import logging
import re

from .element_highlighter import ElementHighlighter


class PageController:
    """Provides enhanced page interaction capabilities."""
    
    def __init__(self, page: Page, highlighter: Optional[ElementHighlighter] = None):
        """
        Initialize the page controller.
        
        Args:
            page: Playwright page object
            highlighter: Optional element highlighter instance
        """
        self.page = page
        self.highlighter = highlighter or ElementHighlighter(page)
        self.logger = logging.getLogger("PageController")
        
    async def setup(self):
        """Set up the controller and its dependencies."""
        # If we created our own highlighter, we need to set it up
        if self.highlighter and not hasattr(self.highlighter, '_initialized'):
            await self.highlighter.setup()
            setattr(self.highlighter, '_initialized', True)
    
    async def navigate(self, url: str, wait_until: str = "networkidle", timeout: int = 30000) -> bool:
        """
        Navigate to a URL with enhanced error handling.
        
        Args:
            url: URL to navigate to
            wait_until: Navigation wait condition ('load', 'domcontentloaded', 'networkidle')
            timeout: Navigation timeout in milliseconds
            
        Returns:
            True if navigation was successful, False otherwise
        """
        try:
            await self.page.goto(url, wait_until=wait_until, timeout=timeout)
            self.logger.info(f"Successfully navigated to {url}")
            return True
        except TimeoutError:
            self.logger.warning(f"Navigation to {url} timed out after {timeout}ms")
            return False
        except Exception as e:
            self.logger.error(f"Failed to navigate to {url}: {str(e)}")
            return False
    
    async def wait_for_element(self, 
                              selector: str, 
                              timeout: int = 10000,
                              state: str = "visible",
                              highlight: bool = True) -> Optional[ElementHandle]:
        """
        Wait for an element to appear and optionally highlight it.
        
        Args:
            selector: CSS selector for the element
            timeout: Maximum time to wait in milliseconds
            state: Element state to wait for ('attached', 'detached', 'visible', 'hidden')
            highlight: Whether to highlight the element when found
            
        Returns:
            Element handle if found, None otherwise
        """
        try:
            await self.page.wait_for_selector(selector, state=state, timeout=timeout)
            element = await self.page.query_selector(selector)
            
            if element and highlight and self.highlighter:
                await self.highlighter.highlight(selector, duration=1000)
                
            return element
        except TimeoutError:
            self.logger.warning(f"Timed out waiting for element: {selector}")
            return None
        except Exception as e:
            self.logger.error(f"Error waiting for element {selector}: {str(e)}")
            return None
    
    async def click_element(self, 
                           selector: str, 
                           timeout: int = 10000,
                           force: bool = False,
                           highlight: bool = True,
                           highlight_color: str = "rgba(0, 255, 0, 0.5)",
                           pre_click_delay: int = 500,
                           post_click_delay: int = 500) -> bool:
        """
        Wait for an element, highlight it, and click it.
        
        Args:
            selector: CSS selector for the element to click
            timeout: Maximum time to wait for the element
            force: Whether to force the click
            highlight: Whether to highlight the element before clicking
            highlight_color: Color for the highlight
            pre_click_delay: Delay before clicking (ms)
            post_click_delay: Delay after clicking (ms)
            
        Returns:
            True if the click was successful, False otherwise
        """
        element = await self.wait_for_element(selector, timeout, highlight=False)
        
        if not element:
            return False
            
        try:
            if highlight and self.highlighter:
                await self.highlighter.highlight_and_click(
                    selector, 
                    color=highlight_color,
                    pre_click_delay=pre_click_delay,
                    post_click_delay=post_click_delay
                )
            else:
                if pre_click_delay > 0:
                    await self.page.wait_for_timeout(pre_click_delay)
                    
                await element.click(force=force)
                
                if post_click_delay > 0:
                    await self.page.wait_for_timeout(post_click_delay)
                    
            return True
        except Exception as e:
            self.logger.error(f"Failed to click element {selector}: {str(e)}")
            return False
    
    async def fill_form(self, 
                       form_data: Dict[str, str], 
                       submit_selector: Optional[str] = None,
                       highlight: bool = True) -> bool:
        """
        Fill a form with the provided data and optionally submit it.
        
        Args:
            form_data: Dictionary mapping selectors to values
            submit_selector: Optional selector for submit button
            highlight: Whether to highlight elements during interaction
            
        Returns:
            True if form was filled (and submitted if requested), False otherwise
        """
        success = True
        
        # Fill each field
        for selector, value in form_data.items():
            try:
                element = await self.wait_for_element(selector, highlight=highlight)
                
                if not element:
                    self.logger.warning(f"Could not find form field: {selector}")
                    success = False
                    continue
                
                # Clear the field first
                await element.fill("")
                
                # Type the value with a realistic typing speed
                await element.type(value, delay=50)
                
            except Exception as e:
                self.logger.error(f"Failed to fill form field {selector}: {str(e)}")
                success = False
        
        # Submit the form if requested
        if submit_selector and success:
            return await self.click_element(submit_selector, highlight=highlight)
            
        return success
    
    async def get_text(self, 
                      selector: str, 
                      timeout: int = 5000,
                      highlight: bool = True) -> Optional[str]:
        """
        Get text content from an element.
        
        Args:
            selector: CSS selector for the element
            timeout: Maximum time to wait for the element
            highlight: Whether to highlight the element
            
        Returns:
            Text content if found, None otherwise
        """
        element = await self.wait_for_element(selector, timeout, highlight=highlight)
        
        if not element:
            return None
            
        try:
            return await element.text_content()
        except Exception as e:
            self.logger.error(f"Failed to get text from {selector}: {str(e)}")
            return None
    
    async def get_elements_text(self, 
                              selector: str, 
                              timeout: int = 5000,
                              highlight: bool = True) -> List[str]:
        """
        Get text content from multiple elements.
        
        Args:
            selector: CSS selector for the elements
            timeout: Maximum time to wait for elements
            highlight: Whether to highlight the elements
            
        Returns:
            List of text content from matching elements
        """
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            elements = await self.page.query_selector_all(selector)
            
            results = []
            for i, element in enumerate(elements):
                if highlight and self.highlighter:
                    # Create a more specific selector for this element
                    specific_selector = f"{selector}:nth-of-type({i+1})"
                    await self.highlighter.highlight(specific_selector, duration=300)
                
                text = await element.text_content()
                if text:
                    results.append(text.strip())
            
            return results
        except Exception as e:
            self.logger.error(f"Failed to get elements text for {selector}: {str(e)}")
            return []
    
    async def wait_for_navigation(self, 
                                timeout: int = 30000, 
                                wait_until: str = "networkidle",
                                url_pattern: Optional[str] = None) -> bool:
        """
        Wait for navigation to complete, optionally matching a URL pattern.
        
        Args:
            timeout: Maximum time to wait in milliseconds
            wait_until: Navigation wait condition
            url_pattern: Optional regex pattern the new URL should match
            
        Returns:
            True if navigation completed successfully, False otherwise
        """
        try:
            await self.page.wait_for_load_state(wait_until, timeout=timeout)
            
            if url_pattern:
                current_url = self.page.url
                if not re.search(url_pattern, current_url):
                    self.logger.warning(f"URL after navigation ({current_url}) doesn't match pattern: {url_pattern}")
                    return False
                    
            return True
        except TimeoutError:
            self.logger.warning(f"Navigation timed out after {timeout}ms")
            return False
        except Exception as e:
            self.logger.error(f"Error during navigation: {str(e)}")
            return False
    
    async def screenshot(self, path: str, full_page: bool = True) -> bool:
        """
        Take a screenshot of the current page.
        
        Args:
            path: Path where to save the screenshot
            full_page: Whether to capture the full page or just the viewport
            
        Returns:
            True if screenshot was taken successfully, False otherwise
        """
        try:
            await self.page.screenshot(path=path, full_page=full_page)
            return True
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {str(e)}")
            return False
            
    async def get_unique_selector(self, element: ElementHandle) -> Optional[str]:
        """
        Generate a unique CSS selector for an element.
        
        Args:
            element: Playwright ElementHandle to generate selector for
            
        Returns:
            A CSS selector string that uniquely identifies the element, or None if failed
        """
        try:
            # Try to get a unique selector using Playwright's built-in functionality
            return await element.evaluate("""element => {
                // Helper function to escape CSS selector special characters
                const escapeCSS = str => str.replace(/[\\:\\.\\/\\[\\]]/g, '\\\\$&');
                
                // Try to find a unique ID first
                if (element.id) {
                    return '#' + escapeCSS(element.id);
                }
                
                // Try using a unique class combination
                if (element.classList && element.classList.length > 0) {
                    const classSelector = Array.from(element.classList).map(c => '.' + escapeCSS(c)).join('');
                    // Test if this selector is unique
                    if (document.querySelectorAll(classSelector).length === 1) {
                        return classSelector;
                    }
                }
                
                // Try using tag name with attributes
                const tagName = element.tagName.toLowerCase();
                
                // Check for common attributes that might be unique
                for (const attr of ['data-testid', 'name', 'aria-label', 'role', 'type']) {
                    if (element.hasAttribute(attr)) {
                        const attrValue = element.getAttribute(attr);
                        const selector = `${tagName}[${attr}="${attrValue}"]`;
                        if (document.querySelectorAll(selector).length === 1) {
                            return selector;
                        }
                    }
                }
                
                // If no unique selector found yet, use nth-child with parent context
                let current = element;
                let selector = tagName;
                let iterations = 0;
                const maxIterations = 5; // Prevent infinite loops
                
                while (document.querySelectorAll(selector).length > 1 && iterations < maxIterations) {
                    // Find the index of the current element among its siblings
                    const parent = current.parentElement;
                    if (!parent) break;
                    
                    const siblings = Array.from(parent.children);
                    const index = siblings.indexOf(current) + 1;
                    
                    // Update the selector with nth-child
                    selector = `${tagName}:nth-child(${index})`;
                    
                    // Add parent context if needed
                    if (document.querySelectorAll(selector).length > 1) {
                        const parentTag = parent.tagName.toLowerCase();
                        selector = `${parentTag} > ${selector}`;
                        current = parent;
                    }
                    
                    iterations++;
                }
                
                return selector;
            }""")
        except Exception as e:
            self.logger.error(f"Failed to get unique selector: {str(e)}")
            return None

    async def get_unique_selector(self, element: ElementHandle) -> Optional[str]:
        """
        Generate a unique CSS selector for an element.
        
        Args:
            element: Playwright ElementHandle to generate selector for
            
        Returns:
            A CSS selector string that uniquely identifies the element, or None if failed
        """
        try:
            # Try to get a unique selector using Playwright's built-in functionality
            return await element.evaluate("""element => {
                // Helper function to escape CSS selector special characters
                const escapeCSS = str => str.replace(/[\\:\\.\\/\\[\\]]/g, '\\\\$&');
                
                // Try to find a unique ID first
                if (element.id) {
                    return '#' + escapeCSS(element.id);
                }
                
                // Try using a unique class combination
                if (element.classList && element.classList.length > 0) {
                    const classSelector = Array.from(element.classList).map(c => '.' + escapeCSS(c)).join('');
                    // Test if this selector is unique
                    if (document.querySelectorAll(classSelector).length === 1) {
                        return classSelector;
                    }
                }
                
                // Try using tag name with attributes
                const tagName = element.tagName.toLowerCase();
                
                // Check for common attributes that might be unique
                for (const attr of ['data-testid', 'name', 'aria-label', 'role', 'type']) {
                    if (element.hasAttribute(attr)) {
                        const attrValue = element.getAttribute(attr);
                        const selector = `${tagName}[${attr}="${attrValue}"]`;
                        if (document.querySelectorAll(selector).length === 1) {
                            return selector;
                        }
                    }
                }
                
                // If no unique selector found yet, use nth-child with parent context
                let current = element;
                let selector = tagName;
                let iterations = 0;
                const maxIterations = 5; // Prevent infinite loops
                
                while (document.querySelectorAll(selector).length > 1 && iterations < maxIterations) {
                    // Find the index of the current element among its siblings
                    const parent = current.parentElement;
                    if (!parent) break;
                    
                    const siblings = Array.from(parent.children);
                    const index = siblings.indexOf(current) + 1;
                    
                    // Update the selector with nth-child
                    selector = `${tagName}:nth-child(${index})`;
                    
                    // Add parent context if needed
                    if (document.querySelectorAll(selector).length > 1) {
                        const parentTag = parent.tagName.toLowerCase();
                        selector = `${parentTag} > ${selector}`;
                        current = parent;
                    }
                    
                    iterations++;
                }
                
                return selector;
            }""")
        except Exception as e:
            self.logger.error(f"Failed to get unique selector: {str(e)}")
            return None
