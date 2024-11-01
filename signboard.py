import imaplib
import email
from email.message import Message
import time
import html
import os
import logging
from datetime import datetime
from email.header import decode_header
from jinja2 import Environment, FileSystemLoader
from typing import List, Dict, Optional
import shutil
import glob

class InfoCard:
    """Class representing an information card with image"""
    def __init__(self, title: str, description: str, image_path: str):
        self.title = title
        self.description = description
        self.image_path = image_path

class SignboardConfig:
    """Configuration settings for the signboard"""
    def __init__(self, 
                 email_address: str,
                 password: str,
                 imap_server: str = "imap.gmail.com",
                 check_interval: int = 300,
                 max_posts: int = 20,
                 template_name: str = "index.html"):
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.check_interval = check_interval
        self.max_posts = max_posts
        self.template_name = template_name

class EmailSignboard:
    """Main signboard class handling email monitoring and webpage updates"""
    
    def __init__(self, config: SignboardConfig):
        self.config = config
        self.info_cards: List[InfoCard] = []
        
        # Setup paths
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.static_dir = os.path.join(self.base_dir, 'static')
        self.images_dir = os.path.join(self.base_dir, 'images')  # Changed to use base images directory
        self.html_path = os.path.join(self.base_dir, 'index.html')
        
        # Create static directory if it doesn't exist
        os.makedirs(self.static_dir, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Setup Jinja2 environment
        self.env = Environment(loader=FileSystemLoader(self.base_dir))
        self.env.globals['now'] = datetime.utcnow
        
        # Scan for existing images
        self.scan_images()

    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        self.logger = logging.getLogger('signboard')
        self.logger.setLevel(logging.INFO)
        
        # Create handlers
        console_handler = logging.StreamHandler()
        file_handler = logging.FileHandler('signboard.log')
        
        # Create formatters and add it to handlers
        log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(log_format)
        file_handler.setFormatter(log_format)
        
        # Add handlers to the logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def scan_images(self) -> None:
        """Scan the images directory for existing card images"""
        try:
            # Clear existing cards
            self.info_cards.clear()
            
            # Look for images with common formats
            image_patterns = ['*.jpg', '*.jpeg', '*.png', '*.gif']
            image_files = []
            for pattern in image_patterns:
                image_files.extend(glob.glob(os.path.join(self.images_dir, pattern)))
            
            for image_path in image_files:
                filename = os.path.basename(image_path)
                title = os.path.splitext(filename)[0].replace('_', ' ').title()
                
                # Create relative path for the image
                relative_path = os.path.join('images', filename)
                
                self.info_cards.append(InfoCard(
                    title=title,
                    description=f"Information about {title}",
                    image_path=relative_path
                ))
            
            self.logger.info(f"Found {len(self.info_cards)} images in {self.images_dir}")
            
            if not self.info_cards:
                self.logger.warning(f"No images found in {self.images_dir}")
            
        except Exception as e:
            self.logger.error(f"Error scanning images: {e}")

    def connect_to_inbox(self) -> imaplib.IMAP4_SSL:
        """Connect to email server and return IMAP connection"""
        try:
            mail = imaplib.IMAP4_SSL(self.config.imap_server)
            mail.login(self.config.email_address, self.config.password)
            mail.select('inbox')
            return mail
        except Exception as e:
            self.logger.error(f"Error connecting to email: {e}")
            raise

    def get_email_content(self, mail: imaplib.IMAP4_SSL) -> List[Dict[str, str]]:
        """Fetch and process email content"""
        try:
            _, messages = mail.search(None, 'UNSEEN')
            email_content = []
            
            for num in messages[0].split():
                _, msg = mail.fetch(num, '(RFC822)')
                email_message = email.message_from_bytes(msg[0][1])
                
                content = self._extract_email_content(email_message)
                if content:
                    email_content.append({
                        'content': content,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
            
            return email_content
        except Exception as e:
            self.logger.error(f"Error getting email content: {e}")
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

    def update_webpage(self, new_posts: List[Dict[str, str]]) -> None:
        """Update the HTML file with new content and info cards"""
        try:
            template = self.env.get_template(self.config.template_name)
            
            # Prepare card data
            card_data = [{
                'title': card.title,
                'description': card.description,
                'image': card.image_path
            } for card in self.info_cards]
            
            # Generate new HTML
            html_content = template.render(
                posts=new_posts[:self.config.max_posts],
                info_cards=card_data
            )
            
            # Write to file
            with open(self.html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            self.logger.info(f"Updated webpage with {len(new_posts)} new posts and {len(card_data)} cards")
        except Exception as e:
            self.logger.error(f"Error updating webpage: {e}")
            raise

    def run(self) -> None:
        """Main loop to check for new emails and update the webpage"""
        self.logger.info("Starting signboard service...")
        
        while True:
            try:
                mail = self.connect_to_inbox()
                new_posts = self.get_email_content(mail)
                
                if new_posts:
                    self.update_webpage(new_posts)
                
                mail.logout()
                time.sleep(self.config.check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("Shutting down signboard service...")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(60)  # Wait before retrying

def create_test_content() -> None:
    """Create test content for development"""
    config = SignboardConfig(
        email_address="test@example.com",
        password="test_password"
    )
    signboard = EmailSignboard(config)
    
    # Create test posts
    test_posts = [
        {
            'content': 'Welcome to BWIS Loveland Digital Signboard! Check out our information cards.',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            'content': 'This is a test post to demonstrate the layout. The cards on the right show our latest updates.',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    
    # Log the cards that were found
    for card in signboard.info_cards:
        print(f"Found card: {card.title} with image: {card.image_path}")
    
    signboard.update_webpage(test_posts)
    print(f"Test content created successfully with {len(signboard.info_cards)} information cards")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='BWIS Digital Signboard')
    parser.add_argument('--email', help='Email address for monitoring')
    parser.add_argument('--password', help='Email password')
    parser.add_argument('--test', action='store_true', help='Create test content')
    parser.add_argument('--interval', type=int, default=300, help='Check interval in seconds')
    
    args = parser.parse_args()
    
    if args.test:
        create_test_content()
    elif args.email and args.password:
        config = SignboardConfig(
            email_address=args.email,
            password=args.password,
            check_interval=args.interval
        )
        signboard = EmailSignboard(config)
        signboard.run()
    else:
        print("Please provide email and password or use --test flag")
