import random
from typing import Tuple, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_
from ..models.image import Image
from ..models.choice import Choice
from ..models.app_state import AppState


class PairingService:
    """Service for intelligent image pairing with skip resurfacing."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_image_pair(self) -> Tuple[Optional[Image], Optional[Image], int]:
        """
        Get a pair of images for comparison.
        
        Returns:
            Tuple[left_image, right_image, current_round]
        """
        current_round = self._get_current_round()
        
        # Update eligible skipped images
        self._update_eligible_skipped_images(current_round)
        
        # Get candidate pool
        candidates = self._get_candidate_pool(current_round)
        
        if len(candidates) < 2:
            return None, None, current_round
        
        # Check for eligible skipped images (30% probability)
        eligible_skipped = self._get_eligible_skipped_images()
        
        left_image = None
        right_image = None
        
        if eligible_skipped and random.random() < 0.3:
            # Inject one eligible skipped image
            skipped_image = random.choice(eligible_skipped)
            remaining_candidates = [c for c in candidates if c.id != skipped_image.id]
            
            if remaining_candidates:
                other_image = self._select_by_exposure(remaining_candidates, 1)[0]
                
                # Randomly assign left/right
                if random.random() < 0.5:
                    left_image, right_image = skipped_image, other_image
                else:
                    left_image, right_image = other_image, skipped_image
                
                # Reset eligibility for the skipped image
                skipped_image.next_eligible_round = None
        
        # If no skipped image injection, select normally
        if not left_image or not right_image:
            selected = self._select_by_exposure(candidates, 2)
            if len(selected) >= 2:
                left_image, right_image = selected[0], selected[1]
        
        return left_image, right_image, current_round
    
    def _get_current_round(self) -> int:
        """Get the current round number."""
        stmt = select(AppState).where(AppState.key == "current_round")
        state = self.db.execute(stmt).scalar_one_or_none()
        
        if not state:
            # Initialize current_round
            state = AppState(key="current_round", val={"current_round": 0})
            self.db.add(state)
            self.db.commit()
            return 0
        
        return state.val.get("current_round", 0)
    
    def _increment_round(self) -> int:
        """Increment and return the new round number."""
        stmt = select(AppState).where(AppState.key == "current_round")
        state = self.db.execute(stmt).scalar_one_or_none()
        
        if state:
            current = state.val.get("current_round", 0)
            state.val = {"current_round": current + 1}
        else:
            state = AppState(key="current_round", val={"current_round": 1})
            self.db.add(state)
        
        self.db.commit()
        return state.val["current_round"]
    
    def _get_candidate_pool(self, current_round: int) -> List[Image]:
        """Get pool of candidate images for pairing."""
        # Start with canonical images only
        stmt = select(Image).where(Image.is_canonical == True)
        all_canonical = list(self.db.execute(stmt).scalars().all())
        
        if len(all_canonical) < 2:
            return all_canonical
        
        # Exclude images from previous round
        previous_round_images = self._get_previous_round_images(current_round - 1)
        candidates = [img for img in all_canonical if img.id not in previous_round_images]
        
        # If we filtered out too many, just use all canonical
        if len(candidates) < 2:
            candidates = all_canonical
        
        return candidates
    
    def _get_previous_round_images(self, round_num: int) -> set:
        """Get image IDs from a specific round."""
        if round_num < 0:
            return set()
        
        stmt = select(Choice.left_id, Choice.right_id).where(Choice.round == round_num)
        results = self.db.execute(stmt).all()
        
        image_ids = set()
        for left_id, right_id in results:
            image_ids.add(left_id)
            image_ids.add(right_id)
        
        return image_ids
    
    def _select_by_exposure(self, candidates: List[Image], count: int) -> List[Image]:
        """Select images preferring those with fewer exposures."""
        if len(candidates) <= count:
            return candidates
        
        # Group by exposure count
        exposure_groups = {}
        for image in candidates:
            exp_count = image.exposures
            if exp_count not in exposure_groups:
                exposure_groups[exp_count] = []
            exposure_groups[exp_count].append(image)
        
        selected = []
        
        # Select from lowest exposure groups first
        for exposure_count in sorted(exposure_groups.keys()):
            group = exposure_groups[exposure_count]
            
            # Shuffle within exposure group for randomness
            random.shuffle(group)
            
            for image in group:
                if len(selected) < count:
                    selected.append(image)
                else:
                    break
            
            if len(selected) >= count:
                break
        
        return selected[:count]
    
    def _update_eligible_skipped_images(self, current_round: int):
        """Mark skipped images as eligible if their requeue round has passed."""
        stmt = select(Image).where(
            and_(
                Image.is_canonical == True,
                Image.next_eligible_round.isnot(None),
                Image.next_eligible_round <= current_round
            )
        )
        images_to_update = list(self.db.execute(stmt).scalars().all())
        
        for image in images_to_update:
            image.next_eligible_round = None
        
        if images_to_update:
            self.db.commit()
    
    def _get_eligible_skipped_images(self) -> List[Image]:
        """Get images that are eligible for resurfacing."""
        stmt = select(Image).where(
            and_(
                Image.is_canonical == True,
                Image.next_eligible_round.is_(None),
                Image.skips > 0
            )
        )
        return list(self.db.execute(stmt).scalars().all())
    
    def record_choice(self, left_id: str, right_id: str, selection: str, user_id: str, round_num: int) -> int:
        """
        Record user choice and update image statistics.
        
        Returns:
            int: Next round number
        """
        # Get images
        left_stmt = select(Image).where(Image.id == left_id)
        right_stmt = select(Image).where(Image.id == right_id)
        
        left_image = self.db.execute(left_stmt).scalar_one()
        right_image = self.db.execute(right_stmt).scalar_one()
        
        # Record choice
        choice = Choice(
            user_id=user_id,
            round=round_num,
            left_id=left_id,
            right_id=right_id,
            selection=selection
        )
        self.db.add(choice)
        
        # Update exposures (both images were shown)
        left_image.exposures += 1
        right_image.exposures += 1
        
        # Update preferences based on selection
        if selection == "LEFT":
            left_image.likes += 1
            right_image.unlikes += 1
        elif selection == "RIGHT":
            right_image.likes += 1
            left_image.unlikes += 1
        elif selection == "SKIP":
            left_image.skips += 1
            right_image.skips += 1
            
            # Set requeue rounds for skipped images
            current_round = self._get_current_round()
            left_image.next_eligible_round = current_round + random.randint(11, 49)
            right_image.next_eligible_round = current_round + random.randint(11, 49)
        
        # Increment round counter
        next_round = self._increment_round()
        
        return next_round