import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.directory_service import DirectoryService
from ...utils.image_utils import get_mime_type

router = APIRouter()


@router.get("/image/{sha256}")
async def serve_image(sha256: str, db: Session = Depends(get_db)):
    """Serve image file directly from filesystem using SHA256."""
    try:
        from ...models.image import Image
        
        # First check if image exists in database with file_path
        image = db.query(Image).filter(Image.sha256 == sha256).first()
        
        if image and image.file_path and os.path.exists(image.file_path):
            # Use file_path from database (for uploaded files)
            file_path = image.file_path
        else:
            # Fallback to directory service (for directory-based files)
            service = DirectoryService(db)
            
            # If cache is empty, try to set samples directory
            if len(service.get_all_sha256s()) == 0:
                service.set_root_directory("/samples")
            
            # Find file in current directory by SHA256
            file_path = service.get_path_by_sha256(sha256)
            
            if not file_path:
                raise HTTPException(status_code=404, detail="Image not found")
        
        # Check if file still exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Image file not found on disk")
        
        # Get MIME type
        mime_type = get_mime_type(file_path)
        
        # Return file directly
        return FileResponse(
            path=file_path,
            media_type=mime_type,
            filename=os.path.basename(file_path)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve image: {str(e)}")