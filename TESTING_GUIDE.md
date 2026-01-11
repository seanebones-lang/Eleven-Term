# Testing Guide - NextEleven Terminal Agent
## Complete Guide to Testing the eleven Agent
**Version:** 1.0  
**Last Updated:** January 2026

---

## 📖 Table of Contents

1. [Quick Start](#quick-start)
2. [Setting Up Testing](#setting-up-testing)
3. [Running Tests](#running-tests)
4. [Manual Testing](#manual-testing)
5. [Integration Testing](#integration-testing)
6. [Security Testing](#security-testing)
7. [Performance Testing](#performance-testing)
8. [Troubleshooting Tests](#troubleshooting-tests)

---

## Quick Start

### Run All Tests (Fastest Way)

```bash
# Install test dependencies
pip3 install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

---

## Setting Up Testing

### 1. Install Test Dependencies

```bash
# Install all development dependencies
pip3 install -r requirements-dev.txt

# Or install individually
pip3 install pytest pytest-cov pytest-asyncio pytest-mock
pip3 install black flake8 mypy isort bandit
```

### 2. Verify Installation

```bash
# Check pytest is installed
pytest --version

# Check all tools are available
pytest --help
python3 -m pytest --help
```

### 3. Check Test Structure

```bash
# List test files
ls -la tests/

# Expected output:
# __init__.py
# conftest.py
# test_security_utils.py
# test_grok_agent.py
# test_integration.py
```

---

## Running Tests

### Unit Tests

#### Run All Unit Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with extra verbose output (shows print statements)
pytest -v -s
```

#### Run Specific Test Files

```bash
# Test security utilities only
pytest tests/test_security_utils.py

# Test grok agent only
pytest tests/test_grok_agent.py

# Test integration tests only
pytest tests/test_integration.py
```

#### Run Specific Test Classes

```bash
# Run specific test class
pytest tests/test_security_utils.py::TestSanitizeInput

# Run specific test function
pytest tests/test_security_utils.py::TestSanitizeInput::test_sanitize_normal_input
```

#### Run Tests by Marker

```bash
# Run only security tests
pytest -m security

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Coverage Reports

#### Terminal Coverage Report

```bash
# Run with coverage (terminal output)
pytest --cov=. --cov-report=term-missing

# Run with coverage (detailed)
pytest --cov=. --cov-report=term-missing --cov-report=html
```

#### HTML Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html

# Open in browser (macOS)
open htmlcov/index.html

# View coverage statistics
coverage report
```

#### Coverage Thresholds

```bash
# Fail if coverage below threshold
pytest --cov=. --cov-fail-under=80
```

### Test Output Options

```bash
# Minimal output
pytest -q

# Verbose output
pytest -v

# Very verbose (show local variables)
pytest -vv

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Stop after N failures
pytest --maxfail=3

# Show slowest tests
pytest --durations=10
```

---

## Manual Testing

### 1. Installation Testing

```bash
# Test the installer
./install.sh

# Verify installation
ls -la ~/.grok_terminal/
cat ~/.zshrc | grep grok
```

**Expected:**
- Files copied to `~/.grok_terminal/`
- `grok.zsh` sourced in `~/.zshrc`
- API key stored in Keychain

### 2. Basic Functionality Testing

#### Test Prefix Mode

```bash
# Restart terminal or reload zsh
source ~/.zshrc

# Test basic query (without API - should show error or help)
NextEleven AI: hello

# Test with flags
NextEleven AI: help --no-log
```

**Expected:**
- Prefix detected correctly
- Query parsed correctly
- Flags processed correctly

#### Test Interactive Mode

```bash
# Start interactive mode
grok

# Test help command
/help

# Test exit
exit
```

**Expected:**
- Interactive mode starts
- Slash commands work
- Exit works correctly

### 3. Command Execution Testing

#### Test Safe Commands

```bash
# Test safe command (should prompt for confirmation)
NextEleven AI: list files in current directory

# Answer prompts:
# Execute? [y/n/e(dit)]: y
```

**Expected:**
- Command preview shown
- Risk level displayed (SAFE)
- Confirmation prompt appears
- Command executes after 'y'

#### Test Dangerous Commands

```bash
# Test dangerous command (should require --force)
NextEleven AI: remove all files in temp directory

# Should show:
# Risk: DANGEROUS
# Requires --force for dangerous commands
```

**Expected:**
- Dangerous command detected
- Requires `--force` flag
- Blocked without flag

#### Test Force Flag

```bash
# Test with force flag
NextEleven AI: remove test file --force

# Should prompt for confirmation even with --force
# Execute? [y/n/e(dit)]: n
```

**Expected:**
- Command allowed with `--force`
- Still requires confirmation
- Doesn't execute if 'n'

#### Test Command Editing

```bash
# Test edit option
NextEleven AI: list files

# Answer prompt:
# Execute? [y/n/e(dit)]: e

# Should open vim with command
# Edit command, save and quit
# Command executes with edits
```

**Expected:**
- vim opens with command
- Edits are saved
- Modified command executes

### 4. API Integration Testing

#### Test API Connection (Requires Valid API Key)

```bash
# Test quota check
grok --interactive
# Type: 1 (Yes)
# Should check API quota
```

**Expected:**
- API key retrieved from Keychain
- Quota check succeeds (if API key valid)
- Interactive mode starts

#### Test API Calls (Requires Valid API Key)

```bash
# Test actual API call
NextEleven AI: explain what ls -la does

# Should stream response from API
```

**Expected:**
- Response streams in real-time
- Commands extracted if present
- History saved

### 5. History & Context Testing

#### Test History Persistence

```bash
# Make a query
NextEleven AI: hello

# Make another query
NextEleven AI: what was my last question?

# Check history file
cat ~/.grok_terminal_history.json
```

**Expected:**
- History file exists
- Previous query saved
- Context maintained

#### Test History Compaction

```bash
# Make many queries (more than 20)
# History should automatically compact
cat ~/.grok_terminal_history.json | wc -l
```

**Expected:**
- History compacts when > 20 messages
- Summarization happens
- Context preserved

### 6. Tool Calling Testing

#### Test View Tool

```bash
# In interactive mode
grok
You: read the README file
```

**Expected:**
- View tool called
- File contents displayed
- Tool result shown

#### Test Bash Tool

```bash
# In interactive mode
grok
You: run git status
```

**Expected:**
- Bash tool called
- Command executed
- Results displayed

#### Test Edit Tool

```bash
# In interactive mode
grok
You: edit the config file
```

**Expected:**
- Edit tool called
- vim opens
- File can be edited

### 7. Security Testing

#### Test Input Sanitization

```bash
# Test with malicious input
NextEleven AI: "'; rm -rf /; echo '"

# Should sanitize input
# Should not execute dangerous commands
```

**Expected:**
- Input sanitized
- Dangerous patterns blocked
- No execution without confirmation

#### Test Command Injection Prevention

```bash
# Test command injection attempts
NextEleven AI: list files && rm -rf /

# Should detect injection attempt
# Should require confirmation
```

**Expected:**
- Command injection detected
- Blocked or requires confirmation
- Safe execution

#### Test File Permissions

```bash
# Check file permissions
ls -la ~/.grok_terminal_history.json
ls -la ~/.grok_terminal_config.json

# Should be 600 (rw-------)
```

**Expected:**
- History file: 600 permissions
- Config file: 600 permissions
- Secure file access

### 8. Configuration Testing

#### Test Default Configuration

```bash
# Run without config file
rm ~/.grok_terminal_config.json
NextEleven AI: help

# Should use defaults
```

**Expected:**
- Defaults loaded
- Works without config file
- No errors

#### Test Custom Configuration

```bash
# Create custom config
cat > ~/.grok_terminal_config.json << EOF
{
  "model": "grok-beta",
  "temperature": 0.2,
  "max_tokens": 4096
}
EOF

# Test with custom config
NextEleven AI: help

# Should use custom values
```

**Expected:**
- Custom config loaded
- Values applied correctly
- No errors

#### Test Invalid Configuration

```bash
# Create invalid config
cat > ~/.grok_terminal_config.json << EOF
{
  "temperature": 5.0,
  "max_tokens": -100
}
EOF

# Should handle gracefully
NextEleven AI: help
```

**Expected:**
- Invalid values detected
- Defaults used for invalid entries
- No crashes

---

## Integration Testing

### 1. Full Workflow Test

```bash
# Complete workflow from start to finish
./install.sh
source ~/.zshrc
NextEleven AI: list files
# Answer: y
grok
# Type: 1 (Yes)
You: help
/help
exit
```

**Expected:**
- Installation works
- Prefix mode works
- Interactive mode works
- All commands work
- Exit works

### 2. Error Handling Test

#### Test API Failures

```bash
# Test with invalid API key
security delete-generic-password -s grok-terminal -a xai-api-key
NextEleven AI: hello

# Should show helpful error
```

**Expected:**
- Error message shown
- Helpful instructions
- No crash

#### Test Network Failures

```bash
# Disable network (unplug ethernet/disable WiFi)
NextEleven AI: hello

# Should handle gracefully or show offline message
```

**Expected:**
- Graceful error handling
- Offline fallback (if implemented)
- No crash

#### Test File System Errors

```bash
# Test with read-only directory
chmod 444 ~/.grok_terminal/
NextEleven AI: hello

# Should handle gracefully
chmod 755 ~/.grok_terminal/  # Restore
```

**Expected:**
- Error handled gracefully
- Helpful error message
- No crash

### 3. Concurrent Access Test

```bash
# Test file locking
# Terminal 1
NextEleven AI: hello

# Terminal 2 (simultaneously)
NextEleven AI: help

# Both should work without corruption
```

**Expected:**
- File locking works
- No corruption
- Both commands succeed

---

## Security Testing

### 1. Command Injection Tests

```bash
# Test various injection patterns
NextEleven AI: "test; rm -rf /"
NextEleven AI: "test | rm -rf /"
NextEleven AI: "test && rm -rf /"
NextEleven AI: "test || rm -rf /"
NextEleven AI: "$(rm -rf /)"
NextEleven AI: "`rm -rf /`"
```

**Expected:**
- All injection attempts blocked
- Commands not executed
- Security maintained

### 2. Path Traversal Tests

```bash
# Test path traversal attempts
NextEleven AI: "../../../etc/passwd"
NextEleven AI: "~/.ssh/id_rsa"
```

**Expected:**
- Path traversal blocked
- Restricted to safe directories
- Security maintained

### 3. Input Validation Tests

```bash
# Test with various malicious inputs
NextEleven AI: "<script>alert('xss')</script>"
NextEleven AI: "'; DROP TABLE users; --"
NextEleven AI: "\x00\x01\x02"
```

**Expected:**
- Malicious input sanitized
- No execution
- Safe handling

---

## Performance Testing

### 1. Response Time Tests

```bash
# Measure response time
time NextEleven AI: help

# Should complete in reasonable time (< 5 seconds)
```

**Expected:**
- Response time < 5 seconds (with API)
- Caching improves subsequent requests
- Reasonable performance

### 2. Memory Usage Tests

```bash
# Monitor memory usage
ps aux | grep grok_agent.py

# Should use reasonable memory (< 100MB)
```

**Expected:**
- Memory usage reasonable
- No memory leaks
- Efficient resource usage

### 3. Cache Performance

```bash
# Test caching
NextEleven AI: help
# First call: API call
NextEleven AI: help
# Second call: Should use cache (faster)
```

**Expected:**
- Cache hit on repeated queries
- Faster response time
- Cache works correctly

---

## Automated Test Execution

### Run All Tests in Sequence

```bash
#!/bin/bash
# test_all.sh

echo "=== Running Unit Tests ==="
pytest tests/test_security_utils.py -v
pytest tests/test_grok_agent.py -v

echo "=== Running Integration Tests ==="
pytest tests/test_integration.py -v

echo "=== Running with Coverage ==="
pytest --cov=. --cov-report=term-missing

echo "=== Security Scan ==="
bandit -r . -f json -o bandit-report.json

echo "=== Linting ==="
flake8 . --max-line-length=100

echo "=== Type Checking ==="
mypy grok_agent.py security_utils.py

echo "=== All Tests Complete ==="
```

### CI/CD Test Script

```bash
#!/bin/bash
# ci_test.sh - For continuous integration

set -e  # Exit on error

echo "Installing dependencies..."
pip3 install -r requirements-dev.txt

echo "Running tests..."
pytest --cov=. --cov-fail-under=80

echo "Security scan..."
bandit -r . -ll

echo "Linting..."
flake8 . --max-line-length=100 --count

echo "Type checking..."
mypy grok_agent.py security_utils.py || true

echo "All CI checks passed!"
```

---

## Testing Checklist

### Pre-Release Testing Checklist

#### Installation
- [ ] Installer works on clean macOS
- [ ] All dependencies installed correctly
- [ ] Files copied to correct locations
- [ ] API key stored securely
- [ ] zshrc updated correctly

#### Basic Functionality
- [ ] Prefix mode works
- [ ] Interactive mode works
- [ ] Slash commands work
- [ ] Help command works
- [ ] Exit works

#### Command Execution
- [ ] Safe commands execute
- [ ] Dangerous commands blocked
- [ ] Force flag works
- [ ] Command editing works
- [ ] Preview shows correctly
- [ ] Confirmation prompts work

#### API Integration
- [ ] API key retrieval works
- [ ] API calls succeed
- [ ] Streaming works
- [ ] Error handling works
- [ ] Rate limiting handled

#### History & Context
- [ ] History saves correctly
- [ ] History loads correctly
- [ ] Context maintained
- [ ] Compaction works
- [ ] Todos persist

#### Security
- [ ] Input sanitization works
- [ ] Command injection prevented
- [ ] File permissions correct
- [ ] API key secure
- [ ] Dangerous patterns blocked

#### Configuration
- [ ] Default config works
- [ ] Custom config works
- [ ] Invalid config handled
- [ ] Config validation works

#### Error Handling
- [ ] API failures handled
- [ ] Network failures handled
- [ ] File system errors handled
- [ ] Invalid input handled
- [ ] Graceful degradation

#### Performance
- [ ] Response time acceptable
- [ ] Memory usage reasonable
- [ ] Caching works
- [ ] No memory leaks

#### Integration
- [ ] Full workflow works
- [ ] Concurrent access works
- [ ] File locking works
- [ ] No data corruption

---

## Troubleshooting Tests

### Common Issues

#### "pytest: command not found"

**Solution:**
```bash
pip3 install pytest
# Or
pip3 install -r requirements-dev.txt
```

#### "ModuleNotFoundError: No module named 'grok_agent'"

**Solution:**
```bash
# Make sure you're in the project directory
cd "/Users/nexteleven/Desktop/Eleven in your Terminal/Eleven-Term"

# Run tests from project root
pytest
```

#### "Permission denied" errors

**Solution:**
```bash
# Fix permissions
chmod +x install.sh
chmod +x tests/*.py
```

#### Tests hang or timeout

**Solution:**
```bash
# Run with timeout
pytest --timeout=10

# Or increase timeout in pytest.ini
```

#### Coverage report not generated

**Solution:**
```bash
# Install coverage
pip3 install pytest-cov

# Run with coverage
pytest --cov=. --cov-report=html
```

---

## Test Results Interpretation

### Understanding Coverage Reports

**Good Coverage:**
- 80%+ overall coverage
- 90%+ for critical functions
- 100% for security functions

**Coverage Types:**
- **Statement Coverage**: Lines of code executed
- **Branch Coverage**: Both branches of conditionals
- **Function Coverage**: Functions called
- **Line Coverage**: Lines executed

### Understanding Test Output

**Passed Tests:**
```
tests/test_security_utils.py::TestSanitizeInput::test_sanitize_normal_input PASSED
```

**Failed Tests:**
```
tests/test_security_utils.py::TestSanitizeInput::test_sanitize_normal_input FAILED
AssertionError: assert 'ls' == 'ls -la'
```

**Skipped Tests:**
```
tests/test_integration.py::TestFullWorkflow::test_api_integration SKIPPED
```

---

## Best Practices

### 1. Write Tests First (TDD)
- Write tests before implementing features
- Ensure tests fail first
- Then implement to pass

### 2. Test Edge Cases
- Test boundary conditions
- Test invalid input
- Test error cases
- Test empty/null values

### 3. Keep Tests Simple
- One assertion per test (when possible)
- Clear test names
- Independent tests
- No test dependencies

### 4. Mock External Dependencies
- Mock API calls
- Mock file system
- Mock Keychain access
- Use pytest fixtures

### 5. Run Tests Frequently
- Run tests before committing
- Run tests after changes
- Run tests in CI/CD
- Keep tests passing

---

## Quick Reference

### Common Test Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test
pytest tests/test_security_utils.py::test_sanitize_normal_input

# Run with verbose output
pytest -v -s

# Run only failed tests
pytest --lf

# Run only new tests
pytest --ff

# List all tests
pytest --collect-only
```

### Test File Structure

```
tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── test_security_utils.py    # Security tests
├── test_grok_agent.py        # Main agent tests
└── test_integration.py       # Integration tests
```

---

## Resources

- **pytest Documentation**: https://docs.pytest.org/
- **Coverage.py Documentation**: https://coverage.readthedocs.io/
- **pytest-cov Documentation**: https://pytest-cov.readthedocs.io/

---

**Made with ❤️ for thorough testing**
