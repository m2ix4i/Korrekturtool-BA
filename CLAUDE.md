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

### Web Interface Setup (NEW)
```bash
# Install all dependencies including web components
pip install -r requirements.txt

# Configure environment for web server
cp .env.example .env
# Add your GOOGLE_API_KEY and configure web settings

# Start web server (development)
python web/app.py

# Or use the production runner
python web/run.py

# Access web interface at: http://localhost:5000
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

#### Production Dependencies
```bash
python-docx==0.8.11      # Word document manipulation
google-generativeai==0.8.3  # AI analysis
python-dotenv==1.0.1     # Environment configuration
colorama==0.4.6          # Terminal colors
tqdm==4.66.5             # Progress bars
lxml==6.0.0              # XML processing
rapidfuzz                # Text matching (auto-installed)
psutil                   # System monitoring (auto-installed)
Flask                    # Web interface framework
Flask-SocketIO           # Real-time web communication
Celery                   # Background job processing
Redis                    # Task queue and caching
```

#### Development Dependencies
```bash
pytest                   # Testing framework
pytest-cov              # Coverage reporting
pytest-mock             # Mocking utilities
pytest-xdist            # Parallel test execution
pytest-benchmark        # Performance benchmarking
flake8                   # Code linting
black                    # Code formatting
isort                    # Import sorting
mypy                     # Type checking
bandit                   # Security analysis
safety                   # Dependency vulnerability scanning
factory-boy              # Test data factories
Faker                    # Synthetic test data
responses                # HTTP mocking
freezegun                # Time mocking
```

### System Requirements
- Python 3.9+
- Google Gemini API key
- Minimum 4GB RAM (8GB+ recommended for large documents)
- 100MB disk space for caching
- Redis server (for web interface and background job processing)

### API Costs
- Google Gemini 1.5 Flash: ~$0.10-0.50 per typical bachelor thesis
- Cost estimation built into the system

## Testing & Development Commands

### Setup Development Environment
```bash
# Install all dependencies (production + development)
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Activate testing configuration (if needed)
cp pytest.ini.backup pytest.ini
cp tests/conftest.py.backup tests/conftest.py
```

### Running Tests
```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Run specific test categories
pytest -m "unit"                    # Unit tests only
pytest -m "integration"             # Integration tests
pytest -m "not slow"                # Skip slow tests
pytest -m "not api"                 # Skip API-dependent tests

# Run tests in parallel
pytest -n auto                      # Auto-detect CPU cores

# Run specific test files
pytest tests/test_advanced_analyzer_pytest.py
pytest tests/test_docx_parser.py

# Performance and benchmark tests
pytest -m "benchmark" --benchmark-only
pytest -m "slow" -v

# Generate detailed HTML coverage report
pytest --cov=src --cov-report=html
# View report: open htmlcov/index.html
```

### Code Quality Commands
```bash
# Code formatting
black .                             # Format code
isort .                            # Sort imports

# Code quality checks
flake8 .                           # Linting
mypy src/                          # Type checking

# Security scanning
bandit -r src/                     # Security analysis
safety check                      # Dependency vulnerabilities
```

### Development Workflow
```bash
# Full development check (mirrors CI)
pytest --cov=src --cov-report=xml --cov-fail-under=80
flake8 . --count --max-complexity=10 --max-line-length=127
black --check .
isort --check-only .

# Test main scripts
python -c "import main_complete_advanced; print('✓ Import successful')"
python -c "import main_performance_optimized; print('✓ Import successful')"
```

### Environment Variables for Testing
```bash
# Required for AI analyzer integration tests
export GOOGLE_API_KEY="your_gemini_api_key"

# Test environment configuration
export TESTING="true"
export LOG_LEVEL="DEBUG"

# Run tests requiring API (skip if no key)
pytest -m "requires_api_key"       # With API key
pytest -m "not api"                # Without API key
```

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

## Continuous Integration & Deployment

### GitHub Actions CI Pipeline
- **Multi-Python Support**: Automated testing on Python 3.9, 3.10, 3.11
- **Test Coverage**: Minimum 80% coverage requirement with Codecov integration
- **Security Scanning**: Automated vulnerability detection with Bandit and Safety
- **Code Quality**: Automated linting with flake8 and formatting checks
- **Performance Testing**: Benchmark tests and memory leak detection

### Local CI Simulation
```bash
# Run the same tests as CI pipeline
pytest tests/ -m "not api" -v --tb=short --cov=src --cov-report=xml
pytest tests/ -m "api" -v --tb=short  # If API key available
pytest tests/ -m "slow" -v --tb=short  # Performance tests

# Full CI check locally
pytest --cov=src --cov-report=xml --cov-fail-under=80
flake8 . --count --max-complexity=10 --max-line-length=127
black --check .
isort --check-only .
bandit -r src/
safety check
```

### Web Interface Deployment
```bash
# Production deployment requirements
export GOOGLE_API_KEY="your_key"
export REDIS_URL="redis://localhost:6379"
export CELERY_BROKER_URL="redis://localhost:6379"

# Start Redis server
redis-server

# Start Celery worker (in separate terminal)
celery -A web.app:celery worker --loglevel=info

# Start Flask application
python web/app.py
```

## Notes for UI Developer

1. **Processing Time**: Normal documents take 30-90 seconds to process due to AI analysis
2. **File Size Limits**: System handles documents up to 100+ pages efficiently
3. **Output Format**: Always generates new .docx file with comments, preserves original
4. **Error Recovery**: System includes comprehensive error handling and user-friendly messages
5. **Performance Monitoring**: Built-in metrics can be exposed via API for UI display
6. **Scalability**: Performance-optimized version designed for high-throughput scenarios

The backend is fully functional and ready for UI integration. Focus should be on creating an intuitive interface that leverages the existing robust processing pipeline.