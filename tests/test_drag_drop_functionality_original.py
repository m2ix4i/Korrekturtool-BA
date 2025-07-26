"""
Test suite for drag-and-drop file upload functionality (Issue #7)
Tests the upload handler implementation and UI components
"""

import pytest
from pathlib import Path
from bs4 import BeautifulSoup
import re


class TestDragDropFileUpload:
    """Test suite for issue #7 drag-and-drop file upload functionality"""
    
    @pytest.fixture
    def static_path(self):
        """Path to static files"""
        return Path(__file__).parent.parent / "web" / "static"
    
    def test_upload_handler_file_exists(self, static_path):
        """Test that UploadHandler JavaScript file exists"""
        upload_handler_path = static_path / "js/handlers/upload-handler.js"
        assert upload_handler_path.exists(), "UploadHandler file missing"
    
    def test_upload_handler_class_structure(self, static_path):
        """Test UploadHandler class structure and methods"""
        upload_handler = (static_path / "js/handlers/upload-handler.js").read_text()
        
        # Test class exists and exports
        assert "export class UploadHandler" in upload_handler
        
        # Test drag-and-drop methods exist
        assert "handleDragOver(" in upload_handler
        assert "handleDragLeave(" in upload_handler  
        assert "handleDrop(" in upload_handler
        
        # Test file selection methods exist
        assert "triggerFileSelection(" in upload_handler
        assert "handleFileSelection(" in upload_handler
        assert "selectFile(" in upload_handler
        
        # Test validation methods exist
        assert "validateFileType(" in upload_handler
        assert "validateFileSize(" in upload_handler
        
        # Test state management methods exist
        assert "setDragoverState(" in upload_handler
        assert "setProcessingState(" in upload_handler
        assert "reset(" in upload_handler
        
        # Test display methods exist
        assert "updateDisplay(" in upload_handler
        assert "updateDisplayForSelectedFile(" in upload_handler
        assert "showError(" in upload_handler
    
    def test_upload_handler_drag_drop_implementation(self, static_path):
        """Test drag-and-drop event handling implementation"""
        upload_handler = (static_path / "js/handlers/upload-handler.js").read_text()
        
        # Test preventDefault calls for proper drag handling
        assert "e.preventDefault()" in upload_handler
        
        # Test file extraction from drop event
        assert "e.dataTransfer.files" in upload_handler
        
        # Test dragover state management
        assert "setDragoverState(true)" in upload_handler
        assert "setDragoverState(false)" in upload_handler
        
        # Test boundary detection for drag leave
        assert "e.relatedTarget" in upload_handler
        assert "uploadArea.contains" in upload_handler
    
    def test_upload_handler_file_validation(self, static_path):
        """Test file validation logic"""
        upload_handler = (static_path / "js/handlers/upload-handler.js").read_text()
        
        # Test DOCX file type validation
        assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in upload_handler
        assert ".docx" in upload_handler
        assert "toLowerCase()" in upload_handler
        assert "endsWith(" in upload_handler
        
        # Test file size validation (50MB limit)
        assert "50 * 1024 * 1024" in upload_handler
        assert "file.size" in upload_handler
        
        # Test error messages
        assert "Nur DOCX-Dateien werden unterstützt" in upload_handler
        assert "Datei ist zu groß" in upload_handler
        assert "Maximum: 50 MB" in upload_handler
    
    def test_upload_handler_accessibility(self, static_path):
        """Test accessibility features in upload handler"""
        upload_handler = (static_path / "js/handlers/upload-handler.js").read_text()
        
        # Test keyboard handling
        assert "handleKeyboard(" in upload_handler
        assert "Enter" in upload_handler
        assert "key ===" in upload_handler
        
        # Test ARIA attributes
        assert "aria-busy" in upload_handler
        
        # Test event prevention for keyboard
        assert "preventDefault()" in upload_handler
    
    def test_upload_handler_state_management(self, static_path):
        """Test state management implementation"""
        upload_handler = (static_path / "js/handlers/upload-handler.js").read_text()
        
        # Test state object structure
        assert "this.state = {" in upload_handler
        assert "isDragover" in upload_handler
        assert "isProcessing" in upload_handler
        assert "selectedFile" in upload_handler
        
        # Test state getters
        assert "getState(" in upload_handler
        assert "hasFile:" in upload_handler
    
    def test_upload_handler_event_bus_integration(self, static_path):
        """Test EventBus integration for loose coupling"""
        upload_handler = (static_path / "js/handlers/upload-handler.js").read_text()
        
        # Test event emissions
        assert "this.eventBus.emit(" in upload_handler
        assert "upload:file-selected" in upload_handler
        assert "upload:error" in upload_handler
        assert "upload:reset" in upload_handler
        assert "upload:selection-triggered" in upload_handler
        
        # Test EventBus is passed to constructor
        assert "eventBus" in upload_handler
        assert "this.eventBus = eventBus" in upload_handler
    
    def test_upload_css_visual_states(self, static_path):
        """Test CSS visual states for drag-and-drop"""
        components_css = (static_path / "css/components.css").read_text()
        
        # Test upload area base styles
        assert ".upload-area" in components_css
        assert "border:" in components_css
        assert "dashed" in components_css
        assert "cursor: pointer" in components_css
        
        # Test hover and dragover states
        assert ".upload-area:hover" in components_css
        assert ".upload-area.dragover" in components_css
        assert "transform:" in components_css
        assert "scale(" in components_css
        
        # Test disabled state
        assert ".upload-area.disabled" in components_css
        assert "cursor: not-allowed" in components_css
        assert "opacity:" in components_css
        
        # Test error state
        assert "file-selected" in components_css or "error" in components_css
        
        # Test visual feedback elements
        assert ".upload-icon" in components_css
        assert ".upload-text" in components_css
        assert ".upload-subtext" in components_css
    
    def test_upload_html_structure(self, static_path):
        """Test HTML structure for upload area"""
        html_content = (static_path / "index.html").read_text()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Test upload area exists with correct structure
        upload_area = soup.find('div', class_='upload-area')
        assert upload_area is not None, "Upload area not found"
        assert upload_area.get('id') == 'uploadArea', "Upload area missing ID"
        assert upload_area.get('role') == 'button', "Upload area missing button role"
        assert upload_area.get('tabindex') == '0', "Upload area not keyboard accessible"
        
        # Test ARIA attributes
        assert upload_area.get('aria-describedby'), "Missing aria-describedby"
        assert upload_area.get('aria-label'), "Missing aria-label"
        
        # Test upload area content elements
        upload_icon = upload_area.find('div', class_='upload-icon')
        assert upload_icon is not None, "Upload icon missing"
        
        upload_text = upload_area.find('div', class_='upload-text')
        assert upload_text is not None, "Upload text missing"
        
        upload_subtext = upload_area.find('div', class_='upload-subtext')
        assert upload_subtext is not None, "Upload subtext missing"
        
        # Test file input exists
        file_input = soup.find('input', id='fileInput')
        assert file_input is not None, "File input missing"
        assert file_input.get('type') == 'file', "File input wrong type"
        assert file_input.get('accept') == '.docx', "File input wrong accept attribute"
    
    def test_app_js_upload_handler_integration(self, static_path):
        """Test UploadHandler integration in main app"""
        app_js = (static_path / "js/app.js").read_text()
        
        # Test import statement
        assert "import { UploadHandler }" in app_js
        assert "from './handlers/upload-handler.js'" in app_js
        
        # Test UploadHandler instantiation
        assert "new UploadHandler(" in app_js
        assert "this.elements.uploadArea" in app_js
        assert "this.elements.fileInput" in app_js
        assert "this.eventBus" in app_js
        
        # Test event listener setup
        assert "setupUploadEventListeners(" in app_js
        assert "upload:file-selected" in app_js
        assert "upload:error" in app_js
        assert "upload:reset" in app_js
        
        # Test DOM element caching
        assert "uploadArea = document.getElementById('uploadArea')" in app_js
        assert "fileInput = document.getElementById('fileInput')" in app_js
    
    def test_upload_handler_file_preview_functionality(self, static_path):
        """Test file preview with metadata display"""
        upload_handler = (static_path / "js/handlers/upload-handler.js").read_text()
        
        # Test file size formatting
        assert "formatFileSize(" in upload_handler
        assert "KB" in upload_handler
        assert "MB" in upload_handler
        assert "GB" in upload_handler
        
        # Test file display update
        assert "updateDisplayForSelectedFile(" in upload_handler
        assert "file.name" in upload_handler
        assert "file.size" in upload_handler
        
        # Test file metadata in display
        assert "Dateigröße:" in upload_handler
        assert "Bereit zur Verarbeitung" in upload_handler
    
    def test_upload_handler_error_handling(self, static_path):
        """Test comprehensive error handling"""
        upload_handler = (static_path / "js/handlers/upload-handler.js").read_text()
        
        # Test error display method
        assert "showError(" in upload_handler
        
        # Test visual error feedback
        assert "addClass(" in upload_handler and "error" in upload_handler
        assert "setTimeout(" in upload_handler
        assert "removeClass(" in upload_handler
        
        # Test specific error messages
        validation_errors = [
            "Nur DOCX-Dateien werden unterstützt",
            "Datei ist zu groß",
            "Maximum: 50 MB"
        ]
        
        for error_msg in validation_errors:
            assert error_msg in upload_handler, f"Error message missing: {error_msg}"
    
    def test_upload_handler_file_replacement(self, static_path):
        """Test file replacement functionality"""
        upload_handler = (static_path / "js/handlers/upload-handler.js").read_text()
        
        # Test that selectFile method can handle new files
        assert "selectFile(" in upload_handler
        assert "this.state.selectedFile = file" in upload_handler
        
        # Test reset functionality for file replacement
        assert "reset(" in upload_handler
        assert "selectedFile: null" in upload_handler
        assert "this.fileInput.value = ''" in upload_handler
        
        # Test state updates for new file selection
        assert "updateDisplayForSelectedFile(" in upload_handler
    
    def test_upload_custom_properties_usage(self, static_path):
        """Test that CSS uses custom properties instead of magic numbers"""
        components_css = (static_path / "css/components.css").read_text()
        
        # Test custom properties are defined
        assert "--upload-icon-size:" in components_css
        assert "--upload-gradient-angle:" in components_css
        assert "--upload-border-width:" in components_css
        assert "--upload-dragover-scale:" in components_css
        
        # Test custom properties are used
        assert "var(--upload-icon-size)" in components_css
        assert "var(--upload-gradient-angle)" in components_css
        assert "var(--upload-dragover-scale)" in components_css
    
    def test_upload_progress_structure_exists(self, static_path):
        """Test that progress bar structure exists for upload progress"""
        html_content = (static_path / "index.html").read_text()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Test progress section exists
        progress_section = soup.find('section', class_='progress-section')
        assert progress_section is not None, "Progress section missing"
        
        # Test progress bar exists
        progress_bar = soup.find('div', class_='progress-bar')
        assert progress_bar is not None, "Progress bar missing"
        assert progress_bar.get('role') == 'progressbar', "Progress bar missing ARIA role"
        
        # Test progress fill exists
        progress_fill = soup.find('div', class_='progress-fill')
        assert progress_fill is not None, "Progress fill missing"
        
        # Test progress text exists
        progress_text = soup.find('div', class_='progress-text')
        assert progress_text is not None, "Progress text missing"
    
    def test_upload_accessibility_live_regions(self, static_path):
        """Test ARIA live regions for screen reader announcements"""
        html_content = (static_path / "index.html").read_text()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Test ARIA live regions exist
        live_polite = soup.find(id='ariaLivePolite')
        assert live_polite is not None, "Polite live region missing"
        assert live_polite.get('aria-live') == 'polite', "Polite live region incorrect"
        
        live_assertive = soup.find(id='ariaLiveAssertive')
        assert live_assertive is not None, "Assertive live region missing"
        assert live_assertive.get('aria-live') == 'assertive', "Assertive live region incorrect"
        
        # Test error container has proper ARIA
        error_container = soup.find(id='errorContainer')
        assert error_container is not None, "Error container missing"
        assert error_container.get('role') == 'alert', "Error container missing alert role"


class TestDragDropRequirementsCoverage:
    """Test coverage of all Issue #7 requirements"""
    
    @pytest.fixture
    def static_path(self):
        """Path to static files"""
        return Path(__file__).parent.parent / "web" / "static"
    
    def test_requirement_1_drag_drop_area(self, static_path):
        """✅ Requirement: Drag-and-drop file upload area"""
        # HTML structure test
        html_content = (static_path / "index.html").read_text()
        assert 'class="upload-area"' in html_content
        assert 'role="button"' in html_content
        
        # JavaScript implementation test
        upload_handler = (static_path / "js/handlers/upload-handler.js").read_text()
        assert "handleDragOver(" in upload_handler
        assert "handleDrop(" in upload_handler
        assert "e.dataTransfer.files" in upload_handler
    
    def test_requirement_2_click_upload_fallback(self, static_path):
        """✅ Requirement: Click-to-upload fallback"""
        upload_handler = (static_path / "js/handlers/upload-handler.js").read_text()
        assert "triggerFileSelection(" in upload_handler
        assert "this.fileInput.click()" in upload_handler
        
        # Test click event listener setup
        assert "DOMUtils.on(this.uploadArea, 'click'" in upload_handler
    
    def test_requirement_3_file_validation_feedback(self, static_path):
        """✅ Requirement: File validation feedback"""
        upload_handler = (static_path / "js/handlers/upload-handler.js").read_text()
        assert "validateFileType(" in upload_handler
        assert "validateFileSize(" in upload_handler
        assert "showError(" in upload_handler
        assert "Nur DOCX-Dateien werden unterstützt" in upload_handler
    
    def test_requirement_4_upload_progress_bar(self, static_path):
        """✅ Requirement: Upload progress bar"""
        html_content = (static_path / "index.html").read_text()
        assert 'class="progress-bar"' in html_content
        assert 'role="progressbar"' in html_content
        
        css_content = (static_path / "css/components.css").read_text()
        assert ".progress-bar" in css_content
        assert ".progress-fill" in css_content
    
    def test_requirement_5_file_preview_metadata(self, static_path):
        """✅ Requirement: File preview with metadata"""
        upload_handler = (static_path / "js/handlers/upload-handler.js").read_text()
        assert "updateDisplayForSelectedFile(" in upload_handler
        assert "formatFileSize(" in upload_handler
        assert "file.name" in upload_handler
        assert "Dateigröße:" in upload_handler
    
    def test_requirement_6_file_replacement(self, static_path):
        """✅ Requirement: File replacement functionality"""
        upload_handler = (static_path / "js/handlers/upload-handler.js").read_text()
        assert "selectFile(" in upload_handler
        assert "reset(" in upload_handler
        assert "this.state.selectedFile = file" in upload_handler
    
    def test_requirement_7_visual_states(self, static_path):
        """✅ Requirement: Visual states (hover, active, error, success)"""
        css_content = (static_path / "css/components.css").read_text()
        assert ".upload-area:hover" in css_content
        assert ".upload-area.dragover" in css_content
        assert ".upload-area.disabled" in css_content
        assert "file-selected" in css_content
    
    def test_requirement_8_clear_error_messages(self, static_path):
        """✅ Requirement: Clear error messages for invalid files"""
        upload_handler = (static_path / "js/handlers/upload-handler.js").read_text()
        error_messages = [
            "Nur DOCX-Dateien werden unterstützt",
            "Datei ist zu groß. Maximum: 50 MB"
        ]
        for msg in error_messages:
            assert msg in upload_handler


if __name__ == "__main__":
    pytest.main([__file__, "-v"])