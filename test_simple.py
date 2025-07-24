#!/usr/bin/env python3
"""
Simple test runner for web application without pytest configuration issues
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from web.app import create_app
    from web.config import TestingConfig
    
    print("🧪 Running Web Application Tests...")
    
    # Create test app
    app = create_app(TestingConfig)
    
    with app.test_client() as client:
        # Test 1: Health endpoint
        print("\n1. Testing /health endpoint...")
        response = client.get('/health')
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.get_json()
        assert data['status'] == 'healthy', f"Expected 'healthy', got {data.get('status')}"
        print("   ✅ PASS")
        
        # Test 2: API info endpoint
        print("\n2. Testing /api/v1/info endpoint...")
        response = client.get('/api/v1/info')
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.get_json()
        assert 'name' in data, "API info should have 'name' field"
        assert 'endpoints' in data, "API info should have 'endpoints' field"
        print("   ✅ PASS")
        
        # Test 3: Index page
        print("\n3. Testing / (index page)...")
        response = client.get('/')
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert 'text/html' in response.headers.get('Content-Type', ''), "Should serve HTML"
        print("   ✅ PASS")
        
        # Test 4: 404 handling
        print("\n4. Testing 404 error handling...")
        response = client.get('/nonexistent')
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        data = response.get_json()
        assert data['error'] == 'Not found', f"Expected 'Not found', got {data.get('error')}"
        print("   ✅ PASS")
        
        # Test 5: CORS headers
        print("\n5. Testing CORS headers...")
        response = client.get('/health')
        assert 'Access-Control-Allow-Origin' in response.headers, "CORS headers should be present"
        print("   ✅ PASS")
    
    # Test 6: Configuration
    print("\n6. Testing application configuration...")
    assert app.config['TESTING'] is True, "Should be in testing mode"
    assert app.config['MAX_CONTENT_LENGTH'] == 1024 * 1024, "Should have 1MB limit for testing"
    assert 'SECRET_KEY' in app.config, "Should have SECRET_KEY configured"
    assert 'GOOGLE_API_KEY' in app.config, "Should have GOOGLE_API_KEY configured"
    print("   ✅ PASS")
    
    print("\n🎉 All tests passed! Web application is working correctly.")
    print("✅ Flask backend structure is complete and functional.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all dependencies are installed: pip install -r requirements.txt")
except AssertionError as e:
    print(f"❌ Test failed: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()