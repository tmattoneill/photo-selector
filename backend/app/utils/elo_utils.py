"""
Elo+σ rating calculation utilities as per algo-update.yaml specification.
"""
import math
import random
from typing import Tuple


class EloCalculator:
    """Elo+σ rating calculator following the exact spec from algo-update.yaml."""
    
    def __init__(self):
        # Constants from spec
        self.k_base = 24
        self.sigma0 = 350
        self.sigma_min = 60
        self.k_min = 8
        self.k_max = 48
        self.sigma_decay = 0.97
    
    def expected_score(self, mu_a: float, mu_b: float) -> float:
        """
        Calculate expected score using Elo formula.
        E(a) = 1 / (1 + 10^((mu_b - mu_a)/400))
        """
        return 1.0 / (1.0 + math.pow(10, (mu_b - mu_a) / 400.0))
    
    def k_factor(self, sigma: float) -> float:
        """
        Calculate dynamic K-factor based on uncertainty.
        K_i = clamp(k_base * (sigma_i / sigma0), k_min, k_max)
        """
        k = self.k_base * (sigma / self.sigma0)
        return max(self.k_min, min(self.k_max, k))
    
    def update_ratings(self, mu_a: float, sigma_a: float, mu_b: float, sigma_b: float, 
                      outcome: str) -> Tuple[float, float, float, float]:
        """
        Update Elo ratings based on outcome.
        
        Args:
            mu_a, sigma_a: Rating and uncertainty for left image
            mu_b, sigma_b: Rating and uncertainty for right image
            outcome: "LEFT", "RIGHT", or "SKIP"
            
        Returns:
            Tuple of (new_mu_a, new_sigma_a, new_mu_b, new_sigma_b)
        """
        if outcome == "SKIP":
            # No rating updates for skips, only sigma updates
            new_sigma_a = sigma_a  # No change for skips
            new_sigma_b = sigma_b  # No change for skips
            return mu_a, new_sigma_a, mu_b, new_sigma_b
        
        # Calculate expected scores
        E_a = self.expected_score(mu_a, mu_b)
        E_b = 1.0 - E_a  # E_b = expected_score(mu_b, mu_a)
        
        # Actual scores based on outcome
        if outcome == "LEFT":
            S_a = 1.0
            S_b = 0.0
        elif outcome == "RIGHT":
            S_a = 0.0
            S_b = 1.0
        else:
            raise ValueError(f"Invalid outcome: {outcome}")
        
        # Calculate K-factors
        K_a = self.k_factor(sigma_a)
        K_b = self.k_factor(sigma_b)
        
        # Update mu values
        new_mu_a = mu_a + K_a * (S_a - E_a)
        new_mu_b = mu_b + K_b * (S_b - E_b)
        
        # Update sigma values (uncertainty decreases on exposure)
        new_sigma_a = max(self.sigma_min, sigma_a * self.sigma_decay)
        new_sigma_b = max(self.sigma_min, sigma_b * self.sigma_decay)
        
        return new_mu_a, new_sigma_a, new_mu_b, new_sigma_b
    
    def confidence_interval(self, mu: float, sigma: float, z: float = 1.0) -> Tuple[float, float]:
        """
        Calculate confidence interval bounds.
        CI = mu ± z*sigma
        """
        lower = mu - z * sigma
        upper = mu + z * sigma
        return lower, upper


def generate_skip_cooldown() -> int:
    """Generate random skip cooldown between 11-49 rounds as per spec."""
    return random.randint(11, 49)


def calculate_information_gain(mu_a: float, sigma_a: float, mu_b: float, sigma_b: float) -> float:
    """
    Estimate information gain from comparing two images.
    Higher sigma (uncertainty) and closer mu values = more information.
    """
    # Uncertainty factor (higher sigma = more info)
    uncertainty_factor = (sigma_a + sigma_b) / 2.0
    
    # Closeness factor (closer mu = more discriminative)
    mu_diff = abs(mu_a - mu_b)
    closeness_factor = 1.0 / (1.0 + mu_diff / 100.0)  # Scale factor
    
    # Combined information gain
    return uncertainty_factor * closeness_factor