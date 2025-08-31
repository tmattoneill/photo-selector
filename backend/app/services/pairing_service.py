"""
Sophisticated pairing engine implementing the algo-update.yaml specification.
"""
import random
import statistics
from collections import deque
from typing import Tuple, Optional, List, Dict, Set
from sqlalchemy.orm import Session
from sqlalchemy import select, text, desc, asc
from ..models.image import Image
from ..models.choice import Choice
from ..models.app_state import AppState
from ..utils.elo_utils import EloCalculator, calculate_information_gain
from ..core.config import settings


class PairingService:
    """Pairing engine with Elo+σ algorithm as per algo-update.yaml spec."""
    
    def __init__(self, db: Session):
        self.db = db
        self.elo_calc = EloCalculator()
        
        # Ring buffers for recent suppression (in-memory)
        self.recent_images: deque = deque(maxlen=settings.recent_image_window)
        self.recent_pairs: deque = deque(maxlen=settings.recent_pair_window)
    
    def get_next_pair(self, directory_service) -> Tuple[Optional[Dict], Optional[Dict], int]:
        """
        Get next image pair following algo-update.yaml specification.
        
        Returns:
            Tuple[left_image_data, right_image_data, current_round]
            Image data includes: {sha256, mu, sigma, exposures} + file info
        """
        # Increment round (locks app_state)
        current_round = self._bump_round()
        
        # Get available SHA256s from directory cache
        available_sha256s = directory_service.get_all_sha256s()
        if len(available_sha256s) < 2:
            return None, None, current_round
        
        # Load image pools
        pools = self._load_eligible_pools(current_round, available_sha256s)
        
        # Apply recent suppression
        pools = self._apply_recent_suppression(pools)
        
        # Select pair using algorithm
        left_sha256, right_sha256 = self._select_pair(pools, current_round)
        
        if not left_sha256 or not right_sha256:
            return None, None, current_round
        
        # Build image data
        left_data = self._build_image_data(left_sha256, directory_service)
        right_data = self._build_image_data(right_sha256, directory_service)
        
        # Update recent suppression rings
        self.recent_images.append(left_sha256)
        self.recent_images.append(right_sha256)
        
        # Create canonical pair representation for recent pairs
        pair_key = tuple(sorted([left_sha256, right_sha256]))
        self.recent_pairs.append(pair_key)
        
        return left_data, right_data, current_round
    
    def _bump_round(self) -> int:
        """Atomically increment and return new round number."""
        # Lock app_state row and increment
        stmt = select(AppState).where(AppState.id == 1).with_for_update()
        app_state = self.db.execute(stmt).scalar_one_or_none()
        
        if not app_state:
            # Initialize if missing (should not happen with migration)
            app_state = AppState(id=1, round=1)
            self.db.add(app_state)
        else:
            app_state.round += 1
        
        self.db.commit()
        return app_state.round
    
    def _load_eligible_pools(self, current_round: int, available_sha256s: Set[str]) -> Dict[str, List[Image]]:
        """Load image pools: UNSEEN, ACTIVE, SKIPPED_ELIGIBLE, SKIPPED_COOLDOWN."""
        # Get all images for available SHA256s
        stmt = select(Image).where(Image.sha256.in_(available_sha256s))
        all_images = {img.sha256: img for img in self.db.execute(stmt).scalars().all()}
        
        # Initialize pools
        pools = {
            "UNSEEN": [],
            "ACTIVE": [],
            "SKIPPED_ELIGIBLE": [],
            "SKIPPED_COOLDOWN": []
        }
        
        # Classify images into pools
        for sha256 in available_sha256s:
            image = all_images.get(sha256)
            if not image:
                # New image not yet in DB - treat as UNSEEN
                pools["UNSEEN"].append(self._create_unseen_image(sha256))
                continue
            
            # Skip archived images
            if image.is_archived_hard_no:
                continue
            
            # Classify based on state
            if image.exposures == 0:
                pools["UNSEEN"].append(image)
            elif image.next_eligible_round is not None:
                if current_round >= image.next_eligible_round:
                    pools["SKIPPED_ELIGIBLE"].append(image)
                else:
                    pools["SKIPPED_COOLDOWN"].append(image)
            else:
                pools["ACTIVE"].append(image)
        
        return pools
    
    def _create_unseen_image(self, sha256: str) -> Image:
        """Create a temporary Image object for unseen image."""
        return Image(
            sha256=sha256,
            mu=settings.initial_mu,
            sigma=settings.initial_sigma,
            exposures=0,
            likes=0,
            unlikes=0,
            skips=0
        )
    
    def _apply_recent_suppression(self, pools: Dict[str, List[Image]]) -> Dict[str, List[Image]]:
        """Remove recently seen images from pools if avoidable."""
        recent_sha256s = set(self.recent_images)
        
        filtered_pools = {}
        for pool_name, images in pools.items():
            # Try to filter out recent images
            filtered = [img for img in images if img.sha256 not in recent_sha256s]
            
            # If filtering leaves too few images, use original pool
            if len(filtered) < 2 and pool_name in ["UNSEEN", "ACTIVE"]:
                filtered_pools[pool_name] = images
            else:
                filtered_pools[pool_name] = filtered
        
        return filtered_pools
    
    def _select_pair(self, pools: Dict[str, List[Image]], current_round: int) -> Tuple[Optional[str], Optional[str]]:
        """Select image pair using algo-update.yaml strategy."""
        
        # Check epsilon-greedy random selection (10%)
        if random.random() < settings.epsilon_greedy:
            return self._select_random_pair(pools)
        
        # Strategy 1: If UNSEEN exists, pair with ACTIVE
        if pools["UNSEEN"]:
            unseen_img = random.choice(pools["UNSEEN"])
            active_img = self._pick_active_near_median_high_sigma(pools["ACTIVE"])
            if active_img:
                return unseen_img.sha256, active_img.sha256
            # Fallback: pair two unseen if no active available
            if len(pools["UNSEEN"]) >= 2:
                pair = random.sample(pools["UNSEEN"], 2)
                return pair[0].sha256, pair[1].sha256
        
        # Strategy 2: Select from ACTIVE with information gain
        if len(pools["ACTIVE"]) >= 2:
            left_sha256, right_sha256 = self._select_by_information_gain(pools["ACTIVE"])
        else:
            left_sha256, right_sha256 = None, None
        
        # Strategy 3: Maybe inject eligible skipped image (30% probability)
        if (pools["SKIPPED_ELIGIBLE"] and random.random() < settings.skip_inject_probability and
            left_sha256 and right_sha256):
            
            # Replace one of the selected images with a skipped one
            skipped_img = random.choice(pools["SKIPPED_ELIGIBLE"])
            if random.random() < 0.5:
                left_sha256 = skipped_img.sha256
            else:
                right_sha256 = skipped_img.sha256
        
        # Ensure no self-pairing and no recent repeats
        if left_sha256 and right_sha256 and left_sha256 != right_sha256:
            pair_key = tuple(sorted([left_sha256, right_sha256]))
            if pair_key not in self.recent_pairs:
                return left_sha256, right_sha256
        
        return None, None
    
    def _select_random_pair(self, pools: Dict[str, List[Image]]) -> Tuple[Optional[str], Optional[str]]:
        """Select completely random pair for epsilon-greedy exploration."""
        all_images = pools["UNSEEN"] + pools["ACTIVE"] + pools["SKIPPED_ELIGIBLE"]
        if len(all_images) >= 2:
            pair = random.sample(all_images, 2)
            return pair[0].sha256, pair[1].sha256
        return None, None
    
    def _pick_active_near_median_high_sigma(self, active_images: List[Image]) -> Optional[Image]:
        """Pick ACTIVE image near median mu with high sigma."""
        if not active_images:
            return None
        
        if len(active_images) == 1:
            return active_images[0]
        
        # Calculate median mu
        mu_values = [img.mu for img in active_images]
        median_mu = statistics.median(mu_values)
        
        # Score by closeness to median (lower is better) and high sigma (higher is better)
        def score_fn(img):
            mu_distance = abs(img.mu - median_mu)
            return img.sigma - mu_distance / 10.0  # Balance sigma vs mu distance
        
        # Select best scoring image
        best_img = max(active_images, key=score_fn)
        return best_img
    
    def _select_by_information_gain(self, active_images: List[Image]) -> Tuple[Optional[str], Optional[str]]:
        """Select pair from ACTIVE images maximizing information gain."""
        if len(active_images) < 2:
            return None, None
        
        # Create shortlist of top K candidates by sigma DESC, then mu closeness to median
        k = min(settings.shortlist_k, len(active_images))
        
        if len(active_images) > k:
            mu_values = [img.mu for img in active_images]
            median_mu = statistics.median(mu_values)
            
            # Sort by sigma DESC, then closeness to median
            def shortlist_key(img):
                mu_distance = abs(img.mu - median_mu)
                return (-img.sigma, mu_distance)  # Negative sigma for DESC
            
            shortlist = sorted(active_images, key=shortlist_key)[:k]
        else:
            shortlist = active_images
        
        # Find pair with maximum information gain
        best_pair = None
        best_gain = -1
        
        for i in range(len(shortlist)):
            for j in range(i + 1, len(shortlist)):
                img_a, img_b = shortlist[i], shortlist[j]
                gain = calculate_information_gain(img_a.mu, img_a.sigma, img_b.mu, img_b.sigma)
                
                if gain > best_gain:
                    best_gain = gain
                    best_pair = (img_a.sha256, img_b.sha256)
        
        return best_pair if best_pair else (None, None)
    
    def _build_image_data(self, sha256: str, directory_service) -> Dict:
        """Build complete image data for API response."""
        # Get image stats from DB
        stmt = select(Image).where(Image.sha256 == sha256)
        image = self.db.execute(stmt).scalar_one_or_none()
        
        if not image:
            # Create default for new images
            image = Image(
                sha256=sha256,
                mu=settings.initial_mu,
                sigma=settings.initial_sigma,
                exposures=0,
                likes=0,
                unlikes=0,
                skips=0
            )
        
        # Get file path from directory service
        file_path = directory_service.get_path_by_sha256(sha256)
        
        return {
            "sha256": sha256,
            "url": f"/api/image/{sha256}",
            "meta": {
                "mu": float(image.mu),
                "sigma": float(image.sigma),
                "exposures": image.exposures,
                "likes": image.likes,
                "unlikes": image.unlikes,
                "skips": image.skips
            },
            "file_path": file_path  # Internal use
        }
    
    def record_choice(self, round_num: int, left_sha256: str, right_sha256: str, outcome: str) -> Dict[str, any]:
        """
        Record choice and update Elo+σ ratings as per algo-update.yaml spec.
        
        Args:
            round_num: Round number from the pair request
            left_sha256: SHA256 of left image  
            right_sha256: SHA256 of right image
            outcome: "LEFT", "RIGHT", or "SKIP"
            
        Returns:
            Dict with success status
        """
        # Get or create image records
        left_image = self._get_or_create_image(left_sha256)
        right_image = self._get_or_create_image(right_sha256)
        
        # Record the choice
        if outcome == "SKIP":
            winner_sha256 = None
            skipped = True
        elif outcome == "LEFT":
            winner_sha256 = left_sha256
            skipped = False
        elif outcome == "RIGHT":
            winner_sha256 = right_sha256
            skipped = False
        else:
            raise ValueError(f"Invalid outcome: {outcome}")
        
        # Insert choice record
        choice = Choice(
            round=round_num,
            left_sha256=left_sha256,
            right_sha256=right_sha256,
            winner_sha256=winner_sha256,
            skipped=skipped
        )
        self.db.add(choice)
        
        # Update ratings and statistics
        if outcome == "SKIP":
            self._handle_skip(left_image, right_image)
        else:
            self._handle_choice(left_image, right_image, outcome)
        
        self.db.commit()
        return {"ok": True}
    
    def _get_or_create_image(self, sha256: str) -> Image:
        """Get existing image or create new one with defaults."""
        stmt = select(Image).where(Image.sha256 == sha256)
        image = self.db.execute(stmt).scalar_one_or_none()
        
        if not image:
            # Create new image with default Elo+σ values
            image = Image(
                sha256=sha256,
                mu=settings.initial_mu,
                sigma=settings.initial_sigma,
                exposures=0,
                likes=0,
                unlikes=0,
                skips=0,
                is_archived_hard_no=False
            )
            self.db.add(image)
        
        return image
    
    def _handle_choice(self, left_image: Image, right_image: Image, outcome: str):
        """Handle LEFT/RIGHT choice with Elo+σ updates."""
        # Update Elo+σ ratings
        new_mu_left, new_sigma_left, new_mu_right, new_sigma_right = \
            self.elo_calc.update_ratings(
                left_image.mu, left_image.sigma,
                right_image.mu, right_image.sigma,
                outcome
            )
        
        # Apply rating updates
        left_image.mu = new_mu_left
        left_image.sigma = new_sigma_left
        right_image.mu = new_mu_right
        right_image.sigma = new_sigma_right
        
        # Update exposure counts (both images were shown)
        left_image.exposures += 1
        right_image.exposures += 1
        
        # Update like/unlike counts
        if outcome == "LEFT":
            left_image.likes += 1
            right_image.unlikes += 1
        else:  # outcome == "RIGHT"
            right_image.likes += 1
            left_image.unlikes += 1
        
        # Clear skip cooldowns (images were chosen, not skipped)
        left_image.next_eligible_round = None
        right_image.next_eligible_round = None
        
        # Update last seen round
        current_round = self._get_current_round()
        left_image.last_seen_round = current_round
        right_image.last_seen_round = current_round
    
    def _handle_skip(self, left_image: Image, right_image: Image):
        """Handle SKIP outcome with cooldown periods."""
        from ..utils.elo_utils import generate_skip_cooldown
        
        # Update skip counts
        left_image.skips += 1
        right_image.skips += 1
        
        # Set skip cooldown periods
        current_round = self._get_current_round()
        left_image.next_eligible_round = current_round + generate_skip_cooldown()
        right_image.next_eligible_round = current_round + generate_skip_cooldown()
        
        # No mu/sigma updates for skips
        # No exposure increments for skips
    
    def _get_current_round(self) -> int:
        """Get current round without incrementing."""
        stmt = select(AppState.round).where(AppState.id == 1)
        result = self.db.execute(stmt).scalar_one_or_none()
        return result if result is not None else 0