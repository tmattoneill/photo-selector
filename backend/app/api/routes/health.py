from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.directory_service import DirectoryService

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@router.get("/debug/directory")
async def debug_directory(db: Session = Depends(get_db)):
    """Debug endpoint to check directory service state."""
    try:
        directory_service = DirectoryService(db)
        cache_info = directory_service.get_cache_info()
        all_sha256s = directory_service.get_all_sha256s()
        
        return {
            "cache_info": cache_info,
            "sha256_count": len(all_sha256s),
            "sha256s": list(all_sha256s) if len(all_sha256s) < 10 else list(list(all_sha256s)[:10])  # Show first 10
        }
    except Exception as e:
        return {"error": str(e)}