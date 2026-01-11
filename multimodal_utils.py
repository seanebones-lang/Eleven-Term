"""
Multi-modal input support
Handles image inputs, file attachments, and other media types
"""
import base64
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import mimetypes

logger = logging.getLogger(__name__)

def encode_image_to_base64(image_path: str) -> Optional[str]:
    """Encode image file to base64
    
    Args:
        image_path: Path to image file
        
    Returns:
        Base64 encoded string with data URI prefix, or None on error
    """
    try:
        image_path_obj = Path(image_path)
        if not image_path_obj.exists():
            logger.error(f"Image file not found: {image_path}")
            return None
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(str(image_path_obj))
        if not mime_type or not mime_type.startswith('image/'):
            logger.error(f"File is not an image: {image_path}")
            return None
        
        # Read and encode
        with open(image_path_obj, 'rb') as f:
            image_data = f.read()
        
        base64_data = base64.b64encode(image_data).decode('utf-8')
        
        # Return data URI format
        return f"data:{mime_type};base64,{base64_data}"
    except Exception as e:
        logger.error(f"Error encoding image {image_path}: {e}")
        return None

def prepare_multimodal_message(
    text: str,
    image_paths: Optional[List[str]] = None,
    file_paths: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Prepare multi-modal message for API
    
    Args:
        text: Text content
        image_paths: List of image file paths
        file_paths: List of other file paths (will be read as text)
        
    Returns:
        List of message content parts (text and images)
    """
    content = []
    
    # Add text content
    if text:
        content.append({
            "type": "text",
            "text": text
        })
    
    # Add images
    if image_paths:
        for image_path in image_paths:
            encoded = encode_image_to_base64(image_path)
            if encoded:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": encoded
                    }
                })
            else:
                logger.warning(f"Could not encode image: {image_path}")
    
    # Add file contents as text
    if file_paths:
        for file_path in file_paths:
            try:
                file_path_obj = Path(file_path)
                if file_path_obj.exists():
                    with open(file_path_obj, 'r', encoding='utf-8', errors='ignore') as f:
                        file_content = f.read()
                    
                    content.append({
                        "type": "text",
                        "text": f"\n\n[File: {file_path_obj.name}]\n{file_content}"
                    })
                else:
                    logger.warning(f"File not found: {file_path}")
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
    
    return content

def create_multimodal_messages(
    user_text: str,
    image_paths: Optional[List[str]] = None,
    file_paths: Optional[List[str]] = None,
    system_prompt: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Create multi-modal messages list for API call
    
    Args:
        user_text: User's text message
        image_paths: List of image file paths
        file_paths: List of file paths to include
        system_prompt: Optional system prompt
        
    Returns:
        List of message dicts ready for API
    """
    messages = []
    
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })
    
    # Prepare multi-modal content
    content = prepare_multimodal_message(user_text, image_paths, file_paths)
    
    messages.append({
        "role": "user",
        "content": content
    })
    
    return messages

def extract_images_from_message(message: Dict[str, Any]) -> List[str]:
    """Extract image URLs/paths from message
    
    Args:
        message: Message dict
        
    Returns:
        List of image URLs or paths
    """
    images = []
    
    content = message.get("content", [])
    if isinstance(content, str):
        # Plain text message, no images
        return images
    
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "image_url":
                    url = item.get("image_url", {}).get("url", "")
                    if url:
                        images.append(url)
    
    return images

def validate_image_file(image_path: str) -> tuple[bool, Optional[str]]:
    """Validate image file
    
    Args:
        image_path: Path to image file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    image_path_obj = Path(image_path)
    
    if not image_path_obj.exists():
        return False, f"Image file not found: {image_path}"
    
    if not image_path_obj.is_file():
        return False, f"Path is not a file: {image_path}"
    
    # Check file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if image_path_obj.stat().st_size > max_size:
        return False, f"Image file too large (max 10MB): {image_path}"
    
    # Check MIME type
    mime_type, _ = mimetypes.guess_type(str(image_path_obj))
    if not mime_type or not mime_type.startswith('image/'):
        return False, f"File is not an image: {image_path}"
    
    return True, None