"""
Test suite for Enhanced Configuration Functionality (Issue #8)
Comprehensive tests for configuration UI, localStorage persistence, and real-time estimation
"""

import pytest
from pathlib import Path
from bs4 import BeautifulSoup
import re


class TestConstants:
    """Test constants for configuration functionality"""
    
    # File paths
    CONFIG_CSS_PATH = "css/config.css"
    CONFIG_JS_PATH = "js/modules/config-manager.js"
    INDEX_HTML_PATH = "index.html"
    APP_JS_PATH = "js/app.js"
    
    # Configuration elements
    RADIO_ELEMENTS = [
        'modeComplete',
        'modePerformance'
    ]
    
    CHECKBOX_ELEMENTS = [
        'categoryGrammar',
        'categoryStyle', 
        'categoryClarity',
        'categoryAcademic'
    ]
    
    # Enhanced UI elements
    ESTIMATION_ELEMENTS = [
        'costEstimate',
        'timeEstimate'
    ]
    
    ADVANCED_ELEMENTS = [
        'advancedToggle',
        'advancedOptions',
        'processingPriority',
        'commentDensity'
    ]
    
    # CSS classes
    CONFIG_CSS_CLASSES = [
        'config-group',
        'config-fieldset',
        'config-legend',
        'radio-group',
        'radio-option',
        'radio-label',
        'checkbox-group',
        'checkbox-option',
        'checkbox-label',
        'estimation-panel',
        'estimation-item',
        'advanced-toggle',
        'advanced-options',
        'tooltip-trigger'
    ]
    
    # JavaScript functionality
    CONFIG_JS_METHODS = [
        'loadSavedPreferences',
        'savePreferences',
        'updateEstimations',
        'validateConfig',
        'exportForProcessing',
        'setupAdvancedOptions',
        'initializeTooltips'
    ]
    
    # Tooltip data attributes
    TOOLTIP_ATTRIBUTES = [
        'data-tooltip'
    ]


class TestHelpers:
    """Helper methods for configuration tests"""
    
    @staticmethod
    def read_static_file(static_path: Path, relative_path: str) -> str:
        """Read file from static directory"""
        return (static_path / relative_path).read_text()
    
    @staticmethod
    def parse_html(static_path: Path) -> BeautifulSoup:
        """Parse HTML file"""
        html_content = TestHelpers.read_static_file(static_path, TestConstants.INDEX_HTML_PATH)
        return BeautifulSoup(html_content, 'html.parser')
    
    @staticmethod
    def assert_elements_exist(content: str, elements: list, context: str = ""):
        """Assert multiple elements exist"""
        for element in elements:
            assert element in content, f"Element {element} missing in {context}"
    
    @staticmethod
    def assert_css_classes_exist(content: str, classes: list, context: str = ""):
        """Assert multiple CSS classes exist"""
        for css_class in classes:
            assert css_class in content, f"CSS class {css_class} missing in {context}"


@pytest.fixture
def static_path():
    """Static file path fixture"""
    return Path(__file__).parent.parent / "web" / "static"


@pytest.fixture
def config_css_content(static_path):
    """Configuration CSS content fixture"""
    return TestHelpers.read_static_file(static_path, TestConstants.CONFIG_CSS_PATH)


@pytest.fixture
def config_js_content(static_path):
    """Configuration JavaScript content fixture"""
    return TestHelpers.read_static_file(static_path, TestConstants.CONFIG_JS_PATH)


@pytest.fixture
def app_js_content(static_path):
    """App.js content fixture"""
    return TestHelpers.read_static_file(static_path, TestConstants.APP_JS_PATH)


@pytest.fixture
def parsed_html(static_path):
    """Parsed HTML fixture"""
    return TestHelpers.parse_html(static_path)


class TestConfigurationUIStructure:
    """Test enhanced configuration UI structure in HTML"""
    
    def test_radio_button_processing_mode_exists(self, parsed_html):
        """Test processing mode radio buttons exist"""
        for radio_id in TestConstants.RADIO_ELEMENTS:
            radio = parsed_html.find('input', id=radio_id)
            assert radio is not None, f"Radio button {radio_id} missing"
            assert radio.get('type') == 'radio', f"Element {radio_id} is not a radio button"
            assert radio.get('name') == 'processing_mode', f"Radio button {radio_id} wrong name"
    
    def test_checkbox_analysis_categories_exist(self, parsed_html):
        """Test analysis category checkboxes exist"""
        for checkbox_id in TestConstants.CHECKBOX_ELEMENTS:
            checkbox = parsed_html.find('input', id=checkbox_id)
            assert checkbox is not None, f"Checkbox {checkbox_id} missing"
            assert checkbox.get('type') == 'checkbox', f"Element {checkbox_id} is not a checkbox"
            assert checkbox.get('name') == 'categories', f"Checkbox {checkbox_id} wrong name"
    
    def test_estimation_display_elements_exist(self, parsed_html):
        """Test cost and time estimation elements exist"""
        for estimation_id in TestConstants.ESTIMATION_ELEMENTS:
            element = parsed_html.find(id=estimation_id)
            assert element is not None, f"Estimation element {estimation_id} missing"
    
    def test_advanced_options_elements_exist(self, parsed_html):
        """Test advanced options elements exist"""
        for advanced_id in TestConstants.ADVANCED_ELEMENTS:
            element = parsed_html.find(id=advanced_id)
            assert element is not None, f"Advanced option element {advanced_id} missing"
    
    def test_tooltip_elements_exist(self, parsed_html):
        """Test tooltip trigger elements exist"""
        tooltip_triggers = parsed_html.find_all(class_='tooltip-trigger')
        assert len(tooltip_triggers) >= 5, "Not enough tooltip triggers found"
        
        for trigger in tooltip_triggers:
            assert trigger.get('data-tooltip'), "Tooltip trigger missing data-tooltip attribute"
    
    def test_fieldset_structure_exists(self, parsed_html):
        """Test proper fieldset structure for accessibility"""
        fieldsets = parsed_html.find_all('fieldset', class_='config-fieldset')
        assert len(fieldsets) >= 2, "Not enough config fieldsets found"
        
        for fieldset in fieldsets:
            legend = fieldset.find('legend', class_='config-legend')
            assert legend is not None, "Fieldset missing legend"
    
    def test_config_group_structure_exists(self, parsed_html):
        """Test config group wrapper structure"""
        config_groups = parsed_html.find_all('div', class_='config-group')
        assert len(config_groups) >= 5, "Not enough config groups found"
    
    def test_estimation_panel_structure(self, parsed_html):
        """Test estimation panel structure"""
        estimation_panel = parsed_html.find('div', class_='estimation-panel')
        assert estimation_panel is not None, "Estimation panel missing"
        
        estimation_items = estimation_panel.find_all('div', class_='estimation-item')
        assert len(estimation_items) >= 2, "Not enough estimation items found"


class TestConfigurationCSSStyling:
    """Test configuration CSS styling implementation"""
    
    @pytest.mark.parametrize("css_class", TestConstants.CONFIG_CSS_CLASSES)
    def test_config_css_classes_defined(self, config_css_content, css_class):
        """Test all configuration CSS classes are defined"""
        assert f".{css_class}" in config_css_content, f"CSS class .{css_class} not defined"
    
    def test_custom_properties_defined(self, config_css_content):
        """Test CSS custom properties for configuration are defined"""
        custom_properties = [
            '--config-primary:',
            '--config-transition:',
            '--config-group-spacing:',
            '--config-border-radius:'
        ]
        
        for prop in custom_properties:
            assert prop in config_css_content, f"Custom property {prop} not defined"
    
    def test_radio_button_styling_exists(self, config_css_content):
        """Test radio button styling implementation"""
        radio_styles = [
            '.radio-group',
            '.radio-option',
            '.radio-option:hover',
            '.radio-option:has(input[type="radio"]:checked)',
            '.radio-label'
        ]
        
        TestHelpers.assert_css_classes_exist(config_css_content, radio_styles, "radio styling")
    
    def test_checkbox_styling_exists(self, config_css_content):
        """Test checkbox styling implementation"""
        checkbox_styles = [
            '.checkbox-group',
            '.checkbox-option',
            '.checkbox-option:hover',
            '.checkbox-option:has(input[type="checkbox"]:checked)',
            '.checkbox-label'
        ]
        
        TestHelpers.assert_css_classes_exist(config_css_content, checkbox_styles, "checkbox styling")
    
    def test_estimation_panel_styling_exists(self, config_css_content):
        """Test estimation panel styling"""
        estimation_styles = [
            '.estimation-panel',
            '.estimation-item',
            '.estimation-label',
            '.estimation-value'
        ]
        
        TestHelpers.assert_css_classes_exist(config_css_content, estimation_styles, "estimation styling")
    
    def test_tooltip_styling_exists(self, config_css_content):
        """Test tooltip styling implementation"""
        tooltip_styles = [
            '.tooltip-trigger',
            '.tooltip-trigger:hover::after',
            '.tooltip-trigger:hover::before'
        ]
        
        TestHelpers.assert_css_classes_exist(config_css_content, tooltip_styles, "tooltip styling")
    
    def test_advanced_options_styling_exists(self, config_css_content):
        """Test advanced options styling"""
        advanced_styles = [
            '.advanced-toggle',
            '.advanced-options',
            '.toggle-icon'
        ]
        
        TestHelpers.assert_css_classes_exist(config_css_content, advanced_styles, "advanced options styling")
    
    def test_responsive_design_exists(self, config_css_content):
        """Test responsive design media queries"""
        assert "@media (max-width: 768px)" in config_css_content, "Tablet responsive design missing"
        assert "@media (max-width: 480px)" in config_css_content, "Mobile responsive design missing"
    
    def test_animation_keyframes_exist(self, config_css_content):
        """Test animation keyframes are defined"""
        animations = [
            "@keyframes configFadeIn",
            "@keyframes tooltipFadeIn"
        ]
        
        for animation in animations:
            assert animation in config_css_content, f"Animation {animation} missing"


class TestConfigurationJavaScript:
    """Test configuration JavaScript functionality"""
    
    def test_config_manager_class_exists(self, config_js_content):
        """Test ConfigManager class is defined"""
        assert "export class ConfigManager" in config_js_content, "ConfigManager class not exported"
    
    @pytest.mark.parametrize("method", TestConstants.CONFIG_JS_METHODS)
    def test_config_js_methods_exist(self, config_js_content, method):
        """Test configuration JavaScript methods exist"""
        assert f"{method}(" in config_js_content, f"Method {method} missing"
    
    def test_localstorage_functionality_exists(self, config_js_content):
        """Test localStorage save/load functionality"""
        localstorage_operations = [
            "localStorage.getItem",
            "localStorage.setItem",
            "korrekturtool_config"
        ]
        
        TestHelpers.assert_elements_exist(config_js_content, localstorage_operations, "localStorage operations")
    
    def test_estimation_calculation_exists(self, config_js_content):
        """Test cost and time estimation calculation logic"""
        estimation_logic = [
            "baseCosts",
            "baseTimes",
            "categoryMultipliers",
            "updateEstimations"
        ]
        
        TestHelpers.assert_elements_exist(config_js_content, estimation_logic, "estimation calculations")
    
    def test_event_bus_integration_exists(self, config_js_content):
        """Test EventBus integration"""
        event_patterns = [
            "this.eventBus.emit",
            "config:initialized",
            "config:saved",
            "config:estimation-updated"
        ]
        
        TestHelpers.assert_elements_exist(config_js_content, event_patterns, "EventBus integration")
    
    def test_config_validation_exists(self, config_js_content):
        """Test configuration validation logic"""
        validation_patterns = [
            "validateConfig(",
            "selectedCategories.length === 0",
            "isValid",
            "errors"
        ]
        
        TestHelpers.assert_elements_exist(config_js_content, validation_patterns, "validation logic")
    
    def test_tooltip_initialization_exists(self, config_js_content):
        """Test tooltip initialization logic"""
        tooltip_patterns = [
            "initializeTooltips",
            "tooltip-trigger",
            "mouseenter"
        ]
        
        TestHelpers.assert_elements_exist(config_js_content, tooltip_patterns, "tooltip initialization")
    
    def test_advanced_options_toggle_exists(self, config_js_content):
        """Test advanced options toggle functionality"""
        toggle_patterns = [
            "setupAdvancedOptions",
            "aria-expanded",
            "aria-hidden"
        ]
        
        TestHelpers.assert_elements_exist(config_js_content, toggle_patterns, "advanced options toggle")


class TestAppJSIntegration:
    """Test app.js integration with ConfigManager"""
    
    def test_config_manager_import_exists(self, app_js_content):
        """Test ConfigManager import statement"""
        assert "import { ConfigManager }" in app_js_content, "ConfigManager import missing"
        assert "from './modules/config-manager.js'" in app_js_content, "ConfigManager import path wrong"
    
    def test_config_manager_initialization_exists(self, app_js_content):
        """Test ConfigManager initialization in app"""
        initialization_patterns = [
            "this.configManager = new ConfigManager",
            "await this.configManager.init()",
            "setupConfigEventListeners"
        ]
        
        TestHelpers.assert_elements_exist(app_js_content, initialization_patterns, "ConfigManager initialization")
    
    def test_config_event_listeners_exist(self, app_js_content):
        """Test configuration event listeners"""
        event_listeners = [
            "config:initialized",
            "config:processing-mode-changed",
            "config:categories-changed",
            "config:estimation-updated"
        ]
        
        TestHelpers.assert_elements_exist(app_js_content, event_listeners, "config event listeners")
    
    def test_form_submission_integration_exists(self, app_js_content):
        """Test form submission integration with configuration"""
        form_patterns = [
            "handleFormSubmission",
            "validateConfig()",
            "exportForProcessing()"
        ]
        
        TestHelpers.assert_elements_exist(app_js_content, form_patterns, "form submission integration")
    
    def test_config_manager_cleanup_exists(self, app_js_content):
        """Test ConfigManager cleanup in destroy method"""
        cleanup_patterns = [
            "this.configManager.destroy()"
        ]
        
        TestHelpers.assert_elements_exist(app_js_content, cleanup_patterns, "ConfigManager cleanup")


class TestRequirementsCoverage:
    """Test Issue #8 requirements coverage"""
    
    def test_requirement_radio_button_processing_mode(self, parsed_html):
        """
        Requirement: Radio buttons for processing mode selection
        GIVEN a user wants to configure processing options
        WHEN they view the processing mode section
        THEN they should see radio buttons for Complete and Performance modes
        """
        complete_radio = parsed_html.find('input', id='modeComplete')
        performance_radio = parsed_html.find('input', id='modePerformance')
        
        assert complete_radio is not None, "Complete mode radio button missing"
        assert performance_radio is not None, "Performance mode radio button missing"
        assert complete_radio.get('type') == 'radio', "Complete mode not a radio button"
        assert performance_radio.get('type') == 'radio', "Performance mode not a radio button"
        assert complete_radio.get('checked') is not None, "Complete mode should be checked by default"
    
    def test_requirement_checkbox_analysis_categories(self, parsed_html):
        """
        Requirement: Individual checkboxes for analysis categories
        GIVEN a user wants to select analysis categories
        WHEN they view the categories section
        THEN they should see individual checkboxes for each category
        """
        categories = ['Grammar', 'Style', 'Clarity', 'Academic']
        
        for category_id in TestConstants.CHECKBOX_ELEMENTS:
            checkbox = parsed_html.find('input', id=category_id)
            assert checkbox is not None, f"Checkbox {category_id} missing"
            assert checkbox.get('type') == 'checkbox', f"{category_id} not a checkbox"
            assert checkbox.get('checked') is not None, f"{category_id} should be checked by default"
    
    def test_requirement_cost_estimation_display(self, parsed_html, config_js_content):
        """
        Requirement: Real-time cost estimation display
        GIVEN a user changes configuration options
        WHEN the configuration changes
        THEN the cost estimate should update in real-time
        """
        cost_estimate = parsed_html.find(id='costEstimate')
        assert cost_estimate is not None, "Cost estimate display missing"
        
        # Check JavaScript has cost calculation logic
        assert "updateEstimations" in config_js_content, "Cost estimation logic missing"
        assert "baseCosts" in config_js_content, "Base cost data missing"
    
    def test_requirement_time_estimation_display(self, parsed_html, config_js_content):
        """
        Requirement: Processing time estimates
        GIVEN a user configures processing options
        WHEN the configuration changes
        THEN the time estimate should update accordingly
        """
        time_estimate = parsed_html.find(id='timeEstimate')
        assert time_estimate is not None, "Time estimate display missing"
        
        # Check JavaScript has time calculation logic
        assert "baseTimes" in config_js_content, "Base time data missing"
        assert "finalTimeMin" in config_js_content, "Time calculation logic missing"
    
    def test_requirement_tooltip_explanations(self, parsed_html, config_css_content):
        """
        Requirement: Tooltip explanations for options
        GIVEN a user needs help understanding options
        WHEN they hover over info icons
        THEN explanatory tooltips should appear
        """
        tooltip_triggers = parsed_html.find_all(class_='tooltip-trigger')
        assert len(tooltip_triggers) >= 5, "Not enough tooltip triggers found"
        
        # Check CSS has tooltip styling
        assert ".tooltip-trigger:hover::after" in config_css_content, "Tooltip CSS missing"
    
    def test_requirement_advanced_options_toggle(self, parsed_html, config_js_content):
        """
        Requirement: Collapsible advanced options
        GIVEN a user wants to access advanced options
        WHEN they click the advanced options toggle
        THEN the advanced section should expand/collapse
        """
        advanced_toggle = parsed_html.find(id='advancedToggle')
        advanced_options = parsed_html.find(id='advancedOptions')
        
        assert advanced_toggle is not None, "Advanced options toggle missing"
        assert advanced_options is not None, "Advanced options section missing"
        assert advanced_toggle.get('aria-expanded') == 'false', "Advanced options should start collapsed"
        
        # Check JavaScript has toggle logic
        assert "setupAdvancedOptions" in config_js_content, "Advanced options toggle logic missing"
    
    def test_requirement_localstorage_persistence(self, config_js_content):
        """
        Requirement: localStorage preference persistence
        GIVEN a user configures their preferences
        WHEN they reload the page
        THEN their preferences should be restored
        """
        localstorage_patterns = [
            "loadSavedPreferences",
            "savePreferences",
            "localStorage.getItem",
            "localStorage.setItem",
            "korrekturtool_config"
        ]
        
        TestHelpers.assert_elements_exist(config_js_content, localstorage_patterns, "localStorage persistence")
    
    def test_requirement_output_filename_customization(self, parsed_html):
        """
        Requirement: Output filename customization
        GIVEN a user wants to specify output filename
        WHEN they enter a custom filename
        THEN the system should use their specified name
        """
        output_filename = parsed_html.find('input', id='outputFilename')
        assert output_filename is not None, "Output filename input missing"
        assert output_filename.get('type') == 'text', "Output filename should be text input"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])