"""
File Utilities

This module provides utility functions for file operations.
"""

import os
import json
from typing import Any


def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory_path: Path to the directory
    """
    os.makedirs(directory_path, exist_ok=True)


def save_to_json(data: Any, filename: str) -> None:
    """
    Save data to a JSON file

    Args:
        data: Data to save (must be JSON serializable)
        filename: Name of the file to save to (will be stored in data/json/)
    """
    ensure_directory_exists("data/json")
    filepath = f"data/json/{filename}"

    try:
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)
        print(f"✅ Successfully saved data to {filepath}")
    except Exception as e:
        print(f"❌ Error saving to JSON: {str(e)}")


def load_from_json(filename: str) -> Any:
    """
    Load data from a JSON file

    Args:
        filename: Name of the file to load from (will be looked for in data/json/)

    Returns:
        The loaded data, or None if the file doesn't exist or can't be parsed
    """
    filepath = f"data/json/{filename}"

    try:
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            return None

        with open(filepath, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
        print(f"✅ Successfully loaded data from {filepath}")
        return data
    except Exception as e:
        print(f"❌ Error loading from JSON: {str(e)}")
        return None
