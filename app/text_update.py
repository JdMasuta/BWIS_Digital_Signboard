"""Text update handler for signboard email updates."""
import xml.etree.ElementTree as ET
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
import re
from email.message import Message
from project_paths import paths

class TextUpdateHandler:
    """Handles processing and storage of text updates"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize text update handler
        
        Args:
            logger (Optional[logging.Logger]): Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.updates_file = paths.data / 'updates.xml'

    def process_update(self, message: Message) -> bool:
        """Process a text update from email
        
        Args:
            message (Message): Email message containing update
            
        Returns:
            bool: True if update was processed successfully
        """
        try:
            self.logger.debug("Processing text update email...")
            
            # Extract update content
            content = self._extract_update_content(message)
            if not content:
                self.logger.warning("No valid update content found in text update email")
                return False
                
            self.logger.debug(f"Extracted update content: {content}")
            
            # Add update to XML file
            return self._add_update_to_xml(content)
            
        except Exception as e:
            self.logger.error(f"Error processing text update: {str(e)}")
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
        self.logger.debug("Extracting update content from email...")
        
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
                self.logger.debug(f"Found update text: {update_text}")
                return update_text
            else:
                self.logger.warning("No update pattern found in email content")
                return None
                
        except Exception as e:
            self.logger.error(f"Error extracting update content: {str(e)}")
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug("Full traceback:", exc_info=True)
            return None

    def _add_update_to_xml(self, content: str) -> bool:
        """Add update to XML file
        
        Args:
            content (str): Update content to add
            
        Returns:
            bool: True if update was added successfully
        """
        try:
            self.logger.debug(f"Adding update to {self.updates_file}")
            
            # Load existing updates
            if self.updates_file.exists():
                self.logger.debug("Loading existing updates file")
                tree = ET.parse(self.updates_file)
                root = tree.getroot()
            else:
                self.logger.debug("Creating new updates file")
                root = ET.Element("updates")
                tree = ET.ElementTree(root)
            
            # Create new update element
            update = ET.SubElement(root, "update")
            
            # Generate unique ID
            update_id = f"update{len(root)}"
            self.logger.debug(f"Generated update ID: {update_id}")
            
            # Add update elements
            ET.SubElement(update, "id").text = update_id
            ET.SubElement(update, "content").text = content
            ET.SubElement(update, "timestamp").text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ET.SubElement(update, "priority").text = "normal"
            ET.SubElement(update, "active").text = "true"
            
            # Write updated XML
            self.logger.debug("Writing updated XML file")
            tree.write(self.updates_file, encoding='utf-8', xml_declaration=True)
            
            self.logger.info(f"Successfully added update {update_id} to updates.xml")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding update to XML: {str(e)}")
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug("Full traceback:", exc_info=True)
            return False

def main():
    """Test function for text update handler"""
    import argparse
    from email.message import EmailMessage
    
    parser = argparse.ArgumentParser(description='Test text update handler')
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
    logger = logging.getLogger('text_update_test')
    
    # Create test message
    msg = EmailMessage()
    msg.set_content('Update: "This is a test update message"')
    
    # Test handler
    handler = TextUpdateHandler(logger)
    success = handler.process_update(msg)
    
    if success:
        logger.info("Test update processed successfully")
    else:
        logger.error("Failed to process test update")
        sys.exit(1)

if __name__ == "__main__":
    main()
