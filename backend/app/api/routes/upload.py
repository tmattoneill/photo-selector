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
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB per file to avoid nginx issues

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
    
    for image in images:
        try:
            print(f"Processing file: {image.filename}, content_type: {image.content_type}")
            
            # Validate file type
            if image.content_type not in ALLOWED_TYPES:
                print(f"File type rejected: {image.content_type}")
                errors.append(f"{image.filename}: Unsupported file type {image.content_type}")
                continue
            
            # Read file content
            content = await image.read()
            
            # Validate file size
            print(f"File size: {len(content)} bytes")
            if len(content) > MAX_FILE_SIZE:
                print(f"File too large: {len(content)} > {MAX_FILE_SIZE}")
                errors.append(f"{image.filename}: File too large ({len(content)} bytes)")
                continue
            
            # Generate SHA256 hash
            sha256_hash = hashlib.sha256(content).hexdigest()
            
            # Check if image already exists
            existing = db.query(Image).filter(Image.sha256 == sha256_hash).first()
            if existing:
                print(f"Duplicate image found: {sha256_hash}")
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
            print(f"Successfully processed: {image.filename} -> {sha256_hash}")
            
        except Exception as e:
            print(f"Error processing {image.filename}: {str(e)}")
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
    
    print(f"Upload summary: {uploaded_count}/{len(images)} uploaded, errors: {errors}")
    
    if uploaded_count == 0:
        print("No images uploaded, raising 400 error")
        raise HTTPException(status_code=400, detail="No images were uploaded successfully")
    
    return JSONResponse(content=response_data)