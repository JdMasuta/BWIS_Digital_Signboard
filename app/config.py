"""Configuration module for the signboard application."""
from dataclasses import dataclass

@dataclass
class SignboardConfig:
    """Configuration settings for the signboard"""
    email_address: str = "bwislovpidisplay@gmail.com"
    password: str = "ajnz ymqn hpqs fxgc"
    imap_server: str = "imap.gmail.com"
    check_interval: int = 300
    max_posts: int = 20
    template_name: str = "index.html"
    
    def validate(self) -> bool:
        """Validate configuration settings"""
        if not self.email_address or not self.password:
            return False
        if self.check_interval < 60:  # Minimum 1 minute interval
            return False
        if self.max_posts < 1:
            return False
        return True
