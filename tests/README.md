# gemsparcl Test Suite

This directory contains the test suite for gemsparcl.

## Test Structure

- `conftest.py` - Pytest fixtures and configuration
- `test_clustering.py` - Tests for clustering functions
- `test_sketching.py` - Tests for sketching and sketchlib integration
- `test_cli.py` - Tests for command-line interface
- `test_integration.py` - End-to-end integration tests

## Running Tests

### Run all tests:
```bash
pytest tests/
```

### Run with coverage:
```bash
pytest tests/ --cov=gemsparcl --cov-report=html
```

### Run specific test file:
```bash
pytest tests/test_clustering.py
```

### Run specific test:
```bash
pytest tests/test_clustering.py::TestCreateGraph::test_create_graph_simple
```

### Skip slow tests:
```bash
pytest tests/ -m "not slow"
```

### Run only integration tests:
```bash
pytest tests/test_integration.py
```

## Test Categories

### Unit Tests
- `test_clustering.py` - Tests core clustering logic
- `test_sketching.py` - Tests sketching validation and setup

### CLI Tests
- `test_cli.py` - Tests command-line interface

### Integration Tests
- `test_integration.py` - Full workflow tests with real data
- Some tests are skipped if:
  - sketchlib is not available
  - E. coli test dataset is not available

## Adding New Tests

1. Create test file: `test_<module_name>.py`
2. Import the module to test
3. Create test classes: `class TestFeatureName`
4. Write test functions: `def test_specific_behavior()`
5. Use fixtures from `conftest.py` for common setup

### Example Test:
```python
def test_my_feature(tmp_dir):
    \"\"\"Test description.\"\"\"
    # Arrange
    input_data = prepare_test_data()

    # Act
    result = my_function(input_data)

    # Assert
    assert result == expected_output
```

## Coverage Goals

- Target: >80% code coverage
- Focus on:
  - Core clustering algorithms
  - Graph creation and refinement
  - CLI option handling
  - Error handling

## CI/CD

Tests are automatically run on:
- Every push to main
- Every pull request
- Before releases

See `.github/workflows/tests.yml` for CI configuration.
