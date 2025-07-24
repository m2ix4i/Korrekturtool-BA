# Testing Guide for Bachelor Thesis Correction Tool

This guide provides comprehensive instructions for running tests and following testing best practices in the Bachelor Thesis Correction Tool project.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Test Categories](#test-categories)
5. [Configuration](#configuration)
6. [Test Data and Fixtures](#test-data-and-fixtures)
7. [Writing New Tests](#writing-new-tests)
8. [Performance Testing](#performance-testing)
9. [Integration Testing](#integration-testing)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

## Quick Start

### Install Dependencies

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Or install production + dev dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Run Basic Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_advanced_analyzer_pytest.py

# Run tests with specific marker
pytest -m "unit"
```

## Test Structure

The test suite is organized into several categories:

```
tests/
├── conftest.py                     # Pytest fixtures and configuration
├── factories.py                    # Test data factories
├── test_utils.py                   # Test utilities and helpers
├── test_advanced_analyzer_pytest.py    # AI analyzer tests
├── test_docx_parser.py             # Document parser tests
├── test_advanced_chunking.py       # Text chunking tests
├── test_multi_strategy_matcher.py  # Text matching tests
├── test_advanced_word_integrator.py # Word integration tests
├── test_performance_suite.py       # Performance benchmarks
├── test_integration_suite.py       # End-to-end integration tests
└── archive/                        # Legacy test files
```

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# Run specific test class
pytest tests/test_advanced_analyzer_pytest.py::TestAdvancedGeminiAnalyzer

# Run specific test method
pytest tests/test_advanced_analyzer_pytest.py::TestAdvancedGeminiAnalyzer::test_analyzer_initialization
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html
# View report: open htmlcov/index.html

# Generate XML coverage report (for CI)
pytest --cov=src --cov-report=xml

# Generate terminal coverage report
pytest --cov=src --cov-report=term-missing

# Fail if coverage below threshold (configured in pytest.ini)
pytest --cov=src --cov-fail-under=80
```

### Test Selection by Markers

```bash
# Run only unit tests
pytest -m "unit"

# Run only integration tests
pytest -m "integration"

# Run only fast tests
pytest -m "fast"

# Exclude slow tests
pytest -m "not slow"

# Run tests that require API keys
pytest -m "api"

# Run tests for specific components
pytest -m "analyzer"
pytest -m "parser"
pytest -m "integrator"
pytest -m "utils"

# Combine markers
pytest -m "unit and not slow"
pytest -m "integration or e2e"
```

### Environment-Specific Testing

```bash
# Run tests requiring API key (set GOOGLE_API_KEY first)
export GOOGLE_API_KEY="your_api_key_here"
pytest -m "requires_api_key"

# Run tests with real test files
pytest -m "requires_test_files"

# Run memory-intensive tests
pytest -m "requires_large_memory"
```

## Test Categories

### Test Markers

The test suite uses pytest markers to categorize tests:

#### Performance Markers
- `slow`: Tests that take more than a few seconds
- `fast`: Quick tests that run in milliseconds
- `benchmark`: Performance benchmark tests
- `memory`: Memory usage tests
- `performance`: Performance-critical tests

#### Test Type Markers
- `unit`: Isolated unit tests (no external dependencies)
- `integration`: Tests involving multiple components
- `e2e`: End-to-end workflow tests

#### Component Markers
- `parser`: Document parsing functionality
- `analyzer`: AI analysis functionality
- `integrator`: Word document integration
- `utils`: Utility function tests

#### External Dependency Markers
- `api`: Tests requiring API keys
- `filesystem`: Tests interacting with file system
- `network`: Tests requiring network access

#### Environment Markers
- `requires_api_key`: Tests needing real API credentials
- `requires_large_memory`: Memory-intensive tests
- `requires_test_files`: Tests needing test document files

## Configuration

### pytest.ini

The main test configuration is in `pytest.ini`:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --strict-config
    --disable-warnings
    --cov=src
    --cov-report=html:htmlcov
    --cov-report=xml:coverage.xml
    --cov-report=term-missing
    --cov-branch
    --cov-fail-under=80
    --durations=10
    --maxfail=5
```

### Environment Variables

Key environment variables for testing:

```bash
# Required for AI analyzer tests
export GOOGLE_API_KEY="your_gemini_api_key"

# Test environment indicator
export TESTING="true"

# Logging level for tests
export LOG_LEVEL="DEBUG"
```

## Test Data and Fixtures

### Common Fixtures (conftest.py)

The test suite provides comprehensive fixtures:

#### Environment Fixtures
- `test_env_setup`: Session-level environment setup
- `mock_google_api_key`: Mock API key for testing
- `real_api_key`: Real API key (skips if not available)

#### File System Fixtures
- `temp_dir`: Temporary directory for test files
- `temp_docx_file`: Temporary DOCX file
- `create_test_docx`: Factory for creating test documents
- `test_document_files`: Pre-created test documents of various sizes

#### Data Fixtures
- `sample_suggestions`: Sample AI suggestions
- `sample_text_data`: Various text samples for testing
- `suggestion_factory`: Factory for creating custom suggestions
- `document_chunk_factory`: Factory for creating document chunks

#### Performance Fixtures
- `memory_monitor`: Memory usage monitoring
- `performance_timer`: Operation timing utilities

### Using Fixtures

```python
def test_example(create_test_docx, sample_suggestions, memory_monitor):
    """Example of using multiple fixtures"""
    # Create test document
    doc_path = create_test_docx("example.docx")
    
    # Monitor memory
    initial_memory = memory_monitor['initial_memory']
    
    # Use sample data
    assert len(sample_suggestions) > 0
    
    # Check memory usage
    current_memory = memory_monitor['get_current_memory']()
    assert current_memory > initial_memory
```

## Writing New Tests

### Test Structure Template

```python
"""
Test module description
"""

import pytest
from unittest.mock import Mock, patch

# Import modules under test
from src.your_module import YourClass


@pytest.mark.your_marker
@pytest.mark.unit
class TestYourClass:
    """Test suite for YourClass"""
    
    def test_basic_functionality(self, your_fixture):
        """Test basic functionality"""
        # Arrange
        instance = YourClass()
        
        # Act
        result = instance.method()
        
        # Assert
        assert result is not None
    
    @pytest.mark.parametrize("input_value,expected", [
        ("input1", "output1"),
        ("input2", "output2"),
    ])
    def test_parametrized(self, input_value, expected):
        """Test with multiple parameter sets"""
        instance = YourClass()
        result = instance.process(input_value)
        assert result == expected
    
    @pytest.mark.slow
    def test_performance_heavy_operation(self, performance_timer):
        """Test that may take longer"""
        with performance_timer.time_operation('heavy_op'):
            # Perform operation
            pass
        
        elapsed = performance_timer.get_time('heavy_op')
        assert elapsed < 10.0  # Should complete in <10 seconds


@pytest.mark.integration
class TestYourClassIntegration:
    """Integration tests for YourClass"""
    
    def test_integration_scenario(self, integration_test_data):
        """Test integration with other components"""
        # Test integration scenarios
        pass
```

### Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`
- Fixtures: Descriptive names without `test_` prefix
- Markers: Use existing markers or request new ones

### Test Data Creation

Use factories for consistent test data:

```python
from tests.factories import SuggestionFactory, DocumentFactory

def test_with_factory_data():
    # Create single suggestion
    suggestion = SuggestionFactory.create(category='grammar')
    
    # Create batch of suggestions
    suggestions = SuggestionFactory.create_batch(5, category='style')
    
    # Create test document
    doc_path = DocumentFactory.create_docx(
        template='academic_paper',
        output_path=Path('test.docx')
    )
```

## Performance Testing

### Benchmarking

Use pytest-benchmark for performance testing:

```python
def test_performance_benchmark(benchmark):
    """Benchmark function performance"""
    def operation_to_benchmark():
        # Your operation here
        return result
    
    result = benchmark(operation_to_benchmark)
    assert result is not None
```

### Memory Testing

Use memory monitoring fixtures:

```python
def test_memory_usage(memory_monitor):
    """Test memory usage of operation"""
    initial = memory_monitor['initial_memory']
    
    # Perform memory-intensive operation
    large_data = create_large_data()
    
    current = memory_monitor['get_current_memory']()
    increase = current - initial
    
    # Assert memory usage is reasonable
    assert increase < 100 * 1024 * 1024  # < 100MB
```

### Performance Assertions

```python
from tests.test_utils import PerformanceTestHelper

def test_performance_limits():
    """Test with performance limits"""
    start_time = time.time()
    
    # Perform operation
    result = expensive_operation()
    
    elapsed = time.time() - start_time
    
    # Use helper for assertions
    PerformanceTestHelper.assert_performance_limit(
        elapsed, 5.0, "expensive_operation"
    )
```

## Integration Testing

### End-to-End Testing

```python
@pytest.mark.e2e
def test_complete_workflow(integration_test_data, mock_google_api_key):
    """Test complete correction workflow"""
    input_doc = integration_test_data['input_document']
    output_doc = integration_test_data['output_document']
    
    # Mock external dependencies
    with patch('google.generativeai.GenerativeModel') as mock_model:
        # Setup mocks
        setup_api_mock(mock_model)
        
        # Run complete workflow
        result = run_correction_workflow(input_doc, output_doc)
        
        # Verify results
        assert output_doc.exists()
        assert result.success
```

### Component Integration

```python
@pytest.mark.integration
def test_parser_analyzer_integration(create_test_docx):
    """Test integration between parser and analyzer"""
    doc_path = create_test_docx("integration_test.docx")
    
    # Test component interaction
    parser = DocxParser(str(doc_path))
    analyzer = AdvancedGeminiAnalyzer()
    
    # Verify data flows correctly between components
    text = extract_text(parser)
    suggestions = analyzer.analyze_text(text)
    
    assert isinstance(suggestions, list)
```

## Best Practices

### Test Organization

1. **Group related tests** in classes
2. **Use descriptive test names** that explain what is being tested
3. **Follow the AAA pattern**: Arrange, Act, Assert
4. **Keep tests independent** - no test should depend on another
5. **Use appropriate markers** to categorize tests

### Mocking Guidelines

1. **Mock external dependencies** (APIs, file system, network)
2. **Use fixtures for common mocks**
3. **Mock at the boundary** - mock the external interface, not internal methods
4. **Verify mock interactions** when behavior matters

```python
def test_with_proper_mocking(mock_google_api_key):
    """Example of proper mocking"""
    with patch('google.generativeai.GenerativeModel') as mock_model:
        # Setup mock behavior
        mock_instance = Mock()
        mock_instance.generate_content.return_value = Mock(text='{"suggestions": []}')
        mock_model.return_value = mock_instance
        
        # Test with mock
        analyzer = AdvancedGeminiAnalyzer()
        result = analyzer.analyze_text("test")
        
        # Verify mock was called correctly
        mock_instance.generate_content.assert_called_once()
```

### Test Data Management

1. **Use factories** for consistent test data creation
2. **Keep test data minimal** but realistic
3. **Clean up test files** automatically
4. **Use temporary directories** for file operations

### Performance Testing Guidelines

1. **Set realistic performance limits**
2. **Test with appropriate data sizes**
3. **Monitor memory usage** for memory-intensive operations
4. **Use benchmarking tools** for detailed performance analysis

### Error Testing

1. **Test error conditions** explicitly
2. **Verify error messages** are helpful
3. **Test error recovery** mechanisms
4. **Mock failures** to test error handling

```python
def test_error_handling():
    """Test error handling"""
    with pytest.raises(ValueError, match="Invalid input"):
        function_that_should_fail("invalid_input")
```

## Troubleshooting

### Common Issues

#### Tests Not Found
```bash
# Make sure you're in the project root
cd /path/to/Korrekturtool-BA

# Check test discovery
pytest --collect-only
```

#### Import Errors
```bash
# Install missing dependencies
pip install -r requirements-dev.txt

# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### API Key Issues
```bash
# Set API key for tests requiring real API
export GOOGLE_API_KEY="your_api_key"

# Skip API tests if no key available
pytest -m "not api"
```

#### Memory Issues
```bash
# Run tests with less parallelism
pytest -n 2  # Instead of -n auto

# Run memory tests separately
pytest -m "not memory"
```

#### Slow Tests
```bash
# Skip slow tests during development
pytest -m "not slow"

# Run only fast tests
pytest -m "fast"

# Increase timeout for slow tests
pytest --timeout=300  # 5 minutes
```

### Debug Mode

```bash
# Run with debugging
pytest --pdb  # Drop into debugger on failure

# Verbose output
pytest -vvv

# Show local variables on failure
pytest --tb=long

# Capture output (normally suppressed)
pytest -s
```

### Test Configuration Issues

Check your `pytest.ini` configuration:

```bash
# Validate configuration
pytest --help

# Show collected tests and markers
pytest --markers

# Show fixtures
pytest --fixtures
```

### Performance Issues

```bash
# Profile test execution
pytest --durations=10  # Show 10 slowest tests

# Run tests in parallel
pytest -n auto

# Memory profiling (if pytest-memray installed)
pytest --memray
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest --cov=src --cov-report=xml
      env:
        GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

### Local CI Simulation

```bash
# Run the same tests as CI
pytest --cov=src --cov-report=xml --cov-fail-under=80

# Test in clean environment
docker run --rm -v $(pwd):/app -w /app python:3.9 \
  bash -c "pip install -r requirements-dev.txt && pytest"
```

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Factory Boy documentation](https://factoryboy.readthedocs.io/) (for advanced factories)
- [pytest-benchmark documentation](https://pytest-benchmark.readthedocs.io/)

For project-specific questions, refer to the main README.md and CLAUDE.md files.