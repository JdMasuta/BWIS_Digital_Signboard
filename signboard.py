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

class SignboardConfig:
    """Configuration settings for the signboard"""
    def __init__(self, 
                 email_address: str,
                 password: str,
                 imap_server: str = "imap.gmail.com",
                 check_interval: int = 300,
                 max_posts: int = 20,
                 template_name: str = "signboard_template.html"):
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.check_interval = check_interval
        self.max_posts = max_posts
        self.template_name = template_name

class InfoCard:
    """Represents a card in the slideshow"""
    def __init__(self, title: str, description: str, image_path: str):
        self.title = title
        self.description = description
        self.image_path = image_path

class EmailSignboard:
    """Main signboard class handling email monitoring and webpage updates"""
    
    def __init__(self, config: SignboardConfig):
        self.config = config
        self.info_cards: List[InfoCard] = []
        
        # Setup paths
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.static_dir = os.path.join(self.base_dir, 'static')
        self.images_dir = os.path.join(self.static_dir, 'images')
        self.html_path = os.path.join(self.base_dir, 'signboard.html')
        
        # Ensure required directories exist
        self._setup_directories()
        
        # Setup logging
        self._setup_logging()
        
        # Setup Jinja2 environment
        self.env = Environment(loader=FileSystemLoader(self.base_dir))
        self.env.globals['now'] = datetime.utcnow
        
        # Scan for existing images
        self.scan_images()

    def _setup_directories(self) -> None:
        """Create necessary directories if they don't exist"""
        os.makedirs(self.static_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)

    def _setup_logging(self) -> None:
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('signboard.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def scan_images(self) -> None:
        """Scan the images directory and create cards for existing images"""
        self.info_cards.clear()
        if os.path.exists(self.images_dir):
            for image_file in os.listdir(self.images_dir):
                if image_file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    image_path = f'/static/images/{image_file}'
                    title = os.path.splitext(image_file)[0].replace('-', ' ').title()
                    self.add_info_card(title, f"Image: {title}", image_path)

    def add_info_card(self, title: str, description: str, image_path: str) -> None:
        """Add a new info card to the rotation"""
        self.info_cards.append(InfoCard(title, description, image_path))
        self.logger.info(f"Added info card: {title}")

    def connect_to_inbox(self) -> imaplib.IMAP4_SSL:
        """Connect to the IMAP server and return the connection"""
        try:
            mail = imaplib.IMAP4_SSL(self.config.imap_server)
            mail.login(self.config.email_address, self.config.password)
            return mail
        except Exception as e:
            self.logger.error(f"Failed to connect to email server: {e}")
            raise

    def process_email_content(self, email_message: Message) -> str:
        """Extract and process content from email message"""
        content = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    content = part.get_payload(decode=True).decode()
                    break
        else:
            content = email_message.get_payload(decode=True).decode()
        
        return html.escape(content.strip())

    def get_email_content(self, mail: imaplib.IMAP4_SSL) -> List[Dict[str, str]]:
        """Fetch and process new emails"""
        posts = []
        try:
            mail.select('inbox')
            _, messages = mail.search(None, 'UNSEEN')
            
            if messages[0]:  # Check if there are any messages
                for num in messages[0].split():
                    try:
                        _, msg_data = mail.fetch(num, '(RFC822)')
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)
                        
                        content = self.process_email_content(email_message)
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        posts.append({
                            'content': content,
                            'timestamp': timestamp
                        })
                        self.logger.info(f"Processed new email at {timestamp}")
                    except Exception as e:
                        self.logger.error(f"Error processing email: {e}")
                        continue
                    
        except Exception as e:
            self.logger.error(f"Error accessing inbox: {e}")
            
        return posts

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
                
            self.logger.info(f"Updated webpage with {len(new_posts)} new posts")
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
            'content': 'Welcome to BWIS Loveland Digital Signboard!',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            'content': 'This is a test post to demonstrate the layout.',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    
    signboard.update_webpage(test_posts)
    print("Test content created successfully")

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
