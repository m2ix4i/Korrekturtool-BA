"""
Comprehensive test suite for file upload API endpoint
Tests security, validation, error handling, and file management functionality
"""

import os
import io
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Flask testing
from flask import Flask
from werkzeug.datastructures import FileStorage

# Import the application and modules to test
from web.app import create_app
from web.config import TestingConfig
from web.utils.file_validation import (
    validate_file_extension, 
    validate_file_type_magic,
    validate_docx_structure,
    generate_secure_filename,
    is_file_size_valid,
    sanitize_filename,
    validate_upload_file,
    cleanup_file
)

class TestFileValidation:
    """Test file validation utilities"""
    
    def test_validate_file_extension_valid(self):
        """Test valid DOCX file extension validation"""
        assert validate_file_extension("document.docx") == True
        assert validate_file_extension("Document.DOCX") == True
        assert validate_file_extension("file.Docx") == True
    
    def test_validate_file_extension_invalid(self):
        """Test invalid file extension validation"""
        assert validate_file_extension("document.pdf") == False
        assert validate_file_extension("document.txt") == False
        assert validate_file_extension("document") == False
        assert validate_file_extension("") == False
        assert validate_file_extension(None) == False
    
    def test_generate_secure_filename(self):
        """Test secure filename generation"""
        filename1 = generate_secure_filename()
        filename2 = generate_secure_filename()
        
        # Should be different each time
        assert filename1 != filename2
        
        # Should end with .docx
        assert filename1.endswith('.docx')
        assert filename2.endswith('.docx')
        
        # Should be UUID format plus extension
        name_part = filename1.replace('.docx', '')
        assert len(name_part) == 36  # UUID length
        assert name_part.count('-') == 4  # UUID has 4 dashes
    
    def test_is_file_size_valid(self):
        """Test file size validation"""
        max_size = 50 * 1024 * 1024  # 50MB
        
        assert is_file_size_valid(1024, max_size) == True
        assert is_file_size_valid(max_size, max_size) == True
        assert is_file_size_valid(max_size + 1, max_size) == False
        assert is_file_size_valid(0, max_size) == False
        assert is_file_size_valid(-1, max_size) == False
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        assert sanitize_filename("document.docx") == "document.docx"
        assert sanitize_filename("/path/to/document.docx") == "document.docx"
        assert sanitize_filename("../../../etc/passwd") == "passwd"
        assert sanitize_filename("") == "unnamed_file.docx"
        assert sanitize_filename(None) == "unnamed_file.docx"
        
        # Test long filename truncation
        long_name = "a" * 300 + ".docx"
        sanitized = sanitize_filename(long_name)
        assert len(sanitized) <= 255
        assert sanitized.endswith('.docx')

class TestFileUploadAPI:
    """Test file upload API endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create test application"""
        app = create_app(TestingConfig)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def create_test_docx_file(self, filename="test.docx", content_size=1024):
        """Create a minimal valid DOCX file for testing"""
        # Create a minimal DOCX structure
        docx_content = b'PK\x03\x04' + b'minimal docx content' + b'\x00' * (content_size - 25)
        return io.BytesIO(docx_content), filename
    
    def create_invalid_file(self, filename="test.txt", content="invalid content"):
        """Create an invalid file for testing"""
        return io.BytesIO(content.encode()), filename
    
    def test_upload_endpoint_no_file(self, client):
        """Test upload endpoint with no file"""
        response = client.post('/api/v1/upload')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] == False
        assert 'No file provided' in data['message']
    
    def test_upload_endpoint_empty_file(self, client):
        """Test upload endpoint with empty file field"""
        response = client.post('/api/v1/upload', data={'file': (io.BytesIO(b''), '')})
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] == False
    
    @patch('web.utils.file_validation.validate_file_type_magic')
    @patch('web.utils.file_validation.validate_docx_structure')
    def test_upload_endpoint_valid_file(self, mock_validate_structure, mock_validate_magic, client, temp_dir):
        """Test upload endpoint with valid DOCX file"""
        # Mock the validation functions to return True
        mock_validate_magic.return_value = True
        mock_validate_structure.return_value = True
        
        # Create test file
        file_content, filename = self.create_test_docx_file()
        
        with patch('web.config.Config.UPLOAD_FOLDER', temp_dir):
            response = client.post('/api/v1/upload', data={
                'file': (file_content, filename, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            })
        
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] == True
        assert 'file_id' in data
        assert data['filename'] == filename
        assert data['size'] > 0
        assert 'File uploaded successfully' in data['message']
    
    def test_upload_endpoint_invalid_extension(self, client):
        """Test upload endpoint with invalid file extension"""
        file_content, filename = self.create_invalid_file("test.txt")
        
        response = client.post('/api/v1/upload', data={
            'file': (file_content, filename)
        })
        
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] == False
        assert 'Invalid file type' in data['message']
    
    @patch('web.utils.file_validation.validate_file_type_magic')
    def test_upload_endpoint_invalid_magic_type(self, mock_validate_magic, client):
        """Test upload endpoint with file that has correct extension but wrong magic type"""
        mock_validate_magic.return_value = False
        
        file_content, filename = self.create_test_docx_file()
        
        response = client.post('/api/v1/upload', data={
            'file': (file_content, filename)
        })
        
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] == False
        assert 'Invalid file format' in data['message']
    
    @patch('web.utils.file_validation.validate_file_type_magic')
    @patch('web.utils.file_validation.validate_docx_structure')
    def test_upload_endpoint_invalid_structure(self, mock_validate_structure, mock_validate_magic, client):
        """Test upload endpoint with file that has correct type but invalid DOCX structure"""
        mock_validate_magic.return_value = True
        mock_validate_structure.return_value = False
        
        file_content, filename = self.create_test_docx_file()
        
        response = client.post('/api/v1/upload', data={
            'file': (file_content, filename)
        })
        
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] == False
        assert 'Invalid DOCX file structure' in data['message']
    
    def test_upload_endpoint_file_too_large(self, client):
        """Test upload endpoint with file that exceeds size limit"""
        # Create a large file (larger than 1MB test limit)
        large_content = b'x' * (2 * 1024 * 1024)  # 2MB
        file_content = io.BytesIO(large_content)
        
        response = client.post('/api/v1/upload', data={
            'file': (file_content, 'large_file.docx')
        })
        
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] == False
        assert 'File too large' in data['message']
    
    def test_upload_endpoint_empty_file_content(self, client):
        """Test upload endpoint with empty file content"""
        empty_file = io.BytesIO(b'')
        
        response = client.post('/api/v1/upload', data={
            'file': (empty_file, 'empty.docx')
        })
        
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] == False
        assert 'File is empty' in data['message']
    
    @patch('web.utils.file_validation.validate_file_type_magic')
    @patch('web.utils.file_validation.validate_docx_structure')
    def test_cleanup_endpoint_success(self, mock_validate_structure, mock_validate_magic, client, temp_dir):
        """Test cleanup endpoint with valid file ID"""
        # Mock validations
        mock_validate_magic.return_value = True
        mock_validate_structure.return_value = True
        
        # First upload a file
        file_content, filename = self.create_test_docx_file()
        
        with patch('web.config.Config.UPLOAD_FOLDER', temp_dir):
            upload_response = client.post('/api/v1/upload', data={
                'file': (file_content, filename, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            })
            
            assert upload_response.status_code == 200
            file_id = upload_response.get_json()['file_id']
            
            # Verify file exists
            file_path = Path(temp_dir) / f"{file_id}.docx"
            assert file_path.exists()
            
            # Now test cleanup
            cleanup_response = client.delete(f'/api/v1/upload/{file_id}/cleanup')
            
            assert cleanup_response.status_code == 200
            
            data = cleanup_response.get_json()
            assert data['success'] == True
            assert 'cleaned up successfully' in data['message']
            
            # Verify file is removed
            assert not file_path.exists()
    
    def test_cleanup_endpoint_file_not_found(self, client, temp_dir):
        """Test cleanup endpoint with non-existent file ID"""
        fake_file_id = "non-existent-file-id"
        
        with patch('web.config.Config.UPLOAD_FOLDER', temp_dir):
            response = client.delete(f'/api/v1/upload/{fake_file_id}/cleanup')
            
            assert response.status_code == 404
            
            data = response.get_json()
            assert data['success'] == False
            assert 'File not found' in data['message']

class TestSecurityFeatures:
    """Test security features of the upload system"""
    
    @pytest.fixture
    def app(self):
        """Create test application"""
        return create_app(TestingConfig)
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_directory_traversal_prevention(self, client):
        """Test that directory traversal attacks are prevented"""
        malicious_filenames = [
            "../../../etc/passwd.docx",
            "..\\..\\windows\\system32\\config\\sam.docx",
            "/etc/passwd.docx",
            "C:\\Windows\\System32\\config\\sam.docx"
        ]
        
        for malicious_filename in malicious_filenames:
            file_content = io.BytesIO(b'malicious content')
            
            response = client.post('/api/v1/upload', data={
                'file': (file_content, malicious_filename)
            })
            
            # Should either fail validation or be sanitized
            # The filename should not contain path traversal elements
            if response.status_code == 200:
                # If it passes, the filename should be sanitized
                data = response.get_json()
                assert '../' not in data.get('filename', '')
                assert '..\\' not in data.get('filename', '')
                assert not data.get('filename', '').startswith('/')
                assert not data.get('filename', '').startswith('C:')
    
    def test_secure_filename_generation(self):
        """Test that generated filenames are secure"""
        for _ in range(10):
            filename = generate_secure_filename()
            
            # Should not contain path separators
            assert '/' not in filename
            assert '\\' not in filename
            assert '..' not in filename
            
            # Should be UUID format
            name_part = filename.replace('.docx', '')
            assert len(name_part) == 36
            assert name_part.count('-') == 4
    
    def test_file_size_limit_enforcement(self, client):
        """Test that file size limits are properly enforced"""
        # Test with file exactly at limit (1MB for testing config)
        limit_size = 1024 * 1024  # 1MB
        large_content = b'x' * (limit_size + 1)  # Just over limit
        
        response = client.post('/api/v1/upload', data={
            'file': (io.BytesIO(large_content), 'large.docx')
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'File too large' in data['message']

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.fixture
    def app(self):
        """Create test application"""
        return create_app(TestingConfig)
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_malformed_request(self, client):
        """Test handling of malformed requests"""
        # Test with no multipart data
        response = client.post('/api/v1/upload', data='not multipart')
        assert response.status_code == 400
    
    def test_api_info_endpoint(self, client):
        """Test that API info endpoint shows upload endpoint"""
        response = client.get('/api/v1/info')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'endpoints' in data
        assert '/api/v1/upload' in data['endpoints']['upload']
    
    @patch('web.utils.file_validation.validate_upload_file')
    def test_validation_exception_handling(self, mock_validate, client):
        """Test handling of validation exceptions"""
        # Mock validation to raise an exception
        mock_validate.side_effect = Exception("Validation error")
        
        file_content = io.BytesIO(b'test content')
        response = client.post('/api/v1/upload', data={
            'file': (file_content, 'test.docx')
        })
        
        assert response.status_code == 500
        data = response.get_json()
        assert data['success'] == False
        assert 'Internal server error' in data['error']

if __name__ == '__main__':
    pytest.main([__file__, '-v'])