from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from ...core.database import get_db

router = APIRouter()


class ResetResponse(BaseModel):
    success: bool
    message: str
    reset_items: list[str]


@router.post("/reset", response_model=ResetResponse)
async def reset_gallery_data(db: Session = Depends(get_db)):
    """Completely reset everything - delete all data and files."""
    
    try:
        import os
        import glob
        
        reset_items = []
        
        # Delete all uploaded files
        upload_dir = "/app/uploads"
        if os.path.exists(upload_dir):
            for file_path in glob.glob(os.path.join(upload_dir, "*")):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
            reset_items.append("All uploaded files deleted")
        
        # Delete all database records in correct order
        db.execute(text("DELETE FROM choices"))
        reset_items.append("All choices deleted")
        
        # Clear all portfolios 
        try:
            db.execute(text("DELETE FROM portfolio_images"))
            db.execute(text("DELETE FROM portfolios"))
            reset_items.append("All portfolios deleted")
        except Exception:
            pass
        
        # Clear galleries
        try:
            db.execute(text("DELETE FROM gallery_images"))
            db.execute(text("DELETE FROM galleries"))
            reset_items.append("All galleries deleted")
        except Exception:
            pass
        
        # Delete all images
        db.execute(text("DELETE FROM images"))
        reset_items.append("All images deleted")
        
        # Reset app state
        try:
            db.execute(text("DELETE FROM app_state"))
            db.execute(text("DELETE FROM app_state_new"))
            reset_items.append("App state reset")
        except Exception:
            pass
        
        db.commit()
        
        return ResetResponse(
            success=True,
            message="Everything has been completely reset - you can now start fresh",
            reset_items=reset_items
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to reset gallery data: {str(e)}"
        )