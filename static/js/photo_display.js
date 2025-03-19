/**
 * Photo Display Utility
 * 
 * Provides functionality to display photos in a fullscreen overlay
 */

// Create a namespace for our photo display functionality
window.photoDisplay = {
    /**
     * Display a photo in the center of the screen with facial landmarks and metrics
     * 
     * @param {string} url - URL of the image to display
     * @param {Array} landmarks - Array of [x,y] coordinates for facial landmarks
     * @param {number} attractivenessScore - Attractiveness score (0-10)
     * @param {Object} metrics - Object containing detailed metrics
     * @param {number} originalWidth - Original width of the image
     * @param {number} originalHeight - Original height of the image
     */
    displayPhoto: function(url, landmarks, attractivenessScore, metrics, originalWidth, originalHeight) {
        // Remove any existing display container
        const existingContainer = document.getElementById('photo-display-container');
        if (existingContainer) {
            existingContainer.remove();
        }
        
        // Create a new container for the photo
        const container = document.createElement('div');
        container.id = 'photo-display-container';
        container.style.position = 'fixed';
        container.style.top = '0';
        container.style.left = '0';
        container.style.width = '100%';
        container.style.height = '100%';
        container.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
        container.style.zIndex = '9999';
        container.style.display = 'flex';
        container.style.justifyContent = 'center';
        container.style.alignItems = 'center';
        container.style.flexDirection = 'column';
        
        // Create a wrapper for the image and overlays
        const wrapper = document.createElement('div');
        wrapper.style.position = 'relative';
        wrapper.style.maxWidth = '100%';
        wrapper.style.maxHeight = '100%';
        
        // Create the image element
        const img = document.createElement('img');
        img.src = url;
        img.style.maxWidth = '100%';
        img.style.maxHeight = '100%';
        img.style.objectFit = 'contain';
        img.style.border = '2px solid white';
        img.style.borderRadius = '8px';
        img.style.boxShadow = '0 0 20px rgba(255, 255, 255, 0.5)';
        
        // Add the image to the wrapper
        wrapper.appendChild(img);
        
        // Wait for the image to load before adding landmarks
        img.onload = function() {
            // If we have landmarks, create a canvas overlay for them
            if (landmarks && landmarks.length > 0 && originalWidth && originalHeight) {
                
                const canvas = document.createElement('canvas');
                canvas.style.position = 'absolute';
                canvas.style.top = '0';
                canvas.style.left = '0';
                canvas.style.width = '100%';
                canvas.style.height = '100%';
                canvas.style.pointerEvents = 'none'; // Allow clicks to pass through
                
                // Set canvas dimensions to match the image
                canvas.width = img.width;
                canvas.height = img.height;
                
                // Calculate scaling factors
                const scaleX = img.width / originalWidth;
                const scaleY = img.height / originalHeight;
                
                // Draw landmarks on canvas
                const ctx = canvas.getContext('2d');
                ctx.fillStyle = 'rgba(255, 0, 0, 0.8)'; // Changed to red for better visibility
                ctx.strokeStyle = 'rgba(255, 0, 0, 0.8)';
                ctx.lineWidth = 2; // Increased line width
                
                // Draw each landmark point with scaling
                const scaledLandmarks = landmarks.map(point => [
                    point[0] * scaleX,
                    point[1] * scaleY
                ]);
                
                scaledLandmarks.forEach((point, index) => {
                    ctx.beginPath();
                    ctx.arc(point[0], point[1], 2, 0, 2 * Math.PI); // Increased point size
                    ctx.fill();
                });
                
                // Connect specific landmark groups with lines
                const connectPoints = (indices) => {
                    ctx.beginPath();
                    ctx.moveTo(scaledLandmarks[indices[0]][0], scaledLandmarks[indices[0]][1]);
                    for (let i = 1; i < indices.length; i++) {
                        ctx.lineTo(scaledLandmarks[indices[i]][0], scaledLandmarks[indices[i]][1]);
                    }
                    ctx.stroke();
                };
                
                // Jaw line
                connectPoints([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]);
                
                // Left eyebrow
                connectPoints([17, 18, 19, 20, 21]);
                
                // Right eyebrow
                connectPoints([22, 23, 24, 25, 26]);
                
                // Nose bridge
                connectPoints([27, 28, 29, 30]);
                
                // Lower nose
                connectPoints([30, 31, 32, 33, 34, 35, 30]);
                
                // Left eye
                connectPoints([36, 37, 38, 39, 40, 41, 36]);
                
                // Right eye
                connectPoints([42, 43, 44, 45, 46, 47, 42]);
                
                // Outer lip
                connectPoints([48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 48]);
                
                // Inner lip
                connectPoints([60, 61, 62, 63, 64, 65, 66, 67, 60]);
                
                wrapper.appendChild(canvas);
            }
            
            // Create metrics overlay
            const metricsOverlay = document.createElement('div');
            metricsOverlay.style.position = 'absolute';
            metricsOverlay.style.top = '10px';
            metricsOverlay.style.right = '10px';
            metricsOverlay.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
            metricsOverlay.style.color = 'white';
            metricsOverlay.style.padding = '10px';
            metricsOverlay.style.borderRadius = '5px';
            metricsOverlay.style.fontFamily = 'Arial, sans-serif';
            metricsOverlay.style.fontSize = '14px';
            metricsOverlay.style.maxWidth = '200px';
            if (attractivenessScore && metrics) {    
                // Create HTML for metrics
                let metricsHtml = `<h3 style="margin-top: 0; color: ${getScoreColor(attractivenessScore)}">Score: ${attractivenessScore}/10</h3>`;
                
                if (metrics.symmetry !== undefined) {
                    metricsHtml += `<p>Symmetry: ${(metrics.symmetry * 100).toFixed(1)}%</p>`;
                }
                
                if (metrics.golden_ratio !== undefined) {
                    metricsHtml += `<p>Golden Ratio: ${(metrics.golden_ratio * 100).toFixed(1)}%</p>`;
                }
                
                if (metrics.thirds !== undefined) {
                    metricsHtml += `<p>Facial Thirds: ${(metrics.thirds * 100).toFixed(1)}%</p>`;
                }
                
                if (metrics.eye_spacing !== undefined) {
                    metricsHtml += `<p>Eye Spacing: ${(metrics.eye_spacing * 100).toFixed(1)}%</p>`;
                }
                
                metricsOverlay.innerHTML = metricsHtml;
            } else {
                let metricsHtml = `<h3 style="margin-top: 0; color: red">Facial analysis unavailable.</h3>`;
                metricsOverlay.innerHTML = metricsHtml;
            }
            wrapper.appendChild(metricsOverlay);
        };
        
        // Add the wrapper to the container
        container.appendChild(wrapper);
        
        // Add click event to close the display
        container.addEventListener('click', () => {
            container.remove();
        });
        
        // Add the container to the body
        document.body.appendChild(container);
    },
    
    /**
     * Remove the photo display container
     */
    removePhotoDisplay: function() {
        const container = document.getElementById('photo-display-container');
        if (container) {
            container.remove();
        }
    }
};

// Helper function to get color based on score
function getScoreColor(score) {
    if (score >= 8) return '#4CAF50'; // Green for high scores
    if (score >= 6) return '#FFC107'; // Amber for medium scores
    return '#F44336'; // Red for low scores
}
