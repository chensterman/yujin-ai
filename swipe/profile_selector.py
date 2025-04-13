"""
Chrome Profile Selector

This module provides utilities for selecting Chrome profiles for browser automation.
"""

import os
from typing import Optional, Dict, List, Any
from browser.browser_manager import BrowserManager


def select_profile_interactive() -> Optional[str]:
    """
    Interactively select a Chrome profile from the available profiles on the system.
    
    Returns:
        Path to the selected user data directory, or None if no profile selected
    """
    profiles = BrowserManager.get_chrome_profiles()
    
    if not profiles:
        print("No Chrome profiles found on this system.")
        return None
    
    print("\nAvailable Chrome profiles:")
    print("--------------------------")
    
    for i, profile in enumerate(profiles):
        # Display the user-friendly name if available, otherwise use the directory name
        display_name = profile.get('display_name', profile['name'])
        print(f"{i+1}. {display_name} ({profile['name']})")
    
    print(f"{len(profiles)+1}. Don't use a profile (use a fresh browser instance)")
    print("--------------------------")
    
    while True:
        try:
            choice = input("\nSelect a profile number (or press Enter to cancel): ")
            
            if not choice.strip():
                return None
                
            choice_num = int(choice)
            
            if choice_num == len(profiles) + 1:
                # User chose not to use a profile
                return None
                
            if 1 <= choice_num <= len(profiles):
                selected_profile = profiles[choice_num - 1]
                # The user_data_dir is the base path (the "User Data" directory)
                # We don't include the profile name in the path because Playwright
                # will use the entire User Data directory
                user_data_dir = selected_profile['path']
                display_name = selected_profile.get('display_name', selected_profile['name'])
                print(f"\nSelected profile: {display_name} ({selected_profile['name']})")
                print(f"Using User Data directory: {user_data_dir}")
                return user_data_dir
            else:
                print(f"Please enter a number between 1 and {len(profiles)+1}")
        except ValueError:
            print("Please enter a valid number")
