"""
Base validator class for file validation
"""

from abc import ABC, abstractmethod
from typing import Tuple


class BaseValidator(ABC):
    """Abstract base class for file validators"""
    
    @abstractmethod
    def validate(self, *args, **kwargs) -> Tuple[bool, str]:
        """
        Validate input and return result
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass