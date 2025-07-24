#!/usr/bin/env python3
"""
Test script for the file upload API endpoint
Tests various scenarios to ensure proper functionality
"""

import requests
import tempfile
import os
from pathlib import Path

def create_test_docx():
    """Create a minimal valid DOCX file for testing"""
    # This creates a basic ZIP structure that mimics a DOCX file
    import zipfile
    
    temp_file = tempfile.NamedTemporaryFile(suffix='.docx', delete=False)
    
    with zipfile.ZipFile(temp_file.name, 'w') as zip_file:
        # Required DOCX structure
        zip_file.writestr('[Content_Types].xml', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>''')
        
        zip_file.writestr('_rels/.rels', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>''')
        
        zip_file.writestr('word/document.xml', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r>
                <w:t>Test document for upload API</w:t>
            </w:r>
        </w:p>
    </w:body>
</w:document>''')
    
    return temp_file.name

def test_upload_api():
    """Test the upload API endpoint"""
    base_url = "http://localhost:5000/api/v1"
    
    print("Testing File Upload API")
    print("=" * 50)
    
    # Test 1: Get upload info
    print("\n1. Testing upload info endpoint...")
    try:
        response = requests.get(f"{base_url}/upload/info")
        if response.status_code == 200:
            print("✅ Upload info endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Upload info failed: {response.status_code}")
    except requests.ConnectionError:
        print("❌ Cannot connect to server. Is Flask app running on port 5000?")
        return
    
    # Test 2: Upload valid DOCX file
    print("\n2. Testing valid DOCX upload...")
    test_file = create_test_docx()
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test_document.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            response = requests.post(f"{base_url}/upload", files=files)
            
        if response.status_code == 200:
            print("✅ Valid DOCX upload successful")
            result = response.json()
            print(f"   File ID: {result.get('file_id')}")
            print(f"   Size: {result.get('size_mb')} MB")
            
            # Test cleanup
            file_id = result.get('file_id')
            if file_id:
                print("\n3. Testing file cleanup...")
                cleanup_response = requests.delete(f"{base_url}/upload/{file_id}/cleanup")
                if cleanup_response.status_code == 200:
                    print("✅ File cleanup successful")
                else:
                    print(f"❌ File cleanup failed: {cleanup_response.status_code}")
        else:
            print(f"❌ Valid DOCX upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    finally:
        # Clean up test file
        os.unlink(test_file)
    
    # Test 3: Upload invalid file (text file)
    print("\n4. Testing invalid file upload...")
    try:
        files = {'file': ('test.txt', b'This is not a DOCX file', 'text/plain')}
        response = requests.post(f"{base_url}/upload", files=files)
        
        if response.status_code == 400:
            print("✅ Invalid file correctly rejected")
            print(f"   Error: {response.json().get('message')}")
        else:
            print(f"❌ Invalid file not rejected properly: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing invalid file: {e}")
    
    # Test 4: No file upload
    print("\n5. Testing no file upload...")
    try:
        response = requests.post(f"{base_url}/upload")
        
        if response.status_code == 400:
            print("✅ No file upload correctly rejected")
            print(f"   Error: {response.json().get('message')}")
        else:
            print(f"❌ No file upload not rejected properly: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing no file upload: {e}")
    
    print("\n" + "=" * 50)
    print("API testing complete!")

if __name__ == "__main__":
    test_upload_api()