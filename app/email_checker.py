"""Email checking module for the signboard application.

This module handles checking for and processing email updates for the signboard.
It coordinates between text updates and card updates, delegating to specialized
handlers for each type of update while managing the email connection and error
handling at a high level.

Typical usage:
    checker = EmailChecker(config, logger)
    checker.check_for_updates()
"""

import os
import imaplib
import email
from email.message import Message
import logging
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
import socket
import ssl
from pathlib import Path

from config import SignboardConfig
from text_update import TextUpdateHandler
from card_update import CardUpdateHandler
from project_paths import paths

class EmailConnectionError(Exception):
    """Raised when there's an error connecting to the email server."""
    pass

class EmailAuthenticationError(Exception):
    """Raised when there's an error authenticating with the email server."""
    pass

class EmailChecker:
    """Handles checking and processing emails for signboard updates.
    
    This class manages the email connection and coordinates processing of
    different types of updates (text and card) using specialized handlers.
    
    Attributes:
        config (SignboardConfig): Application configuration
        logger (logging.Logger): Logger instance
        text_handler (TextUpdateHandler): Handles text update processing
        card_handler (CardUpdateHandler): Handles card update processing
    """
    
    # Constants for email operations
    SOCKET_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    
    def __init__(self, config: SignboardConfig, logger: Optional[logging.Logger] = None):
        """Initialize email checker with configuration.
        
        Args:
            config (SignboardConfig): Application configuration
            logger (Optional[logging.Logger]): Logger instance
            
        Raises:
            ValueError: If configuration is invalid
        """
        if not config.validate():
            raise ValueError("Invalid configuration provided")
            
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize update handlers
        self.text_handler = TextUpdateHandler(self.logger)
        self.card_handler = CardUpdateHandler(self.logger)
        
        # Set socket timeout for email operations
        socket.setdefaulttimeout(self.SOCKET_TIMEOUT)

    def check_for_updates(self) -> bool:
        """Check email for updates and process them.
        
        Connects to the email server, checks for new messages with specific
        subject lines, and processes them appropriately based on type.
        
        Returns:
            bool: True if all operations completed successfully
        """
        mail = None
        try:
            self.logger.info("Starting email check for updates...")
            
            # Connect and authenticate
            mail = self._connect_to_mail_server()
            
            # Search for relevant messages
            messages = self._search_for_update_messages(mail)
            
            if not messages:
                self.logger.info("No new updates found")
                return True
                
            # Process messages
            success = self._process_messages(mail, messages)
            
            self.logger.info("Email check completed successfully")
            return success
            
        except EmailConnectionError as e:
            self.logger.error(f"Failed to connect to email server: {str(e)}")
            return False
        except EmailAuthenticationError as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during email check: {str(e)}")
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug("Full traceback:", exc_info=True)
            return False
        finally:
            if mail:
                try:
                    mail.logout()
                    self.logger.debug("Logged out from email server")
                except Exception as e:
                    self.logger.warning(f"Error during logout: {str(e)}")

    def _connect_to_mail_server(self) -> imaplib.IMAP4_SSL:
        """Connect to the email server with retry logic.
        
        Returns:
            imaplib.IMAP4_SSL: Connected mail server instance
            
        Raises:
            EmailConnectionError: If connection fails after retries
            EmailAuthenticationError: If authentication fails
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                self.logger.debug(f"Attempting to connect to {self.config.imap_server} (attempt {attempt + 1})")
                mail = imaplib.IMAP4_SSL(self.config.imap_server)
                
                try:
                    mail.login(self.config.email_address, self.config.password)
                    self.logger.debug("Successfully authenticated with email server")
                    return mail
                except imaplib.IMAP4.error as e:
                    raise EmailAuthenticationError(f"Authentication failed: {str(e)}")
                    
            except (socket.gaierror, socket.timeout, ssl.SSLError) as e:
                self.logger.warning(f"Connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                    continue
                raise EmailConnectionError(f"Failed to connect after {self.MAX_RETRIES} attempts")

    def _search_for_update_messages(self, mail: imaplib.IMAP4_SSL) -> List[bytes]:
        """Search for unread update messages.
        
        Args:
            mail (imaplib.IMAP4_SSL): Connected mail server instance
            
        Returns:
            List[bytes]: List of message IDs
            
        Raises:
            Exception: If mailbox selection or search fails
        """
        self.logger.debug("Selecting inbox...")
        mail.select('inbox')
        
        # Search for unread messages with specific subjects
        self.logger.debug("Searching for update messages...")
        _, messages = mail.search(None, 'UNSEEN', '(OR SUBJECT "Text Update" SUBJECT "Card Update")')
        
        message_ids = messages[0].split()
        self.logger.debug(f"Found {len(message_ids)} unread update messages")
        
        return message_ids

    def _process_messages(self, mail: imaplib.IMAP4_SSL, message_ids: List[bytes]) -> bool:
        """Process all found update messages.
        
        Args:
            mail (imaplib.IMAP4_SSL): Connected mail server instance
            message_ids (List[bytes]): List of message IDs to process
            
        Returns:
            bool: True if all messages processed successfully
        """
        success = True
        processed_count = 0
        
        for msg_id in message_ids:
            try:
                # Fetch message
                self.logger.debug(f"Fetching message {msg_id}")
                _, msg_data = mail.fetch(msg_id, '(RFC822)')
                email_body = msg_data[0][1]
                message = email.message_from_bytes(email_body)
                
                # Process based on subject
                subject = message.get('subject', '').strip()
                self.logger.debug(f"Processing message with subject: {subject}")
                
                if subject == 'Text Update':
                    if not self.text_handler.process_update(message):
                        self.logger.error(f"Failed to process text update from message {msg_id}")
                        success = False
                elif subject == 'Card Update':
                    if not self.card_handler.process_update(message):
                        self.logger.error(f"Failed to process card update from message {msg_id}")
                        success = False
                else:
                    self.logger.warning(f"Unknown update type for message {msg_id}: {subject}")
                    continue
                    
                processed_count += 1
                
            except Exception as e:
                self.logger.error(f"Error processing message {msg_id}: {str(e)}")
                if self.logger.isEnabledFor(logging.DEBUG):
                    self.logger.debug("Full traceback:", exc_info=True)
                success = False
                
        self.logger.info(f"Processed {processed_count} of {len(message_ids)} messages successfully")
        return success

def main():
    """Command-line interface for email checker."""
    import argparse
    import time
    
    parser = argparse.ArgumentParser(description='Check for signboard email updates')
    parser.add_argument('--continuous', action='store_true',
                      help='Run continuously, checking at configured intervals')
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
    logger = logging.getLogger('email_checker')
    
    # Create config and checker
    config = SignboardConfig()
    checker = EmailChecker(config, logger)
    
    try:
        if args.continuous:
            logger.info(f"Starting continuous email checking (interval: {config.check_interval}s)")
            while True:
                checker.check_for_updates()
                time.sleep(config.check_interval)
        else:
            checker.check_for_updates()
            
    except KeyboardInterrupt:
        logger.info("Email checking stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Full traceback:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
