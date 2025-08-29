import os
import random
from typing import List, Tuple, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models.app_state import AppState
from ..models.image import Image
from ..utils.image_utils import get_sha256_hash, is_supported_image, get_image_dimensions, get_mime_type
from ..core.config import settings


class DirectoryService:
    """Service for directory-based image operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_current_directory(self) -> Optional[str]:
        """Get the currently selected directory."""
        stmt = select(AppState).where(AppState.key == "current_directory")
        state = self.db.execute(stmt).scalar_one_or_none()
        
        if state and "directory" in state.val:
            return state.val["directory"]
        return None
    
    def scan_directory_images(self) -> List[str]:
        """Scan current directory for supported images."""
        directory = self.get_current_directory()
        if not directory:
            return []
        
        image_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if is_supported_image(file_path, settings.supported_formats):
                    image_files.append(file_path)
        
        return image_files
    
    def get_image_pair_from_directory(self) -> Tuple[Optional[Dict], Optional[Dict], int]:
        """
        Get a pair of images from the current directory.
        
        Returns:
            Tuple[left_image_data, right_image_data, current_round]
            Each image_data contains: {sha256, file_path, width, height, mime_type}
        """
        # Get current round
        current_round = self._get_current_round()
        
        # Get all images from directory
        image_files = self.scan_directory_images()
        if len(image_files) < 2:
            return None, None, current_round
        
        # Get image stats from database for intelligent selection
        image_stats = self._get_image_stats_by_files(image_files)
        
        # Update eligible skipped images
        self._update_eligible_skipped_images(current_round)
        
        # Select pair using existing logic adapted for file-based approach
        left_file, right_file = self._select_image_pair(image_files, image_stats, current_round)
        
        if not left_file or not right_file:
            return None, None, current_round
        
        # Build image data with calculated SHA256
        left_data = self._build_image_data(left_file)
        right_data = self._build_image_data(right_file)
        
        return left_data, right_data, current_round
    
    def _build_image_data(self, file_path: str) -> Dict:
        """Build image data dictionary from file path."""
        sha256 = get_sha256_hash(file_path)
        width, height = get_image_dimensions(file_path)
        mime_type = get_mime_type(file_path)
        
        return {
            "sha256": sha256,
            "file_path": file_path,
            "width": width,
            "height": height,
            "mime_type": mime_type
        }
    
    def _get_image_stats_by_files(self, image_files: List[str]) -> Dict[str, Image]:
        """Get image statistics mapped by SHA256."""
        stats_by_sha256 = {}
        
        for file_path in image_files:
            try:
                sha256 = get_sha256_hash(file_path)
                stmt = select(Image).where(Image.sha256 == sha256)
                image_stats = self.db.execute(stmt).scalar_one_or_none()
                if image_stats:
                    stats_by_sha256[sha256] = image_stats
            except Exception:
                # Skip files that can't be processed
                continue
        
        return stats_by_sha256
    
    def _select_image_pair(self, image_files: List[str], image_stats: Dict[str, Image], current_round: int) -> Tuple[Optional[str], Optional[str]]:
        """Select two images using exposure-balanced logic."""
        if len(image_files) < 2:
            return None, None
        
        # Get previous round images to avoid repetition
        previous_round_sha256s = self._get_previous_round_sha256s(current_round - 1)
        
        # Filter out previous round images
        available_files = []
        for file_path in image_files:
            try:
                sha256 = get_sha256_hash(file_path)
                if sha256 not in previous_round_sha256s:
                    available_files.append(file_path)
            except Exception:
                continue
        
        if len(available_files) < 2:
            available_files = image_files  # Use all if too few available
        
        # Check for eligible skipped images (30% injection probability)
        eligible_skipped = self._get_eligible_skipped_files(available_files, image_stats)
        
        if eligible_skipped and random.random() < 0.3:
            # Inject one eligible skipped image
            skipped_file = random.choice(eligible_skipped)
            remaining_files = [f for f in available_files if f != skipped_file]
            
            if remaining_files:
                other_file = self._select_by_exposure(remaining_files, image_stats, 1)[0]
                
                # Randomly assign left/right
                if random.random() < 0.5:
                    return skipped_file, other_file
                else:
                    return other_file, skipped_file
        
        # Normal selection by exposure
        selected_files = self._select_by_exposure(available_files, image_stats, 2)
        if len(selected_files) >= 2:
            return selected_files[0], selected_files[1]
        
        return None, None
    
    def _select_by_exposure(self, files: List[str], image_stats: Dict[str, Image], count: int) -> List[str]:
        """Select files preferring those with fewer exposures."""
        if len(files) <= count:
            return files
        
        # Group files by exposure count
        exposure_groups = {}
        for file_path in files:
            try:
                sha256 = get_sha256_hash(file_path)
                exposure_count = 0
                if sha256 in image_stats:
                    exposure_count = image_stats[sha256].exposures
                
                if exposure_count not in exposure_groups:
                    exposure_groups[exposure_count] = []
                exposure_groups[exposure_count].append(file_path)
            except Exception:
                continue
        
        selected = []
        
        # Select from lowest exposure groups first
        for exposure_count in sorted(exposure_groups.keys()):
            group = exposure_groups[exposure_count]
            random.shuffle(group)
            
            for file_path in group:
                if len(selected) < count:
                    selected.append(file_path)
                else:
                    break
            
            if len(selected) >= count:
                break
        
        return selected[:count]
    
    def _get_eligible_skipped_files(self, available_files: List[str], image_stats: Dict[str, Image]) -> List[str]:
        """Get files that are eligible for resurfacing."""
        eligible = []
        
        for file_path in available_files:
            try:
                sha256 = get_sha256_hash(file_path)
                if sha256 in image_stats:
                    stats = image_stats[sha256]
                    if stats.next_eligible_round is None and stats.skips > 0:
                        eligible.append(file_path)
            except Exception:
                continue
        
        return eligible
    
    def _update_eligible_skipped_images(self, current_round: int):
        """Mark skipped images as eligible if their requeue round has passed."""
        stmt = select(Image).where(
            Image.next_eligible_round.isnot(None),
            Image.next_eligible_round <= current_round
        )
        images_to_update = list(self.db.execute(stmt).scalars().all())
        
        for image in images_to_update:
            image.next_eligible_round = None
        
        if images_to_update:
            self.db.commit()
    
    def _get_previous_round_sha256s(self, round_num: int) -> set:
        """Get SHA256s from a specific round."""
        if round_num < 0:
            return set()
        
        from ..models.choice import Choice
        stmt = select(Choice.left_sha256, Choice.right_sha256).where(Choice.round == round_num)
        results = self.db.execute(stmt).all()
        
        sha256s = set()
        for left_sha256, right_sha256 in results:
            sha256s.add(left_sha256)
            sha256s.add(right_sha256)
        
        return sha256s
    
    def _get_current_round(self) -> int:
        """Get the current round number."""
        stmt = select(AppState).where(AppState.key == "current_round")
        state = self.db.execute(stmt).scalar_one_or_none()
        
        if not state:
            state = AppState(key="current_round", val={"current_round": 0})
            self.db.add(state)
            self.db.commit()
            return 0
        
        return state.val.get("current_round", 0)
    
    def find_file_by_sha256(self, sha256: str) -> Optional[str]:
        """Find file path in current directory by SHA256."""
        image_files = self.scan_directory_images()
        
        for file_path in image_files:
            try:
                file_sha256 = get_sha256_hash(file_path)
                if file_sha256 == sha256:
                    return file_path
            except Exception:
                continue
        
        return None