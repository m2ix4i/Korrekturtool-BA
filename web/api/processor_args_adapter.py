"""
Processor arguments adapter following Adapter pattern
Handles ONLY adapting request data to processor CLI interface
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ProcessorArgsAdapter:
    """
    Adapter for processor CLI interface following Adapter pattern
    
    ONLY responsible for:
    - Converting request data to processor arguments format
    - Providing consistent interface for different processors
    """
    
    def __init__(self, input_file: str, output_file: str, categories: List[str]):
        self.input_file = input_file
        self.output_file = output_file
        self.categories = categories
        self.verbose = False
    
    @classmethod
    def from_request_data(cls, request_data: Dict[str, Any], 
                         input_file: str, output_file: str) -> 'ProcessorArgsAdapter':
        """Create adapter from request data"""
        return cls(
            input_file=input_file,
            output_file=output_file,
            categories=request_data['categories']
        )