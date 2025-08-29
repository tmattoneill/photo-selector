from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...services.image_service import ImageService

router = APIRouter()


class IngestRequest(BaseModel):
    dir: str


class IngestResponse(BaseModel):
    ingested: int
    duplicates: int
    existing: int


@router.post("/ingest", response_model=IngestResponse)
async def ingest_directory(
    request: IngestRequest,
    db: Session = Depends(get_db)
):
    """Ingest images from a directory."""
    try:
        service = ImageService(db)
        ingested, duplicates, existing = service.ingest_directory(request.dir)
        
        return IngestResponse(
            ingested=ingested,
            duplicates=duplicates,
            existing=existing
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")