"""
Progress calculation component for progress tracking
Following Single Responsibility Principle - handles only progress calculations
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class ProgressCalculator:
    """
    Calculates progress percentages based on stage weights and completion
    
    Responsibility: Progress calculations and percentage computations
    """
    
    def __init__(self, stages: List[str], weights: Dict[str, float]):
        """
        Initialize progress calculator
        
        Args:
            stages: List of stage names
            weights: Dictionary mapping stage names to weights (should sum to 1.0)
        """
        self.stages = stages
        self.stage_weights = weights
        
        # Validate weights
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.01:  # Allow small floating point errors
            logger.warning(f"Stage weights sum to {total_weight}, not 1.0")
        
        logger.debug(f"ProgressCalculator initialized with weights: {weights}")
    
    def calculate_overall_progress(self, completed_stage_count: int, current_stage_progress: int) -> int:
        """
        Calculate overall progress percentage
        
        Args:
            completed_stage_count: Number of completed stages
            current_stage_progress: Progress within current stage (0-100)
            
        Returns:
            Overall progress percentage (0-100)
        """
        # Weight of completed stages
        completed_weight = self._calculate_completed_weight(completed_stage_count)
        
        # Weight contribution from current stage
        current_stage_contribution = self._calculate_current_stage_contribution(
            completed_stage_count, current_stage_progress
        )
        
        total_progress = completed_weight + current_stage_contribution
        return int(total_progress * 100)
    
    def _calculate_completed_weight(self, completed_stage_count: int) -> float:
        """Calculate total weight of completed stages"""
        if completed_stage_count <= 0:
            return 0.0
        
        completed_stages = self.stages[:completed_stage_count]
        return sum(self.stage_weights.get(stage, 0) for stage in completed_stages)
    
    def _calculate_current_stage_contribution(self, completed_stage_count: int, stage_progress: int) -> float:
        """Calculate weight contribution from current stage progress"""
        if completed_stage_count >= len(self.stages):
            return 0.0
        
        current_stage = self.stages[completed_stage_count]
        current_stage_weight = self.stage_weights.get(current_stage, 0)
        
        # Normalize stage progress to 0-1 range
        normalized_progress = max(0, min(100, stage_progress)) / 100.0
        
        return current_stage_weight * normalized_progress
    
    def get_stage_weight(self, stage: str) -> float:
        """Get weight for specific stage"""
        return self.stage_weights.get(stage, 0.0)
    
    def normalize_progress(self, progress: int) -> int:
        """Normalize progress to 0-100 range"""
        return max(0, min(100, progress))