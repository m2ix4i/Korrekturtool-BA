# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **German Bachelor Thesis Correction Tool** that uses AI (Google Gemini) to analyze Word documents and insert intelligent comments for improvements. The system has evolved through 3 major development phases and is now production-ready with two main entry points.

## Quick Start Commands

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your GOOGLE_API_KEY to .env

# Test basic functionality
python main_complete_advanced.py "path/to/document.docx"

# Test performance-optimized version
python main_performance_optimized.py "path/to/document.docx"
```

### Production Commands
```bash
# Complete Advanced System (recommended for development)
python main_complete_advanced.py document.docx --output corrected.docx

# Performance-Optimized System (for large documents)
python main_performance_optimized.py document.docx --output optimized.docx
```

## Architecture Overview

The system follows a modular pipeline architecture with two production-ready implementations:

### 1. Complete Advanced System (`main_complete_advanced.py`)
- **Purpose**: Full-featured system with all research-based improvements
- **Target**: Standard documents, development, and testing
- **Features**: Multi-pass analysis, smart formatting, advanced integration

### 2. Performance-Optimized System (`main_performance_optimized.py`)
- **Purpose**: System-adaptive configuration for large documents and production use
- **Target**: Large documents, memory-constrained environments
- **Features**: Batch processing, memory management, caching, performance dashboard

### Core Pipeline Flow
```
Document (.docx) → Parser → Chunker → AI Analyzer → Formatter → Word Integrator → Output (.docx)
```

## Module Architecture

### `/src/parsers/`
- **`docx_parser.py`**: Extracts and structures text from Word documents while preserving metadata

### `/src/analyzers/`
- **`advanced_gemini_analyzer.py`**: Multi-pass AI analysis with category-specific prompts
  - Supports 4 main categories: grammar, style, clarity, academic
  - Implements cost estimation and performance tracking

### `/src/utils/`
- **`advanced_chunking.py`**: Context-aware intelligent text segmentation
- **`multi_strategy_matcher.py`**: Text matching with multiple algorithms (RapidFuzz-based)
- **`smart_comment_formatter.py`**: Template-based comment formatting without redundant prefixes
- **`batch_processor_optimized.py`**: Memory-aware batch processing for large documents
- **`memory_optimizer.py`**: Real-time memory monitoring and optimization
- **`caching_system.py`**: Intelligent caching with memory + disk persistence
- **`parallel_processor.py`**: Multi-threaded chunk processing
- **`style_manager.py`**: Comment styling and template management

### `/src/integrators/`
- **`advanced_word_integrator_fixed.py`**: Microsoft Word-compatible XML comment integration
- **`zip_word_comments.py`**: Legacy ZIP-based DOCX manipulation (backup)

## Key Implementation Details

### Multi-Pass Analysis System
The `AdvancedGeminiAnalyzer` performs category-specific analysis:
```python
categories = ['grammar', 'style', 'clarity', 'academic']
# Each category uses specialized prompts for better results
```

### Performance Optimization Features
- **Adaptive Configuration**: System automatically adjusts based on available RAM and CPU cores
- **Memory Management**: Real-time monitoring with automatic garbage collection
- **Intelligent Caching**: Prevents redundant API calls for similar text segments
- **Batch Processing**: Optimized for documents with multiple chunks

### Text Matching Strategy
Uses multiple algorithms for precise text positioning:
- Exact matching
- Partial ratio matching (RapidFuzz)
- Token sort ratio
- Token set ratio
- WRatio (weighted)

### Comment Integration
- Generates Microsoft Word-compatible XML comments
- Creates proper relationship files and content types
- Maintains document integrity and compatibility

## Development Patterns

### Error Handling
- All major operations wrapped in try-catch with graceful degradation
- Fallback strategies for failed components (e.g., parser fallback, simplified integration)
- Comprehensive logging throughout the pipeline

### Configuration Management
- Environment variables in `.env` file
- Dataclass-based configuration objects for each module
- System-adaptive parameter adjustment

### Performance Tracking
- Built-in performance monitoring in all major components
- JSON dashboard export for detailed metrics
- Memory usage tracking and optimization

## Current Status for UI Development

### Production-Ready Components
✅ **Core Processing Pipeline**: Fully functional with two optimized versions  
✅ **AI Integration**: Advanced Gemini API integration with multi-pass analysis  
✅ **Word Integration**: Microsoft-compatible comment insertion  
✅ **Performance Optimization**: Memory management, caching, batch processing  
✅ **Error Handling**: Comprehensive fallback strategies  

### Ready for UI Integration
The backend systems are production-ready and provide:
- Clear input/output interfaces (DOCX files)
- Detailed progress reporting and performance metrics
- Configurable processing options
- Robust error handling with user-friendly messages

### UI Integration Points
1. **File Upload/Selection**: Interface for `.docx` file selection
2. **Processing Configuration**: Options for analysis categories, processing mode (standard vs performance-optimized)
3. **Progress Monitoring**: Real-time progress display during processing
4. **Results Display**: Success/failure status, processing metrics, download link
5. **Error Handling**: User-friendly error messages and troubleshooting guidance

### Recommended UI Architecture
- Web-based interface (Flask/FastAPI backend + modern frontend)
- File upload with drag-and-drop support
- Real-time progress updates via WebSocket or SSE
- Configuration panel for processing options
- Results dashboard with metrics and download options

## Environment Requirements

### Python Dependencies
```bash
python-docx==0.8.11      # Word document manipulation
google-generativeai==0.8.3  # AI analysis
python-dotenv==1.0.1     # Environment configuration
colorama==0.4.6          # Terminal colors
tqdm==4.66.5             # Progress bars
lxml==6.0.0              # XML processing
rapidfuzz                # Text matching (auto-installed)
psutil                   # System monitoring (auto-installed)
```

### System Requirements
- Python 3.9+
- Google Gemini API key
- Minimum 4GB RAM (8GB+ recommended for large documents)
- 100MB disk space for caching

### API Costs
- Google Gemini 1.5 Flash: ~$0.10-0.50 per typical bachelor thesis
- Cost estimation built into the system

## Testing Strategy

### Test Files Location
- Test documents in `/archive/test_files/`
- Use small test documents for development
- Large document testing available via performance system

### Manual Testing Commands
```bash
# Test with small document
python main_complete_advanced.py "archive/test_files/test_document.docx"

# Test performance system
python main_performance_optimized.py "large_document.docx"
```

## Notes for UI Developer

1. **Processing Time**: Normal documents take 30-90 seconds to process due to AI analysis
2. **File Size Limits**: System handles documents up to 100+ pages efficiently
3. **Output Format**: Always generates new .docx file with comments, preserves original
4. **Error Recovery**: System includes comprehensive error handling and user-friendly messages
5. **Performance Monitoring**: Built-in metrics can be exposed via API for UI display
6. **Scalability**: Performance-optimized version designed for high-throughput scenarios

The backend is fully functional and ready for UI integration. Focus should be on creating an intuitive interface that leverages the existing robust processing pipeline.