import random
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models.image import Image
from ..models.choice import Choice
from ..models.app_state import AppState
from ..models.user import User


class DirectoryChoiceService:
    """Service for recording choices in directory-based mode."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def ensure_default_user(self) -> str:
        """Ensure a default user exists and return its ID."""
        stmt = select(User)
        user = self.db.execute(stmt).scalar_one_or_none()
        
        if not user:
            user = User()
            self.db.add(user)
            self.db.commit()
        
        return str(user.id)
    
    def record_choice(self, left_sha256: str, right_sha256: str, selection: str, user_id: str, round_num: int) -> int:
        """
        Record user choice and update image statistics.
        
        Args:
            left_sha256: SHA256 of left image
            right_sha256: SHA256 of right image 
            selection: "LEFT", "RIGHT", or "SKIP"
            user_id: User ID
            round_num: Current round number
            
        Returns:
            int: Next round number
        """
        # Ensure image records exist for statistics tracking
        left_image = self._ensure_image_record(left_sha256)
        right_image = self._ensure_image_record(right_sha256)
        
        # Record choice
        choice = Choice(
            user_id=user_id,
            round=round_num,
            left_sha256=left_sha256,
            right_sha256=right_sha256,
            selection=selection
        )
        self.db.add(choice)
        
        # Update exposures (both images were shown)
        left_image.exposures = (left_image.exposures or 0) + 1
        right_image.exposures = (right_image.exposures or 0) + 1
        
        # Update preferences based on selection
        if selection == "LEFT":
            left_image.likes = (left_image.likes or 0) + 1
            right_image.unlikes = (right_image.unlikes or 0) + 1
        elif selection == "RIGHT":
            right_image.likes = (right_image.likes or 0) + 1
            left_image.unlikes = (left_image.unlikes or 0) + 1
        elif selection == "SKIP":
            left_image.skips = (left_image.skips or 0) + 1
            right_image.skips = (right_image.skips or 0) + 1
            
            # Set requeue rounds for skipped images
            current_round = self._get_current_round()
            left_image.next_eligible_round = current_round + random.randint(11, 49)
            right_image.next_eligible_round = current_round + random.randint(11, 49)
        
        # Increment round counter
        next_round = self._increment_round()
        
        self.db.commit()
        return next_round
    
    def _ensure_image_record(self, sha256: str) -> Image:
        """Ensure an image record exists for statistics tracking."""
        stmt = select(Image).where(Image.sha256 == sha256)
        image = self.db.execute(stmt).scalar_one_or_none()
        
        if not image:
            # Create new image record with explicit default values
            image = Image(
                sha256=sha256,
                exposures=0,
                likes=0,
                unlikes=0,
                skips=0
            )
            self.db.add(image)
            self.db.flush()  # Ensure the object gets its defaults applied
        
        return image
    
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
        
        return state.val["current_round"]