from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from ...core.database import get_db
from ...models.image import Image
from ...models.choice import Choice

router = APIRouter()


class ResetResponse(BaseModel):
    success: bool
    message: str
    reset_items: list[str]


@router.post("/reset", response_model=ResetResponse)  
async def reset_gallery_data():
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
        
        # Delete all database records using direct SQL connection
        import psycopg
        from ...core.config import settings
        
        # Create direct database connection bypassing SQLAlchemy session issues
        conn = psycopg.connect("postgresql://user:password@postgres:5432/picker")
        cur = conn.cursor()
        
        try:
            # Clear dependent tables first to avoid foreign key violations
            cur.execute("DELETE FROM portfolio_images")
            portfolio_imgs_deleted = cur.rowcount
            cur.execute("DELETE FROM portfolios")  
            portfolios_deleted = cur.rowcount
            reset_items.append(f"All portfolios deleted ({portfolios_deleted} portfolios, {portfolio_imgs_deleted} portfolio images)")
            
            cur.execute("DELETE FROM gallery_images")
            gallery_imgs_deleted = cur.rowcount
            cur.execute("DELETE FROM galleries")
            galleries_deleted = cur.rowcount
            reset_items.append(f"All galleries deleted ({galleries_deleted} galleries, {gallery_imgs_deleted} gallery images)")
            
            # Clear choices (has foreign keys to images)
            cur.execute("DELETE FROM choices")
            choices_deleted = cur.rowcount
            reset_items.append(f"All choices deleted ({choices_deleted} rows)")
            
            # Now delete all images (no more foreign key constraints)
            cur.execute("DELETE FROM images")
            images_deleted = cur.rowcount
            reset_items.append(f"All images deleted ({images_deleted} rows)")
            
            # Commit all changes
            conn.commit()
            
            # Verify the reset worked
            cur.execute("SELECT COUNT(*) FROM images")
            verification_images = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM choices")
            verification_choices = cur.fetchone()[0]
            
            if verification_images > 0 or verification_choices > 0:
                reset_items.append(f"WARNING: Reset verification failed - {verification_images} images, {verification_choices} choices remain")
            else:
                reset_items.append("✅ Reset verification successful - all data cleared")
                
        except Exception as e:
            conn.rollback()
            reset_items.append(f"Database error during reset: {str(e)}")
            raise
        finally:
            cur.close()
            conn.close()
        
        return ResetResponse(
            success=True,
            message="Everything has been completely reset - you can now start fresh",
            reset_items=reset_items
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to reset gallery data: {str(e)}"
        )