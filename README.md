# PitchBook Scraper

A tool for scraping company data from PitchBook profiles.

## Project Structure

The project is organized into several modules:

- `browser/`: Contains all browser automation functionality

  - `browser_manager.py`: Manages the browser instance
  - `element_highlighter.py`: Highlights elements on the page
  - `page_controller.py`: Controls page navigation and interaction
  - `browser_helpers.py`: Helper functions for browser initialization

- `scraping/`: Contains PitchBook-specific scraping logic

  - `scraper.py`: Core scraping functionality

- `utils/`: Utility functions
  - `config.py`: Configuration management
  - `logger.py`: Logging utilities
  - `file_utils.py`: File operation utilities
  - `profile_selector.py`: Profile selection utilities

## Usage

To run the scraper, use:

```bash
python pitchbook_scraper.py [company_id]
```

If no company ID is provided, it will default to "65298-34".

## Legacy Support

The original `yujin-adapted.py` script is maintained for backward compatibility but redirects to the new modular code.
