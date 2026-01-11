"""Tests for multi-modal utilities"""
import pytest
import tempfile
from pathlib import Path
from multimodal_utils import (
    encode_image_to_base64, prepare_multimodal_message,
    create_multimodal_messages, validate_image_file
)

def test_encode_image_to_base64_nonexistent():
    """Test encoding non-existent image"""
    result = encode_image_to_base64("/nonexistent/image.png")
    assert result is None

def test_prepare_multimodal_message_text_only():
    """Test preparing message with text only"""
    content = prepare_multimodal_message("Hello world")
    assert len(content) == 1
    assert content[0]["type"] == "text"
    assert content[0]["text"] == "Hello world"

def test_create_multimodal_messages():
    """Test creating multi-modal messages"""
    messages = create_multimodal_messages("Hello", image_paths=None, file_paths=None)
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert isinstance(messages[0]["content"], list)

def test_validate_image_file_nonexistent():
    """Test validating non-existent image"""
    valid, error = validate_image_file("/nonexistent/image.png")
    assert not valid
    assert "not found" in error.lower()