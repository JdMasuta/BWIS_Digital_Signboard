#!/usr/bin/env python3
"""Main runner script for the BWIS Digital Signboard."""
import os
import sys
import time
import logging
import argparse
from datetime import datetime

# Add the parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Now we can import our local modules
from config import SignboardConfig
from cards import CardManager
from updates import UpdateManager
from webpage import WebpageManager

def setup_logging() -> logging.Logger:
    """Setup logging configuration"""
    logger = logging.getLogger('signboard')
    logger.setLevel(logging.INFO)
    
    # Create handlers
    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler('signboard.log')
    
    # Create formatters and add it to handlers
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(log_format)
    file_handler.setFormatter(log_format)
    
    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def create_test_content(base_dir: str, logger: logging.Logger) -> None:
    """Create test content for development"""
    try:
        card_manager = CardManager(base_dir, logger)
        update_manager = UpdateManager(base_dir, logger)
        webpage_manager = WebpageManager(base_dir, logger)
        
        # Load cards and updates
        cards = card_manager.load_cards()
        updates = update_manager.load_updates()
        
        # Prepare card data for webpage
        card_data = [{
            'title': card.title,
            'description': card.description,
            'image': card.image_path
        } for card in cards]
        
        # Update webpage
        webpage_manager.update_webpage(updates, card_data)
        logger.info("Test content created successfully")
        
    except Exception as e:
        logger.error(f"Error creating test content: {e}")
        raise

def run_signboard(config: SignboardConfig, logger: logging.Logger) -> None:
    """Main function to run the signboard"""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        card_manager = CardManager(base_dir, logger)
        update_manager = UpdateManager(base_dir, logger)
        webpage_manager = WebpageManager(base_dir, logger)
        
        logger.info("Starting signboard service...")
        
        while True:
            try:
                # Load cards
                cards = card_manager.load_cards()
                
                # Validate card images
                if not card_manager.validate_card_images():
                    logger.error("Missing card images, skipping update")
                    continue
                
                # Get updates from email
                updates = update_manager.get_email_updates(config)
                
                # Prepare card data
                card_data = [{
                    'title': card.title,
                    'description': card.description,
                    'image': card.image_path
                } for card in cards]
                
                # Update webpage
                webpage_manager.update_webpage(updates, card_data, 
                                            config.template_name, 
                                            config.max_posts)
                
                time.sleep(config.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Shutting down signboard service...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)  # Wait before retrying
                
    except Exception as e:
        logger.error(f"Error starting signboard: {e}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='BWIS Digital Signboard')
    parser.add_argument('--email', help='Email address for monitoring')
    parser.add_argument('--password', help='Email password')
    parser.add_argument('--test', action='store_true', help='Create test content')
    parser.add_argument('--interval', type=int, default=300, help='Check interval in seconds')
    
    args = parser.parse_args()
    logger = setup_logging()
    
    try:
        if args.test:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            create_test_content(base_dir, logger)
        elif args.email and args.password:
            config = SignboardConfig(
                email_address=args.email,
                password=args.password,
                check_interval=args.interval
            )
            
            if not config.validate():
                logger.error("Invalid configuration")
                exit(1)
                
            run_signboard(config, logger)
        else:
            print("Please provide email and password or use --test flag")
            
    except Exception as e:
        logger.error(f"Application error: {e}")
        exit(1)
