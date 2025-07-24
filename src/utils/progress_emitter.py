"""
Progress emitter utility for processing pipeline integration

REFACTORED VERSION - Following Sandi Metz principles with dependency injection
and separated concerns. Original functionality maintained for backward compatibility.

Provides a generic interface for emitting progress updates during document processing
that can be used by any processor (CompleteAdvanced, PerformanceOptimized, etc.)
"""

import logging
from typing import List, Optional, Dict, Any
from .progress_emitter_refactored import ProgressEmitter as RefactoredProgressEmitter, ProgressEmitterFactory
from .processor_config_registry import ProcessorConfigRegistry

logger = logging.getLogger(__name__)

# Export the refactored classes for new usage
ProgressEmitter = RefactoredProgressEmitter
ProcessorProgressAdapter = ProcessorConfigRegistry  # Registry replaces old adapter

# Backward compatibility functions
def create_progress_emitter(job_id: str, processor_type: str = "basic") -> ProgressEmitter:
    """
    Create progress emitter for specific processor type
    
    Args:
        job_id: Job identifier
        processor_type: Type of processor ("complete_advanced", "performance_optimized", "basic")
        
    Returns:
        Configured ProgressEmitter instance
    """
    return ProgressEmitterFactory.create(job_id, processor_type)


# Legacy class for backward compatibility (deprecated)
class LegacyProcessorProgressAdapter:
    """
    DEPRECATED: Legacy adapter class for backward compatibility
    
    Use ProcessorConfigRegistry instead for new code.
    """
    
    @classmethod
    def create_for_complete_advanced(cls, job_id: str) -> ProgressEmitter:
        """Create progress emitter configured for CompleteAdvancedKorrekturtool"""
        logger.warning("LegacyProcessorProgressAdapter is deprecated. Use ProgressEmitterFactory instead.")
        return ProgressEmitterFactory.create(job_id, "complete_advanced")
    
    @classmethod
    def create_for_performance_optimized(cls, job_id: str) -> ProgressEmitter:
        """Create progress emitter configured for PerformanceOptimizedKorrekturtool"""
        logger.warning("LegacyProcessorProgressAdapter is deprecated. Use ProgressEmitterFactory instead.")
        return ProgressEmitterFactory.create(job_id, "performance_optimized")
    
    @classmethod
    def create_for_basic(cls, job_id: str) -> ProgressEmitter:
        """Create progress emitter configured for basic processing"""
        logger.warning("LegacyProcessorProgressAdapter is deprecated. Use ProgressEmitterFactory instead.")
        return ProgressEmitterFactory.create(job_id, "basic")
    
    @classmethod
    def create_custom(cls, job_id: str, stages: List[str], weights: Optional[Dict[str, float]] = None) -> ProgressEmitter:
        """Create progress emitter with custom stages and weights"""
        logger.warning("LegacyProcessorProgressAdapter is deprecated. Use ProgressEmitterFactory instead.")
        return ProgressEmitterFactory.create_custom(job_id, stages, weights)


# Deprecated: Example function moved to examples/progress_emitter_examples.py
def example_processor_integration():
    """
    MOVED: This example has been moved to examples/progress_emitter_examples.py
    
    Please use the examples in that file for reference and testing.
    """
    logger.warning(
        "example_processor_integration() has been moved to examples/progress_emitter_examples.py. "
        "Please update your imports and use the examples in that module instead."
    )
    
    # Import and run the example from the new location
    try:
        from examples.progress_emitter_examples import complete_advanced_example
        complete_advanced_example()
    except ImportError:
        logger.error("Could not import examples. Please check examples/progress_emitter_examples.py exists.")
        raise