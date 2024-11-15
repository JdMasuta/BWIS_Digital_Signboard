"""Test content generation module for the signboard application."""
import os
import logging
from typing import Optional, Dict, List
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw
from project_paths import paths

class TestContentManager:
    """Manages generation of test content for development and testing"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize test content manager
        
        Args:
            logger (Optional[logging.Logger]): Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Ensure required directories exist
        paths.ensure_directories()

    def create_test_content(self) -> None:
        """Create complete set of test content"""
        try:
            self._create_test_updates()
            self._create_test_cards()
            self._create_test_images()
            self._update_webpage()
            self.logger.info("Test content created successfully")
            
        except Exception as e:
            self.logger.error(f"Error creating test content: {str(e)}")
            raise

    def _create_test_updates(self) -> None:
        """Create test updates.xml file"""
        self.logger.debug("Creating test updates.xml...")
        
        test_updates = [
            {
                "id": "update1",
                "content": "Test Update 1: This is a test message",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "priority": "high",
                "active": "true"
            },
            {
                "id": "update2", 
                "content": "Test Update 2: Another test message",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "priority": "normal",
                "active": "true"
            }
        ]
        
        root = ET.Element("updates")
        for update_data in test_updates:
            update = ET.SubElement(root, "update")
            for key, value in update_data.items():
                elem = ET.SubElement(update, key)
                elem.text = value
                
        tree = ET.ElementTree(root)
        tree.write(paths.data / "updates.xml", encoding='utf-8', xml_declaration=True)
        self.logger.debug(f"Created updates.xml with {len(test_updates)} updates")

    def _create_test_cards(self) -> None:
        """Create test card_content.xml file"""
        self.logger.debug("Creating test card_content.xml...")
        
        self.test_cards = [
            {
                "id": "card1",
                "title": "Test Card 1",
                "description": "This is a test card description",
                "image": "test1.png",
                "created_date": datetime.now().strftime("%Y-%m-%d"),
                "active": "true"
            },
            {
                "id": "card2",
                "title": "Test Card 2",
                "description": "Another test card description",
                "image": "test2.png",
                "created_date": datetime.now().strftime("%Y-%m-%d"),
                "active": "true"
            }
        ]
        
        root = ET.Element("cards")
        for card_data in self.test_cards:
            card = ET.SubElement(root, "card")
            for key, value in card_data.items():
                elem = ET.SubElement(card, key)
                elem.text = value
                
        tree = ET.ElementTree(root)
        tree.write(paths.data / "card_content.xml", encoding='utf-8', xml_declaration=True)
        self.logger.debug(f"Created card_content.xml with {len(self.test_cards)} cards")

    def _create_test_images(self) -> None:
        """Create test image files"""
        self.logger.debug("Creating test card images...")
        
        def create_test_image(filename: str, text: str):
            """Create a simple test image with text"""
            img = Image.new('RGB', (400, 300), color='white')
            draw = ImageDraw.Draw(img)
            draw.text((10, 10), text, fill='black')
            
            # Add some shapes to make the test image more distinctive
            draw.rectangle([50, 50, 350, 250], outline='blue', width=2)
            draw.ellipse([150, 100, 250, 200], outline='red', width=2)
            
            save_path = paths.cards / filename
            img.save(save_path)
            self.logger.debug(f"Created test image: {save_path}")
            
        for card in self.test_cards:
            create_test_image(card['image'], f"Test Image for {card['title']}")

    def _update_webpage(self) -> None:
        """Update webpage with test content"""
        self.logger.debug("Updating webpage with test content...")
        
        try:
            from webpage import WebpageManager
            webpage_manager = WebpageManager(paths.root, self.logger)
            
            # Prepare card data for webpage
            card_data = [{
                'title': card['title'],
                'description': card['description'],
                'image': os.path.join('/assets/cards', card['image'])
            } for card in self.test_cards]
            
            # Get updates from XML
            tree = ET.parse(paths.data / "updates.xml")
            root = tree.getroot()
            
            updates = []
            for update in root.findall('update'):
                updates.append({
                    'content': update.find('content').text,
                    'timestamp': update.find('timestamp').text
                })
            
            webpage_manager.update_webpage(updates, card_data)
            self.logger.info("Webpage updated with test content")
            
        except Exception as e:
            self.logger.error(f"Error updating webpage with test content: {str(e)}")
            raise

    @staticmethod
    def cleanup_test_content() -> None:
        """Remove all test content files"""
        try:
            # Remove test XML files
            if (paths.data / "updates.xml").exists():
                (paths.data / "updates.xml").unlink()
            if (paths.data / "card_content.xml").exists():
                (paths.data / "card_content.xml").unlink()
                
            # Remove test images
            for image_file in paths.cards.glob("test*.png"):
                image_file.unlink()
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Error cleaning up test content: {str(e)}")
            raise

def main():
    """Main entry point for creating test content"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create test content for signboard')
    parser.add_argument('--clean', action='store_true', 
                       help='Remove test content instead of creating it')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('test_content')
    
    try:
        if args.clean:
            logger.info("Cleaning up test content...")
            TestContentManager.cleanup_test_content()
            logger.info("Test content cleanup complete")
        else:
            logger.info("Creating test content...")
            manager = TestContentManager(logger)
            manager.create_test_content()
            logger.info("Test content creation complete")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if logger.level == logging.DEBUG:
            logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
