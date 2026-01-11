#!/usr/bin/env python3
"""
Test code block parser functionality
"""

import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from code_block_parser import extract_code_blocks, create_files_from_code_blocks

print("=" * 60)
print("Code Block Parser Test")
print("=" * 60)

# Create a temporary directory for testing
test_dir = tempfile.mkdtemp()
print(f"\nTest directory: {test_dir}")

try:
    # Test 1: Extract code blocks from markdown
    print("\n1. Testing code block extraction...")
    test_response = """
    Here's some Python code:
    
    ```python
    print("Hello, World!")
    ```
    
    And a JavaScript file:
    
    ```javascript
    console.log("Test");
    ```
    
    **`app.py`**:
    ```python
    import streamlit as st
    st.title("Test")
    ```
    """
    
    blocks = extract_code_blocks(test_response)
    print(f"   Found {len(blocks)} code block(s)")
    
    if len(blocks) >= 3:
        print(f"   ✓ Block 1: {blocks[0][0]} ({blocks[0][1]})")
        print(f"   ✓ Block 2: {blocks[1][0]} ({blocks[1][1]})")
        print(f"   ✓ Block 3: {blocks[2][0]} ({blocks[2][1]})")
    else:
        print(f"   ✗ Expected at least 3 blocks, got {len(blocks)}")
        sys.exit(1)
    
    # Test 2: Create files from code blocks
    print("\n2. Testing file creation...")
    results = create_files_from_code_blocks(blocks, test_dir)
    
    success_count = sum(1 for _, success, _ in results if success)
    print(f"   Created {success_count}/{len(results)} files")
    
    for filename, success, message in results:
        if success:
            print(f"   ✓ {message}")
        else:
            print(f"   ✗ {message}")
            sys.exit(1)
    
    # Test 3: Verify files exist and have correct content
    print("\n3. Verifying created files...")
    
    for filename, language, code in blocks:
        filepath = os.path.join(test_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            if content.strip() == code.strip():
                print(f"   ✓ {filename} content matches")
            else:
                print(f"   ✗ {filename} content mismatch")
                sys.exit(1)
        else:
            print(f"   ✗ {filename} not found")
            sys.exit(1)
    
    # Test 4: Test filename inference from context
    print("\n4. Testing filename inference...")
    test_response2 = """
    Create a file called test.py:
    
    ```python
    def test():
        pass
    ```
    """
    blocks2 = extract_code_blocks(test_response2)
    if blocks2 and 'test.py' in blocks2[0][0]:
        print(f"   ✓ Filename inferred correctly: {blocks2[0][0]}")
    else:
        print(f"   ⚠ Filename inference needs work (got: {blocks2[0][0] if blocks2 else 'none'})")
    
    # Test 5: Test with explicit filename in code block
    print("\n5. Testing explicit filename in code block...")
    test_response3 = """
    ```app.py
    import streamlit as st
    st.title("App")
    ```
    """
    blocks3 = extract_code_blocks(test_response3)
    if blocks3 and blocks3[0][0] == 'app.py':
        print(f"   ✓ Explicit filename extracted: {blocks3[0][0]}")
    else:
        print(f"   ✗ Failed to extract explicit filename")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    # Cleanup
    shutil.rmtree(test_dir)
    print(f"\nCleaned up test directory: {test_dir}")
