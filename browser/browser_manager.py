"""
Browser Manager for Tinder Automation

This module handles browser initialization, configuration, and management.
"""

import asyncio
import os
import glob
from pathlib import Path
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from typing import Optional, Dict, Any, Tuple, List


class BrowserManager:
    """Manages browser instances for automation tasks."""
    
    def __init__(self, 
                 headless: bool = False, 
                 slow_mo: int = 50,
                 viewport_size: Dict[str, int] = {"width": 1280, "height": 800},
                 user_agent: Optional[str] = None,
                 user_data_dir: Optional[str] = None):
        """
        Initialize the browser manager.
        
        Args:
            headless: Whether to run browser in headless mode
            slow_mo: Slow down operations by specified milliseconds
            viewport_size: Browser viewport dimensions
            user_agent: Custom user agent string
            user_data_dir: Path to Chrome user data directory for using existing profiles
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.viewport_size = viewport_size
        self.user_agent = user_agent
        self.user_data_dir = user_data_dir
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    @staticmethod
    def get_chrome_profiles() -> List[Dict[str, str]]:
        """
        Get list of available Chrome profiles on the system.
        
        Returns:
            List of dictionaries with profile name and path
        """
        profiles = []
        
        # Default Chrome profile locations based on OS
        if os.name == 'posix':  # macOS or Linux
            if os.path.exists('/Applications/Google Chrome.app'):
                # macOS path
                base_path = os.path.expanduser('~/Library/Application Support/Google/Chrome')
            else:
                # Linux path
                base_path = os.path.expanduser('~/.config/google-chrome')
        elif os.name == 'nt':  # Windows
            base_path = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data')
        else:
            return profiles  # Unsupported OS
            
        if not os.path.exists(base_path):
            return profiles
        
        def get_profile_name(profile_dir):
            """Extract the user-friendly profile name from the Preferences file"""
            try:
                prefs_file = os.path.join(profile_dir, 'Preferences')
                if os.path.exists(prefs_file):
                    with open(prefs_file, 'r', encoding='utf-8') as f:
                        import json
                        prefs = json.load(f)
                        if 'profile' in prefs and 'name' in prefs['profile']:
                            return prefs['profile']['name']
            except Exception:
                pass
            # Return the directory name if we can't find the profile name
            return os.path.basename(profile_dir)
            
        # Get all profile directories
        default_profile = os.path.join(base_path, 'Default')
        if os.path.exists(default_profile):
            display_name = get_profile_name(default_profile)
            profiles.append({
                'name': 'Default',
                'display_name': display_name,
                'path': base_path,
                'profile': 'Default'
            })
            
        # Look for numbered profiles (Profile 1, Profile 2, etc.)
        for profile_dir in glob.glob(os.path.join(base_path, 'Profile *')):
            profile_name = os.path.basename(profile_dir)
            display_name = get_profile_name(profile_dir)
            profiles.append({
                'name': profile_name,
                'display_name': display_name,
                'path': base_path,
                'profile': profile_name
            })
            
        return profiles
    
    async def start(self) -> Page:
        """
        Start the browser and return the main page.
        
        Returns:
            The main browser page
        """
        # Launch playwright
        self.playwright = await async_playwright().start()
        
        # Common browser arguments to avoid detection
        browser_args = [
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars',
            '--disable-background-timer-throttling',
            '--disable-popup-blocking',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-window-activation',
            '--disable-focus-on-load',
            '--no-first-run',
            '--no-default-browser-check',
            '--no-startup-window',
            '--window-position=0,0',
            f'--window-size={self.viewport_size["width"]},{self.viewport_size["height"]}',
        ]
        
        # Context options
        context_options = {
            "viewport": self.viewport_size,
        }
        
        if self.user_agent:
            context_options["user_agent"] = self.user_agent
            
        # If user data directory is specified, use persistent context
        if self.user_data_dir and os.path.exists(self.user_data_dir):
            # When using a persistent context, we don't need to create a browser instance
            # The persistent context is both the browser and the context
            executable_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
            
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                executable_path=executable_path if os.path.exists(executable_path) else None,
                headless=self.headless,
                slow_mo=self.slow_mo,
                args=browser_args,
                **context_options
            )
            
            # Get the first page or create a new one
            pages = self.context.pages
            self.page = pages[0] if pages else await self.context.new_page()
        else:
            # Launch a regular browser and context
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                slow_mo=self.slow_mo,
                args=browser_args
            )
            
            # Create a browser context
            self.context = await self.browser.new_context(**context_options)
            self.page = await self.context.new_page()
        
        return self.page
    
    async def close(self):
        """Close the browser and all associated resources."""
        if self.context and not self.browser:
            # If we have a context but no browser, we're using a persistent context
            await self.context.close()
        elif self.browser:
            await self.browser.close()
            
        if self.playwright:
            await self.playwright.stop()
            
    async def new_page(self) -> Page:
        """Create and return a new page in the current context."""
        if not self.context:
            raise RuntimeError("Browser context not initialized. Call start() first.")
        
        return await self.context.new_page()
    
    async def save_storage_state(self, path: str):
        """Save browser storage state (cookies, localStorage) to a file."""
        if self.context:
            await self.context.storage_state(path=path)
            
    async def load_storage_state(self, path: str):
        """Load browser storage state from a file."""
        if self.context:
            await self.context.storage_state(path=path)
            
    async def screenshot(self, path: str):
        """Take a screenshot of the current page."""
        if self.page:
            await self.page.screenshot(path=path)
