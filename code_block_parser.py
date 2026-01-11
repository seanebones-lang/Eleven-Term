#!/usr/bin/env python3
"""
Parse code blocks from AI responses and automatically create files
"""

import re
import os
from typing import List, Tuple, Dict, Any


def extract_code_blocks(response: str) -> List[Tuple[str, str, str]]:
    """
    Extract code blocks from markdown format: ```language\ncode\n``` or ```filename\ncode\n```
    
    Returns:
        List of (filename, language, code) tuples
    """
    code_blocks = []
    
    # Pattern 1: Standard markdown code blocks with language
    # ```python\ncode\n```
    pattern1 = r'```(\w+)?\n(.*?)```'
    matches1 = re.finditer(pattern1, response, re.DOTALL)
    
    for match in matches1:
        language = match.group(1) or 'txt'
        code = match.group(2).strip()
        
        # Try to infer filename from language and context
        filename = None
        
        # Look for filename hints before the code block
        context_start = max(0, match.start() - 200)
        context = response[context_start:match.start()]
        
        # Pattern: "**`filename`**" or "`filename`" or "filename:" before code block
        filename_patterns = [
            r'\*\*`([a-zA-Z0-9_./-]+\.\w+)`\*\*',
            r'`([a-zA-Z0-9_./-]+\.\w+)`',
            r'([a-zA-Z0-9_./-]+\.(?:py|js|ts|jsx|tsx|json|md|txt|yml|yaml|toml|rs|go|java|kt|swift|cpp|c|h|hpp|rb|php|sh|bash|zsh|fish|html|css|sql|dockerfile|makefile)):',
            r'file[:\s]+([a-zA-Z0-9_./-]+\.\w+)',
            r'create[:\s]+([a-zA-Z0-9_./-]+\.\w+)',
            r'save[:\s]+([a-zA-Z0-9_./-]+\.\w+)',
        ]
        
        for pattern in filename_patterns:
            filename_match = re.search(pattern, context, re.IGNORECASE)
            if filename_match:
                filename = filename_match.group(1).strip()
                break
        
        # If no filename found, try language-based defaults
        if not filename:
            lang_to_ext = {
                'python': 'py',
                'javascript': 'js',
                'typescript': 'ts',
                'jsx': 'jsx',
                'tsx': 'tsx',
                'json': 'json',
                'markdown': 'md',
                'yaml': 'yml',
                'toml': 'toml',
                'rust': 'rs',
                'go': 'go',
                'java': 'java',
                'kotlin': 'kt',
                'swift': 'swift',
                'cpp': 'cpp',
                'c': 'c',
                'html': 'html',
                'css': 'css',
                'sql': 'sql',
                'bash': 'sh',
                'shell': 'sh',
                'dockerfile': 'Dockerfile',
                'makefile': 'Makefile',
            }
            ext = lang_to_ext.get(language.lower(), 'txt')
            filename = f"code.{ext}"
        
        code_blocks.append((filename, language, code))
    
    # Pattern 2: Code blocks with filename in first line
    # ```filename.py\ncode\n```
    pattern2 = r'```([a-zA-Z0-9_./-]+\.\w+)\n(.*?)```'
    matches2 = re.finditer(pattern2, response, re.DOTALL)
    
    for match in matches2:
        filename = match.group(1).strip()
        code = match.group(2).strip()
        # Infer language from extension
        ext = filename.split('.')[-1] if '.' in filename else 'txt'
        ext_to_lang = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'jsx': 'jsx',
            'tsx': 'tsx',
            'json': 'json',
            'md': 'markdown',
            'yml': 'yaml',
            'yaml': 'yaml',
            'toml': 'toml',
            'rs': 'rust',
            'go': 'go',
            'java': 'java',
            'kt': 'kotlin',
            'swift': 'swift',
            'cpp': 'cpp',
            'c': 'c',
            'html': 'html',
            'css': 'css',
            'sql': 'sql',
            'sh': 'bash',
        }
        language = ext_to_lang.get(ext, ext)
        code_blocks.append((filename, language, code))
    
    # Deduplicate (keep first occurrence)
    seen = set()
    unique_blocks = []
    for filename, language, code in code_blocks:
        key = (filename, code[:100])  # Use first 100 chars as key
        if key not in seen:
            seen.add(key)
            unique_blocks.append((filename, language, code))
    
    return unique_blocks


def create_files_from_code_blocks(code_blocks: List[Tuple[str, str, str]], base_path: str = ".") -> List[Tuple[str, bool, str]]:
    """
    Create files from code blocks
    
    Returns:
        List of (filename, success, message) tuples
    """
    results = []
    
    for filename, language, code in code_blocks:
        # Clean filename (remove any path traversal attempts)
        filename = os.path.basename(filename)
        filepath = os.path.join(base_path, filename)
        
        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
            
            # Write file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(code)
            
            results.append((filename, True, f"Created {filename} ({len(code)} bytes)"))
        except Exception as e:
            results.append((filename, False, f"Failed to create {filename}: {str(e)}"))
    
    return results
