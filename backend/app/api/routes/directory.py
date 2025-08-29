import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select
from ...core.database import get_db
from ...models.app_state import AppState
from ...utils.image_utils import is_supported_image
from ...core.config import settings

router = APIRouter()


class SetDirectoryRequest(BaseModel):
    dir: str


class DirectoryResponse(BaseModel):
    directory: str
    image_count: int
    message: str


@router.post("/directory", response_model=DirectoryResponse)
async def set_current_directory(
    request: SetDirectoryRequest,
    db: Session = Depends(get_db)
):
    """Set the current working directory for image comparisons."""
    try:
        directory = request.dir
        
        # Validate directory exists and is accessible
        if not os.path.exists(directory):
            raise HTTPException(status_code=400, detail=f"Directory does not exist: {directory}")
        
        if not os.path.isdir(directory):
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {directory}")
        
        # Check if directory is readable
        if not os.access(directory, os.R_OK):
            raise HTTPException(status_code=400, detail=f"Directory is not readable: {directory}")
        
        # Count supported images in directory
        image_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if is_supported_image(file_path, settings.supported_formats):
                    image_files.append(file_path)
        
        if len(image_files) == 0:
            raise HTTPException(status_code=400, detail=f"No supported images found in directory: {directory}")
        
        # Store directory in app state
        stmt = select(AppState).where(AppState.key == "current_directory")
        state = db.execute(stmt).scalar_one_or_none()
        
        if state:
            state.val = {"directory": directory}
        else:
            state = AppState(key="current_directory", val={"directory": directory})
            db.add(state)
        
        db.commit()
        
        return DirectoryResponse(
            directory=directory,
            image_count=len(image_files),
            message=f"Set working directory to {directory} with {len(image_files)} images"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set directory: {str(e)}")