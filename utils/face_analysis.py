"""
Face Analysis Module

This module provides functions for facial landmark detection and attractiveness analysis.
"""

import os
import cv2
import dlib
import numpy as np
import math
import json
import urllib.request
import tempfile
from typing import List, Dict, Any, Optional, Tuple

def calculate_distance(point1, point2):
    """Calculate Euclidean distance between two points."""
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def calculate_facial_symmetry(landmarks):
    """
    Calculate facial symmetry score based on landmarks.
    
    Args:
        landmarks: List of (x, y) coordinates for the 68 facial landmarks
        
    Returns:
        symmetry_score: Score between 0-1, where 1 is perfectly symmetrical
    """
    # Define pairs of landmarks that should be symmetrical
    # Format: (left_point_idx, right_point_idx, midline_point_idx)
    symmetry_pairs = [
        # Jaw
        (2, 14, 8),  # Jaw points with chin as midline
        (3, 13, 8),
        (4, 12, 8),
        (5, 11, 8),
        (6, 10, 8),
        (7, 9, 8),
        
        # Eyebrows
        (17, 26, 8),  # Eyebrows with nose bridge as midline
        (18, 25, 8),
        (19, 24, 8),
        (20, 23, 8),
        (21, 22, 8),
        
        # Eyes
        (36, 45, 27),  # Eyes with nose bridge as midline
        (37, 44, 27),
        (38, 43, 27),
        (39, 42, 27),
        (40, 47, 27),
        (41, 46, 27),
        
        # Nose
        (31, 35, 33),  # Nose with nose tip as midline
        
        # Mouth
        (48, 54, 51),  # Mouth with center of upper lip as midline
        (49, 53, 51),
        (50, 52, 51),
        (59, 55, 57),  # Lower lip with center of lower lip as midline
        (58, 56, 57),
    ]
    
    # Calculate asymmetry for each pair
    asymmetry_scores = []
    for left_idx, right_idx, midline_idx in symmetry_pairs:
        left_point = landmarks[left_idx]
        right_point = landmarks[right_idx]
        midline_point = landmarks[midline_idx]
        
        # Calculate distances from each point to the midline point
        left_distance = calculate_distance(left_point, midline_point)
        right_distance = calculate_distance(right_point, midline_point)
        
        # Calculate asymmetry as the difference in distances
        if max(left_distance, right_distance) > 0:
            pair_asymmetry = abs(left_distance - right_distance) / max(left_distance, right_distance)
            asymmetry_scores.append(pair_asymmetry)
    
    # Calculate overall symmetry score (1 - average asymmetry)
    if asymmetry_scores:
        symmetry_score = 1 - (sum(asymmetry_scores) / len(asymmetry_scores))
        return symmetry_score
    else:
        return 0

def calculate_golden_ratio(landmarks):
    """
    Calculate how well facial proportions match the golden ratio (1.618).
    
    Args:
        landmarks: List of (x, y) coordinates for the 68 facial landmarks
        
    Returns:
        golden_ratio_score: Score between 0-1, where 1 is perfect match to golden ratio
    """
    # The golden ratio
    phi = 1.618
    
    # Define ratios to check against the golden ratio
    # Format: (point1_idx, point2_idx, point3_idx, point4_idx)
    # We'll check if distance(point1, point2) / distance(point3, point4) is close to phi
    golden_ratio_pairs = [
        # Face height to width ratio
        ((8, 27), (0, 16)),  # (chin to nose bridge) / (ear to ear)
        
        # Eye spacing ratio
        ((39, 42), (36, 39)),  # (inner eye distance) / (eye width)
        ((39, 42), (42, 45)),
        
        # Mouth to nose ratio
        ((33, 51), (51, 57)),  # (nose tip to upper lip) / (upper lip to lower lip)
        
        # Eye to eyebrow ratio
        ((37, 19), (40, 37)),  # (eyebrow to upper eye) / (upper eye to lower eye)
        ((44, 24), (47, 44)),
        
        # Nose length to width ratio
        ((27, 33), (31, 35)),  # (nose bridge to nose tip) / (nose width)
    ]
    
    # Calculate how close each ratio is to the golden ratio
    ratio_scores = []
    for (p1_idx, p2_idx), (p3_idx, p4_idx) in golden_ratio_pairs:
        dist1 = calculate_distance(landmarks[p1_idx], landmarks[p2_idx])
        dist2 = calculate_distance(landmarks[p3_idx], landmarks[p4_idx])
        
        if dist2 > 0:
            ratio = dist1 / dist2
            # Calculate how close the ratio is to phi (1 - normalized difference)
            ratio_score = 1 - min(abs(ratio - phi) / phi, 1.0)
            ratio_scores.append(ratio_score)
    
    # Calculate overall golden ratio score
    if ratio_scores:
        golden_ratio_score = sum(ratio_scores) / len(ratio_scores)
        return golden_ratio_score
    else:
        return 0

def calculate_facial_thirds(landmarks):
    """
    Calculate how well the face follows the rule of facial thirds.
    
    Args:
        landmarks: List of (x, y) coordinates for the 68 facial landmarks
        
    Returns:
        thirds_score: Score between 0-1, where 1 is perfect facial thirds
    """
    # Ideal facial thirds:
    # 1. Hairline to eyebrows
    # 2. Eyebrows to bottom of nose
    # 3. Bottom of nose to bottom of chin
    
    # Since we don't have hairline, we'll use the top of the face (highest point of eyebrows)
    top_of_face = min(landmarks[17:27], key=lambda p: p[1])[1]  # Minimum y-value of eyebrows
    eyebrows_y = top_of_face
    nose_bottom_y = landmarks[33][1]  # Bottom of nose (point 33)
    chin_y = landmarks[8][1]  # Bottom of chin (point 8)
    
    # Calculate the three thirds
    upper_third = nose_bottom_y - eyebrows_y
    middle_third = chin_y - nose_bottom_y
    
    # Ideal proportion is when all thirds are equal
    ideal_third = (chin_y - eyebrows_y) / 2
    
    # Calculate deviation from ideal
    upper_deviation = abs(upper_third - ideal_third) / ideal_third
    middle_deviation = abs(middle_third - ideal_third) / ideal_third
    
    # Calculate thirds score (1 - average deviation)
    thirds_score = 1 - ((upper_deviation + middle_deviation) / 2)
    return max(0, min(thirds_score, 1))  # Ensure score is between 0-1

def calculate_eye_spacing(landmarks):
    """
    Calculate how well the eyes follow the ideal spacing rule.
    
    Args:
        landmarks: List of (x, y) coordinates for the 68 facial landmarks
        
    Returns:
        eye_spacing_score: Score between 0-1, where 1 is perfect eye spacing
    """
    # Ideal eye spacing: The distance between the eyes should be equal to the width of one eye
    
    # Calculate eye widths
    left_eye_width = calculate_distance(landmarks[36], landmarks[39])
    right_eye_width = calculate_distance(landmarks[42], landmarks[45])
    
    # Calculate distance between eyes
    inner_eye_distance = calculate_distance(landmarks[39], landmarks[42])
    
    # Calculate average eye width
    avg_eye_width = (left_eye_width + right_eye_width) / 2
    
    # Calculate deviation from ideal (inner eye distance should equal average eye width)
    if avg_eye_width > 0:
        deviation = abs(inner_eye_distance - avg_eye_width) / avg_eye_width
        eye_spacing_score = 1 - min(deviation, 1.0)
        return eye_spacing_score
    else:
        return 0

def calculate_attractiveness(landmarks):
    """
    Calculate overall attractiveness score based on various facial metrics.
    
    Args:
        landmarks: List of (x, y) coordinates for the 68 facial landmarks
        
    Returns:
        attractiveness_score: Score between 0-10
        metrics: Dictionary of individual metrics
    """
    # Calculate individual metrics
    symmetry_score = calculate_facial_symmetry(landmarks)
    golden_ratio_score = calculate_golden_ratio(landmarks)
    thirds_score = calculate_facial_thirds(landmarks)
    eye_spacing_score = calculate_eye_spacing(landmarks)
    
    # Calculate weighted overall score (0-1 scale)
    weights = {
        'symmetry': 0.35,
        'golden_ratio': 0.25,
        'thirds': 0.2,
        'eye_spacing': 0.2
    }
    
    overall_score = (
        symmetry_score * weights['symmetry'] +
        golden_ratio_score * weights['golden_ratio'] +
        thirds_score * weights['thirds'] +
        eye_spacing_score * weights['eye_spacing']
    )
    
    # Convert to 0-10 scale
    attractiveness_score = overall_score * 10
    
    # Round to 1 decimal place
    attractiveness_score = round(attractiveness_score, 1)
    
    # Compile metrics
    metrics = {
        'symmetry': round(symmetry_score, 3),
        'golden_ratio': round(golden_ratio_score, 3),
        'thirds': round(thirds_score, 3),
        'eye_spacing': round(eye_spacing_score, 3),
        'overall': attractiveness_score
    }
    
    return attractiveness_score, metrics

async def ensure_shape_predictor_exists():
    """
    Download the shape predictor model if it doesn't exist.
    """
    # Create models directory if it doesn't exist
    os.makedirs("models", exist_ok=True)
    
    model_path = "models/shape_predictor_68_face_landmarks.dat"
    if not os.path.exists(model_path):
        print("Downloading facial landmark predictor model...")
        model_url = "https://github.com/davisking/dlib-models/raw/master/shape_predictor_68_face_landmarks.dat.bz2"
        
        # Download the compressed model
        compressed_path = f"{model_path}.bz2"
        urllib.request.urlretrieve(model_url, compressed_path)
        
        # Decompress the model
        import bz2
        with open(model_path, 'wb') as f_out, bz2.BZ2File(compressed_path, 'rb') as f_in:
            f_out.write(f_in.read())
            
        # Remove the compressed file
        os.remove(compressed_path)
        print("Model downloaded and extracted successfully")

def extract_facial_landmarks(image_path):
    """
    Extract 68 facial landmarks from an image.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        landmarks: List of (x, y) coordinates for the 68 facial landmarks
        image_dimensions: Tuple of (width, height) of the original image
    """
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Failed to load image from {image_path}")
        return None, None
        
    # Get image dimensions for debugging
    height, width, channels = image.shape
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Try different face detection approaches
    
    # 1. First try: dlib's HOG-based detector
    detector = dlib.get_frontal_face_detector()
    faces = detector(gray)
    
    # 2. If that fails, try with different parameters
    if len(faces) == 0:
        # Try with upsampling to detect smaller faces
        faces = detector(gray, 1)  # Upsample 1 time
    
    # 3. If still no faces, try OpenCV's Haar cascade
    if len(faces) == 0:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        opencv_faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(opencv_faces) > 0:
            # Convert OpenCV face format to dlib format
            x, y, w, h = opencv_faces[0]
            faces = [dlib.rectangle(x, y, x+w, y+h)]
    
    # Return None if no faces detected
    if len(faces) == 0:
        print("No faces detected in the image with any method.")
        return None, None

    # Return None if multiple faces detected
    if len(faces) > 1:
        print("Multiple faces detected in the image, skipping.")
        return None, None
        
    # Get the first (and only) face
    face = faces[0]
    
    # Draw the face rectangle for visualization
    cv2.rectangle(image, (face.left(), face.top()), (face.right(), face.bottom()), (0, 0, 255), 2)
    
    try:
        # Get facial landmarks
        predictor = dlib.shape_predictor("models/shape_predictor_68_face_landmarks.dat")
        shape = predictor(gray, face)
        
        # Convert landmarks to numpy array
        landmarks = []
        for i in range(68):
            x = shape.part(i).x
            y = shape.part(i).y
            landmarks.append((x, y))
        return landmarks, (width, height)
    except Exception as e:
        print(f"Error extracting landmarks: {e}")
        return None, None

async def process_image_from_url(url, index=0):
    """
    Process an image from a URL, extract facial landmarks, and calculate attractiveness.
    
    Args:
        url: URL of the image
        index: Index of the image (for saving files)
        
    Returns:
        landmarks: List of (x, y) coordinates for the 68 facial landmarks
        attractiveness_score: Overall attractiveness score
        metrics: Dictionary of attractiveness metrics
        image_dimensions: Tuple of (width, height) of the original image
    """
    try:
        # Download the image from URL
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_path = temp_file.name
            try:
                urllib.request.urlretrieve(url, temp_path)
            except Exception as e:
                print(f"Error downloading image: {e}")
                return None, None, None, None
        
        # Extract facial landmarks
        landmarks, image_dimensions = extract_facial_landmarks(temp_path)
        
        if landmarks:
            # Calculate attractiveness metrics
            attractiveness_score, metrics = calculate_attractiveness(landmarks)
            
            # Clean up the temporary file
            os.unlink(temp_path)
            
            return landmarks, attractiveness_score, metrics, image_dimensions
        else:
            # Clean up the temporary file
            os.unlink(temp_path)
            
            return None, None, None, None
            
    except Exception as e:
        print(f"Error processing image: {e}")
        return None, None, None, None
