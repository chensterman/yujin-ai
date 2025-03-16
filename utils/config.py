"""
Configuration Utility for Tinder Automation

This module handles loading and managing configuration settings.
"""

import os
import json
from typing import Dict, Any, Optional
import logging


class Config:
    """Configuration manager for the application."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.logger = logging.getLogger("Config")
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "config.json"
        )
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Returns:
            Configuration dictionary
        """
        # Default configuration
        default_config = {
            "browser": {
                "headless": False,
                "slow_mo": 50,
                "viewport_size": {
                    "width": 1280,
                    "height": 800
                },
                "user_agent": None
            },
            "highlighting": {
                "enabled": True,
                "default_color": "rgba(255, 105, 180, 0.5)",
                "success_color": "rgba(0, 255, 0, 0.5)",
                "error_color": "rgba(255, 0, 0, 0.5)",
                "duration": 2000,
                "pulse_effect": True
            },
            "tinder": {
                "base_url": "https://tinder.com",
                "swipe_delay": 1000,
                "message_check_interval": 60000,  # 1 minute
                "auto_message": True,
                "max_swipes_per_session": 100
            },
            "storage": {
                "cookies_path": "data/cookies.json",
                "screenshots_dir": "data/screenshots",
                "logs_dir": "logs"
            }
        }
        
        # Try to load from file
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    
                # Merge with defaults (keeping loaded values)
                self._deep_update(default_config, loaded_config)
                self.logger.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                self.logger.error(f"Failed to load configuration: {str(e)}")
        else:
            self.logger.warning(f"Configuration file not found at {self.config_path}, using defaults")
            
            # Create the default config file
            self._save_config(default_config)
            
        return default_config
    
    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Recursively update a nested dictionary.
        
        Args:
            target: Target dictionary to update
            source: Source dictionary with new values
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def _save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save configuration to file.
        
        Args:
            config: Configuration to save, or current config if None
            
        Returns:
            True if saved successfully, False otherwise
        """
        config = config or self.config
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
                
            self.logger.info(f"Saved configuration to {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Dot-separated path to the configuration value
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        parts = key.split('.')
        current = self.config
        
        for part in parts:
            if part not in current:
                return default
            current = current[part]
            
        return current
    
    def set(self, key: str, value: Any, save: bool = True) -> bool:
        """
        Set a configuration value.
        
        Args:
            key: Dot-separated path to the configuration value
            value: New value to set
            save: Whether to save to file immediately
            
        Returns:
            True if set successfully, False otherwise
        """
        parts = key.split('.')
        current = self.config
        
        # Navigate to the parent of the target key
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
            
        # Set the value
        current[parts[-1]] = value
        
        # Save if requested
        if save:
            return self._save_config()
            
        return True
    
    def save(self) -> bool:
        """
        Save the current configuration to file.
        
        Returns:
            True if saved successfully, False otherwise
        """
        return self._save_config()
