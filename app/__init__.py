"""
BWIS Digital Signboard
A modular digital signboard system that displays information cards and updates.
"""

from .config import SignboardConfig
from .cards import InfoCard
from .signboard import EmailSignboard

__version__ = '1.0.0'
__all__ = ['SignboardConfig', 'InfoCard', 'EmailSignboard']
