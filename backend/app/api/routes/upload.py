import os
import hashlib
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.directory_service import DirectoryService
from ...models.image import Image

router = APIRouter()

UPLOAD_DIR = "/app/uploads"
ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB per file

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_images(
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload multiple images and add them to the database."""
    
    if not images:
        raise HTTPException(status_code=400, detail="No images provided")
    
    # Log the upload attempt
    print(f"Received {len(images)} files for upload")
    
    uploaded_count = 0
    errors = []
    
    # Initialize directory service
    directory_service = DirectoryService(db)
    directory_service.root_directory = UPLOAD_DIR
    
    for image in images:
        try:
            # Validate file type
            if image.content_type not in ALLOWED_TYPES:
                errors.append(f"{image.filename}: Unsupported file type {image.content_type}")
                continue
            
            # Read file content
            content = await image.read()
            
            # Validate file size
            if len(content) > MAX_FILE_SIZE:
                errors.append(f"{image.filename}: File too large ({len(content)} bytes)")
                continue
            
            # Generate SHA256 hash
            sha256_hash = hashlib.sha256(content).hexdigest()
            
            # Check if image already exists
            existing = db.query(Image).filter(Image.sha256 == sha256_hash).first()
            if existing:
                errors.append(f"{image.filename}: Image already exists (duplicate)")
                continue
            
            # Save file with SHA256 as filename
            file_extension = os.path.splitext(image.filename)[1] or '.jpg'
            file_path = os.path.join(UPLOAD_DIR, f"{sha256_hash}{file_extension}")
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Get image dimensions (simplified)
            width, height = 1920, 1080  # Default dimensions
            try:
                from PIL import Image as PILImage
                with PILImage.open(file_path) as img:
                    width, height = img.size
            except Exception:
                pass  # Use defaults if PIL fails
            
            # Create database entry
            new_image = Image(
                sha256=sha256_hash,
                file_path=file_path,
                original_filename=image.filename,
                width=width,
                height=height,
                file_size=len(content),
                mu=1500.0,  # Default Elo rating
                sigma=350.0,  # Default uncertainty
                exposures=0,
                likes=0,
                unlikes=0,
                skips=0
            )
            
            db.add(new_image)
            uploaded_count += 1
            
        except Exception as e:
            errors.append(f"{image.filename}: {str(e)}")
            continue
    
    # Commit all changes
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    response_data = {
        "uploaded": uploaded_count,
        "total": len(images),
        "errors": errors
    }
    
    if uploaded_count == 0:
        raise HTTPException(status_code=400, detail="No images were uploaded successfully")
    
    return JSONResponse(content=response_data)