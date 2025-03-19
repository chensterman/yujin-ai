"""
Browser Manager for Tinder Automation

This module handles browser initialization, configuration, and management.
"""

import asyncio
import os
import glob
import random
import json
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
                 user_data_dir: Optional[str] = None,
                 proxy: Optional[Dict[str, str]] = None,
                 enable_stealth_mode: bool = True,
                 randomize_behavior: bool = True,
                 bypass_webdriver_flags: bool = True,
                 use_debug_mode: bool = True):
        """
        Initialize the browser manager.
        
        Args:
            headless: Whether to run browser in headless mode
            slow_mo: Slow down operations by specified milliseconds
            viewport_size: Browser viewport dimensions
            user_agent: Custom user agent string
            user_data_dir: Path to Chrome user data directory for using existing profiles
            proxy: Proxy configuration (e.g., {"server": "http://myproxy.com:3128"})
            enable_stealth_mode: Whether to enable stealth mode to avoid detection
            randomize_behavior: Whether to randomize behavior to appear more human-like
            bypass_webdriver_flags: Whether to bypass webdriver detection flags
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.viewport_size = viewport_size
        self.user_agent = user_agent or self._get_random_user_agent()
        self.user_data_dir = user_data_dir
        self.proxy = proxy
        self.enable_stealth_mode = enable_stealth_mode
        self.randomize_behavior = randomize_behavior
        self.bypass_webdriver_flags = bypass_webdriver_flags
        self.use_debug_mode = use_debug_mode
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    def _get_random_user_agent(self) -> str:
        """
        Get a random modern user agent string.
        
        Returns:
            A random user agent string
        """
        modern_user_agents = [
            # Chrome on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            # Chrome on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            # Firefox on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            # Firefox on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
            # Safari on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
            # Edge on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        ]
        return random.choice(modern_user_agents)
    
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
    
    async def _apply_stealth_mode(self, page: Page):
        """
        Apply stealth mode to avoid detection.
        
        Args:
            page: Playwright page object
        """
        # Inject stealth scripts to mask automation
        await page.add_init_script("""
        () => {
            // Override navigator properties to avoid detection
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
                configurable: true
            });
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );
            
            // Prevent fingerprinting via canvas
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            CanvasRenderingContext2D.prototype.getImageData = function(x, y, w, h) {
                const imageData = originalGetImageData.call(this, x, y, w, h);
                // Add slight random noise to canvas data to prevent fingerprinting
                for (let i = 0; i < imageData.data.length; i += 4) {
                    // Only modify a small percentage of pixels
                    if (Math.random() < 0.005) {
                        const offset = Math.floor(Math.random() * 2);
                        imageData.data[i] = Math.max(0, Math.min(255, imageData.data[i] + offset));
                        imageData.data[i+1] = Math.max(0, Math.min(255, imageData.data[i+1] + offset));
                        imageData.data[i+2] = Math.max(0, Math.min(255, imageData.data[i+2] + offset));
                    }
                }
                return imageData;
            };
            
            // Mask plugins and mime types
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const plugins = [
                        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: 'Portable Document Format' },
                        { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
                    ];
                    
                    plugins.__proto__ = window.PluginArray.prototype;
                    plugins.length = plugins.length;
                    plugins.item = function(index) { return this[index]; };
                    plugins.namedItem = function(name) {
                        for (const plugin of plugins) {
                            if (plugin.name === name) return plugin;
                        }
                        return null;
                    };
                    
                    return plugins;
                }
            });
            
            // Mask platform
            Object.defineProperty(navigator, 'platform', {
                get: () => {
                    const platforms = ['MacIntel', 'Win32', 'Linux x86_64'];
                    return platforms[Math.floor(Math.random() * platforms.length)];
                }
            });
        }
        """)
        
        # Set hardware concurrency to a common value
        await page.evaluate("""
        () => {
            try {
                // Check if the property is configurable
                const descriptor = Object.getOwnPropertyDescriptor(navigator, 'hardwareConcurrency');
                if (descriptor && descriptor.configurable) {
                    Object.defineProperty(navigator, 'hardwareConcurrency', {
                        get: () => {
                            return [2, 4, 8][Math.floor(Math.random() * 3)];
                        }
                    });
                }
            } catch (e) {
                console.log('Could not modify hardwareConcurrency:', e);
            }
        }
        """)
        
        # Randomize device memory
        await page.evaluate("""
        () => {
            try {
                // Check if the property is configurable
                const descriptor = Object.getOwnPropertyDescriptor(navigator, 'deviceMemory');
                if (descriptor && descriptor.configurable) {
                    Object.defineProperty(navigator, 'deviceMemory', {
                        get: () => {
                            return [2, 4, 8][Math.floor(Math.random() * 3)];
                        }
                    });
                }
            } catch (e) {
                console.log('Could not modify deviceMemory:', e);
            }
        }
        """)
    
    async def _randomize_mouse_movements(self, page: Page):
        """
        Add a script to randomize mouse movements to appear more human-like.
        
        Args:
            page: Playwright page object
        """
        await page.add_init_script("""
        () => {
            // Store original mouse methods
            const originalMouseMove = window.MouseEvent.prototype.movementX;
            const originalMouseDown = window.MouseEvent.prototype.movementY;
            
            // Add slight randomness to mouse movements
            Object.defineProperties(MouseEvent.prototype, {
                movementX: {
                    get: function() {
                        const value = typeof originalMouseMove === 'function' ? 
                            originalMouseMove.call(this) : this.screenX - this.screenX;
                        return value + (Math.random() < 0.1 ? (Math.random() * 2 - 1) : 0);
                    }
                },
                movementY: {
                    get: function() {
                        const value = typeof originalMouseDown === 'function' ? 
                            originalMouseDown.call(this) : this.screenY - this.screenY;
                        return value + (Math.random() < 0.1 ? (Math.random() * 2 - 1) : 0);
                    }
                }
            });
        }
        """)
    
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
        
        if self.bypass_webdriver_flags:
            browser_args.extend([
                '--disable-blink-features=AutomationControlled',
                '--disable-features=AutomationControlled',
            ])
        
        # Context options
        context_options = {
            "viewport": self.viewport_size,
        }
        
        # Additional options for regular (non-persistent) context
        regular_context_options = {
            "ignoreHTTPSErrors": True,
            "javaScriptEnabled": True,
        }
        
        if self.user_agent:
            context_options["userAgent"] = self.user_agent
            
        if self.proxy:
            context_options["proxy"] = self.proxy
            
        # Add timezone and locale for more realistic browser fingerprint
        context_options["locale"] = "en-US"
        context_options["timezoneId"] = "America/New_York"
        
        # Add geolocation for more realistic browser fingerprint
        context_options["geolocation"] = {
            "latitude": 40.7128,  # New York City coordinates
            "longitude": -74.0060,
            "accuracy": 100
        }
        
        # Add permissions
        context_options["permissions"] = ["geolocation", "notifications"]
        
        if self.use_debug_mode:
            self.browser = await self.playwright.chromium.connect_over_cdp("http://localhost:9222")
            self.context = self.browser.contexts[0]
            self.page = self.context.pages[0]
        elif self.user_data_dir and os.path.exists(self.user_data_dir):
            # If user data directory is specified, use persistent context
            # When using a persistent context, we don't need to create a browser instance
            # The persistent context is both the browser and the context
            executable_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
            
            # For persistent context, we use only the compatible options
            persistent_context_options = {}
            
            # Only add viewport as it's the only guaranteed compatible option
            if "viewport" in context_options:
                persistent_context_options["viewport"] = context_options["viewport"]
                
            # Add user-agent as a command-line argument instead
            if self.user_agent:
                browser_args.append(f'--user-agent="{self.user_agent}"')
            
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                executable_path=executable_path if os.path.exists(executable_path) else None,
                headless=self.headless,
                slow_mo=self.slow_mo,
                args=browser_args,
                **persistent_context_options
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
            
            # Create a browser context with all options
            all_context_options = {**context_options, **regular_context_options}
            self.context = await self.browser.new_context(**all_context_options)
            self.page = await self.context.new_page()
        
        # Apply stealth mode if enabled
        if self.enable_stealth_mode:
            await self._apply_stealth_mode(self.page)
            
        # Add randomized mouse movements if enabled
        if self.randomize_behavior:
            await self._randomize_mouse_movements(self.page)
            
        # Add random viewport noise to avoid fingerprinting
        if self.randomize_behavior:
            # Slightly randomize the viewport size (±5 pixels)
            width_noise = random.randint(-5, 5)
            height_noise = random.randint(-5, 5)
            await self.page.set_viewport_size({
                "width": self.viewport_size["width"] + width_noise,
                "height": self.viewport_size["height"] + height_noise
            })
        
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
        
        page = await self.context.new_page()
        
        # Apply stealth mode to new page if enabled
        if self.enable_stealth_mode:
            await self._apply_stealth_mode(page)
            
        # Add randomized mouse movements if enabled
        if self.randomize_behavior:
            await self._randomize_mouse_movements(page)
        
        return page
    
    async def save_storage_state(self, path: str):
        """Save browser storage state (cookies, localStorage) to a file."""
        if self.context:
            await self.context.storage_state(path=path)
            
    async def load_storage_state(self, path: str):
        """Load browser storage state (cookies, localStorage) from a file."""
        if os.path.exists(path):
            if self.context:
                await self.context.add_cookies(json.load(open(path))["cookies"])
    
    async def add_random_delays(self, min_delay: int = 100, max_delay: int = 500):
        """
        Add random delays between actions to mimic human behavior.
        
        Args:
            min_delay: Minimum delay in milliseconds
            max_delay: Maximum delay in milliseconds
        """
        delay = random.randint(min_delay, max_delay)
        await asyncio.sleep(delay / 1000)  # Convert to seconds
    
    async def screenshot(self, path: str):
        """Take a screenshot of the current page."""
        if self.page:
            await self.page.screenshot(path=path)
