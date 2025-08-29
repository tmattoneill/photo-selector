import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from ...core.database import get_db
from ...models.image import Image

router = APIRouter()


@router.get("/image/{image_id}")
async def serve_image(image_id: str, db: Session = Depends(get_db)):
    """Serve image file directly from filesystem."""
    try:
        # Get image record
        stmt = select(Image).where(Image.id == image_id)
        image = db.execute(stmt).scalar_one_or_none()
        
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Check if file exists
        if not os.path.exists(image.file_path):
            raise HTTPException(status_code=404, detail="Image file not found on disk")
        
        # Return file directly
        return FileResponse(
            path=image.file_path,
            media_type=image.mime_type,
            filename=os.path.basename(image.file_path)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve image: {str(e)}")