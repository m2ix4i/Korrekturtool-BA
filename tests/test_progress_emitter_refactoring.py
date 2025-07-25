"""
Test suite for refactored ProgressEmitter components
Validates that the refactoring maintains functionality while improving structure
"""

import unittest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.stage_manager import StageManager
from src.utils.progress_calculator import ProgressCalculator
from src.utils.job_lifecycle_manager import JobLifecycleManager
from src.utils.processor_config_registry import ProcessorConfigRegistry, ProcessorConfig
from src.utils.progress_emitter_refactored import ProgressEmitter, ProgressEmitterFactory


class TestStageManager(unittest.TestCase):
    """Test StageManager component"""
    
    def setUp(self):
        self.stages = ["parsing", "analyzing", "integrating"]
        self.manager = StageManager(self.stages)
    
    def test_initialization(self):
        """Test proper initialization"""
        self.assertEqual(self.manager.stages, self.stages)
        self.assertEqual(self.manager.get_current_stage(), "parsing")
        self.assertEqual(self.manager.get_current_stage_index(), 0)
    
    def test_stage_validation(self):
        """Test stage validation"""
        self.assertTrue(self.manager.is_valid_stage("parsing"))
        self.assertFalse(self.manager.is_valid_stage("invalid"))
    
    def test_stage_advancement(self):
        """Test stage advancement"""
        self.assertEqual(self.manager.advance_to_next_stage(), "analyzing")
        self.assertEqual(self.manager.get_current_stage(), "analyzing")
        self.assertEqual(self.manager.get_current_stage_index(), 1)
        
        self.assertEqual(self.manager.advance_to_next_stage(), "integrating")
        self.assertIsNone(self.manager.advance_to_next_stage())  # No more stages
    
    def test_stage_setting(self):
        """Test setting current stage"""
        self.assertTrue(self.manager.set_current_stage("integrating"))
        self.assertEqual(self.manager.get_current_stage(), "integrating")
        self.assertEqual(self.manager.get_current_stage_index(), 2)
        
        self.assertFalse(self.manager.set_current_stage("invalid"))


class TestProgressCalculator(unittest.TestCase):
    """Test ProgressCalculator component"""
    
    def setUp(self):
        self.stages = ["parsing", "analyzing", "integrating"]
        self.weights = {"parsing": 0.2, "analyzing": 0.6, "integrating": 0.2}
        self.calculator = ProgressCalculator(self.stages, self.weights)
    
    def test_progress_calculation(self):
        """Test progress calculation"""
        # No stages completed, 0% current stage progress
        progress = self.calculator.calculate_overall_progress(0, 0)
        self.assertEqual(progress, 0)
        
        # No stages completed, 50% current stage progress
        progress = self.calculator.calculate_overall_progress(0, 50)
        self.assertEqual(progress, 10)  # 20% * 50% = 10%
        
        # One stage completed (parsing), 50% analyzing
        progress = self.calculator.calculate_overall_progress(1, 50)
        self.assertEqual(progress, 50)  # 20% + (60% * 50%) = 50%
        
        # All stages completed
        progress = self.calculator.calculate_overall_progress(3, 100)
        self.assertEqual(progress, 100)
    
    def test_weight_access(self):
        """Test weight access methods"""
        self.assertEqual(self.calculator.get_stage_weight("parsing"), 0.2)
        self.assertEqual(self.calculator.get_stage_weight("invalid"), 0.0)
    
    def test_progress_normalization(self):
        """Test progress normalization"""
        self.assertEqual(self.calculator.normalize_progress(-10), 0)
        self.assertEqual(self.calculator.normalize_progress(50), 50)
        self.assertEqual(self.calculator.normalize_progress(150), 100)


class TestJobLifecycleManager(unittest.TestCase):
    """Test JobLifecycleManager component"""
    
    def setUp(self):
        self.job_id = "test_job_123"
        self.mock_tracker = Mock()
        self.manager = JobLifecycleManager(self.job_id, self.mock_tracker)
    
    def test_job_start(self):
        """Test job start functionality"""
        stages = ["parsing", "analyzing"]
        self.manager.start_job(stages, 120)
        
        self.mock_tracker.start_job.assert_called_once_with(self.job_id, stages, 120)
    
    def test_progress_update(self):
        """Test progress update functionality"""
        self.manager.update_progress("analyzing", 50, "Processing data", 75)
        
        self.mock_tracker.update_progress.assert_called_once_with(
            self.job_id, "analyzing", 50, "Processing data", 75
        )
    
    def test_stage_completion(self):
        """Test stage completion functionality"""
        self.manager.complete_stage("parsing")
        
        self.mock_tracker.complete_stage.assert_called_once_with(self.job_id, "parsing")
    
    def test_job_completion(self):
        """Test job completion functionality"""
        result_data = {"download_url": "/test", "comments": 5}
        self.manager.complete_job(True, result_data)
        
        self.mock_tracker.complete_job.assert_called_once_with(self.job_id, True, result_data)
    
    def test_job_failure(self):
        """Test job failure functionality"""
        self.manager.fail_job("Test error", "analyzing")
        
        self.mock_tracker.fail_job.assert_called_once_with(self.job_id, "Test error", "analyzing")


class TestProcessorConfigRegistry(unittest.TestCase):
    """Test ProcessorConfigRegistry component"""
    
    def setUp(self):
        # Clear registry for clean tests
        ProcessorConfigRegistry.clear_registry()
        # Re-register default configurations for other tests
        from src.utils.processor_config_registry import _register_default_configs
        _register_default_configs()
    
    def test_registration(self):
        """Test configuration registration"""
        stages = ["stage1", "stage2"]
        weights = {"stage1": 0.3, "stage2": 0.7}
        
        ProcessorConfigRegistry.register("test_processor", stages, weights, 25)
        
        self.assertTrue(ProcessorConfigRegistry.is_registered("test_processor"))
        config = ProcessorConfigRegistry.get_config("test_processor")
        self.assertIsNotNone(config)
        self.assertEqual(config.stages, stages)
        self.assertEqual(config.weights, weights)
        self.assertEqual(config.estimated_duration_per_stage, 25)
    
    def test_invalid_weights(self):
        """Test validation of invalid weights"""
        stages = ["stage1", "stage2"]
        weights = {"stage1": 0.3, "stage2": 0.5}  # Sum = 0.8, not 1.0
        
        with self.assertRaises(ValueError):
            ProcessorConfigRegistry.register("invalid_processor", stages, weights)
    
    def test_mismatched_stages_weights(self):
        """Test validation of mismatched stages and weights"""
        stages = ["stage1", "stage2"]
        weights = {"stage1": 0.5, "stage3": 0.5}  # stage3 not in stages
        
        with self.assertRaises(ValueError):
            ProcessorConfigRegistry.register("mismatched_processor", stages, weights)
    
    def test_config_access(self):
        """Test configuration access methods"""
        stages = ["stage1", "stage2"]
        weights = {"stage1": 0.4, "stage2": 0.6}
        
        ProcessorConfigRegistry.register("access_test", stages, weights, 30)
        
        self.assertEqual(ProcessorConfigRegistry.get_stages("access_test"), stages)
        self.assertEqual(ProcessorConfigRegistry.get_weights("access_test"), weights)
        self.assertEqual(ProcessorConfigRegistry.get_estimated_duration("access_test"), 60)  # 2 stages * 30s


class TestProgressEmitterFactory(unittest.TestCase):
    """Test ProgressEmitterFactory"""
    
    def setUp(self):
        self.job_id = "test_factory_job"
        self.mock_tracker = Mock()
    
    def test_factory_create(self):
        """Test factory creation with processor type"""
        emitter = ProgressEmitterFactory.create(self.job_id, "basic", self.mock_tracker)
        
        self.assertIsInstance(emitter, ProgressEmitter)
        self.assertEqual(emitter.job_id, self.job_id)
        
        # Verify job was started with basic stages
        basic_config = ProcessorConfigRegistry.get_config("basic")
        self.mock_tracker.start_job.assert_called_once_with(
            self.job_id, basic_config.stages, len(basic_config.stages) * 30
        )
    
    def test_factory_create_custom(self):
        """Test factory creation with custom configuration"""
        stages = ["custom1", "custom2"]
        weights = {"custom1": 0.3, "custom2": 0.7}
        
        emitter = ProgressEmitterFactory.create_custom(self.job_id, stages, weights, self.mock_tracker)
        
        self.assertIsInstance(emitter, ProgressEmitter)
        self.assertEqual(emitter.job_id, self.job_id)
        
        # Verify job was started with custom stages
        self.mock_tracker.start_job.assert_called_once_with(self.job_id, stages, 60)  # 2 stages * 30s


class TestProgressEmitterIntegration(unittest.TestCase):
    """Integration test for refactored ProgressEmitter"""
    
    def setUp(self):
        self.job_id = "integration_test_job"
        self.mock_tracker = Mock()
        self.emitter = ProgressEmitterFactory.create(self.job_id, "basic", self.mock_tracker)
    
    def test_complete_workflow(self):
        """Test complete processing workflow"""
        # Start parsing stage
        self.emitter.start_stage("parsing", "Starting document parsing")
        
        # Update parsing progress
        self.emitter.update_stage_progress(50, "Halfway through parsing")
        
        # Complete parsing stage
        self.emitter.complete_stage("Parsing completed")
        
        # Start analyzing stage
        self.emitter.start_stage("analyzing", "Starting analysis")
        
        # Update analyzing progress multiple times
        self.emitter.update_stage_progress(25, "Analysis 25% complete")
        self.emitter.update_stage_progress(75, "Analysis 75% complete")
        
        # Complete analyzing stage
        self.emitter.complete_stage("Analysis completed")
        
        # Start integrating stage
        self.emitter.start_stage("integrating", "Starting integration")
        
        # Complete integrating stage
        self.emitter.update_stage_progress(100, "Integration complete")
        self.emitter.complete_stage("Integration completed")
        
        # Complete job
        result_data = {"download_url": "/test", "comments": 10}
        self.emitter.complete_job(True, result_data)
        
        # Verify all tracker calls were made
        # Expected calls:
        # - start_stage calls: 3 (parsing, analyzing, integrating)
        # - update_stage_progress calls: 4 (parsing 50%, analyzing 25%, analyzing 75%, integrating 100%)
        # - complete_stage final updates: 3 (one for each completed stage)
        # Total update_progress calls: 3 + 4 + 3 = 10
        self.assertEqual(self.mock_tracker.update_progress.call_count, 10)
        self.assertEqual(self.mock_tracker.complete_stage.call_count, 3)   # 3 stages completed
        self.mock_tracker.complete_job.assert_called_once_with(self.job_id, True, result_data)
    
    def test_error_handling(self):
        """Test error handling in workflow"""
        self.emitter.start_stage("parsing", "Starting parsing")
        self.emitter.update_stage_progress(30, "Parsing in progress")
        
        # Simulate error
        self.emitter.fail_job("Test error occurred", "parsing")
        
        self.mock_tracker.fail_job.assert_called_once_with(self.job_id, "Test error occurred", "parsing")


if __name__ == '__main__':
    # Create __init__.py files if they don't exist
    init_files = [
        Path(__file__).parent.parent / "src" / "__init__.py",
        Path(__file__).parent.parent / "src" / "utils" / "__init__.py",
    ]
    
    for init_file in init_files:
        init_file.parent.mkdir(parents=True, exist_ok=True)
        if not init_file.exists():
            init_file.touch()
    
    unittest.main()