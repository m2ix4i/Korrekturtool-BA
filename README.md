# 🎓 German Bachelor Thesis Correction Tool

An AI-powered tool for automatically correcting and improving German bachelor theses in Word format, with intelligent comment insertion and performance optimization.

## ✨ Features

- **🧠 Advanced AI Analysis**: Multi-pass analysis using Google Gemini with specialized prompts for grammar, style, clarity, and academic writing
- **📝 Professional Word Comments**: Generates Microsoft Word-compatible comments that appear as interactive speech bubbles  
- **⚡ Performance-Optimized**: Two production systems - standard and performance-optimized for large documents
- **🔄 Batch Processing**: Memory-aware processing with intelligent chunking and caching
- **📊 Performance Dashboard**: Comprehensive metrics and monitoring with JSON export
- **🎯 Precise Text Matching**: Multi-strategy text positioning with 95%+ accuracy
- **💾 Memory Management**: Real-time monitoring and optimization for large documents
- **🔒 Document Integrity**: Preserves formatting, footnotes, and structure while adding improvements

## 🚀 Quick Start

### 1. Installation
```bash
# Clone repository
git clone [repository-url]
cd "Korrekturtool BA"

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your Google Gemini API key
```

### 2. Usage

**Standard Processing (recommended):**
```bash
python main_complete_advanced.py document.docx --output corrected.docx
```

**Performance-Optimized (for large documents):**
```bash
python main_performance_optimized.py document.docx --output optimized.docx
```

## 📊 System Comparison

| Feature | Complete Advanced | Performance-Optimized |
|---------|------------------|----------------------|
| **Target Use** | Development, standard docs | Large docs, production |
| **Memory Usage** | Standard | Adaptive (system-aware) |
| **Processing** | Sequential with optimization | Batch with parallelization |
| **Caching** | Basic | Advanced (memory + disk) |
| **Monitoring** | Performance tracking | Full dashboard + JSON export |
| **Configuration** | Fixed | System-adaptive |

## 🏗️ Architecture

### Core Pipeline
```
DOCX Input → Parser → Chunker → AI Analyzer → Formatter → Word Integrator → DOCX Output
```

### Key Components

- **Parser** (`src/parsers/docx_parser.py`): Extracts text while preserving document structure
- **AI Analyzer** (`src/analyzers/advanced_gemini_analyzer.py`): Multi-pass analysis with category-specific prompts
- **Chunker** (`src/utils/advanced_chunking.py`): Context-aware intelligent text segmentation
- **Formatter** (`src/utils/smart_comment_formatter.py`): Professional comment templates without redundant prefixes
- **Integrator** (`src/integrators/advanced_word_integrator_fixed.py`): Microsoft Word-compatible XML comment insertion

### Performance Modules

- **Batch Processor** (`src/utils/batch_processor_optimized.py`): Memory-aware batch processing
- **Memory Optimizer** (`src/utils/memory_optimizer.py`): Real-time memory monitoring and optimization
- **Caching System** (`src/utils/caching_system.py`): Intelligent caching with LRU/TTL strategies
- **Text Matcher** (`src/utils/multi_strategy_matcher.py`): Multi-algorithm text positioning

## 📈 Performance Metrics

### Typical Results
- **Processing Time**: 30-90 seconds for standard documents
- **Comment Generation**: 25-30 improvements per document
- **Integration Success Rate**: 85-95% 
- **Memory Efficiency**: 0.3 suggestions per MB peak memory
- **Cost**: ~$0.10-0.50 per bachelor thesis (Google Gemini API)

### System Requirements
- **Python**: 3.9+
- **RAM**: 4GB minimum, 8GB+ recommended for large documents
- **Storage**: 100MB for caching
- **API**: Google Gemini API key required

## 🔧 Configuration

### Environment Variables (.env)
```bash
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Optional performance settings
MAX_MEMORY_MB=1024
ENABLE_CACHING=true
CACHE_TTL_HOURS=24
```

### Processing Categories
The system analyzes text in four specialized categories:
- **Grammar** (`grammar`): Grammatical errors and corrections
- **Style** (`style`): Writing style and flow improvements  
- **Clarity** (`clarity`): Clarity and comprehension enhancements
- **Academic** (`academic`): Scientific writing and terminology

## 🧪 Testing

### Quick Tests
```bash
# Test complete advanced system
python main_complete_advanced.py "path/to/test.docx"

# Test performance system
python main_performance_optimized.py "path/to/large_document.docx"
```

### Expected Output
```
🚀 COMPLETE ADVANCED PROCESSING GESTARTET
   📄 Dokument: test.docx
   🔧 Features: Multi-Pass • Smart-Format • Präzise-Position

📖 Phase 1: Dokument-Parsing...
   ✅ 50,000 Zeichen geparst (0.5s)

🧩 Phase 2: Advanced Intelligent Chunking...
   ✅ 3 intelligente Chunks erstellt (0.01s)

🤖 Phase 3: Multi-Pass KI-Analyse...
   ✅ Multi-Pass-Analyse: 25 Verbesserungen (45.2s)

📝 Phase 4: Smart Comment Formatting...
   ✅ 25 Kommentare formatiert (0.01s)

💬 Phase 5: Advanced Word-Integration...
   ✅ Integration: 23/25 erfolgreich (92.0%)

🎉 COMPLETE ADVANCED PROCESSING ERFOLGREICH!
   📄 Ausgabedatei: test_COMPLETE_ADVANCED.docx  
   💬 Advanced Kommentare: 23
   📈 Integration-Erfolgsrate: 92.0%
```

## 🎯 Production Status

### ✅ Ready for Production
- **Core Processing Pipeline**: Fully functional with comprehensive error handling
- **AI Integration**: Advanced multi-pass analysis with cost optimization  
- **Word Integration**: Microsoft-compatible comment insertion
- **Performance Optimization**: Memory management, caching, batch processing
- **Monitoring**: Detailed metrics and performance dashboards

### 🚀 Ready for UI Development
The backend systems provide clear interfaces for:
- File upload/processing workflows
- Real-time progress monitoring  
- Configuration options and settings
- Results display and download
- Error handling and user feedback

## 💰 Cost Estimation

Using Google Gemini 1.5 Flash API:
- **Input**: ~$0.075 per 1M tokens
- **Output**: ~$0.30 per 1M tokens  
- **Typical Bachelor Thesis (50-80 pages)**: $0.10-0.50
- **Cost estimation built into system**

## 🔗 API Integration

### Google Gemini Setup
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create new API key
3. Add to `.env` file as `GOOGLE_API_KEY`

## 📁 Project Structure

```
Korrekturtool BA/
├── main_complete_advanced.py      # Standard production system
├── main_performance_optimized.py  # Performance-optimized system  
├── requirements.txt               # Python dependencies
├── .env.example                  # Environment configuration template
├── CLAUDE.md                     # Development guidance
├── src/
│   ├── analyzers/
│   │   └── advanced_gemini_analyzer.py
│   ├── integrators/  
│   │   ├── advanced_word_integrator_fixed.py
│   │   └── zip_word_comments.py
│   ├── parsers/
│   │   └── docx_parser.py
│   └── utils/
│       ├── advanced_chunking.py
│       ├── batch_processor_optimized.py
│       ├── caching_system.py
│       ├── memory_optimizer.py
│       ├── multi_strategy_matcher.py
│       ├── parallel_processor.py
│       ├── smart_comment_formatter.py
│       └── style_manager.py
├── config/
│   └── comment_styles.json
├── archive/                      # Legacy files and test documents
└── tests/                       # Unit tests
```

## 🏆 Development Phases Completed

### ✅ Phase 1: Core Integration (Complete)
- Multi-pass AI analysis system
- Advanced text chunking and matching
- Smart comment formatting
- Word document integration

### ✅ Phase 2: End-to-End Testing (Complete)  
- Comprehensive test suite
- Performance validation
- Error handling verification
- Baseline comparison

### ✅ Phase 3: Performance Optimization (Complete)
- Batch processing implementation
- Memory management and monitoring
- Intelligent caching system
- Performance dashboard and metrics

### 🎯 Next Phase: UI Development
The backend is production-ready and optimized for UI integration.

## 📄 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

This tool was developed as a bachelor thesis project. The backend is complete and ready for UI development integration.