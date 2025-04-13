/**
 * Loading Indicator Module
 * 
 * This module provides functionality to display a loading indicator in the middle of the screen
 * with a customizable message.
 */

if (!window.loadingIndicator) {
    window.loadingIndicator = {
        loadingContainer: null,
        
        show: function(message = "Loading...") {
            // Remove any existing container
            this.hide();
            
            // Create container
            const container = document.createElement('div');
            container.id = 'loading-indicator-container';
            container.style.position = 'fixed';
            container.style.top = '0';
            container.style.left = '0';
            container.style.width = '100%';
            container.style.height = '100%';
            container.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
            container.style.display = 'flex';
            container.style.justifyContent = 'center';
            container.style.alignItems = 'center';
            container.style.zIndex = '10000';
            container.style.fontFamily = 'Arial, sans-serif';
            
            // Create content wrapper
            const wrapper = document.createElement('div');
            wrapper.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
            wrapper.style.borderRadius = '10px';
            wrapper.style.padding = '30px';
            wrapper.style.display = 'flex';
            wrapper.style.flexDirection = 'column';
            wrapper.style.alignItems = 'center';
            wrapper.style.boxShadow = '0 0 20px rgba(0, 0, 0, 0.3)';
            
            // Create spinner
            const spinner = document.createElement('div');
            spinner.style.width = '50px';
            spinner.style.height = '50px';
            spinner.style.border = '5px solid #f3f3f3';
            spinner.style.borderTop = '5px solid #3498db';
            spinner.style.borderRadius = '50%';
            spinner.style.marginBottom = '15px';
            spinner.style.animation = 'spin 1s linear infinite';
            
            // Add keyframes for spinner animation
            const style = document.createElement('style');
            style.textContent = `
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
            
            // Create message
            const messageElement = document.createElement('div');
            messageElement.textContent = message;
            messageElement.style.color = '#333';
            messageElement.style.fontSize = '18px';
            messageElement.style.fontWeight = 'bold';
            
            // Assemble elements
            wrapper.appendChild(spinner);
            wrapper.appendChild(messageElement);
            container.appendChild(wrapper);
            document.body.appendChild(container);
            
            this.loadingContainer = container;
        },
        
        hide: function() {
            if (this.loadingContainer) {
                document.body.removeChild(this.loadingContainer);
                this.loadingContainer = null;
            }
        }
    };
}
