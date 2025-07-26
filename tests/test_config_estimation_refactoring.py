"""
RSpec-style tests for refactored ConfigManager estimation methods
Tests specifically for the PR feedback improvements: extracted methods and constants
"""

import pytest
from pathlib import Path
import re


class TestHelpers:
    """Helper methods for testing refactored estimation functionality"""
    
    @staticmethod
    def read_static_file(static_path: Path, relative_path: str) -> str:
        """Read file from static directory"""
        return (static_path / relative_path).read_text()


@pytest.fixture
def static_path():
    """Static file path fixture"""
    return Path(__file__).parent.parent / "web" / "static"


@pytest.fixture
def config_js_content(static_path):
    """Configuration JavaScript content fixture"""
    return TestHelpers.read_static_file(static_path, "js/modules/config-manager.js")


class TestEstimationConstantsRefactoring:
    """RSpec-style tests for extracted estimation constants"""
    
    def test_estimation_constants_extraction(self, config_js_content):
        """
        GIVEN the complex estimation logic needs maintainable constants
        WHEN constants are extracted from magic numbers
        THEN all estimation values should be defined in ESTIMATION_CONSTANTS
        """
        # THEN constants should be defined at module level
        assert "const ESTIMATION_CONSTANTS = {" in config_js_content, "ESTIMATION_CONSTANTS not defined"
        
        # AND base costs should be extracted
        assert "BASE_COSTS: {" in config_js_content, "BASE_COSTS not extracted"
        assert "complete: { min: 0.25, max: 0.75 }" in config_js_content, "Complete mode costs not defined"
        assert "performance: { min: 0.15, max: 0.45 }" in config_js_content, "Performance mode costs not defined"
        
        # AND base times should be extracted  
        assert "BASE_TIMES: {" in config_js_content, "BASE_TIMES not extracted"
        assert "complete: { min: 45, max: 120 }" in config_js_content, "Complete mode times not defined"
        assert "performance: { min: 20, max: 60 }" in config_js_content, "Performance mode times not defined"
        
        # AND category multipliers should be extracted
        assert "CATEGORY_MULTIPLIERS: {" in config_js_content, "CATEGORY_MULTIPLIERS not extracted"
        assert "grammar: 1.0" in config_js_content, "Grammar multiplier not defined"
        assert "style: 1.2" in config_js_content, "Style multiplier not defined"
        assert "clarity: 1.1" in config_js_content, "Clarity multiplier not defined"
        assert "academic: 1.3" in config_js_content, "Academic multiplier not defined"
    
    def test_priority_and_density_constants_defined(self, config_js_content):
        """
        GIVEN priority and density modifiers need to be maintainable
        WHEN constants are extracted for these values
        THEN PRIORITY_MULTIPLIERS and DENSITY_MULTIPLIERS should be defined
        """
        # THEN priority multipliers should be defined
        assert "PRIORITY_MULTIPLIERS: {" in config_js_content, "PRIORITY_MULTIPLIERS not defined"
        assert "normal: 1.0" in config_js_content, "Normal priority multiplier not defined"
        assert "high: 1.3" in config_js_content, "High priority multiplier not defined"
        
        # AND density multipliers should be defined
        assert "DENSITY_MULTIPLIERS: {" in config_js_content, "DENSITY_MULTIPLIERS not defined"
        assert "low: 0.7" in config_js_content, "Low density multiplier not defined"
        assert "medium: 1.0" in config_js_content, "Medium density multiplier not defined"
        assert "high: 1.4" in config_js_content, "High density multiplier not defined"
    
    def test_constants_used_in_constructor(self, config_js_content):
        """
        GIVEN constants are extracted to reduce magic numbers
        WHEN the ConfigManager constructor initializes estimation data
        THEN it should use the extracted constants instead of hardcoded values
        """
        # THEN constructor should use extracted constants
        assert "baseCosts: ESTIMATION_CONSTANTS.BASE_COSTS" in config_js_content, "Constructor not using BASE_COSTS constant"
        assert "baseTimes: ESTIMATION_CONSTANTS.BASE_TIMES" in config_js_content, "Constructor not using BASE_TIMES constant"
        assert "categoryMultipliers: ESTIMATION_CONSTANTS.CATEGORY_MULTIPLIERS" in config_js_content, "Constructor not using CATEGORY_MULTIPLIERS constant"


class TestEstimationMethodDecomposition:
    """RSpec-style tests for decomposed estimation methods"""
    
    def test_main_estimation_method_simplification(self, config_js_content):
        """
        GIVEN the updateEstimations method was too complex
        WHEN it is refactored into smaller focused methods
        THEN the main method should delegate to specific calculation methods
        """
        # THEN main method should be simplified
        assert "updateEstimations() {" in config_js_content, "Main updateEstimations method missing"
        
        # AND it should delegate to calculation methods
        assert "const estimationResults = this.calculateEstimations();" in config_js_content, "Main method not delegating to calculateEstimations"
        assert "this.updateEstimationDisplay(estimationResults);" in config_js_content, "Main method not delegating to updateEstimationDisplay"
        assert "this.emitEstimationUpdate(estimationResults);" in config_js_content, "Main method not delegating to emitEstimationUpdate"
    
    def test_calculation_methods_extracted(self, config_js_content):
        """
        GIVEN complex calculation logic needs to be maintainable
        WHEN calculation methods are extracted
        THEN focused methods should handle specific calculation aspects
        """
        # THEN core calculation method should exist
        assert "calculateEstimations() {" in config_js_content, "calculateEstimations method missing"
        
        # AND base calculation methods should exist
        assert "calculateBaseCost() {" in config_js_content, "calculateBaseCost method missing"
        assert "calculateBaseTime() {" in config_js_content, "calculateBaseTime method missing"
        
        # AND category calculation method should exist
        assert "calculateCategoryMultiplier() {" in config_js_content, "calculateCategoryMultiplier method missing"
        
        # AND modifier calculation method should exist
        assert "calculateModifiers() {" in config_js_content, "calculateModifiers method missing"
    
    def test_display_and_event_methods_extracted(self, config_js_content):
        """
        GIVEN display and event logic should be separated from calculation
        WHEN display and event methods are extracted
        THEN specific methods should handle UI updates and event emission
        """
        # THEN display update method should exist
        assert "updateEstimationDisplay(estimationResults) {" in config_js_content, "updateEstimationDisplay method missing"
        
        # AND event emission method should exist
        assert "emitEstimationUpdate(estimationResults) {" in config_js_content, "emitEstimationUpdate method missing"
    
    def test_method_single_responsibility_principle(self, config_js_content):
        """
        GIVEN each method should have a single responsibility
        WHEN methods are examined for their purpose
        THEN each method should focus on one specific aspect of estimation
        """
        # THEN calculateBaseCost should only handle base cost retrieval
        base_cost_pattern = r"calculateBaseCost\(\)\s*\{[^}]*return\s+this\.estimationData\.baseCosts\[this\.config\.processingMode\]"
        assert re.search(base_cost_pattern, config_js_content, re.DOTALL), "calculateBaseCost not following SRP"
        
        # AND calculateBaseTime should only handle base time retrieval
        base_time_pattern = r"calculateBaseTime\(\)\s*\{[^}]*return\s+this\.estimationData\.baseTimes\[this\.config\.processingMode\]"
        assert re.search(base_time_pattern, config_js_content, re.DOTALL), "calculateBaseTime not following SRP"
        
        # AND calculateModifiers should only handle modifier calculation
        assert "calculateModifiers() {" in config_js_content, "calculateModifiers method missing"
        assert "ESTIMATION_CONSTANTS.PRIORITY_MULTIPLIERS[priority]" in config_js_content, "calculateModifiers not using priority constants"
        assert "ESTIMATION_CONSTANTS.DENSITY_MULTIPLIERS[density]" in config_js_content, "calculateModifiers not using density constants"


class TestMethodTestability:
    """RSpec-style tests for improved method testability"""
    
    def test_pure_calculation_methods(self, config_js_content):
        """
        GIVEN methods should be easily testable
        WHEN calculation methods are extracted
        THEN they should return values that can be independently tested
        """
        # THEN calculateBaseCost should return a value
        assert "return this.estimationData.baseCosts[this.config.processingMode];" in config_js_content, "calculateBaseCost not returning value"
        
        # AND calculateBaseTime should return a value
        assert "return this.estimationData.baseTimes[this.config.processingMode];" in config_js_content, "calculateBaseTime not returning value"
        
        # AND calculateCategoryMultiplier should return a number
        assert "return totalMultiplier / selectedCategories.length;" in config_js_content, "calculateCategoryMultiplier not returning calculated value"
        
        # AND calculateModifiers should return an object
        assert "return {" in config_js_content, "calculateModifiers not returning object"
        assert "priority:" in config_js_content and "density:" in config_js_content, "calculateModifiers not returning both modifiers"
    
    def test_error_handling_in_extracted_methods(self, config_js_content):
        """
        GIVEN extracted methods should be robust
        WHEN edge cases occur
        THEN methods should handle them gracefully
        """
        # THEN calculateCategoryMultiplier should handle empty categories
        assert "if (selectedCategories.length === 0) return 1.0;" in config_js_content, "calculateCategoryMultiplier not handling empty categories"
        
        # AND calculateModifiers should have fallback values
        assert "|| 1.0" in config_js_content, "calculateModifiers not providing fallback values"


class TestMethodDocumentation:
    """RSpec-style tests for method documentation"""
    
    def test_method_jsdoc_comments(self, config_js_content):
        """
        GIVEN methods should be well-documented
        WHEN JSDoc comments are added
        THEN each method should have clear documentation
        """
        # THEN calculateEstimations should be documented
        assert "* Calculate cost and time estimations based on current configuration" in config_js_content, "calculateEstimations missing documentation"
        assert "* @returns {Object} Estimation results with cost and time ranges" in config_js_content, "calculateEstimations missing return documentation"
        
        # AND calculateBaseCost should be documented
        assert "* Get base cost range for current processing mode" in config_js_content, "calculateBaseCost missing documentation"
        assert "* @returns {Object} Base cost range {min, max}" in config_js_content, "calculateBaseCost missing return documentation"
        
        # AND calculateBaseTime should be documented
        assert "* Get base time range for current processing mode" in config_js_content, "calculateBaseTime missing documentation"
        assert "* @returns {Object} Base time range {min, max}" in config_js_content, "calculateBaseTime missing return documentation"
        
        # AND calculateCategoryMultiplier should be documented
        assert "* Calculate category complexity multiplier based on selected categories" in config_js_content, "calculateCategoryMultiplier missing documentation"
        assert "* @returns {number} Combined category multiplier" in config_js_content, "calculateCategoryMultiplier missing return documentation"


class TestRefactoringBenefits:
    """RSpec-style tests verifying the benefits of refactoring"""
    
    def test_maintainability_improvement(self, config_js_content):
        """
        GIVEN code maintainability should be improved
        WHEN constants and methods are extracted
        THEN changes to business rules should be easier to implement
        """
        # THEN cost adjustments only require constant updates
        cost_constants_count = config_js_content.count("min: 0.")
        assert cost_constants_count >= 2, "Cost constants not centralized"
        
        # AND time adjustments only require constant updates
        time_constants_count = config_js_content.count("min: ")
        assert time_constants_count >= 4, "Time constants not centralized"
        
        # AND multiplier adjustments only require constant updates
        multiplier_constants_count = config_js_content.count(": 1.")
        assert multiplier_constants_count >= 6, "Multiplier constants not centralized"
    
    def test_code_readability_improvement(self, config_js_content):
        """
        GIVEN code should be easier to understand
        WHEN complex logic is broken into focused methods
        THEN method names should clearly indicate their purpose
        """
        # THEN method names should be descriptive
        descriptive_methods = [
            "calculateBaseCost",
            "calculateBaseTime", 
            "calculateCategoryMultiplier",
            "calculateModifiers",
            "updateEstimationDisplay",
            "emitEstimationUpdate"
        ]
        
        for method in descriptive_methods:
            assert f"{method}(" in config_js_content, f"Descriptive method {method} missing"
    
    def test_testability_improvement(self, config_js_content):
        """
        GIVEN individual methods should be testable in isolation
        WHEN methods are extracted with clear inputs and outputs
        THEN each calculation step can be tested independently
        """
        # THEN methods should have clear return statements
        return_statements = config_js_content.count("return ")
        assert return_statements >= 6, "Not enough focused methods with return values"
        
        # AND methods should have minimal dependencies
        # calculateBaseCost and calculateBaseTime should only depend on processingMode
        assert "this.config.processingMode" in config_js_content, "Methods not accessing config appropriately"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])