#!/usr/bin/env python3
"""
Test script for the processing API endpoints
Tests the complete pipeline: upload → process → status → download
"""

import requests
import tempfile
import os
import time
import json
from pathlib import Path

def create_test_docx():
    """Create a minimal valid DOCX file for testing"""
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
                <w:t>This is a test document for the processing API. It contains some grammatical error and could be improve for better clarity and style.</w:t>
            </w:r>
        </w:p>
    </w:body>
</w:document>''')
    
    return temp_file.name

def test_processing_pipeline():
    """Test the complete processing pipeline"""
    base_url = "http://localhost:5000/api/v1"
    
    print("Testing Processing Pipeline")
    print("=" * 50)
    
    # Step 1: Upload file
    print("\n1. Testing file upload...")
    test_file = create_test_docx()
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test_document.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            upload_response = requests.post(f"{base_url}/upload", files=files)
            
        if upload_response.status_code == 200:
            upload_result = upload_response.json()
            file_id = upload_result.get('file_id')
            print(f"✅ File upload successful")
            print(f"   File ID: {file_id}")
        else:
            print(f"❌ File upload failed: {upload_response.status_code}")
            print(f"   Response: {upload_response.text}")
            return
            
    except requests.ConnectionError:
        print("❌ Cannot connect to server. Is Flask app running on port 5000?")
        return
    finally:
        os.unlink(test_file)
    
    # Step 2: Submit processing job
    print("\n2. Testing processing job submission...")
    
    processing_request = {
        "file_id": file_id,
        "processing_mode": "complete",
        "options": {
            "categories": ["grammar", "style", "clarity"],
            "output_filename": "test_corrected.docx"
        }
    }
    
    try:
        process_response = requests.post(
            f"{base_url}/process",
            json=processing_request,
            headers={'Content-Type': 'application/json'}
        )
        
        if process_response.status_code == 200:
            process_result = process_response.json()
            job_id = process_result.get('job_id')
            estimated_time = process_result.get('estimated_time_seconds')
            
            print(f"✅ Processing job submitted successfully")
            print(f"   Job ID: {job_id}")
            print(f"   Estimated time: {estimated_time} seconds")
        else:
            print(f"❌ Processing job submission failed: {process_response.status_code}")
            print(f"   Response: {process_response.text}")
            return
            
    except Exception as e:
        print(f"❌ Error submitting processing job: {e}")
        return
    
    # Step 3: Monitor job status
    print("\n3. Testing job status monitoring...")
    
    max_wait_time = 300  # 5 minutes max
    check_interval = 5   # Check every 5 seconds
    waited_time = 0
    
    while waited_time < max_wait_time:
        try:
            status_response = requests.get(f"{base_url}/status/{job_id}")
            
            if status_response.status_code == 200:
                status_result = status_response.json()
                job_status = status_result.get('status')
                progress = status_result.get('progress', {})
                current_step = progress.get('current_step', 'Unknown')
                progress_percent = progress.get('progress_percent', 0)
                
                print(f"   📊 Status: {job_status} | Step: {current_step} | Progress: {progress_percent}%")
                
                if job_status == 'completed':
                    print("✅ Processing completed successfully!")
                    result = status_result.get('result', {})
                    output_file_id = result.get('output_file_id')
                    total_suggestions = result.get('total_suggestions', 0)
                    print(f"   📝 Total suggestions: {total_suggestions}")
                    print(f"   📁 Output file ID: {output_file_id}")
                    break
                elif job_status == 'failed':
                    error_message = status_result.get('error_message', 'Unknown error')
                    print(f"❌ Processing failed: {error_message}")
                    return
                else:
                    # Job still processing
                    time.sleep(check_interval)
                    waited_time += check_interval
            else:
                print(f"❌ Status check failed: {status_response.status_code}")
                return
                
        except Exception as e:
            print(f"❌ Error checking job status: {e}")
            return
    
    if waited_time >= max_wait_time:
        print("❌ Processing timed out after 5 minutes")
        return
    
    # Step 4: Download result (if completed)
    if 'output_file_id' in locals():
        print("\n4. Testing file download...")
        
        try:
            download_response = requests.get(f"{base_url}/download/{output_file_id}")
            
            if download_response.status_code == 200:
                # Save downloaded file
                download_path = f"test_output_{output_file_id}.docx"
                with open(download_path, 'wb') as f:
                    f.write(download_response.content)
                
                file_size = len(download_response.content)
                print(f"✅ File download successful")
                print(f"   📁 Downloaded to: {download_path}")
                print(f"   📊 File size: {file_size} bytes")
                
                # Clean up downloaded file
                os.unlink(download_path)
                
            else:
                print(f"❌ File download failed: {download_response.status_code}")
                print(f"   Response: {download_response.text}")
        
        except Exception as e:
            print(f"❌ Error downloading file: {e}")
    
    # Step 5: Test cleanup
    print("\n5. Testing file cleanup...")
    
    try:
        cleanup_response = requests.delete(f"{base_url}/upload/{file_id}/cleanup")
        
        if cleanup_response.status_code == 200:
            print("✅ File cleanup successful")
        else:
            print(f"⚠️ File cleanup warning: {cleanup_response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Error during cleanup: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Processing pipeline test complete!")

if __name__ == "__main__":
    test_processing_pipeline()