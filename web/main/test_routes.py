#!/usr/bin/env python3
"""
Test routes for progress tracking system
Provides endpoints for testing the progress tracking functionality
"""

from flask import Blueprint, render_template, jsonify, request
import logging
import time

# Create blueprint for test routes
test_bp = Blueprint('test', __name__, url_prefix='/test')
logger = logging.getLogger(__name__)


@test_bp.route('/progress')
def progress_test():
    """
    Render progress tracking test interface
    
    GET /test/progress
    """
    return render_template('progress_test.html')


@test_bp.route('/api/simulate-job', methods=['POST'])
def simulate_job():
    """
    API endpoint to simulate a processing job for testing
    
    POST /test/api/simulate-job
    {
        "job_type": "complete|performance",
        "duration": 30
    }
    """
    try:
        data = request.get_json() or {}
        job_type = data.get('job_type', 'complete')
        duration = data.get('duration', 30)
        
        # In a real implementation, this would start an actual job
        # For now, it just returns a mock response
        
        mock_job_id = f"test-{job_type}-{int(time.time())}"
        
        response = {
            'success': True,
            'job_id': mock_job_id,
            'job_type': job_type,
            'estimated_duration': duration,
            'message': f'Mock {job_type} job created for testing',
            'websocket_room': f'job_{mock_job_id}'
        }
        
        logger.info(f"Created mock job {mock_job_id} for testing")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error creating mock job: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@test_bp.route('/api/system-status')
def system_status():
    """
    Get system status for testing
    
    GET /test/api/system-status
    """
    try:
        from web.services.enhanced_progress_tracker import get_web_progress_tracker
        
        web_tracker = get_web_progress_tracker()
        
        status = {
            'active_jobs': web_tracker.get_active_job_count(),
            'job_ids': web_tracker.get_active_job_ids(),
            'websocket_available': True,  # Assume available in test
            'progress_tracking_enabled': True,
            'system_ready': True
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return jsonify({
            'active_jobs': 0,
            'job_ids': [],
            'websocket_available': False,
            'progress_tracking_enabled': False,
            'system_ready': False,
            'error': str(e)
        }), 500