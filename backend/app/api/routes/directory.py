from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.directory_service import DirectoryService

router = APIRouter()


class SetDirectoryRequest(BaseModel):
    root: str  # Changed from 'dir' to 'root' per algo-update.yaml spec


class DirectoryResponse(BaseModel):
    ok: bool
    discovered: int


@router.post("/directory", response_model=DirectoryResponse)
async def set_root_directory(
    request: SetDirectoryRequest,
    db: Session = Depends(get_db)
):
    """Set root directory and scan for images as per algo-update.yaml spec."""
    try:
        directory_service = DirectoryService(db)
        result = directory_service.set_root_directory(request.root)
        return DirectoryResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set directory: {str(e)}")