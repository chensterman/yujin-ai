/**
 * Research Display Module
 * 
 * This module provides functionality to display research results in a floating panel.
 * It shows the person's name, description, and thumbnails of found images with match scores.
 */

if (!window.researchDisplay) {
    window.researchDisplay = {
        displayContainer: null,
        
        createDisplayContainer: function() {
            // Remove any existing container
            this.removeResearchDisplay();
            
            // Create container
            const container = document.createElement('div');
            container.id = 'research-display-container';
            container.style.position = 'fixed';
            container.style.top = '20px';
            container.style.right = '20px';
            container.style.width = '400px';
            container.style.maxHeight = '80vh';
            container.style.overflowY = 'auto';
            container.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
            container.style.color = 'white';
            container.style.padding = '20px';
            container.style.borderRadius = '10px';
            container.style.zIndex = '9999';
            container.style.fontFamily = 'Arial, sans-serif';
            container.style.boxShadow = '0 0 20px rgba(0, 0, 0, 0.5)';
            
            document.body.appendChild(container);
            this.displayContainer = container;
            return container;
        },
        
        displayResearch: function(data) {
            const container = this.createDisplayContainer();
            
            // Create header
            const header = document.createElement('div');
            header.style.borderBottom = '1px solid #444';
            header.style.paddingBottom = '10px';
            header.style.marginBottom = '15px';
            header.style.display = 'flex';
            header.style.justifyContent = 'space-between';
            header.style.alignItems = 'center';
            
            const title = document.createElement('h2');
            title.textContent = 'Research Results';
            title.style.margin = '0';
            title.style.color = '#3498db';
            
            header.appendChild(title);
            container.appendChild(header);
            
            // Display name
            if (data.name) {
                const nameEl = document.createElement('h3');
                nameEl.textContent = data.name;
                nameEl.style.color = '#2ecc71';
                nameEl.style.marginBottom = '10px';
                container.appendChild(nameEl);
            }
            
            // Display description
            if (data.description) {
                const descEl = document.createElement('div');
                descEl.style.marginBottom = '20px';
                descEl.style.lineHeight = '1.5';
                descEl.textContent = data.description;
                container.appendChild(descEl);
            }
            
            // Display metadata/thumbnails
            if (data.metadata && data.metadata.length > 0) {
                const metaTitle = document.createElement('h4');
                metaTitle.textContent = 'Found Images:';
                metaTitle.style.color = '#f39c12';
                metaTitle.style.marginTop = '20px';
                metaTitle.style.marginBottom = '10px';
                container.appendChild(metaTitle);
                
                const grid = document.createElement('div');
                grid.style.display = 'grid';
                grid.style.gridTemplateColumns = 'repeat(2, 1fr)';
                grid.style.gap = '10px';
                
                data.metadata.forEach(item => {
                    if (item.thumbnailUrl) {
                        const card = document.createElement('div');
                        card.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                        card.style.borderRadius = '5px';
                        card.style.padding = '10px';
                        card.style.display = 'flex';
                        card.style.flexDirection = 'column';
                        card.style.alignItems = 'center';
                        
                        const imgLink = document.createElement('a');
                        imgLink.href = item.url || '#';
                        imgLink.target = '_blank';
                        
                        const img = document.createElement('img');
                        img.src = item.thumbnailUrl;
                        img.style.width = '100%';
                        img.style.height = 'auto';
                        img.style.borderRadius = '5px';
                        img.style.marginBottom = '5px';
                        
                        imgLink.appendChild(img);
                        card.appendChild(imgLink);
                        
                        if (item.likenessScore) {
                            const score = document.createElement('div');
                            score.textContent = `Match: ${Math.round(item.likenessScore)}%`;
                            score.style.fontSize = '12px';
                            score.style.color = '#3498db';
                            card.appendChild(score);
                        }
                        
                        grid.appendChild(card);
                    }
                });
                
                container.appendChild(grid);
            }
        },
        
        removeResearchDisplay: function() {
            if (this.displayContainer) {
                document.body.removeChild(this.displayContainer);
                this.displayContainer = null;
            }
        }
    };
}
