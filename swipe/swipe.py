from utils.config import Config
from browser.page_controller import PageController
from browser.element_highlighter import ElementHighlighter
from browser.browser_manager import BrowserManager
from swipe.face_analysis import ensure_shape_predictor_exists, process_image_from_url
from researcher.researcher import research_image
from playwright.async_api import Page
from typing import List, Dict, Any, Optional
import pathlib
import asyncio
import os
import sys
import numpy as np


async def retrieve_profile_info(controller: PageController, highlighter: ElementHighlighter) -> str:
    # Extract all text from the profile
    profile_info = []
    story_sections = {}
    try:
        # Get all story sections (each containing different profile information)
        story_elements = await controller.page.query_selector_all("div.encounters-album__story")
        print(f"\nFound {len(story_elements)} profile sections")
        
        # Process each section separately
        for i, section in enumerate(story_elements):
            section_text = []
            section_title = f"Section {i+1}"
            
            # Try to identify the section type
            section_header = await section.query_selector("h2, h3")
            if section_header:
                header_text = await section_header.text_content()
                if header_text:
                    section_title = header_text.strip()
            
            # Get all text elements within this section
            text_elements = await section.query_selector_all("*")
            for element in text_elements:
                text_content = await element.text_content()
                if text_content and text_content.strip():
                    clean_text = text_content.strip()
                    section_text.append(clean_text)
                    profile_info.append(clean_text)
            
            # Store the section text
            story_sections[section_title] = section_text
        
        # Print the profile information by section
        print("\nProfile Information by Section:")
        for section_title, section_text in story_sections.items():
            print(f"\n[{section_title}]")
            # Remove duplicates within each section
            unique_texts = []
            for text in section_text:
                if text not in unique_texts and len(text) > 1:  # Skip single characters
                    unique_texts.append(text)
                    print(f"- {text}")
        
        # Also create a consolidated view with duplicates removed
        unique_profile_info = []
        for text in profile_info:
            if text not in unique_profile_info and len(text) > 1:  # Skip single characters
                unique_profile_info.append(text)
        
        profile_info = unique_profile_info
        print("\n")
    except Exception as e:
        print(f"Error extracting profile text: {str(e)}")
    
    # Scroll to bottom of profile by clicking the next button until it doesn't exist anymore
    next_button_selector = "div.encounters-album__nav-item.encounters-album__nav-item--next"
    encounters_selector = "div.encounters-album__stories-container"
    encounters_count = len(await controller.page.query_selector_all("div.encounters-album__story"))
    try:
        for i in range(encounters_count):
            # Highlight all text on profile, then extract text data
            await highlighter.highlight_all_text(encounters_selector)
            await asyncio.sleep(0.25)
            await highlighter.remove_all_highlights()
            await asyncio.sleep(0.25)
            next_button = await controller.page.query_selector(next_button_selector)
            await next_button.click()
            await controller.page.wait_for_timeout(500)
    except Exception as e:
        print(f"Error scrolling through profile: {str(e)}")

    # Join all profile text items into a single string
    profile_text = "\n".join(profile_info)
    return profile_text


async def attractiveness_rating(controller: PageController, highlighter: ElementHighlighter):
    """Rate profiles based on attractiveness."""
    
    # Try multiple selectors for profile photos
    profile_photo_selectors = [
        'img.media-box__picture-image',
        'img.profile__photo',
        'div.encounters-story-profile-image img',
        'div[data-qa-role="profile-card"] img',
        'div[data-qa-role="profile-photo"] img',
        'img[alt*="profile"]',
        'img[alt*="photo"]'
    ]
    
    profile_photos = []
    
    # Try each selector
    for selector in profile_photo_selectors:
        photos = await controller.page.query_selector_all(selector)
        if photos and len(photos) > 0:
            profile_photos = photos
            break
    
    if not profile_photos:
        print("No profile photos found with any of the known selectors.")
        return False
    
    # Extract src URLs from all photos
    photo_urls = []
    for photo in profile_photos:
        try:
            src = await photo.get_attribute('src')
            if src:
                # Add HTTPS prefix if missing
                if not src.startswith('https:'):
                    src = 'https:' + src
                # Filter out SVG files
                if not src.endswith('.svg'):
                    photo_urls.append(src)
        except Exception as e:
            print(f"Error extracting src from photo: {e}")
    
    if not photo_urls:
        print("No valid photo URLs found. The page structure might have changed.")
        return False
    
    # Download the shape predictor model if needed
    await ensure_shape_predictor_exists()
    
    root_dir = pathlib.Path(__file__).parent.parent.absolute()
    js_file_path = os.path.join(root_dir, "static", "js", "photo_display.js")
    
    # Read the JavaScript file
    with open(js_file_path, 'r') as file:
        js_code = file.read()
        
    # Inject the JavaScript into the page
    await controller.page.add_script_tag(content=js_code)
    
    # Cycle through each photo and gather total + count for attractiveness
    total_attractiveness = 0
    count = 0
    for i, url in enumerate(photo_urls):
        try:
            # Process the image using the face_analysis module
            landmarks, attractiveness_score, metrics, image_dimensions = await process_image_from_url(url, i)
            
            # Use the injected JavaScript to display the photo with landmarks and metrics
            if landmarks and attractiveness_score and metrics and image_dimensions:

                # Update total attractiveness and count
                total_attractiveness += attractiveness_score
                count += 1

                # Convert landmarks to a format that can be passed to JavaScript
                landmarks_js = [[point[0], point[1]] for point in landmarks]
                
                # Create a data object to pass to JavaScript
                data = {
                    'url': url,
                    'landmarks': landmarks_js,
                    'score': attractiveness_score,
                    'metrics': metrics,
                    'originalWidth': image_dimensions[0],
                    'originalHeight': image_dimensions[1]
                }
                
                # Pass the data to the JavaScript function
                await controller.page.evaluate("""
                    (data) => {
                        window.photoDisplay.displayPhoto(
                            data.url, 
                            data.landmarks, 
                            data.score, 
                            data.metrics,
                            data.originalWidth,
                            data.originalHeight
                        );
                    }
                """, data)
            else:
                # If no landmarks were detected, just display the photo
                await controller.page.evaluate("(url) => window.photoDisplay.displayPhoto(url, null, null, null)", url)
            
            # Wait for the specified duration
            await controller.page.wait_for_timeout(500)  # Display each photo for 0.5 seconds
            
        except Exception as e:
            print(f"Error processing photo: {e}")
    
    # Remove the display container at the end
    await controller.page.evaluate("() => window.photoDisplay.removePhotoDisplay()")

    # Calculate average attractiveness and return True if average attractiveness is greater than 7.0
    average_attractiveness = total_attractiveness / count if count > 0 else 0
    if average_attractiveness > 7.0:
        return True
    return False


async def attractiveness_rating(controller: PageController, highlighter: ElementHighlighter):
    """Rate profiles based on attractiveness."""
    
    # Try multiple selectors for profile photos
    profile_photo_selectors = [
        'img.media-box__picture-image',
        'img.profile__photo',
        'div.encounters-story-profile-image img',
        'div[data-qa-role="profile-card"] img',
        'div[data-qa-role="profile-photo"] img',
        'img[alt*="profile"]',
        'img[alt*="photo"]'
    ]

    profile_photos = []

    # Try each selector
    for selector in profile_photo_selectors:
        photos = await controller.page.query_selector_all(selector)
        if photos and len(photos) > 0:
            profile_photos = photos
            break

    if not profile_photos:
        print("No profile photos found with any of the known selectors.")
        return False

    # Extract src URLs from all photos
    photo_urls = []
    for photo in profile_photos:
        try:
            src = await photo.get_attribute('src')
            if src:
                # Add HTTPS prefix if missing
                if not src.startswith('https:'):
                    src = 'https:' + src
                # Filter out SVG files
                if not src.endswith('.svg'):
                    photo_urls.append(src)
        except Exception as e:
            print(f"Error extracting src from photo: {e}")

    if not photo_urls:
        print("No valid photo URLs found. The page structure might have changed.")
        return False

    # Download the shape predictor model if needed
    await ensure_shape_predictor_exists()

    root_dir = pathlib.Path(__file__).parent.parent.absolute()
    js_file_path = os.path.join(root_dir, "static", "js", "photo_display.js")

    # Read the JavaScript file
    with open(js_file_path, 'r') as file:
        js_code = file.read()

    # Inject the JavaScript into the page
    await controller.page.add_script_tag(content=js_code)

    # Cycle through each photo and gather total + count for attractiveness
    total_attractiveness = 0
    count = 0
    for i, url in enumerate(photo_urls):
        try:
            # Process the image using the face_analysis module
            landmarks, attractiveness_score, metrics, image_dimensions = await process_image_from_url(url, i)

            # Use the injected JavaScript to display the photo with landmarks and metrics
            if landmarks and attractiveness_score and metrics and image_dimensions:

                # Update total attractiveness and count
                total_attractiveness += attractiveness_score
                count += 1

                # Convert landmarks to a format that can be passed to JavaScript
                landmarks_js = [[point[0], point[1]] for point in landmarks]

                # Create a data object to pass to JavaScript
                data = {
                    'url': url,
                    'landmarks': landmarks_js,
                    'score': attractiveness_score,
                    'metrics': metrics,
                    'originalWidth': image_dimensions[0],
                    'originalHeight': image_dimensions[1]
                }

                # Pass the data to the JavaScript function
                await controller.page.evaluate("""
                    (data) => {
                        window.photoDisplay.displayPhoto(
                            data.url, 
                            data.landmarks, 
                            data.score, 
                            data.metrics,
                            data.originalWidth,
                            data.originalHeight
                        );
                    }
                """, data)
            else:
                # If no landmarks were detected, just display the photo
                await controller.page.evaluate("(url) => window.photoDisplay.displayPhoto(url, null, null, null)", url)

            # Wait for the specified duration
            # Display each photo for 2 seconds
            await controller.page.wait_for_timeout(1000)

        except Exception as e:
            print(f"Error processing photo: {e}")

    # Remove the display container at the end
    await controller.page.evaluate("() => window.photoDisplay.removePhotoDisplay()")

    # Calculate average attractiveness and return True if average attractiveness is greater than 7.0
    average_attractiveness = total_attractiveness / count if count > 0 else 0
    if average_attractiveness > 7.0:
        return True
    return False


async def retrieve_profile_photo_url(controller: PageController, highlighter: ElementHighlighter) -> str:
    """Extract the URL of the first profile photo."""
    try:
        # Find the first profile photo with the specified class
        photo_element = await controller.page.query_selector('img.media-box__picture-image')
        
        if not photo_element:
            print("No profile photo found with class 'media-box__picture-image'")
            return ""
        
        # Get the src attribute
        src = await photo_element.get_attribute('src')
        
        if not src:
            print("Profile photo found but no src attribute")
            return ""
        
        # Remove leading slashes if present
        if src.startswith('//'):
            src = src[2:]
        
        # Add https:// if needed
        if not src.startswith('http'):
            src = 'https://' + src
        
        return src
    
    except Exception as e:
        print(f"Error retrieving profile photo URL: {str(e)}")
        return ""


async def swipe_on_latest(controller: PageController, highlighter: ElementHighlighter, testing: bool = False):
    # Navigate to Bumble (assuming logged in) and wait for page to load
    await controller.navigate("https://bumble.com/app")
    await controller.page.wait_for_load_state("domcontentloaded")

    # Retrieve profile information
    profile_photo_url = await retrieve_profile_photo_url(controller, highlighter)
    profile_text = await retrieve_profile_info(controller, highlighter)
    
    # Research personal info
    if not testing:
        person_research = research_image(profile_photo_url, profile_text)
    else:
        person_research = {'name': 'Rieley', 'description': "Rieley is a 27-year-old Account Executive at a SaaS company, who studied at Endicott College. He is based in Boston, Massachusetts, and originally from Hartford, Connecticut. Rieley is 6'1'' tall, identifies as a Sagittarius, and holds a graduate degree. He is active and values consistency and compassion. Rieley enjoys music from artists like Yeat, Playboi Carti, and Lil Uzi Vert.", 'metadata': [{'url': 'https://endicott.prestosports.com/sports/msoc', 'thumbnailUrl': 'https://jsc4.pimeyes.com/proxy/d8ab19d5c7a0f27c10fa57540506ac68c126b9bd1ca84d5db720bf86c391405628829c11fda45e115bdfd565e73e92350d5632c7408f21f1cd86f41c312516518184ddbda6e50e28bcfbf19713d86194d761d44c656bc0da8e1b6493ce5b93c579da5b3336dc4ecfbe2aeedd9fc73b1edf4ce5de5902e1f5585738458b0c3a5746b4aa2719e832eda90a2770b26a0ac0a776450acd6b86c8e7e8e0b18a1da15be9463b2f38590a4c8537a50d72e821d065ae7ca8260104b0c97b190d2f8b1ac67484d6c374c85900d24c5613f3218dcde45e01e49b3a78e07b01a56975fa414f7fea21621b7b059bbefe3c2257c0d6f90a01599037a382fa9acb6d65e225ebd1fb8049d06e99e8ad7cc6ed1758cd5e7901b8af0174bbf97ee324a929e9dc895abce292f007f2c33068e3eed66dcd5a442d6e89c05227e39a4b441562d710ce545b2aaaab52b225ed380cee24384e8cf2', 'likenessScore': 82.97387361526489}]}
    
    # Rate profile attractiveness
    swipe_right = await attractiveness_rating(controller, highlighter)
    
    # Determine swiping based on attractiveness
    button_selector = ""
    if swipe_right:
        button_selector = "div.encounters-action.tooltip-activator.encounters-action--like"
    else:
        button_selector = "div.encounters-action.tooltip-activator.encounters-action--dislike"

    # If testing mode is off, perform the swipe
    if not testing:
        # Highlight and click the swipe button
        await highlighter.highlight_and_click(
            selector=button_selector,
            color="rgba(0, 255, 0, 0.5)",
            pre_click_delay=1000,
            post_click_delay=1000
        )
    
        # Wait for the swipe animation to complete
        await controller.page.wait_for_timeout(1000)

        # If match occurs, check for "continue bumbling" button and click it if present
        continue_button = "button.button.button--size-m:has-text('Continue Bumbling')"
        await highlighter.highlight_and_click(
            selector=continue_button,
            color="rgba(0, 255, 0, 0.5)",  # Green highlight
            pre_click_delay=1000,  # Wait 1 second before clicking
            post_click_delay=1000   # Wait 1 second after clicking
        )
