"""Update management module for the signboard application."""
import xml.etree.ElementTree as ET
import os
import logging
from typing import List, Dict, Optional
import imaplib
import email
from email.message import Message
import html
from datetime import datetime

class UpdateManager:
    """Manages content updates from XML and email"""
    def __init__(self, base_dir: str, logger: Optional[logging.Logger] = None):
        self.base_dir = base_dir
        self.logger = logger or logging.getLogger(__name__)

    def load_updates(self) -> List[Dict[str, str]]:
        """Load updates from XML file"""
        try:
            tree = ET.parse(os.path.join(self.base_dir, 'data', 'updates.xml'))
            root = tree.getroot()
            
            updates = []
            for update_elem in root.findall('update'):
                if update_elem.find('active').text.lower() == 'true':
                    updates.append({
                        'content': update_elem.find('content').text,
                        'timestamp': update_elem.find('timestamp').text
                    })
            
            return updates
            
        except Exception as e:
            self.logger.error(f"Error loading updates: {e}")
            return []

    def get_email_updates(self, config) -> List[Dict[str, str]]:
        """Fetch updates from email"""
        try:
            mail = imaplib.IMAP4_SSL(config.imap_server)
            mail.login(config.email_address, config.password)
            mail.select('inbox')
            
            _, messages = mail.search(None, 'UNSEEN')
            updates = []
            
            for num in messages[0].split():
                _, msg = mail.fetch(num, '(RFC822)')
                email_message = email.message_from_bytes(msg[0][1])
                content = self._extract_email_content(email_message)
                
                if content:
                    updates.append({
                        'content': content,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
            
            mail.logout()
            return updates
            
        except Exception as e:
            self.logger.error(f"Error getting email updates: {e}")
            return []

    def _extract_email_content(self, email_message: Message) -> Optional[str]:
        """Extract content from email message"""
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        return html.escape(part.get_payload(decode=True).decode())
            else:
                return html.escape(email_message.get_payload(decode=True).decode())
        except Exception as e:
            self.logger.error(f"Error extracting email content: {e}")
            return None
