"""Webpage generation module for the signboard application."""
from jinja2 import Environment, FileSystemLoader
import os
import logging
from typing import List, Dict, Optional

class WebpageManager:
    """Manages webpage generation and updates"""
    def __init__(self, base_dir: str, logger: Optional[logging.Logger] = None):
        self.base_dir = base_dir
        self.logger = logger or logging.getLogger(__name__)
        
        # Setup Jinja2 environment
        self.env = Environment(loader=FileSystemLoader(os.path.join(base_dir, 'templates')))

    def update_webpage(self, updates: List[Dict[str, str]], card_data: List[Dict[str, str]], 
                      template_name: str = 'index.html', max_posts: int = 20) -> None:
        """Update the HTML file with content"""
        try:
            template = self.env.get_template(template_name)
            
            # Generate new HTML
            html_content = template.render(
                posts=updates[:max_posts],
                info_cards=card_data
            )
            
            # Write to file
            html_path = os.path.join(self.base_dir, 'templates', 'index.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            self.logger.info(f"Updated webpage with {len(updates)} updates and {len(card_data)} cards")
            
        except Exception as e:
            self.logger.error(f"Error updating webpage: {e}")
            raise
