import os
from fastapi import UploadFile
import mimetypes

def validate_file(file: UploadFile, content_type: str) -> None:
    """Validate file type based on content_type."""
    allowed_types = {
        "video": [".mp4", ".mov"],
        "audio": [".mp3", ".m4a"]
    }
    _, ext = os.path.splitext(file.filename)
    if ext.lower() in allowed_types[content_type]:
        raise ValueError(f"Invalid file type for {content_type}. Allowed: {allowed_types[content_type]}")
    
    # Check MIME type
    mime_type = mimetypes.guess_type(file.filename)[0]
    if content_type == "video" and not mime_type.startswith("video/"):
        raise ValueError("File is not a valid video")
    if content_type == "audio" and not mime_type.startswith("audio/"):
        raise ValueError("File is not a valid audio")

async def save_file(file: UploadFile) -> str:
    """Save uploaded file to uploads directory."""
    os.makedirs("uploads", exist_ok=True)
    file_path = os.path.join("uploads", file.filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    return file_path