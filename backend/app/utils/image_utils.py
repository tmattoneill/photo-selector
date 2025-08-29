import hashlib
import base64
import os
from typing import Tuple, Optional
from PIL import Image
import magic


def get_sha256_hash(file_path: str) -> str:
    """Generate SHA-256 hash from file content."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_image_dimensions(file_path: str) -> Tuple[int, int]:
    """Get image width and height."""
    try:
        with Image.open(file_path) as img:
            return img.size
    except Exception:
        return (0, 0)


def get_mime_type(file_path: str) -> str:
    """Get MIME type using python-magic."""
    try:
        mime = magic.Magic(mime=True)
        return mime.from_file(file_path)
    except Exception:
        # Fallback to extension-based detection
        ext = os.path.splitext(file_path)[1].lower()
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg', 
            '.png': 'image/png',
            '.webp': 'image/webp'
        }
        return mime_map.get(ext, 'application/octet-stream')


def encode_image_to_base64(file_path: str) -> str:
    """Convert image file to base64 data URL."""
    mime_type = get_mime_type(file_path)
    with open(file_path, 'rb') as f:
        encoded = base64.b64encode(f.read()).decode('utf-8')
        return f"data:{mime_type};base64,{encoded}"


def is_supported_image(file_path: str, supported_formats: tuple) -> bool:
    """Check if file is a supported image format."""
    if not os.path.isfile(file_path):
        return False
    
    # Check extension
    ext = os.path.splitext(file_path)[1].lower().lstrip('.')
    if ext not in supported_formats:
        return False
    
    # Verify MIME type
    mime_type = get_mime_type(file_path)
    return mime_type.startswith('image/')


def get_file_size(file_path: str) -> int:
    """Get file size in bytes."""
    try:
        return os.path.getsize(file_path)
    except Exception:
        return 0