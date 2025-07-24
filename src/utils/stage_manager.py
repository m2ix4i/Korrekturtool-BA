"""
Stage management component for progress tracking
Following Single Responsibility Principle - handles only stage progression logic
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class StageManager:
    """
    Manages processing stages and stage progression
    
    Responsibility: Stage navigation, validation, and current stage tracking
    """
    
    def __init__(self, stages: List[str]):
        """
        Initialize stage manager
        
        Args:
            stages: List of stage names
        """
        self.stages = stages
        self.current_stage_index = 0
        self.current_stage = stages[0] if stages else None
        
        logger.debug(f"StageManager initialized with stages: {stages}")
    
    def get_current_stage(self) -> Optional[str]:
        """Get current stage name"""
        return self.current_stage
    
    def get_current_stage_index(self) -> int:
        """Get current stage index"""
        return self.current_stage_index
    
    def is_valid_stage(self, stage: str) -> bool:
        """Check if stage is valid"""
        return stage in self.stages
    
    def set_current_stage(self, stage: str) -> bool:
        """
        Set current stage by name
        
        Args:
            stage: Stage name to set as current
            
        Returns:
            True if stage was set successfully, False otherwise
        """
        if not self.is_valid_stage(stage):
            logger.warning(f"Attempted to set invalid stage: {stage}")
            return False
        
        self.current_stage = stage
        self.current_stage_index = self.stages.index(stage)
        return True
    
    def advance_to_next_stage(self) -> Optional[str]:
        """
        Advance to next stage
        
        Returns:
            Next stage name or None if at end
        """
        if self.current_stage_index + 1 < len(self.stages):
            self.current_stage_index += 1
            self.current_stage = self.stages[self.current_stage_index]
            return self.current_stage
        else:
            self.current_stage = None
            return None
    
    def has_next_stage(self) -> bool:
        """Check if there's a next stage"""
        return self.current_stage_index + 1 < len(self.stages)
    
    def get_completed_stage_count(self) -> int:
        """Get number of completed stages"""
        return self.current_stage_index
    
    def get_total_stage_count(self) -> int:
        """Get total number of stages"""
        return len(self.stages)