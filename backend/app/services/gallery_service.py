"""
Gallery system implementing algo-update.yaml section 7.
"""
import statistics
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, asc, text, delete
from ..models.image import Image
from ..models.gallery import Gallery, GalleryImage
from ..models.duplicate import Duplicate
from ..models.app_state import AppState
from ..core.config import settings


class GalleryService:
    """Gallery management service per algo-update.yaml specification."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_gallery(self, name: str, selection_policy: str, 
                      selection_params: Dict[str, Any], 
                      duplicates_policy: str = "collapse_to_canonical") -> Dict[str, Any]:
        """Create a gallery with specified selection policy."""
        
        # Get current round for snapshot
        current_round = self._get_current_round()
        
        # Get candidate images based on selection policy
        candidates = self._select_candidates(selection_policy, selection_params, duplicates_policy)
        
        # Create gallery record
        gallery = Gallery(
            name=name,
            selection_policy=selection_policy,
            selection_params=selection_params,
            duplicates_policy=duplicates_policy,
            app_round_at_creation=current_round
        )
        
        self.db.add(gallery)
        self.db.flush()  # Get ID
        
        # Insert gallery images with dense ranking
        gallery_images = [
            GalleryImage(
                gallery_id=gallery.id,
                sha256=candidate['sha256'],
                rank=rank + 1  # Dense ranking starts at 1
            )
            for rank, candidate in enumerate(candidates)
        ]
        
        self.db.add_all(gallery_images)
        self.db.commit()
        
        # Return sample for response
        sample = candidates[:5] if len(candidates) > 5 else candidates
        for i, img in enumerate(sample):
            img['rank'] = i + 1
        
        return {
            'gallery_id': gallery.id,
            'name': gallery.name,
            'size': len(candidates),
            'created_at': gallery.created_at,
            'sample': sample
        }
    
    def list_galleries(self) -> List[Dict[str, Any]]:
        """List all galleries with summary info."""
        stmt = select(
            Gallery.id,
            Gallery.name,
            Gallery.created_at,
            func.count(GalleryImage.sha256).label('size')
        ).outerjoin(GalleryImage).group_by(
            Gallery.id, Gallery.name, Gallery.created_at
        ).order_by(desc(Gallery.created_at))
        
        results = self.db.execute(stmt).fetchall()
        
        return [
            {
                'gallery_id': row.id,
                'name': row.name,
                'size': row.size,
                'created_at': row.created_at
            }
            for row in results
        ]
    
    def get_gallery(self, gallery_id: int) -> Optional[Dict[str, Any]]:
        """Get gallery with all images."""
        # Get gallery info
        gallery_stmt = select(Gallery).where(Gallery.id == gallery_id)
        gallery = self.db.execute(gallery_stmt).scalar_one_or_none()
        
        if not gallery:
            return None
        
        # Get gallery images with image data
        images_stmt = select(
            GalleryImage.sha256,
            GalleryImage.rank,
            Image.mu,
            Image.sigma,
            Image.exposures
        ).select_from(
            GalleryImage
        ).join(
            Image, GalleryImage.sha256 == Image.sha256
        ).where(
            GalleryImage.gallery_id == gallery_id
        ).order_by(GalleryImage.rank)
        
        images = self.db.execute(images_stmt).fetchall()
        
        return {
            'gallery_id': gallery.id,
            'name': gallery.name,
            'size': len(images),
            'created_at': gallery.created_at,
            'images': [
                {
                    'sha256': img.sha256,
                    'mu': img.mu,
                    'sigma': img.sigma,
                    'exposures': img.exposures,
                    'rank': img.rank
                }
                for img in images
            ]
        }
    
    def update_gallery(self, gallery_id: int, name: Optional[str] = None,
                      remove_sha256: Optional[str] = None,
                      add_sha256: Optional[str] = None,
                      re_rank: bool = False) -> bool:
        """Update gallery (rename, add/remove images, re-rank)."""
        
        # Check gallery exists
        gallery_stmt = select(Gallery).where(Gallery.id == gallery_id)
        gallery = self.db.execute(gallery_stmt).scalar_one_or_none()
        
        if not gallery:
            return False
        
        # Update name if provided
        if name is not None:
            gallery.name = name
        
        # Remove image if specified
        if remove_sha256:
            delete_stmt = delete(GalleryImage).where(
                GalleryImage.gallery_id == gallery_id,
                GalleryImage.sha256 == remove_sha256
            )
            self.db.execute(delete_stmt)
        
        # Add image if specified (get its current stats)
        if add_sha256:
            # Check if image exists
            image_stmt = select(Image.mu, Image.sigma, Image.exposures).where(
                Image.sha256 == add_sha256
            )
            image_data = self.db.execute(image_stmt).first()
            
            if image_data:
                # Get next rank
                max_rank_stmt = select(func.max(GalleryImage.rank)).where(
                    GalleryImage.gallery_id == gallery_id
                )
                max_rank = self.db.execute(max_rank_stmt).scalar() or 0
                
                # Add to gallery
                new_gallery_image = GalleryImage(
                    gallery_id=gallery_id,
                    sha256=add_sha256,
                    rank=max_rank + 1
                )
                self.db.add(new_gallery_image)
        
        # Re-rank if requested
        if re_rank:
            self._rerank_gallery(gallery_id)
        
        self.db.commit()
        return True
    
    def delete_gallery(self, gallery_id: int) -> bool:
        """Delete gallery and all its images."""
        
        # Check gallery exists
        gallery_stmt = select(Gallery).where(Gallery.id == gallery_id)
        gallery = self.db.execute(gallery_stmt).scalar_one_or_none()
        
        if not gallery:
            return False
        
        # Delete gallery (cascade will handle gallery_images)
        self.db.delete(gallery)
        self.db.commit()
        return True
    
    def _get_current_round(self) -> int:
        """Get current round from app state."""
        stmt = select(AppState.round).where(AppState.id == 1)
        result = self.db.execute(stmt).scalar()
        return result or 0
    
    def _select_candidates(self, selection_policy: str, selection_params: Dict[str, Any],
                          duplicates_policy: str) -> List[Dict[str, Any]]:
        """Select candidate images based on policy."""
        
        # Base query: all non-archived images ordered per algo-update.yaml
        base_stmt = select(
            Image.sha256,
            Image.mu,
            Image.sigma,
            Image.exposures
        ).where(
            Image.is_archived_hard_no == False
        ).order_by(
            desc(Image.mu),      # mu DESC
            asc(Image.sigma),    # sigma ASC  
            desc(Image.exposures), # exposures DESC
            asc(Image.sha256)    # sha256 ASC (tie-breaker)
        )
        
        # Apply selection policy filter
        if selection_policy == "top_k":
            k = selection_params.get('k', settings.target_top_k)
            if k:
                base_stmt = base_stmt.limit(k)
        elif selection_policy == "threshold_mu":
            min_mu = selection_params.get('min_mu', 1500)
            base_stmt = base_stmt.where(Image.mu >= min_mu)
        elif selection_policy == "threshold_ci":
            z = selection_params.get('z', settings.confidence_z)
            min_ci_lower = selection_params.get('min_ci_lower', 1500)
            base_stmt = base_stmt.where(
                (Image.mu - z * Image.sigma) >= min_ci_lower
            )
        elif selection_policy == "manual":
            sha256_list = selection_params.get('sha256_list', [])
            if sha256_list:
                base_stmt = base_stmt.where(Image.sha256.in_(sha256_list))
            else:
                # Empty manual selection
                return []
        else:
            raise ValueError(f"Unknown selection policy: {selection_policy}")
        
        candidates = self.db.execute(base_stmt).fetchall()
        
        # Apply duplicates policy
        if duplicates_policy == "collapse_to_canonical":
            # Collapse duplicates to their canonical representations
            canonical_candidates = []
            seen_sha256s = set()
            
            for row in candidates:
                # Check if this is a duplicate
                canonical_stmt = select(Duplicate.canonical_sha256).where(
                    Duplicate.duplicate_sha256 == row.sha256
                )
                canonical_sha256 = self.db.execute(canonical_stmt).scalar()
                
                # Use canonical if it's a duplicate, otherwise use original
                final_sha256 = canonical_sha256 or row.sha256
                
                # Only include each canonical once
                if final_sha256 not in seen_sha256s:
                    # Get stats for the canonical image
                    if canonical_sha256:
                        canonical_stmt = select(
                            Image.sha256, Image.mu, Image.sigma, Image.exposures
                        ).where(Image.sha256 == canonical_sha256)
                        canonical_row = self.db.execute(canonical_stmt).first()
                        if canonical_row:
                            canonical_candidates.append(canonical_row)
                            seen_sha256s.add(final_sha256)
                    else:
                        canonical_candidates.append(row)
                        seen_sha256s.add(final_sha256)
            
            candidates = canonical_candidates
            
        elif duplicates_policy == "exclude_duplicates":
            # Only include canonical images (exclude duplicates entirely)
            filtered_candidates = []
            for row in candidates:
                # Check if this is a duplicate - if so, skip it
                duplicate_stmt = select(Duplicate.canonical_sha256).where(
                    Duplicate.duplicate_sha256 == row.sha256
                )
                is_duplicate = self.db.execute(duplicate_stmt).scalar() is not None
                
                if not is_duplicate:
                    filtered_candidates.append(row)
            
            candidates = filtered_candidates
        # "include_duplicates" - no filtering needed
        
        return [
            {
                'sha256': row.sha256,
                'mu': row.mu,
                'sigma': row.sigma,
                'exposures': row.exposures
            }
            for row in candidates
        ]
    
    def _rerank_gallery(self, gallery_id: int):
        """Re-rank gallery images based on current ratings."""
        
        # Get current images with their stats
        stmt = select(
            GalleryImage.sha256,
            Image.mu,
            Image.sigma,
            Image.exposures
        ).select_from(
            GalleryImage
        ).join(
            Image, GalleryImage.sha256 == Image.sha256
        ).where(
            GalleryImage.gallery_id == gallery_id
        ).order_by(
            desc(Image.mu),
            asc(Image.sigma),
            desc(Image.exposures),
            asc(Image.sha256)
        )
        
        images = self.db.execute(stmt).fetchall()
        
        # Update ranks
        for rank, img in enumerate(images, 1):
            update_stmt = text("""
                UPDATE gallery_images 
                SET rank = :rank
                WHERE gallery_id = :gallery_id AND sha256 = :sha256
            """)
            self.db.execute(update_stmt, {
                'rank': rank,
                'gallery_id': gallery_id,
                'sha256': img.sha256
            })