"""Card update handler for signboard email updates."""
import xml.etree.ElementTree as ET
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Tuple
import re
from email.message import Message
import imghdr
from project_paths import paths

class CardUpdateHandler:
    """Handles processing and storage of card updates"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize card update handler
        
        Args:
            logger (Optional[logging.Logger]): Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.cards_file = paths.data / 'card_content.xml'
        self.images_dir = paths.cards

    def process_update(self, message: Message) -> bool:
        """Process a card update from email
        
        Args:
            message (Message): Email message containing update
            
        Returns:
            bool: True if update was processed successfully
        """
        try:
            self.logger.debug("Processing card update email...")
            
            # Extract update content
            content = self._extract_update_content(message)
            if not content:
                self.logger.warning("No valid update content found in card update email")
                return False
            
            self.logger.debug(f"Extracted card content: {content}")
            
            # Process image attachment
            image_filename = self._process_image_attachment(message)
            if not image_filename:
                self.logger.warning("No valid image attachment found in card update email")
                return False
                
            # Add card to XML file
            return self._add_card_to_xml(content, image_filename)
            
        except Exception as e:
            self.logger.error(f"Error processing card update: {str(e)}")
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug("Full traceback:", exc_info=True)
            return False

    def _extract_update_content(self, message: Message) -> Optional[str]:
        """Extract update content from email message
        
        Args:
            message (Message): Email message to process
            
        Returns:
            Optional[str]: Extracted update content or None if not found
        """
        self.logger.debug("Extracting card content from email...")
        
        try:
            # Get email body
            if message.is_multipart():
                for part in message.walk():
                    if part.get_content_type() == "text/plain":
                        content = part.get_payload(decode=True).decode()
                        break
            else:
                content = message.get_payload(decode=True).decode()
                
            if not content:
                self.logger.warning("No email content found")
                return None
                
            # Look for "Update: " followed by quoted content
            self.logger.debug("Searching for update pattern in content...")
            match = re.search(r'Update:\s*"([^"]+)"', content)
            if match:
                update_text = match.group(1).strip()
                self.logger.debug(f"Found card text: {update_text}")
                return update_text
            else:
                self.logger.warning("No update pattern found in email content")
                return None
                
        except Exception as e:
            self.logger.error(f"Error extracting card content: {str(e)}")
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug("Full traceback:", exc_info=True)
            return None

    def _process_image_attachment(self, message: Message) -> Optional[str]:
        """Process and save image attachment from email
        
        Args:
            message (Message): Email message with attachment
            
        Returns:
            Optional[str]: Filename of saved image or None if failed
        """
        try:
            self.logger.debug("Processing image attachment...")
            
            for part in message.walk():
                if part.get_content_maintype() == 'image':
                    # Get filename from attachment
                    filename = part.get_filename()
                    if not filename:
                        self.logger.warning("No filename in image attachment")
                        continue
                        
                    # Ensure filename is safe
                    safe_filename = Path(filename).name
                    image_path = self.images_dir / safe_filename
                    
                    self.logger.debug(f"Saving image to: {image_path}")
                    
                    # Save image file
                    with open(image_path, 'wb') as f:
                        f.write(part.get_payload(decode=True))
                    
                    # Verify it's a valid image
                    if imghdr.what(image_path):
                        self.logger.info(f"Saved card image: {safe_filename}")
                        return safe_filename
                    else:
                        self.logger.warning(f"Invalid image file: {safe_filename}")
                        image_path.unlink()
                        
            return None
            
        except Exception as e:
            self.logger.error(f"Error processing image attachment: {str(e)}")
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug("Full traceback:", exc_info=True)
            return None

    def _add_card_to_xml(self, content: str, image_filename: str) -> bool:
        """Add card to XML file
        
        Args:
            content (str): Card description content
            image_filename (str): Name of saved image file
            
        Returns:
            bool: True if card was added successfully
        """
        try:
            self.logger.debug(f"Adding card to {self.cards_file}")
            
            # Load existing cards
            if self.cards_file.exists():
                self.logger.debug("Loading existing cards file")
                tree = ET.parse(self.cards_file)
                root = tree.getroot()
            else:
                self.logger.debug("Creating new cards file")
                root = ET.Element("cards")
                tree = ET.ElementTree(root)
            
            # Create new card element
            card = ET.SubElement(root, "card")
            
            # Generate unique ID
            card_id = f"card{len(root)}"
            self.logger.debug(f"Generated card ID: {card_id}")
            
            # Add card elements
            ET.SubElement(card, "id").text = card_id
            ET.SubElement(card, "title").text = "New Card"  # Could be extracted from content
            ET.SubElement(card, "description").text = content
            ET.SubElement(card, "image").text = image_filename
            ET.SubElement(card, "created_date").text = datetime.now().strftime("%Y-%m-%d")
            ET.SubElement(card, "active").text = "true"
            
            # Write updated XML
            self.logger.debug("Writing updated XML file")
            tree.write(self.cards_file, encoding='utf-8', xml_declaration=True)
            
            self.logger.info(f"Successfully added card {card_id} to card_content.xml")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding card to XML: {str(e)}")
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug("Full traceback:", exc_info=True)
            return False

def main():
    """Test function for card update handler"""
    import argparse
    from email.message import EmailMessage
    import mimetypes
    
    parser = argparse.ArgumentParser(description='Test card update handler')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                       help='Increase verbosity (use -v or -vv)')
    args = parser.parse_args()
    
    # Setup logging
    log_level = {
        0: logging.INFO,
        1: logging.DEBUG,
    }.get(args.verbose, logging.DEBUG)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('card_update_test')
    
    # Create test message with image
    msg = EmailMessage()
    msg.set_content('Update: "This is a test card description"')
    
    # Add test image
    test_image_path = paths.root / 'tests' / 'test_image.png'
    if not test_image_path.exists():
        logger.error(f"Test image not found: {test_image_path}")
        sys.exit(1)
        
    with open(test_image_path, 'rb') as img:
        msg.add_attachment(
            img.read(),
            maintype='image',
            subtype='png',
            filename='test_image.png'
        )
    
    # Test handler
    handler = CardUpdateHandler(logger)
    success = handler.process_update(msg)
    
    if success:
        logger.info("Test card update processed successfully")
    else:
        logger.error("Failed to process test card update")
        sys.exit(1)

if __name__ == "__main__":
    main()
