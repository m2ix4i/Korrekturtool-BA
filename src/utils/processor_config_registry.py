"""
Processor configuration registry using Strategy pattern
Following Open/Closed Principle - allows adding new processor types without modifying existing code
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProcessorConfig:
    """Configuration for a processor type"""
    stages: List[str]
    weights: Dict[str, float]
    estimated_duration_per_stage: int = 30  # seconds


class ProcessorConfigRegistry:
    """
    Registry for processor configurations using Strategy pattern
    
    Allows registering new processor types without modifying existing code
    """
    
    _configs: Dict[str, ProcessorConfig] = {}
    
    @classmethod
    def register(cls, processor_type: str, stages: List[str], weights: Dict[str, float], 
                 estimated_duration_per_stage: int = 30) -> None:
        """
        Register a new processor configuration
        
        Args:
            processor_type: Unique identifier for processor type
            stages: List of processing stages
            weights: Dictionary mapping stage names to weights (should sum to 1.0)
            estimated_duration_per_stage: Estimated seconds per stage
        """
        # Validate weights
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Stage weights for {processor_type} sum to {total_weight}, not 1.0")
        
        # Validate stages match weights
        if set(stages) != set(weights.keys()):
            raise ValueError(f"Stages and weights keys don't match for {processor_type}")
        
        config = ProcessorConfig(
            stages=stages,
            weights=weights,
            estimated_duration_per_stage=estimated_duration_per_stage
        )
        
        cls._configs[processor_type] = config
        logger.info(f"Registered processor config: {processor_type}")
    
    @classmethod
    def get_config(cls, processor_type: str) -> Optional[ProcessorConfig]:
        """
        Get configuration for processor type
        
        Args:
            processor_type: Processor type identifier
            
        Returns:
            ProcessorConfig or None if not found
        """
        return cls._configs.get(processor_type)
    
    @classmethod
    def get_available_types(cls) -> List[str]:
        """Get list of registered processor types"""
        return list(cls._configs.keys())
    
    @classmethod
    def is_registered(cls, processor_type: str) -> bool:
        """Check if processor type is registered"""
        return processor_type in cls._configs
    
    @classmethod
    def clear_registry(cls) -> None:
        """Clear all registered configurations (mainly for testing)"""
        cls._configs.clear()
    
    @classmethod
    def get_stages(cls, processor_type: str) -> Optional[List[str]]:
        """Get stages for processor type"""
        config = cls.get_config(processor_type)
        return config.stages if config else None
    
    @classmethod
    def get_weights(cls, processor_type: str) -> Optional[Dict[str, float]]:
        """Get weights for processor type"""
        config = cls.get_config(processor_type)
        return config.weights if config else None
    
    @classmethod
    def get_estimated_duration(cls, processor_type: str) -> Optional[int]:
        """Get total estimated duration for processor type"""
        config = cls.get_config(processor_type)
        if config:
            return len(config.stages) * config.estimated_duration_per_stage
        return None


# Register default processor configurations
def _register_default_configs():
    """Register default processor configurations"""
    
    # Complete Advanced processor
    ProcessorConfigRegistry.register(
        'complete_advanced',
        stages=['parsing', 'chunking', 'analyzing', 'formatting', 'integrating'],
        weights={
            'parsing': 0.10,
            'chunking': 0.05,
            'analyzing': 0.60,
            'formatting': 0.05,
            'integrating': 0.20
        },
        estimated_duration_per_stage=35
    )
    
    # Performance Optimized processor
    ProcessorConfigRegistry.register(
        'performance_optimized',
        stages=['system_analysis', 'parsing', 'batch_processing', 'integrating', 'dashboard'],
        weights={
            'system_analysis': 0.05,
            'parsing': 0.10,
            'batch_processing': 0.65,
            'integrating': 0.15,
            'dashboard': 0.05
        },
        estimated_duration_per_stage=25
    )
    
    # Basic processor
    ProcessorConfigRegistry.register(
        'basic',
        stages=['parsing', 'analyzing', 'integrating'],
        weights={
            'parsing': 0.15,
            'analyzing': 0.65,
            'integrating': 0.20
        },
        estimated_duration_per_stage=30
    )


# Register default configurations on module import
_register_default_configs()