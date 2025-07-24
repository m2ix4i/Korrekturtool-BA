"""
Directory management utilities
"""

from pathlib import Path
from typing import List


class DirectoryManager:
    """Handles directory creation and management"""
    
    @staticmethod
    def ensure_directories_exist(folders: List[str]) -> None:
        """
        Create necessary directories if they don't exist
        
        Args:
            folders: List of folder paths to create
        """
        for folder in folders:
            Path(folder).mkdir(parents=True, exist_ok=True)