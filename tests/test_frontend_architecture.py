"""
Tests for the modern frontend architecture implementation
Tests the JavaScript modules, CSS structure, and overall frontend functionality
"""

import pytest
import requests
import time
from pathlib import Path
from bs4 import BeautifulSoup
import re


class TestFrontendArchitecture:
    """Test suite for modern frontend architecture"""
    
    @pytest.fixture
    def base_url(self):
        """Base URL for testing"""
        return "http://localhost:8000"
    
    @pytest.fixture
    def static_path(self):
        """Path to static files"""
        return Path(__file__).parent.parent / "web" / "static"
    
    def test_static_file_structure(self, static_path):
        """Test that all required static files exist with correct structure"""
        # Test CSS files exist
        css_files = [
            "css/main.css",
            "css/components.css", 
            "css/themes.css",
            "css/responsive.css"
        ]
        for css_file in css_files:
            assert (static_path / css_file).exists(), f"Missing CSS file: {css_file}"
        
        # Test JavaScript files exist
        js_files = [
            "js/app.js",
            "js/modules/theme-manager.js",
            "js/handlers/upload-handler.js",
            "js/utils/accessibility.js",
            "js/utils/dom-utils.js",
            "js/utils/event-bus.js"
        ]
        for js_file in js_files:
            assert (static_path / js_file).exists(), f"Missing JS file: {js_file}"
        
        # Test HTML structure
        assert (static_path / "index.html").exists(), "Missing index.html"
    
    def test_css_custom_properties(self, static_path):
        """Test that CSS files use custom properties instead of magic numbers"""
        components_css = (static_path / "css/components.css").read_text()
        
        # Test that component-specific custom properties are defined
        assert "--upload-icon-size:" in components_css
        assert "--upload-gradient-angle:" in components_css
        assert "--progress-height:" in components_css
        assert "--button-hover-scale:" in components_css
        
        # Test that custom properties are used instead of magic numbers
        assert "var(--upload-icon-size)" in components_css
        assert "var(--upload-gradient-angle)" in components_css
        assert "var(--progress-height)" in components_css
    
    def test_javascript_module_structure(self, static_path):
        """Test JavaScript ES6 module structure and imports"""
        app_js = (static_path / "js/app.js").read_text()
        
        # Test ES6 imports
        assert "import { ThemeManager }" in app_js
        assert "import { EventBus }" in app_js
        assert "import { UploadHandler }" in app_js
        
        # Test class structure
        assert "class KorrekturtoolApp" in app_js
        
        # Test method decomposition
        assert "initializeDOMCache()" in app_js
        assert "cacheMainSections()" in app_js
        assert "cacheFormElements()" in app_js
        assert "cacheProgressElements()" in app_js
        assert "cacheMessageContainers()" in app_js
    
    def test_upload_handler_separation(self, static_path):
        """Test that UploadHandler follows Tell, Don't Ask principle"""
        upload_handler = (static_path / "js/handlers/upload-handler.js").read_text()
        
        # Test class exists and exports
        assert "export class UploadHandler" in upload_handler
        
        # Test encapsulated behavior methods
        assert "triggerFileSelection()" in upload_handler
        assert "handleDragOver(" in upload_handler
        assert "handleDrop(" in upload_handler
        assert "validateFileType(" in upload_handler
        assert "setProcessingState(" in upload_handler
        
        # Test state management
        assert "this.state = {" in upload_handler
    
    def test_theme_manager_simplification(self, static_path):
        """Test that ThemeManager uses simplified theme cycling"""
        theme_manager = (static_path / "js/modules/theme-manager.js").read_text()
        
        # Test theme order array exists
        assert "this.themeOrder = [" in theme_manager
        
        # Test simplified cycling logic
        cycle_theme_method = re.search(
            r'cycleTheme\(\) \{([^}]+)\}', 
            theme_manager, 
            re.DOTALL
        )
        assert cycle_theme_method, "cycleTheme method not found"
        
        # Should not contain switch statement
        cycle_code = cycle_theme_method.group(1)
        assert "switch" not in cycle_code, "Theme cycling still uses switch statement"
        assert "indexOf" in cycle_code, "Should use array-based cycling"
    
    def test_html_semantic_structure(self, static_path):
        """Test HTML semantic structure and accessibility"""
        html_content = (static_path / "index.html").read_text()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Test semantic HTML elements
        assert soup.find('main'), "Missing main element"
        assert soup.find('header') or soup.find('[role="banner"]'), "Missing header/banner"
        assert soup.find('footer') or soup.find('[role="contentinfo"]'), "Missing footer"
        
        # Test accessibility features
        assert soup.find('a', class_='skip-link'), "Missing skip link"
        assert soup.find(attrs={'aria-live': True}), "Missing ARIA live regions"
        
        # Test meta tags
        assert soup.find('meta', attrs={'name': 'viewport'}), "Missing viewport meta tag"
        assert soup.find('meta', attrs={'name': 'description'}), "Missing description meta tag"
    
    @pytest.mark.skipif(
        not requests.get("http://localhost:8000", timeout=1).status_code == 200,
        reason="Web server not running"
    )
    def test_web_application_loads(self, base_url):
        """Test that the web application loads successfully"""
        try:
            response = requests.get(base_url, timeout=5)
            assert response.status_code == 200
            
            # Test content type
            assert 'text/html' in response.headers.get('content-type', '')
            
            # Test that page contains expected elements
            soup = BeautifulSoup(response.text, 'html.parser')
            assert soup.find('title'), "Missing page title"
            assert 'Korrekturtool' in soup.find('title').text
            
        except requests.exceptions.RequestException:
            pytest.skip("Web server not available for testing")
    
    @pytest.mark.skipif(
        not requests.get("http://localhost:8000", timeout=1).status_code == 200,
        reason="Web server not running"
    )
    def test_static_files_serve_correctly(self, base_url):
        """Test that static files are served with correct content types"""
        static_files = [
            ("/static/css/main.css", "text/css"),
            ("/static/js/app.js", "javascript"),
            ("/static/js/modules/theme-manager.js", "javascript")
        ]
        
        try:
            for file_path, expected_content_type in static_files:
                response = requests.get(f"{base_url}{file_path}", timeout=5)
                assert response.status_code == 200
                assert expected_content_type in response.headers.get('content-type', '')
                
        except requests.exceptions.RequestException:
            pytest.skip("Web server not available for testing")
    
    @pytest.mark.skipif(
        not requests.get("http://localhost:8000/api/v1/info", timeout=1).status_code == 200,
        reason="API server not running"
    )
    def test_api_connectivity(self, base_url):
        """Test that the API is accessible and returns expected format"""
        try:
            response = requests.get(f"{base_url}/api/v1/info", timeout=5)
            assert response.status_code == 200
            
            data = response.json()
            assert "name" in data
            assert "version" in data
            assert "endpoints" in data
            
        except requests.exceptions.RequestException:
            pytest.skip("API server not available for testing")


class TestFrontendCodeQuality:
    """Test suite for frontend code quality and architecture principles"""
    
    @pytest.fixture
    def static_path(self):
        """Path to static files"""
        return Path(__file__).parent.parent / "web" / "static"
    
    def test_single_responsibility_principle(self, static_path):
        """Test that classes follow Single Responsibility Principle"""
        app_js = (static_path / "js/app.js").read_text()
        
        # Test that constructor is focused
        constructor_match = re.search(
            r'constructor\(\) \{([^}]+(?:\{[^}]*\}[^}]*)*)\}',
            app_js,
            re.DOTALL
        )
        
        if constructor_match:
            constructor_code = constructor_match.group(1)
            # Constructor should not contain complex logic
            assert "cacheElements" not in constructor_code, "Constructor should not cache elements directly"
            assert "addEventListener" not in constructor_code, "Constructor should not set up events directly"
    
    def test_method_length_compliance(self, static_path):
        """Test that methods follow reasonable length guidelines"""
        js_files = [
            "js/app.js",
            "js/modules/theme-manager.js", 
            "js/handlers/upload-handler.js"
        ]
        
        for js_file in js_files:
            content = (static_path / js_file).read_text()
            
            # Find all methods and check their length
            methods = re.findall(
                r'(\w+)\([^)]*\)\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}',
                content,
                re.DOTALL
            )
            
            for method_name, method_body in methods:
                # Skip constructors and very simple getters
                if method_name in ['constructor', 'get', 'set']:
                    continue
                    
                # Count logical lines (excluding comments and empty lines)
                logical_lines = [
                    line.strip() for line in method_body.split('\n')
                    if line.strip() and not line.strip().startswith('//')
                ]
                
                # Methods should generally be under 20 logical lines
                assert len(logical_lines) < 25, f"Method {method_name} in {js_file} is too long ({len(logical_lines)} lines)"
    
    def test_event_driven_architecture(self, static_path):
        """Test that components use event-driven communication"""
        app_js = (static_path / "js/app.js").read_text()
        upload_handler = (static_path / "js/handlers/upload-handler.js").read_text()
        
        # Test EventBus usage
        assert "this.eventBus = new EventBus()" in app_js
        assert "this.eventBus.on(" in app_js
        assert "this.eventBus.emit(" in upload_handler
        
        # Test loose coupling through events
        assert "upload:file-selected" in app_js
        assert "upload:error" in upload_handler
    
    def test_accessibility_compliance_features(self, static_path):
        """Test that accessibility features are properly implemented"""
        accessibility_js = (static_path / "js/utils/accessibility.js").read_text()
        html_content = (static_path / "index.html").read_text()
        
        # Test ARIA features in JavaScript
        assert "aria-live" in accessibility_js
        assert "aria-label" in accessibility_js
        assert "aria-hidden" in accessibility_js
        
        # Test screen reader support
        assert "announce(" in accessibility_js
        assert "liveRegions" in accessibility_js
        
        # Test keyboard navigation
        assert "trapFocus(" in accessibility_js
        assert "handleTabKey(" in accessibility_js
        
        # Test HTML accessibility
        soup = BeautifulSoup(html_content, 'html.parser')
        assert soup.find(attrs={'aria-live': 'polite'}), "Missing polite live region"
        assert soup.find(attrs={'aria-live': 'assertive'}), "Missing assertive live region"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])