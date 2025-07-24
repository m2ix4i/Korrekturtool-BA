"""
Path management utilities
"""

from pathlib import Path


class PathHelper:
    """Centralized path management to avoid Law of Demeter violations"""
    
    @staticmethod
    def get_static_directory() -> Path:
        """
        Get static files directory with absolute path
        
        Returns:
            Path object pointing to static directory
        """
        return Path(__file__).parent.parent / 'static'
    
    @staticmethod
    def get_project_root() -> Path:
        """
        Get project root directory
        
        Returns:
            Path object pointing to project root
        """
        return Path(__file__).parent.parent.parent