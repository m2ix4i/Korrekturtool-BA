"""
Document processing API endpoints
Handles processing requests and job management
"""

import os
import logging
from pathlib import Path
from flask import request, current_app, send_file

from web.services.job_manager import JobManager
from web.services.background_processor import BackgroundProcessor
from web.services.processor_integration import ProcessorIntegration
from web.models.job import ProcessingMode, ProcessingOptions
from web.utils.error_builder import APIErrorBuilder
from web.utils.errors import ValidationError, ProcessingError

logger = logging.getLogger(__name__)

# Initialize services
job_manager = JobManager()
background_processor = BackgroundProcessor()

def process_document():
    """
    Handle document processing request
    
    POST /api/v1/process
    {
        "file_id": "uuid-string",
        "processing_mode": "complete|performance",
        "options": {
            "categories": ["grammar", "style", "clarity", "academic"],
            "output_filename": "custom_name.docx"
        }
    }
    """
    try:
        # Validate request
        if not request.is_json:
            return APIErrorBuilder.validation_error("Request must be JSON")
        
        data = request.get_json()
        
        # Extract and validate required fields
        file_id = data.get('file_id')
        processing_mode = data.get('processing_mode', 'complete')
        options = data.get('options', {})
        
        if not file_id:
            return APIErrorBuilder.validation_error("file_id is required")
        
        # Validate processing mode
        if processing_mode not in ['complete', 'performance']:
            return APIErrorBuilder.validation_error(
                "processing_mode must be 'complete' or 'performance'"
            )
        
        # Validate file exists in upload directory
        file_path = _get_uploaded_file_path(file_id)
        if not file_path or not os.path.exists(file_path):
            return APIErrorBuilder.validation_error(
                f"File {file_id} not found. Please upload the file first."
            )
        
        # Create processing options
        try:
            processing_options = ProcessingOptions.from_dict(options)
            
            # Validate categories
            valid_categories = {'grammar', 'style', 'clarity', 'academic'}
            if not all(cat in valid_categories for cat in processing_options.categories):
                return APIErrorBuilder.validation_error(
                    f"Invalid categories. Valid options: {', '.join(valid_categories)}"
                )
            
            if not processing_options.categories:
                processing_options.categories = ['grammar', 'style', 'clarity', 'academic']
                
        except Exception as e:
            return APIErrorBuilder.validation_error(f"Invalid options: {str(e)}")
        
        # Create job
        job = job_manager.create_job(
            file_id=file_id,
            file_path=file_path,
            processing_mode=processing_mode,
            options=processing_options.to_dict()
        )
        
        # Submit job to background processor
        if not background_processor.submit_job(job.job_id):
            return APIErrorBuilder.processing_error(
                "Failed to submit job for processing. Please try again."
            )
        
        # Return job information
        response_data = {
            'job_id': job.job_id,
            'status': job.status.value,
            'estimated_time_seconds': job.estimated_time_seconds,
            'message': 'Job submitted for processing'
        }
        
        logger.info(f"Created processing job {job.job_id} for file {file_id}")
        return APIErrorBuilder.success_response(response_data)
        
    except ValidationError as e:
        logger.error(f"Validation error in process_document: {str(e)}")
        return APIErrorBuilder.validation_error(str(e))
    
    except ProcessingError as e:
        logger.error(f"Processing error in process_document: {str(e)}")
        return APIErrorBuilder.processing_error(str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error in process_document: {str(e)}")
        return APIErrorBuilder.internal_error("An error occurred while creating the processing job")

def get_processing_status(job_id: str):
    """
    Get processing status for a job
    
    GET /api/v1/status/{job_id}
    """
    try:
        # Get job from manager
        job = job_manager.get_job(job_id)
        if not job:
            return APIErrorBuilder.not_found_error(f"Job {job_id} not found")
        
        # Prepare response data
        response_data = {
            'job_id': job.job_id,
            'status': job.status.value,
            'progress': job.progress.to_dict(),
            'estimated_time_seconds': job.estimated_time_seconds,
            'elapsed_time_seconds': job.get_elapsed_time(),
            'created_at': job.created_at.isoformat(),
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None
        }
        
        # Add error message if failed
        if job.error_message:
            response_data['error_message'] = job.error_message
        
        # Add result if completed
        if job.result:
            response_data['result'] = {
                'output_file_id': job.result.output_file_id,
                'total_suggestions': job.result.total_suggestions,
                'successful_integrations': job.result.successful_integrations,
                'processing_time_seconds': job.result.processing_time_seconds,
                'cost_estimate': job.result.cost_estimate,
                'download_url': f"/api/v1/download/{job.result.output_file_id}" if job.result.output_file_id else None
            }
        
        return APIErrorBuilder.success_response(response_data)
        
    except Exception as e:
        logger.error(f"Error getting job status {job_id}: {str(e)}")
        return APIErrorBuilder.internal_error("Failed to retrieve job status")

def download_result(file_id: str):
    """
    Download processed file
    
    GET /api/v1/download/{file_id}
    """
    try:
        # Find output file
        output_dir = Path(current_app.config.get('OUTPUT_FOLDER', 'outputs'))
        file_path = output_dir / f"{file_id}.docx"
        
        if not file_path.exists():
            return APIErrorBuilder.not_found_error(
                "File not found. It may have been processed too long ago and cleaned up."
            )
        
        # Send file
        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=f"corrected_{file_id}.docx",
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {str(e)}")
        return APIErrorBuilder.internal_error("Failed to download file")


def get_processor_status():
    """
    Get background processor status (for debugging/monitoring)
    
    GET /api/v1/processor/status
    """
    try:
        status = background_processor.get_status()
        return APIErrorBuilder.success_response(status)
        
    except Exception as e:
        logger.error(f"Error getting processor status: {str(e)}")
        return APIErrorBuilder.internal_error("Failed to get processor status")


def _get_uploaded_file_path(file_id: str) -> str:
    """Get file path for uploaded file ID"""
    upload_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'uploads'))
    file_path = upload_dir / f"{file_id}.docx"
    return str(file_path)


def _estimate_processing_time(processing_mode: str, categories: list) -> int:
    """Estimate processing time in seconds"""
    integration = ProcessorIntegration()
    mode = ProcessingMode(processing_mode)
    return integration.estimate_processing_time(mode, categories)

# Initialization function for the Flask app
def init_processor(app):
    """Initialize the background processor with the Flask app"""
    with app.app_context():
        # Start the background processor
        background_processor.start()
        logger.info("Background processor started for Flask app")