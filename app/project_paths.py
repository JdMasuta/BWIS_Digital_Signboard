"""Project path resolution without configuration."""
from pathlib import Path
import sys
from typing import Optional

class ProjectPaths:
    """Handles project path resolution relative to project root."""
    _instance = None
    _root = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._find_project_root()
        return cls._instance

    def _find_project_root(self) -> None:
        """Find project root by looking for key project files/directories."""
        current = Path(__file__).resolve().parent.parent
        
        # Look for key project markers going up the directory tree
        while current != current.parent:
            if any((
                (current / 'app').is_dir(),
                (current / 'requirements.txt').exists(),
                (current / 'README.md').exists()
            )):
                self._root = current
                break
            current = current.parent
        
        if self._root is None:
            # If no root found, use the parent of the current file's directory
            self._root = Path(__file__).resolve().parent.parent

        # Add project root to Python path if not already there
        if str(self._root) not in sys.path:
            sys.path.insert(0, str(self._root))

    @property
    def root(self) -> Path:
        """Get project root directory."""
        return self._root

    @property
    def static(self) -> Path:
        """Get static files directory."""
        return self._root / 'static'

    @property
    def assets(self) -> Path:
        """Get assets directory."""
        return self._root / 'assets'

    @property
    def data(self) -> Path:
        """Get data directory."""
        return self._root / 'data'

    @property
    def templates(self) -> Path:
        """Get templates directory."""
        return self._root / 'templates'

    @property
    def cards(self) -> Path:
        """Get cards directory."""
        return self.assets / 'cards'

    def get_static_url(self, path: str) -> str:
        """Get URL for static files."""
        return f'/static/{path}'

    def get_asset_url(self, path: str) -> str:
        """Get URL for assets."""
        return f'/assets/{path}'

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        for path in [self.static, self.assets, self.data, self.templates, self.cards]:
            path.mkdir(parents=True, exist_ok=True)

# Create singleton instance
paths = ProjectPaths()
