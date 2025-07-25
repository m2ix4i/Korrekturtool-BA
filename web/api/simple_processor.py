"""
Simple document processing API endpoint
Integrates directly with existing main_complete_advanced and main_performance_optimized
"""

import os
import sys
import json
import uuid
import logging
import threading
from datetime import datetime
from pathlib import Path
from flask import request, current_app, send_file

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from web.utils.errors import ValidationError, ProcessingError
from web.utils.error_builder import APIErrorBuilder

# Configure logging
logger = logging.getLogger(__name__)

# Store processing jobs in memory (in production, use Redis or database)
processing_jobs = {}

def process_document():
    """Handle document processing POST request"""
    try:
        request_data = _extract_processing_request()
        job_id = str(uuid.uuid4())
        
        # Start processing in background thread
        thread = threading.Thread(
            target=_process_document_async,
            args=(job_id, request_data)
        )
        thread.start()
        
        # Store job info
        processing_jobs[job_id] = {
            'status': 'processing',
            'created_at': datetime.now().isoformat(),
            'file_id': request_data.get('file_id'),
            'processing_mode': request_data.get('processing_mode', 'complete'),
            'progress': 0,
            'message': 'Processing started'
        }
        
        return APIErrorBuilder.success_response({
            'job_id': job_id,
            'status': 'processing',
            'message': 'Document processing started',
            'estimated_time': '30-90 seconds'
        })
        
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return APIErrorBuilder.validation_error(str(e))
    except Exception as e:
        logger.error(f"Unexpected error during processing request: {str(e)}")
        return APIErrorBuilder.internal_error("Failed to start document processing")

def _extract_processing_request():
    """Extract and validate processing request data"""
    if not request.is_json:
        raise ValidationError('Request must be JSON')
    
    data = request.get_json()
    
    if not data.get('file_id'):
        raise ValidationError('file_id is required')
    
    # Validate processing mode
    valid_modes = ['complete', 'optimized']
    processing_mode = data.get('processing_mode', 'complete')
    if processing_mode not in valid_modes:
        raise ValidationError(f'processing_mode must be one of: {valid_modes}')
    
    # Validate analysis categories
    valid_categories = ['grammar', 'style', 'clarity', 'academic']
    categories = data.get('categories', valid_categories)
    if not isinstance(categories, list):
        raise ValidationError('categories must be a list')
    
    invalid_categories = [cat for cat in categories if cat not in valid_categories]
    if invalid_categories:
        raise ValidationError(f'Invalid categories: {invalid_categories}')
    
    return {
        'file_id': data['file_id'],
        'processing_mode': processing_mode,
        'categories': categories,
        'output_filename': data.get('output_filename')
    }

def _process_document_async(job_id, request_data):
    """Process document asynchronously"""
    try:
        # Update job status
        processing_jobs[job_id].update({
            'status': 'processing',
            'progress': 10,
            'message': 'Initializing processing pipeline'
        })
        
        # Get file paths
        upload_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads'))
        output_dir = Path(current_app.config.get('OUTPUT_FOLDER', 'outputs'))
        output_dir.mkdir(exist_ok=True)
        
        input_file = upload_dir / f"{request_data['file_id']}.docx"
        if not input_file.exists():
            raise ProcessingError(f"Input file not found: {input_file}")
        
        # Generate output filename
        output_filename = request_data.get('output_filename') or f"{request_data['file_id']}_corrected.docx"
        if not output_filename.endswith('.docx'):
            output_filename += '.docx'
        output_file = output_dir / output_filename
        
        # Update progress
        processing_jobs[job_id].update({
            'progress': 20,
            'message': 'Loading processing modules'
        })
        
        # Import processing modules (lazy import to avoid startup delays)
        if request_data['processing_mode'] == 'optimized':
            from main_performance_optimized import main as process_main
        else:
            from main_complete_advanced import main as process_main
        
        # Update progress
        processing_jobs[job_id].update({
            'progress': 30,
            'message': 'Starting AI analysis'
        })
        
        # Process the document
        success = _run_document_processing(
            process_main, 
            str(input_file), 
            str(output_file),
            request_data['categories']
        )
        
        if success and output_file.exists():
            # Processing completed successfully
            processing_jobs[job_id].update({
                'status': 'completed',
                'progress': 100,
                'message': 'Document processing completed successfully',
                'output_file': str(output_file),
                'completed_at': datetime.now().isoformat()
            })
            logger.info(f"Document processing completed successfully for job {job_id}")
        else:
            # Processing failed
            processing_jobs[job_id].update({
                'status': 'failed',
                'progress': 0,
                'message': 'Document processing failed',
                'error': 'Processing did not complete successfully',
                'failed_at': datetime.now().isoformat()
            })
            logger.error(f"Document processing failed for job {job_id}")
            
    except Exception as e:
        # Processing error
        processing_jobs[job_id].update({
            'status': 'failed',
            'progress': 0,
            'message': f'Processing error: {str(e)}',
            'error': str(e),
            'failed_at': datetime.now().isoformat()
        })
        logger.error(f"Processing error for job {job_id}: {str(e)}")

def _run_document_processing(process_func, input_file, output_file, categories):
    """Run the document processing function safely"""
    try:
        # Create a minimal arguments object that matches what the main functions expect
        class Args:
            def __init__(self, input_file, output_file, categories):
                self.input_file = input_file
                self.output_file = output_file
                self.categories = categories
                self.verbose = False
        
        args = Args(input_file, output_file, categories)
        
        # Call the processing function
        result = process_func(args)
        return result is not False  # Consider success if not explicitly False
        
    except Exception as e:
        logger.error(f"Error in document processing: {str(e)}")
        return False

def get_processing_status(job_id):
    """Get processing status for a job ID"""
    try:
        if job_id not in processing_jobs:
            return APIErrorBuilder.not_found_error("Job not found")
        
        job_data = processing_jobs[job_id].copy()
        
        # Clean up sensitive data
        if 'output_file' in job_data and job_data['status'] == 'completed':
            job_data['download_available'] = True
        
        return APIErrorBuilder.success_response(job_data)
        
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        return APIErrorBuilder.internal_error("Failed to retrieve job status")

def download_result(file_id):
    """Download processed result file"""
    try:
        # Find job with this file_id
        job = None
        for job_data in processing_jobs.values():
            if (job_data.get('file_id') == file_id and 
                job_data.get('status') == 'completed' and 
                'output_file' in job_data):
                job = job_data
                break
        
        if not job:
            return APIErrorBuilder.not_found_error("Processed file not found or not ready")
        
        output_file = Path(job['output_file'])
        if not output_file.exists():
            return APIErrorBuilder.not_found_error("Output file not found on disk")
        
        return send_file(
            str(output_file),
            as_attachment=True,
            download_name=output_file.name,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return APIErrorBuilder.internal_error("Failed to download file")

def cleanup_processing_jobs():
    """Clean up old processing jobs (call periodically)"""
    try:
        cutoff_time = datetime.now().timestamp() - (24 * 60 * 60)  # 24 hours ago
        
        jobs_to_remove = []
        for job_id, job_data in processing_jobs.items():
            created_at = datetime.fromisoformat(job_data['created_at']).timestamp()
            if created_at < cutoff_time:
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del processing_jobs[job_id]
            
        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old processing jobs")
            
    except Exception as e:
        logger.error(f"Error cleaning up processing jobs: {str(e)}")