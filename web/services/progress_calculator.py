"""
Progress calculation following Single Responsibility Principle
Handles ONLY progress calculations and time estimations
"""

import logging
from typing import Optional
from datetime import datetime
from .job_state_manager import JobInfo

logger = logging.getLogger(__name__)


class ProgressCalculator:
    """
    Handles progress calculations following Single Responsibility Principle
    
    ONLY responsible for:
    - Calculating estimated remaining time
    - Formatting time estimates for display
    - Progress percentage calculations
    """
    
    def __init__(self):
        logger.info("ProgressCalculator initialized")
    
    def calculate_estimated_remaining(self, job_info: JobInfo) -> Optional[str]:
        """Calculate estimated remaining time based on current progress"""
        try:
            current_progress = job_info['overall_progress']
            
            if current_progress <= 0:
                return None
            
            elapsed = self._calculate_elapsed_seconds(job_info['start_time'])
            
            if current_progress >= 100:
                return "0 seconds"
            
            estimated_total = elapsed * (100 / current_progress)
            remaining = estimated_total - elapsed
            
            return self._format_time_remaining(remaining)
            
        except Exception as e:
            logger.error(f"Error calculating remaining time: {str(e)}")
            return None
    
    def _calculate_elapsed_seconds(self, start_time: datetime) -> float:
        """Calculate elapsed time in seconds"""
        return (datetime.utcnow() - start_time).total_seconds()
    
    def _format_time_remaining(self, remaining_seconds: float) -> str:
        """Format remaining time as human-readable string"""
        if remaining_seconds <= 0:
            return "0 seconds"
        elif remaining_seconds < 60:
            return f"{int(remaining_seconds)} seconds"
        elif remaining_seconds < 3600:
            minutes = int(remaining_seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        else:
            hours = int(remaining_seconds / 3600)
            minutes = int((remaining_seconds % 3600) / 60)
            return f"{hours}h {minutes}m"