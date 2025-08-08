# BFI Signals - Crush Configuration

## Build/Lint/Test Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the main application
python main.py

# Run a single test file
python test_file_name.py

# Run specific tests (if pytest is available)
pytest test_file_name.py::test_function_name

# Test Discord connection
python main.py --test-connection

# Generate signals for testing
python main.py --test
```

## Code Style Guidelines

### Imports
- Standard library imports first
- Third-party libraries next
- Local project imports last
- Separate groups with blank lines

### Naming Conventions
- snake_case for variables and functions
- PascalCase for classes
- UPPERCASE for constants

### Formatting
- 4-space indentation
- ~88 character line length
- Spaces around operators
- Blank lines between functions

### Type Hinting
- Use type hints for function parameters and return values
- Common patterns: Dict[str, Any], pd.DataFrame, Optional[str]

### Error Handling
- Use try/except with specific exception types
- Log errors appropriately
- Provide fallback mechanisms when possible

### Comments and Docstrings
- Google-style docstrings with Args/Returns sections
- Inline comments for complex logic
- F-strings for string formatting