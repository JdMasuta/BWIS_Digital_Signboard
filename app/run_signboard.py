#!/usr/bin/env python3
"""Main runner script for the BWIS Digital Signboard with enhanced logging."""
import os
import sys
import time
import logging
import argparse
from datetime import datetime
from typing import Optional
import traceback

class VerboseAction(argparse.Action):
    """Custom action to handle multiple verbose flags"""
    def __call__(self, parser, namespace, values, option_string=None):
        current = getattr(namespace, self.dest, 0) or 0
        setattr(namespace, self.dest, current + 1)

def setup_logging(verbose_level: int = 0) -> logging.Logger:
    """Setup logging with configurable verbosity
    
    Args:
        verbose_level (int): 0=INFO, 1=DEBUG, 2=DEBUG with extra detail
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger('signboard')
    
    # Set base logging level based on verbosity
    if verbose_level == 0:
        logger.setLevel(logging.INFO)
        format_string = '%(asctime)s - %(levelname)s - %(message)s'
    elif verbose_level == 1:
        logger.setLevel(logging.DEBUG)
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    else:  # verbose_level >= 2
        logger.setLevel(logging.DEBUG)
        format_string = ('%(asctime)s - %(name)s - %(levelname)s - '
                        '%(filename)s:%(lineno)d - %(message)s')

    # Create handlers
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(format_string))
    
    # Create file handler with full verbosity
    file_handler = logging.FileHandler('signboard.log')
    file_format = ('%(asctime)s - %(name)s - %(levelname)s - '
                  '%(filename)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(logging.Formatter(file_format))
    file_handler.setLevel(logging.DEBUG)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def check_environment(logger: logging.Logger) -> bool:
    """Check if required directories and files exist
    
    Args:
        logger (logging.Logger): Logger instance
        
    Returns:
        bool: True if environment is valid, False otherwise
    """
    required_dirs = ['templates', 'static', 'assets', 'data']
    required_files = [
        os.path.join('data', 'card_content.xml'),
        os.path.join('data', 'updates.xml'),
        os.path.join('templates', 'index.html')
    ]
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Check directories
    for dir_name in required_dirs:
        dir_path = os.path.join(base_dir, dir_name)
        if not os.path.isdir(dir_path):
            logger.error(f"Required directory missing: {dir_name}")
            return False
        logger.debug(f"Found required directory: {dir_name}")
    
    # Check files
    for file_name in required_files:
        file_path = os.path.join(base_dir, file_name)
        if not os.path.isfile(file_path):
            logger.error(f"Required file missing: {file_name}")
            return False
        logger.debug(f"Found required file: {file_name}")
    
    return True

def create_test_content(base_dir: str, logger: logging.Logger) -> None:
    """Create test content for development
    
    Args:
        base_dir (str): Base directory path
        logger (logging.Logger): Logger instance
        
    Raises:
        Exception: If content creation fails
    """
    try:
        logger.debug("Importing required modules...")
        from cards import CardManager
        from updates import UpdateManager
        from webpage import WebpageManager
        
        logger.debug("Initializing managers...")
        card_manager = CardManager(base_dir, logger)
        update_manager = UpdateManager(base_dir, logger)
        webpage_manager = WebpageManager(base_dir, logger)
        
        logger.debug("Loading cards from XML...")
        cards = card_manager.load_cards()
        logger.debug(f"Loaded {len(cards)} cards")
        
        logger.debug("Loading updates from XML...")
        updates = update_manager.load_updates()
        logger.debug(f"Loaded {len(updates)} updates")
        
        logger.debug("Preparing card data for webpage...")
        logger.debug("Building image paths from asset directory...")
        card_data = [{
            'title': card.title,
            'description': card.description,
            'image': os.path.join('/assets/cards', card.image_path)  # Prepend web-accessible path
        } for card in cards]
        logger.debug(f"Processed {len(card_data)} cards with image paths")

        # Log individual card paths in very verbose mode
        if logger.level <= logging.DEBUG:
            for i, card in enumerate(card_data):
                logger.debug(f"Card {i+1}: {card['title']} -> {card['image']}")
        
        logger.debug("Updating webpage...")
        webpage_manager.update_webpage(updates, card_data)
        logger.info("Test content created successfully")
        
    except Exception as e:
        logger.error(f"Error creating test content: {str(e)}")
        if logger.level <= logging.DEBUG:
            logger.debug("Traceback:", exc_info=True)
        raise

def main():
    """Main entry point with enhanced error handling and logging"""
    parser = argparse.ArgumentParser(
        description='BWIS Digital Signboard',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Verbose mode details:
  -v    Show debug logs and basic operational information
  -vv   Show detailed debug logs including file locations and line numbers
        """
    )
    parser.add_argument('--test', action='store_true', 
                       help='Create test content')
    parser.add_argument('-v', dest='verbose', action=VerboseAction, nargs=0,
                       help='Increase verbosity level (can be used multiple times)')
    
    args = parser.parse_args()
    verbose_level = getattr(args, 'verbose', 0) or 0
    
    # Setup logging
    logger = setup_logging(verbose_level)
    logger.debug(f"Verbosity level: {verbose_level}")
    
    try:
        # Get base directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logger.debug(f"Base directory: {base_dir}")
        
        # Check environment
        logger.debug("Checking environment...")
        if not check_environment(logger):
            logger.error("Environment check failed")
            sys.exit(1)
        
        # Execute requested operation
        if args.test:
            logger.info("Creating test content...")
            create_test_content(base_dir, logger)
        else:
            logger.error("Please use --test flag for now")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        if verbose_level >= 1:
            logger.debug("Full traceback:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
