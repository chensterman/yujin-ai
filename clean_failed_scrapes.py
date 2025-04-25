#!/usr/bin/env python3
"""
Clean Failed Scrapes

This script scans through the data/json directory and removes company directories
where the scraping failed with a 402 error (payment required).
"""

import os
import json
import shutil


def is_failed_scrape(file_path):
    """
    Check if a company_data.json file contains failed scrape data

    Args:
        file_path: Path to the company_data.json file

    Returns:
        True if the file contains failed scrape data, False otherwise
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Check if the file has the specific error pattern
        if (data.get("name") == "Unknown" and
            data.get("investors_data", {}).get("error") == "Failed to fetch investors" and
            data.get("investors_data", {}).get("status") == 402 and
            data.get("founders_data", {}).get("error") == "Failed to fetch founders" and
            data.get("founders_data", {}).get("status") == 402 and
            data.get("general_info_data", {}).get("error") == "Failed to fetch general_info" and
                data.get("general_info_data", {}).get("status") == 402):
            return True

        return False
    except (json.JSONDecodeError, FileNotFoundError, KeyError):
        # If there's an error reading the file, return False
        return False


def clean_failed_scrapes(base_dir="data/json"):
    """
    Scan through the data/json directory and remove directories with failed scrapes

    Args:
        base_dir: Base directory containing company subdirectories
    """
    if not os.path.exists(base_dir):
        print(f"Directory {base_dir} does not exist.")
        return

    removed_count = 0
    for company_dir in os.listdir(base_dir):
        company_path = os.path.join(base_dir, company_dir)

        # Skip if not a directory
        if not os.path.isdir(company_path):
            continue

        # Check for company_data.json
        company_data_file = os.path.join(company_path, "company_data.json")
        if os.path.exists(company_data_file):
            if is_failed_scrape(company_data_file):
                print(f"Removing failed scrape directory: {company_dir}")
                shutil.rmtree(company_path)
                removed_count += 1

    print(
        f"Cleaning complete. Removed {removed_count} failed scrape directories.")


if __name__ == "__main__":
    # Run the clean-up process
    clean_failed_scrapes()
    print("Done.")
