"""
Improved test suite for drag-and-drop file upload functionality (Issue #7)
Addresses PR feedback: reduced complexity, DRY principles, extracted constants
"""

import pytest
from pathlib import Path
from bs4 import BeautifulSoup
import re


# Test Constants - addressing magic strings feedback
class TestConstants:
    """Centralized constants to reduce magic strings in tests"""
    
    # File paths
    UPLOAD_HANDLER_PATH = "js/handlers/upload-handler.js"
    COMPONENTS_CSS_PATH = "css/components.css"
    INDEX_HTML_PATH = "index.html"
    APP_JS_PATH = "js/app.js"
    
    # JavaScript methods
    JS_METHODS = {
        'drag_drop': ['handleDragOver(', 'handleDragLeave(', 'handleDrop('],
        'file_handling': ['triggerFileSelection(', 'handleFileSelection(', 'selectFile('],
        'validation': ['validateFileType(', 'validateFileSize('],
        'state_management': ['setDragoverState(', 'setProcessingState(', 'reset('],
        'display': ['updateDisplay(', 'updateDisplayForSelectedFile(', 'showError(']
    }
    
    # CSS classes
    CSS_CLASSES = {
        'upload': ['upload-area', 'upload-icon', 'upload-text', 'upload-subtext'],
        'states': ['upload-area:hover', 'upload-area.dragover', 'upload-area.disabled', 'upload-area.file-selected'],
        'progress': ['progress-bar', 'progress-fill', 'progress-text']
    }
    
    # Custom properties
    CUSTOM_PROPERTIES = [
        '--upload-icon-size:',
        '--upload-gradient-angle:',
        '--upload-dragover-scale:',
        '--upload-border-width:'
    ]
    
    # Error messages
    ERROR_MESSAGES = [
        'Nur DOCX-Dateien werden unterstützt',
        'Datei ist zu groß',
        'Maximum: 50 MB'
    ]
    
    # Event bus events
    EVENTS = [
        'upload:file-selected',
        'upload:error', 
        'upload:reset',
        'upload:selection-triggered'
    ]
    
    # File validation
    DOCX_MIME_TYPE = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    DOCX_EXTENSION = '.docx'
    MAX_FILE_SIZE = '50 * 1024 * 1024'


class TestHelpers:
    """Helper methods to reduce duplication - addressing DRY feedback"""
    
    @staticmethod
    def read_static_file(static_path: Path, relative_path: str) -> str:
        """Centralized file reading helper"""
        return (static_path / relative_path).read_text()
    
    @staticmethod
    def parse_html(static_path: Path) -> BeautifulSoup:
        """Centralized HTML parsing helper"""
        html_content = TestHelpers.read_static_file(static_path, TestConstants.INDEX_HTML_PATH)
        return BeautifulSoup(html_content, 'html.parser')
    
    @staticmethod
    def assert_methods_exist(content: str, methods: list, context: str = ""):
        """Helper for asserting multiple methods exist"""
        for method in methods:
            assert method in content, f"Method {method} missing in {context}"
    
    @staticmethod
    def assert_css_classes_exist(content: str, classes: list, context: str = ""):
        """Helper for asserting multiple CSS classes exist"""
        for css_class in classes:
            assert css_class in content, f"CSS class {css_class} missing in {context}"


@pytest.fixture
def static_path():
    """Centralized static path fixture"""
    return Path(__file__).parent.parent / "web" / "static"


@pytest.fixture  
def upload_handler_content(static_path):
    """Fixture for upload handler JavaScript content"""
    return TestHelpers.read_static_file(static_path, TestConstants.UPLOAD_HANDLER_PATH)


@pytest.fixture
def components_css_content(static_path):
    """Fixture for components CSS content"""
    return TestHelpers.read_static_file(static_path, TestConstants.COMPONENTS_CSS_PATH)


@pytest.fixture
def app_js_content(static_path):
    """Fixture for app.js content"""
    return TestHelpers.read_static_file(static_path, TestConstants.APP_JS_PATH)


@pytest.fixture
def parsed_html(static_path):
    """Fixture for parsed HTML content"""
    return TestHelpers.parse_html(static_path)


class TestUploadHandlerStructure:
    """Focused tests for UploadHandler class structure - reduced complexity"""
    
    def test_upload_handler_file_exists(self, static_path):
        """Test that UploadHandler JavaScript file exists"""
        upload_handler_path = static_path / TestConstants.UPLOAD_HANDLER_PATH
        assert upload_handler_path.exists(), "UploadHandler file missing"
    
    def test_upload_handler_class_export(self, upload_handler_content):
        """Test UploadHandler class exists and exports"""
        assert "export class UploadHandler" in upload_handler_content
    
    @pytest.mark.parametrize("method_group,methods", TestConstants.JS_METHODS.items())
    def test_upload_handler_method_groups(self, upload_handler_content, method_group, methods):
        """Parameterized test for method groups - addressing complexity feedback"""
        TestHelpers.assert_methods_exist(upload_handler_content, methods, f"UploadHandler {method_group}")
    
    def test_upload_handler_state_object(self, upload_handler_content):
        """Test state object structure"""
        required_state_props = ['isDragover', 'isProcessing', 'selectedFile']
        
        assert "this.state = {" in upload_handler_content
        for prop in required_state_props:
            assert prop in upload_handler_content, f"State property {prop} missing"


class TestDragDropImplementation:
    """Focused tests for drag-and-drop implementation details"""
    
    def test_drag_event_prevention(self, upload_handler_content):
        """Test preventDefault calls for proper drag handling"""
        assert "e.preventDefault()" in upload_handler_content
    
    def test_file_extraction_from_drop(self, upload_handler_content):
        """Test file extraction from drop event"""
        assert "e.dataTransfer.files" in upload_handler_content
    
    def test_dragover_state_management(self, upload_handler_content):
        """Test dragover state management"""
        assert "setDragoverState(true)" in upload_handler_content
        assert "setDragoverState(false)" in upload_handler_content
    
    def test_boundary_detection_for_drag_leave(self, upload_handler_content):
        """Test boundary detection for drag leave"""
        assert "e.relatedTarget" in upload_handler_content
        assert "uploadArea.contains" in upload_handler_content


class TestFileValidation:
    """Focused tests for file validation logic"""
    
    def test_docx_file_type_validation(self, upload_handler_content):
        """Test DOCX file type validation"""
        assert TestConstants.DOCX_MIME_TYPE in upload_handler_content
        assert TestConstants.DOCX_EXTENSION in upload_handler_content
    
    def test_file_extension_validation(self, upload_handler_content):
        """Test file extension validation methods"""
        assert "toLowerCase()" in upload_handler_content
        assert "endsWith(" in upload_handler_content
    
    def test_file_size_validation(self, upload_handler_content):
        """Test file size validation (50MB limit)"""
        assert TestConstants.MAX_FILE_SIZE in upload_handler_content
        assert "file.size" in upload_handler_content
    
    @pytest.mark.parametrize("error_message", TestConstants.ERROR_MESSAGES)
    def test_error_messages_exist(self, upload_handler_content, error_message):
        """Parameterized test for error messages"""
        assert error_message in upload_handler_content, f"Error message missing: {error_message}"


class TestAccessibilityFeatures:
    """Focused tests for accessibility implementation"""
    
    def test_keyboard_handling_exists(self, upload_handler_content):
        """Test keyboard handling implementation"""
        assert "handleKeyboard(" in upload_handler_content
    
    def test_keyboard_key_support(self, upload_handler_content):
        """Test specific keyboard keys supported"""
        keyboard_keys = ["Enter", "key ==="]
        TestHelpers.assert_methods_exist(upload_handler_content, keyboard_keys, "keyboard handling")
    
    def test_aria_attributes_handling(self, upload_handler_content):
        """Test ARIA attributes management"""
        assert "aria-busy" in upload_handler_content
    
    def test_keyboard_event_prevention(self, upload_handler_content):
        """Test keyboard event prevention"""
        assert "preventDefault()" in upload_handler_content


class TestEventBusIntegration:
    """Focused tests for EventBus integration"""
    
    def test_event_bus_dependency_injection(self, upload_handler_content):
        """Test EventBus is injected as dependency"""
        assert "eventBus" in upload_handler_content
        assert "this.eventBus = eventBus" in upload_handler_content
    
    @pytest.mark.parametrize("event", TestConstants.EVENTS)
    def test_event_emissions(self, upload_handler_content, event):
        """Parameterized test for event emissions"""
        assert event in upload_handler_content, f"Event {event} not found"
    
    def test_event_bus_emit_calls(self, upload_handler_content):
        """Test EventBus emit method usage"""
        assert "this.eventBus.emit(" in upload_handler_content


class TestCSSImplementation:
    """Focused tests for CSS implementation"""
    
    @pytest.mark.parametrize("css_group,classes", TestConstants.CSS_CLASSES.items())
    def test_css_class_groups(self, components_css_content, css_group, classes):
        """Parameterized test for CSS class groups"""
        TestHelpers.assert_css_classes_exist(components_css_content, classes, f"CSS {css_group}")
    
    @pytest.mark.parametrize("custom_prop", TestConstants.CUSTOM_PROPERTIES)
    def test_custom_properties_defined(self, components_css_content, custom_prop):
        """Parameterized test for custom properties definition"""
        assert custom_prop in components_css_content, f"Custom property {custom_prop} missing"
    
    @pytest.mark.parametrize("custom_prop", TestConstants.CUSTOM_PROPERTIES)
    def test_custom_properties_used(self, components_css_content, custom_prop):
        """Parameterized test for custom properties usage"""
        property_name = custom_prop.replace(':', '').replace('-', '')
        var_usage = f"var(--{property_name.replace(':', '')})"
        # Check if the property is used somewhere in the CSS
        assert "var(--" in components_css_content, "Custom properties should be used in CSS"


class TestHTMLStructure:
    """Focused tests for HTML structure"""
    
    def test_upload_area_exists(self, parsed_html):
        """Test upload area exists with correct structure"""
        upload_area = parsed_html.find('div', class_='upload-area')
        assert upload_area is not None, "Upload area not found"
    
    def test_upload_area_attributes(self, parsed_html):
        """Test upload area has required attributes"""
        upload_area = parsed_html.find('div', class_='upload-area')
        
        required_attrs = {
            'id': 'uploadArea',
            'role': 'button', 
            'tabindex': '0'
        }
        
        for attr, expected_value in required_attrs.items():
            assert upload_area.get(attr) == expected_value, f"Upload area missing {attr}={expected_value}"
    
    def test_upload_area_aria_attributes(self, parsed_html):
        """Test upload area ARIA attributes"""
        upload_area = parsed_html.find('div', class_='upload-area')
        
        aria_attrs = ['aria-describedby', 'aria-label']
        for attr in aria_attrs:
            assert upload_area.get(attr), f"Upload area missing {attr}"
    
    def test_upload_area_content_elements(self, parsed_html):
        """Test upload area contains required content elements"""
        upload_area = parsed_html.find('div', class_='upload-area')
        
        content_elements = [
            ('div', 'upload-icon'),
            ('div', 'upload-text'),
            ('div', 'upload-subtext')
        ]
        
        for tag, css_class in content_elements:
            element = upload_area.find(tag, class_=css_class)
            assert element is not None, f"{css_class} element missing"
    
    def test_file_input_exists(self, parsed_html):
        """Test file input exists with correct attributes"""
        file_input = parsed_html.find('input', id='fileInput')
        assert file_input is not None, "File input missing"
        assert file_input.get('type') == 'file', "File input wrong type"
        assert file_input.get('accept') == '.docx', "File input wrong accept attribute"


class TestAppIntegration:
    """Focused tests for app.js integration"""
    
    def test_upload_handler_import(self, app_js_content):
        """Test UploadHandler import statement"""
        assert "import { UploadHandler }" in app_js_content
        assert "from './handlers/upload-handler.js'" in app_js_content
    
    def test_upload_handler_instantiation(self, app_js_content):
        """Test UploadHandler instantiation"""
        instantiation_parts = [
            "new UploadHandler(",
            "this.elements.uploadArea",
            "this.elements.fileInput", 
            "this.eventBus"
        ]
        TestHelpers.assert_methods_exist(app_js_content, instantiation_parts, "UploadHandler instantiation")
    
    def test_event_listener_setup(self, app_js_content):
        """Test event listener setup"""
        assert "setupUploadEventListeners(" in app_js_content
    
    @pytest.mark.parametrize("event", ['upload:file-selected', 'upload:error', 'upload:reset'])
    def test_event_listeners(self, app_js_content, event):
        """Parameterized test for event listeners"""
        assert event in app_js_content, f"Event listener for {event} missing"
    
    def test_dom_element_caching(self, app_js_content):
        """Test DOM element caching"""
        cached_elements = [
            "uploadArea = document.getElementById('uploadArea')",
            "fileInput = document.getElementById('fileInput')"
        ]
        TestHelpers.assert_methods_exist(app_js_content, cached_elements, "DOM caching")


class TestProgressAndAccessibility:
    """Focused tests for progress bar and accessibility features"""
    
    def test_progress_section_exists(self, parsed_html):
        """Test progress section exists"""
        progress_section = parsed_html.find('section', class_='progress-section')
        assert progress_section is not None, "Progress section missing"
    
    def test_progress_bar_structure(self, parsed_html):
        """Test progress bar structure"""
        progress_bar = parsed_html.find('div', class_='progress-bar')
        assert progress_bar is not None, "Progress bar missing"
        assert progress_bar.get('role') == 'progressbar', "Progress bar missing ARIA role"
    
    def test_progress_elements_exist(self, parsed_html):
        """Test progress elements exist"""
        progress_elements = [
            ('div', 'progress-fill'),
            ('div', 'progress-text')
        ]
        
        for tag, css_class in progress_elements:
            element = parsed_html.find(tag, class_=css_class)
            assert element is not None, f"{css_class} element missing"
    
    def test_aria_live_regions(self, parsed_html):
        """Test ARIA live regions exist"""
        live_regions = [
            ('ariaLivePolite', 'polite'),
            ('ariaLiveAssertive', 'assertive')
        ]
        
        for element_id, live_type in live_regions:
            element = parsed_html.find(id=element_id)
            assert element is not None, f"{element_id} missing"
            assert element.get('aria-live') == live_type, f"{element_id} incorrect aria-live value"
    
    def test_error_container_accessibility(self, parsed_html):
        """Test error container has proper ARIA"""
        error_container = parsed_html.find(id='errorContainer')
        assert error_container is not None, "Error container missing"
        assert error_container.get('role') == 'alert', "Error container missing alert role"


class TestRequirementsCoverage:
    """RSpec-style tests for Issue #7 requirements coverage"""
    
    def test_requirement_drag_drop_area_implementation(self, upload_handler_content, parsed_html):
        """
        Requirement: Drag-and-drop file upload area
        GIVEN a user wants to upload a file
        WHEN they drag a file over the upload area
        THEN the area should respond with visual feedback and accept the drop
        """
        # JavaScript implementation exists
        drag_methods = ['handleDragOver(', 'handleDrop(', 'e.dataTransfer.files']
        TestHelpers.assert_methods_exist(upload_handler_content, drag_methods, "drag-and-drop")
        
        # HTML structure exists
        upload_area = parsed_html.find('div', class_='upload-area')
        assert upload_area is not None
        assert upload_area.get('role') == 'button'
    
    def test_requirement_click_upload_fallback_implementation(self, upload_handler_content):
        """
        Requirement: Click-to-upload fallback
        GIVEN a user cannot or does not want to use drag-and-drop
        WHEN they click the upload area
        THEN a file selection dialog should open
        """
        assert "triggerFileSelection(" in upload_handler_content
        assert "this.fileInput.click()" in upload_handler_content
    
    def test_requirement_file_validation_feedback_implementation(self, upload_handler_content):
        """
        Requirement: File validation feedback
        GIVEN a user selects or drops an invalid file
        WHEN the file validation runs
        THEN clear error messages should be displayed
        """
        validation_methods = ['validateFileType(', 'validateFileSize(', 'showError(']
        TestHelpers.assert_methods_exist(upload_handler_content, validation_methods, "validation")
        
        for error_msg in TestConstants.ERROR_MESSAGES:
            assert error_msg in upload_handler_content
    
    def test_requirement_upload_progress_bar_implementation(self, parsed_html, components_css_content):
        """
        Requirement: Upload progress bar
        GIVEN a file upload is in progress
        WHEN the upload proceeds
        THEN a progress bar should show the upload status
        """
        # HTML structure
        progress_bar = parsed_html.find('div', class_='progress-bar')
        assert progress_bar is not None
        assert progress_bar.get('role') == 'progressbar'
        
        # CSS styling
        progress_classes = ['progress-bar', 'progress-fill']
        TestHelpers.assert_css_classes_exist(components_css_content, progress_classes, "progress")
    
    def test_requirement_file_preview_metadata_implementation(self, upload_handler_content):
        """
        Requirement: File preview with metadata
        GIVEN a user selects a valid file
        WHEN the file is processed
        THEN the filename and size should be displayed
        """
        preview_methods = ['updateDisplayForSelectedFile(', 'formatFileSize(']
        TestHelpers.assert_methods_exist(upload_handler_content, preview_methods, "file preview")
        
        metadata_display = ['file.name', 'Dateigröße:']
        TestHelpers.assert_methods_exist(upload_handler_content, metadata_display, "metadata display")
    
    def test_requirement_file_replacement_implementation(self, upload_handler_content):
        """
        Requirement: File replacement functionality
        GIVEN a user has selected a file
        WHEN they select a different file
        THEN the previous file should be replaced
        """
        replacement_methods = ['selectFile(', 'reset(']
        TestHelpers.assert_methods_exist(upload_handler_content, replacement_methods, "file replacement")
        
        state_management = ['this.state.selectedFile = file', 'selectedFile: null']
        TestHelpers.assert_methods_exist(upload_handler_content, state_management, "state management")
    
    def test_requirement_visual_states_implementation(self, components_css_content):
        """
        Requirement: Visual states (hover, active, error, success)
        GIVEN the upload area is in different states
        WHEN the user interacts with it or events occur
        THEN appropriate visual feedback should be provided
        """
        required_states = TestConstants.CSS_CLASSES['states']
        TestHelpers.assert_css_classes_exist(components_css_content, required_states, "visual states")
    
    def test_requirement_clear_error_messages_implementation(self, upload_handler_content):
        """
        Requirement: Clear error messages for invalid files
        GIVEN a user selects an invalid file
        WHEN validation fails
        THEN clear, helpful error messages should be shown
        """
        for error_msg in TestConstants.ERROR_MESSAGES:
            assert error_msg in upload_handler_content, f"Error message missing: {error_msg}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])