"""Card management module for the signboard application."""
from dataclasses import dataclass
from datetime import datetime
import xml.etree.ElementTree as ET
import os
from typing import List, Optional
import logging

@dataclass
class InfoCard:
    """Class representing an information card with image"""
    id: str
    title: str
    description: str
    image_path: str
    created_date: datetime
    active: bool

class CardManager:
    """Manages card content and operations"""
    def __init__(self, base_dir: str, logger: Optional[logging.Logger] = None):
        self.base_dir = base_dir
        self.cards_dir = os.path.join(base_dir, 'assets', 'cards')
        self.cards: List[InfoCard] = []
        self.logger = logger or logging.getLogger(__name__)

    def load_cards(self) -> List[InfoCard]:
        """Load cards from XML configuration"""
        try:
            tree = ET.parse(os.path.join(self.base_dir, 'data', 'card_content.xml'))
            root = tree.getroot()
            
            cards = []
            for card_elem in root.findall('card'):
                if card_elem.find('active').text.lower() == 'true':
                    card = InfoCard(
                        id=card_elem.find('id').text,
                        title=card_elem.find('title').text,
                        description=card_elem.find('description').text,
                        image_path=card_elem.find('image').text,
                        created_date=datetime.strptime(card_elem.find('created_date').text, '%Y-%m-%d'),
                        active=True
                    )
                    cards.append(card)
            
            self.cards = cards
            self.logger.info(f"Loaded {len(cards)} cards from XML")
            return cards
            
        except Exception as e:
            self.logger.error(f"Error loading card content: {e}")
            return []

    def validate_card_images(self) -> bool:
        """Verify all card images exist"""
        for card in self.cards:
            image_path = os.path.join(self.cards_dir, card.image_path)
            if not os.path.exists(image_path):
                self.logger.error(f"Missing image for card {card.id}: {image_path}")
                return False
        return True
