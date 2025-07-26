#!/usr/bin/env python3
"""
Unit tests for the Flask web application
"""

import pytest
import json
import os
from pathlib import Path
import sys

# Add the web directory to the path  
sys.path.append(str(Path(__file__).parent.parent))

from web.app import create_app
from web.config import TestingConfig

@pytest.fixture
def app():
    """Create application for testing"""
    app, socketio = create_app(TestingConfig, validate_startup=False)
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

class TestWebApplication:
    """Test suite for the web application"""
    
    def test_health_endpoint(self, client):
        """Test the health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'German Thesis Correction Tool Web API'
        assert data['version'] == '1.0.0'
    
    def test_api_info_endpoint(self, client):
        """Test the API info endpoint"""
        response = client.get('/api/v1/info')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['name'] == 'German Thesis Correction Tool API'
        assert data['version'] == '1.0.0'
        assert 'endpoints' in data
        assert 'health' in data['endpoints']
    
    def test_index_page(self, client):
        """Test the index page serves HTML"""
        response = client.get('/')
        assert response.status_code == 200
        assert 'text/html' in response.headers.get('Content-Type', '')
        assert b'Korrekturtool' in response.data
    
    def test_static_file_serving(self, client):
        """Test static file serving"""
        response = client.get('/static/index.html')
        assert response.status_code == 200
        assert 'text/html' in response.headers.get('Content-Type', '')
    
    def test_404_error_handler(self, client):
        """Test 404 error handling"""
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 404
        
        data = response.get_json()
        assert data['error'] == 'Not found'
        assert 'message' in data
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.get('/health')
        assert response.status_code == 200
        # CORS headers should be present in response
        assert 'Access-Control-Allow-Origin' in response.headers
    
    def test_app_configuration(self, app):
        """Test application configuration"""
        assert app.config['TESTING'] is True
        assert app.config['DEBUG'] is True
        assert app.config['MAX_CONTENT_LENGTH'] == 1024 * 1024  # 1MB for testing
    
    def test_json_response_format(self, client):
        """Test JSON response format consistency"""
        response = client.get('/api/v1/info')
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'application/json'
        
        # Ensure response is valid JSON
        data = response.get_json()
        assert isinstance(data, dict)
        
    def test_environment_variables(self, app):
        """Test environment variable handling"""
        # Testing config should override defaults
        assert app.config['TESTING'] is True
        assert 'SECRET_KEY' in app.config
        
    def test_file_upload_configuration(self, app):
        """Test file upload configuration"""
        assert app.config['MAX_CONTENT_LENGTH'] == 1024 * 1024  # 1MB for testing
        assert app.config['ALLOWED_EXTENSIONS'] == {'docx'}
        assert 'UPLOAD_FOLDER' in app.config
        
    def test_cors_configuration(self, app):
        """Test CORS configuration"""
        assert 'CORS_ORIGINS' in app.config
        assert isinstance(app.config['CORS_ORIGINS'], list)
        
    def test_google_api_configuration(self, app):
        """Test Google API configuration is available"""
        # Should have GOOGLE_API_KEY key (even if None in testing)
        assert 'GOOGLE_API_KEY' in app.config