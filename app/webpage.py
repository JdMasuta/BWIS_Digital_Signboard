"""Webpage generation module for the signboard application."""
from jinja2 import Environment, FileSystemLoader
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime

class WebpageManager:
    """Manages webpage generation and updates"""
    def __init__(self, base_dir: str, logger: Optional[logging.Logger] = None):
        self.base_dir = base_dir
        self.logger = logger or logging.getLogger(__name__)
        
        # Setup Jinja2 environment
        template_dir = os.path.join(base_dir, 'templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))
        
        # Output path is at project root
        self.output_path = os.path.join(base_dir, 'index.html')

    def update_webpage(self, updates: List[Dict[str, str]], card_data: List[Dict[str, str]], 
                      template_name: str = 'index.html', max_posts: int = 20) -> None:
        """Update the HTML file with content"""
        try:
            # Generate update section HTML
            updates_html = ""
            for update in updates[:max_posts]:
                updates_html += f"""
                    <div class="post">
                        <div class="content">
                            {update['content']}
                        </div>
                        <div class="timestamp">
                            Posted: {update['timestamp']}
                        </div>
                    </div>
                """

            # Generate cards section HTML
            cards_html = ""
            for i, card in enumerate(card_data):
                # First card should be active
                active_class = " active" if i == 0 else ""
                cards_html += f"""
                    <div class="card-slide{active_class}">
                        <img src="{card['image']}" 
                             alt="{card['title']}" 
                             class="card-image" 
                             loading="lazy">
                        <div class="card-content">
                            <h3>{card['title']}</h3>
                            <p>{card['description']}</p>
                        </div>
                    </div>
                """

            # Make sure the header section includes the clock container
            header_html = """
            <div class="header">
                <h1>BWIS Loveland</h1>
                <div class="header-time-container">
                    <div id="date-display" class="header-date"></div>
                    <div id="clock-display" class="header-clock"></div>
                </div>
            </div>
            """

            # Read base template
            with open(os.path.join(self.base_dir, 'templates', template_name), 'r', encoding='utf-8') as f:
                template_content = f.read()

            # Insert content into template sections
            html_content = template_content.replace(
                '::: header', 
                f'::: header\n{header_html}'
            ).replace(
                '<div class="posts-area">', 
                f'<div class="posts-area">{updates_html}'
            ).replace(
                '<div class="card-container">', 
                f'<div class="card-container">{cards_html}'
            )

            # Write updated content
            self.logger.debug(f"Writing output to: {self.output_path}")
            with open(self.output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            self.logger.info(f"Updated webpage with {len(updates)} updates and {len(card_data)} cards")

        except Exception as e:
            self.logger.error(f"Error updating webpage: {e}")
            raise
