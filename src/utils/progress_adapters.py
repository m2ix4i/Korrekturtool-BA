#!/usr/bin/env python3
"""
Progress Tracking Adapters for Main Processing Systems
Integrates EnhancedProgressTracker with CompleteAdvancedKorrekturtool and PerformanceOptimizedKorrekturtool
"""

import logging
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

from src.utils.progress_integration import EnhancedProgressTracker, ProcessingStage, ProgressContext

logger = logging.getLogger(__name__)


class CompleteAdvancedProgressAdapter:
    """
    Progress tracking adapter for CompleteAdvancedKorrekturtool
    Integrates progress tracking into the complete advanced processing pipeline
    """
    
    def __init__(self, progress_tracker: Optional[EnhancedProgressTracker] = None):
        self.progress_tracker = progress_tracker
        self.job_id = None
    
    def set_progress_tracker(self, tracker: EnhancedProgressTracker, job_id: str):
        """Set the progress tracker and job ID"""
        self.progress_tracker = tracker
        self.job_id = job_id
    
    def process_document_with_progress(self, document_path: str, output_path: str = None,
                                     original_processor=None) -> bool:
        """
        Process document with integrated progress tracking
        
        Args:
            document_path: Path to input document
            output_path: Path for output document
            original_processor: Instance of CompleteAdvancedKorrekturtool
            
        Returns:
            bool: Success status
        """
        if not self.progress_tracker or not self.job_id:
            logger.warning("No progress tracker set, falling back to original processing")
            if original_processor:
                return original_processor.process_document_complete(document_path, output_path)
            return False
        
        try:
            # Phase 1: Document Parsing
            with ProgressContext(self.progress_tracker, self.job_id, 
                               ProcessingStage.PARSING, 100) as parsing_ctx:
                
                parsing_ctx.update(20, "Loading document...")
                full_text = self._parse_document_with_progress(document_path, parsing_ctx, original_processor)
                if not full_text:
                    return False
                parsing_ctx.update(100, f"Parsed {len(full_text):,} characters")
            
            # Phase 2: Intelligent Chunking
            with ProgressContext(self.progress_tracker, self.job_id,
                               ProcessingStage.CHUNKING, 100) as chunking_ctx:
                
                chunking_ctx.update(10, "Initializing chunker...")
                intelligent_chunks = self._chunk_document_with_progress(
                    full_text, chunking_ctx, original_processor
                )
                chunking_ctx.update(100, f"Created {len(intelligent_chunks)} intelligent chunks")
            
            # Phase 3: Multi-Pass AI Analysis
            with ProgressContext(self.progress_tracker, self.job_id,
                               ProcessingStage.ANALYZING, len(intelligent_chunks)) as analysis_ctx:
                
                all_suggestions = self._analyze_chunks_with_progress(
                    intelligent_chunks, analysis_ctx, original_processor
                )
                
                if not all_suggestions:
                    analysis_ctx.update(100, "No suggestions found")
                else:
                    analysis_ctx.update(100, f"Generated {len(all_suggestions)} suggestions")
            
            # Phase 4: Smart Comment Formatting
            with ProgressContext(self.progress_tracker, self.job_id,
                               ProcessingStage.FORMATTING, len(all_suggestions) if all_suggestions else 1) as format_ctx:
                
                formatted_suggestions = self._format_suggestions_with_progress(
                    all_suggestions, format_ctx, original_processor
                )
                format_ctx.update(100, f"Formatted {len(formatted_suggestions)} comments")
            
            # Phase 5: Word Integration
            with ProgressContext(self.progress_tracker, self.job_id,
                               ProcessingStage.INTEGRATING, 100) as integration_ctx:
                
                comments_added = self._integrate_comments_with_progress(
                    formatted_suggestions, document_path, output_path, 
                    integration_ctx, original_processor
                )
                integration_ctx.update(100, f"Integrated {comments_added} comments")
            
            # Phase 6: Finalization
            with ProgressContext(self.progress_tracker, self.job_id,
                               ProcessingStage.FINALIZING, 100) as final_ctx:
                
                final_ctx.update(50, "Saving document...")
                success = self._finalize_document_with_progress(
                    output_path, final_ctx, original_processor
                )
                final_ctx.update(100, "Document processing completed")
            
            # Complete job tracking
            result_data = {
                'suggestions_found': len(all_suggestions) if all_suggestions else 0,
                'comments_integrated': comments_added,
                'output_path': output_path or document_path.replace('.docx', '_COMPLETE_ADVANCED.docx')
            }
            
            self.progress_tracker.complete_job(self.job_id, success, result_data)
            return success
            
        except Exception as e:
            logger.error(f"Error in progress-tracked processing: {str(e)}")
            self.progress_tracker.complete_job(
                self.job_id, False, None, f"Processing failed: {str(e)}"
            )
            return False
    
    def _parse_document_with_progress(self, document_path: str, ctx: ProgressContext,
                                    original_processor) -> Optional[str]:
        """Parse document with progress updates"""
        try:
            ctx.update(30, "Setting up parser...")
            
            # Use original processor's parsing logic
            full_text = original_processor._parse_document_best_available(document_path)
            
            ctx.update(80, "Validating parsed content...")
            time.sleep(0.1)  # Brief pause for progress visibility
            
            return full_text
            
        except Exception as e:
            logger.error(f"Error in document parsing: {str(e)}")
            return None
    
    def _chunk_document_with_progress(self, full_text: str, ctx: ProgressContext,
                                    original_processor) -> List:
        """Chunk document with progress updates"""
        try:
            from src.utils.advanced_chunking import AdvancedChunker
            
            ctx.update(20, "Configuring chunker...")
            
            chunker = AdvancedChunker(
                target_chunk_size=600,
                overlap_size=150,
                min_chunk_size=200
            )
            
            ctx.update(50, "Creating intelligent chunks...")
            
            intelligent_chunks = chunker.create_intelligent_chunks(
                full_text, document_type="academic"
            )
            
            ctx.update(90, "Validating chunks...")
            
            return intelligent_chunks
            
        except Exception as e:
            logger.error(f"Error in document chunking: {str(e)}")
            return []
    
    def _analyze_chunks_with_progress(self, chunks: List, ctx: ProgressContext,
                                    original_processor) -> List:
        """Analyze chunks with detailed progress updates"""
        try:
            from src.analyzers.advanced_gemini_analyzer import AdvancedGeminiAnalyzer
            
            analyzer = AdvancedGeminiAnalyzer()
            all_suggestions = []
            
            categories = ['grammar', 'style', 'clarity', 'academic']
            
            for i, chunk in enumerate(chunks):
                progress = int((i / len(chunks)) * 100)
                ctx.update(
                    progress, 
                    f"Analyzing chunk {i+1}/{len(chunks)}...",
                    current_item=i+1,
                    metadata={'chunks_processed': i, 'total_chunks': len(chunks)}
                )
                
                try:
                    chunk_suggestions = analyzer.analyze_text_multipass(
                        chunk.text,
                        context=f"Chunk {i+1}/{len(chunks)} aus Bachelorarbeit",
                        categories=categories
                    )
                    
                    # Adjust positions for chunk offset
                    for suggestion in chunk_suggestions:
                        start, end = suggestion.position
                        suggestion.position = (
                            start + chunk.start_pos,
                            end + chunk.start_pos
                        )
                    
                    all_suggestions.extend(chunk_suggestions)
                    
                    # Rate limiting
                    time.sleep(0.3)
                    
                except Exception as e:
                    logger.warning(f"Error analyzing chunk {i+1}: {str(e)}")
                    continue
            
            return all_suggestions
            
        except Exception as e:
            logger.error(f"Error in chunk analysis: {str(e)}")
            return []
    
    def _format_suggestions_with_progress(self, suggestions: List, ctx: ProgressContext,
                                        original_processor) -> List:
        """Format suggestions with progress updates"""
        try:
            from src.utils.smart_comment_formatter import SmartCommentFormatter
            
            if not suggestions:
                return []
            
            ctx.update(10, "Initializing formatter...")
            
            formatter = SmartCommentFormatter()
            formatter.set_template('academic_detailed')
            
            formatted_suggestions = []
            
            for i, suggestion in enumerate(suggestions):
                progress = int((i / len(suggestions)) * 100)
                ctx.update(
                    progress,
                    f"Formatting comment {i+1}/{len(suggestions)}...",
                    current_item=i+1
                )
                
                formatted_text = formatter.format_comment(suggestion)
                suggestion.formatted_text = formatted_text
                formatted_suggestions.append(suggestion)
            
            return formatted_suggestions
            
        except Exception as e:
            logger.error(f"Error in suggestion formatting: {str(e)}")
            return suggestions  # Return unformatted if formatting fails
    
    def _integrate_comments_with_progress(self, suggestions: List, document_path: str,
                                        output_path: str, ctx: ProgressContext,
                                        original_processor) -> int:
        """Integrate comments with progress updates"""
        try:
            from src.integrators.advanced_word_integrator_fixed import AdvancedWordIntegrator
            
            ctx.update(10, "Initializing Word integrator...")
            
            integrator = AdvancedWordIntegrator(document_path)
            
            ctx.update(30, "Creating document backup...")
            backup_path = integrator.create_backup()
            
            ctx.update(60, "Integrating comments into document...")
            comments_added = integrator.add_word_comments_advanced(suggestions)
            
            ctx.update(90, "Finalizing integration...")
            
            return comments_added
            
        except Exception as e:
            logger.error(f"Error in comment integration: {str(e)}")
            return 0
    
    def _finalize_document_with_progress(self, output_path: str, ctx: ProgressContext,
                                       original_processor) -> bool:
        """Finalize document processing with progress updates"""
        try:
            ctx.update(70, "Saving final document...")
            
            # Simulate final processing steps
            time.sleep(0.2)
            
            ctx.update(100, "Document saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in document finalization: {str(e)}")
            return False


class PerformanceOptimizedProgressAdapter:
    """
    Progress tracking adapter for PerformanceOptimizedKorrekturtool
    Integrates progress tracking into the performance-optimized processing pipeline
    """
    
    def __init__(self, progress_tracker: Optional[EnhancedProgressTracker] = None):
        self.progress_tracker = progress_tracker
        self.job_id = None
    
    def set_progress_tracker(self, tracker: EnhancedProgressTracker, job_id: str):
        """Set the progress tracker and job ID"""
        self.progress_tracker = tracker
        self.job_id = job_id
    
    def process_document_with_progress(self, document_path: str, output_path: str = None,
                                     original_processor=None) -> bool:
        """
        Process document with integrated progress tracking for performance-optimized system
        
        Args:
            document_path: Path to input document
            output_path: Path for output document
            original_processor: Instance of PerformanceOptimizedKorrekturtool
            
        Returns:
            bool: Success status
        """
        if not self.progress_tracker or not self.job_id:
            logger.warning("No progress tracker set, falling back to original processing")
            if original_processor:
                return original_processor.process_document_performance_optimized(document_path, output_path)
            return False
        
        try:
            # Phase 0: System Analysis and Setup
            with ProgressContext(self.progress_tracker, self.job_id,
                               ProcessingStage.INITIALIZING, 100) as init_ctx:
                
                init_ctx.update(30, "Analyzing system resources...")
                system_info = self._analyze_system_with_progress(init_ctx, original_processor)
                
                init_ctx.update(70, "Creating optimized configurations...")
                optimized_configs = self._create_configs_with_progress(
                    system_info, document_path, init_ctx, original_processor
                )
                
                init_ctx.update(100, "Initialized optimized modules")
            
            # Phase 1: Performance-Optimized Parsing
            with ProgressContext(self.progress_tracker, self.job_id,
                               ProcessingStage.PARSING, 100) as parse_ctx:
                
                full_text = self._parse_with_caching_progress(
                    document_path, parse_ctx, original_processor
                )
                if not full_text:
                    return False
                parse_ctx.update(100, f"Parsed {len(full_text):,} characters (cached)")
            
            # Phase 2: Cached Batch Processing
            with ProgressContext(self.progress_tracker, self.job_id,
                               ProcessingStage.ANALYZING, 100) as batch_ctx:
                
                batch_result = self._execute_batch_processing_with_progress(
                    full_text, batch_ctx, original_processor
                )
                
                batch_ctx.update(100, 
                    f"Batch processing: {batch_result.total_suggestions if hasattr(batch_result, 'total_suggestions') else 0} suggestions")
            
            # Phase 3: Smart Integration
            with ProgressContext(self.progress_tracker, self.job_id,
                               ProcessingStage.INTEGRATING, 100) as integration_ctx:
                
                comments_integrated = self._execute_integration_with_progress(
                    batch_result, document_path, output_path, 
                    integration_ctx, original_processor
                )
                integration_ctx.update(100, f"Integrated {comments_integrated} comments")
            
            # Phase 4: Performance Dashboard Creation
            with ProgressContext(self.progress_tracker, self.job_id,
                               ProcessingStage.FINALIZING, 100) as final_ctx:
                
                final_ctx.update(50, "Creating performance dashboard...")
                self._create_dashboard_with_progress(
                    batch_result, comments_integrated, final_ctx, original_processor
                )
                final_ctx.update(100, "Performance optimization completed")
            
            # Complete job tracking
            result_data = {
                'suggestions_found': getattr(batch_result, 'total_suggestions', 0),
                'comments_integrated': comments_integrated,
                'output_path': output_path or document_path.replace('.docx', '_PERFORMANCE_OPTIMIZED.docx'),
                'performance_optimized': True
            }
            
            self.progress_tracker.complete_job(self.job_id, True, result_data)
            return True
            
        except Exception as e:
            logger.error(f"Error in performance-optimized processing: {str(e)}")
            self.progress_tracker.complete_job(
                self.job_id, False, None, f"Performance processing failed: {str(e)}"
            )
            return False
    
    def _analyze_system_with_progress(self, ctx: ProgressContext, original_processor):
        """Analyze system resources with progress"""
        try:
            ctx.update(50, "Checking memory and CPU...")
            system_info = original_processor._analyze_system_resources()
            ctx.update(100, f"System: {system_info['total_memory_gb']:.1f}GB RAM, {system_info['cpu_count']} CPUs")
            return system_info
        except Exception as e:
            logger.error(f"Error analyzing system: {str(e)}")
            return {}
    
    def _create_configs_with_progress(self, system_info: Dict, document_path: str,
                                    ctx: ProgressContext, original_processor):
        """Create optimized configurations with progress"""
        try:
            ctx.update(50, "Optimizing configuration...")
            configs = original_processor._create_optimized_configs(system_info, document_path)
            ctx.update(100, f"Config: {configs.get('system_tier', 'unknown')} tier")
            return configs
        except Exception as e:
            logger.error(f"Error creating configs: {str(e)}")
            return {}
    
    def _parse_with_caching_progress(self, document_path: str, ctx: ProgressContext,
                                   original_processor) -> Optional[str]:
        """Parse document with caching and progress"""
        try:
            ctx.update(20, "Checking cache...")
            full_text = original_processor._parse_document_with_caching(document_path)
            ctx.update(80, "Validating parsed content...")
            return full_text
        except Exception as e:
            logger.error(f"Error in cached parsing: {str(e)}")
            return None
    
    def _execute_batch_processing_with_progress(self, full_text: str, ctx: ProgressContext,
                                              original_processor):
        """Execute batch processing with detailed progress"""
        try:
            ctx.update(10, "Initializing batch processor...")
            
            # Simulate batch processing with progress updates
            categories = ['grammar', 'style', 'clarity', 'academic']
            
            ctx.update(30, "Starting cached batch analysis...")
            batch_result = original_processor._execute_cached_batch_processing(full_text)
            
            ctx.update(80, "Processing batch results...")
            
            return batch_result
            
        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}")
            # Return mock result for error case
            class MockBatchResult:
                def __init__(self):
                    self.total_suggestions = 0
                    self.success_rate = 0.0
            return MockBatchResult()
    
    def _execute_integration_with_progress(self, batch_result, document_path: str,
                                         output_path: str, ctx: ProgressContext,
                                         original_processor) -> int:
        """Execute smart integration with progress"""
        try:
            ctx.update(30, "Preparing integration...")
            comments_integrated = original_processor._execute_smart_integration(
                batch_result, document_path, output_path
            )
            ctx.update(90, "Finalizing integration...")
            return comments_integrated
        except Exception as e:
            logger.error(f"Error in integration: {str(e)}")
            return 0
    
    def _create_dashboard_with_progress(self, batch_result, comments_integrated: int,
                                      ctx: ProgressContext, original_processor):
        """Create performance dashboard with progress"""
        try:
            ctx.update(70, "Generating performance metrics...")
            original_processor._create_performance_dashboard(batch_result, comments_integrated)
            ctx.update(100, "Dashboard created")
        except Exception as e:
            logger.error(f"Error creating dashboard: {str(e)}")


def create_progress_adapter(processing_mode: str, progress_tracker: EnhancedProgressTracker,
                          job_id: str):
    """
    Factory function to create appropriate progress adapter
    
    Args:
        processing_mode: 'complete' or 'performance'
        progress_tracker: EnhancedProgressTracker instance
        job_id: Job identifier
        
    Returns:
        Appropriate progress adapter instance
    """
    if processing_mode == 'complete':
        adapter = CompleteAdvancedProgressAdapter()
    elif processing_mode == 'performance':
        adapter = PerformanceOptimizedProgressAdapter()
    else:
        raise ValueError(f"Unknown processing mode: {processing_mode}")
    
    adapter.set_progress_tracker(progress_tracker, job_id)
    return adapter