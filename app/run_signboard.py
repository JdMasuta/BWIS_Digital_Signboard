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
from pathlib import Path
from project_paths import paths

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
    log_file = paths.root / 'signboard.log'
    file_handler = logging.FileHandler(log_file)
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
    try:
        # Ensure required directories exist
        paths.ensure_directories()
        logger.debug("Required directories exist or were created")
        
        # Check required files
        required_files = [
            paths.data / 'card_content.xml',
            paths.data / 'updates.xml',
            paths.templates / 'index.html'
        ]
        
        for file_path in required_files:
            if not file_path.is_file():
                logger.error(f"Required file missing: {file_path}")
                return False
            logger.debug(f"Found required file: {file_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking environment: {str(e)}")
        return False

def update_webpage_content(logger: logging.Logger) -> None:
    """Update webpage with current content from cards and updates
    
    Args:
        logger (logging.Logger): Logger instance
        
    Raises:
        Exception: If update process fails
    """
    try:
        logger.debug("Importing required modules...")
        from cards import CardManager
        from updates import UpdateManager
        from webpage import WebpageManager
        
        # Initialize managers
        logger.debug("Initializing content managers...")
        card_manager = CardManager(paths.root, logger)
        update_manager = UpdateManager(paths.root, logger)
        webpage_manager = WebpageManager(paths.root, logger)
        
        # Load current content
        logger.debug("Loading content...")
        cards = card_manager.load_cards()
        updates = update_manager.load_updates()
        
        logger.debug(f"Loaded {len(cards)} cards and {len(updates)} updates")
        
        # Prepare card data for webpage
        card_data = [{
            'title': card.title,
            'description': card.description,
            'image': os.path.join('/assets/cards', card.image_path)
        } for card in cards]
        
        # Update webpage
        logger.debug("Updating webpage...")
        webpage_manager.update_webpage(updates, card_data)
        logger.info("Webpage updated successfully")
        
    except Exception as e:
        logger.error(f"Error updating webpage content: {str(e)}")
        raise

def check_email_updates(logger: logging.Logger) -> None:
    """Check for email updates and process them
    
    Args:
        logger (logging.Logger): Logger instance
        
    Raises:
        Exception: If update process fails
    """
    try:
        logger.debug("Importing required modules...")
        from email_checker import EmailChecker
        from config import SignboardConfig
        
        # Initialize and run email checker
        logger.info("Checking for email updates...")
        config = SignboardConfig()
        if not config.validate():
            raise ValueError("Invalid configuration")
            
        email_checker = EmailChecker(config, logger)
        email_checker.check_for_updates()
        
        # Update webpage with any new content
        update_webpage_content(logger)
        
    except Exception as e:
        logger.error(f"Error checking email updates: {str(e)}")
        raise

def main():
    """Main entry point with enhanced error handling and logging"""
    parser = argparse.ArgumentParser(
        description='BWIS Digital Signboard',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Operating modes:
  Default:    Check for email updates and update the webpage
  Test:       Create test content and update the webpage

Verbose mode details:
  -v         Show debug logs and basic operational information
  -vv        Show detailed debug logs including file locations and line numbers
        """
    )
    parser.add_argument('--test', action='store_true', 
                       help='Create test content instead of checking emails')
    parser.add_argument('--clean-test', action='store_true',
                       help='Remove test content')
    parser.add_argument('-v', dest='verbose', action=VerboseAction, nargs=0,
                       help='Increase verbosity level (can be used multiple times)')
    
    args = parser.parse_args()
    verbose_level = getattr(args, 'verbose', 0) or 0
    
    # Setup logging
    logger = setup_logging(verbose_level)
    logger.debug(f"Verbosity level: {verbose_level}")
    
    try:
        # Check environment
        logger.debug("Checking environment...")
        if not check_environment(logger):
            logger.error("Environment check failed")
            sys.exit(1)
        
        # Handle test content cleanup if requested
        if args.clean_test:
            logger.info("Cleaning up test content...")
            from test_content import TestContentManager
            TestContentManager.cleanup_test_content()
            logger.info("Test content cleanup complete")
            sys.exit(0)
        
        # Execute requested operation
        if args.test:
            logger.info("Creating test content...")
            from test_content import TestContentManager
            test_manager = TestContentManager(logger)
            test_manager.create_test_content()
        else:
            logger.info("Running email update check...")
            check_email_updates(logger)
            
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
