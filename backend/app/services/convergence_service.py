"""
Convergence detection system implementing algo-update.yaml section 6.
"""
import statistics
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, text, desc, asc
from ..models.image import Image
from ..models.choice import Choice
from ..models.app_state import AppState
from ..core.config import settings


class ConvergenceService:
    """Convergence detection and stability tracking per algo-update.yaml spec."""
    
    def __init__(self, db: Session):
        self.db = db
        self.config = {
            'target_top_k': settings.target_top_k,
            'natural_cutoff_delta': settings.natural_cutoff_delta,
            'min_exposures_per_image': settings.min_exposures_per_image,
            'confidence_z': settings.confidence_z,
            'sigma_confident_max': settings.sigma_confident_max,
            'min_boundary_gap': settings.min_boundary_gap,
            'stability_window_rounds': settings.stability_window_rounds,
            'max_rank_swaps_in_window': settings.max_rank_swaps_in_window,
            'coverage_required': settings.coverage_required
        }
    
    def get_convergence_state(self) -> Dict[str, Any]:
        """
        Get comprehensive convergence state per algo-update.yaml telemetry spec.
        
        Returns:
            Dict with convergence metrics, predicates, and UI signals
        """
        current_round = self._get_current_round()
        
        # Get ordered images by ranking
        ordered_images = self._get_ordered_images()
        
        # Coverage metrics
        coverage = self._compute_coverage()
        
        # Top-K analysis
        top_k_data = self._analyze_top_k(ordered_images)
        
        # Stability analysis
        stability = self._analyze_stability(current_round)
        
        # Boundary analysis
        boundary = self._analyze_boundary_gap(ordered_images)
        
        # Predicate evaluation
        predicates = self._evaluate_predicates(coverage, top_k_data, boundary, stability)
        
        # Auto-finish decision
        auto_finish = self._decide_auto_finish(predicates)
        
        return {
            'current_round': current_round,
            'coverage': coverage,
            'top_k': top_k_data,
            'stability': stability,
            'boundary': boundary,
            'predicates': predicates,
            'auto_finish': auto_finish,
            'ui_signals': self._generate_ui_signals(boundary, stability)
        }
    
    def _get_current_round(self) -> int:
        """Get current round from app state."""
        stmt = select(AppState.round).where(AppState.id == 1)
        result = self.db.execute(stmt).scalar()
        return result or 0
    
    def _get_ordered_images(self) -> List[Dict[str, Any]]:
        """Get images ordered by ranking per algo-update.yaml ordering spec."""
        stmt = select(
            Image.sha256,
            Image.mu,
            Image.sigma,
            Image.exposures
        ).order_by(
            desc(Image.mu),  # ORDER BY mu DESC
            asc(Image.sigma),  # sigma ASC  
            desc(Image.exposures),  # exposures DESC
            asc(Image.sha256)  # sha256 ASC (tie-breaker)
        )
        
        results = self.db.execute(stmt).fetchall()
        return [
            {
                'sha256': row.sha256,
                'mu': row.mu,
                'sigma': row.sigma,
                'exposures': row.exposures,
                'rank': idx + 1,
                'ci_lower': row.mu - self.config['confidence_z'] * row.sigma,
                'ci_upper': row.mu + self.config['confidence_z'] * row.sigma
            }
            for idx, row in enumerate(results)
        ]
    
    def _compute_coverage(self) -> Dict[str, Any]:
        """Compute coverage metrics per algo-update.yaml coverage spec."""
        # Count unseen images (exposures = 0)
        unseen_stmt = select(func.count()).select_from(Image).where(Image.exposures == 0)
        unseen_count = self.db.execute(unseen_stmt).scalar() or 0
        
        # Count seen images (exposures > 0)  
        seen_stmt = select(func.count()).select_from(Image).where(Image.exposures > 0)
        seen_count = self.db.execute(seen_stmt).scalar() or 0
        
        total_count = unseen_count + seen_count
        
        return {
            'unseen_count': unseen_count,
            'seen_count': seen_count,
            'total_count': total_count,
            'coverage_pct': (seen_count / total_count * 100) if total_count > 0 else 0,
            'coverage_complete': unseen_count == 0
        }
    
    def _analyze_top_k(self, ordered_images: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze top-K selection and properties."""
        k = self.config['target_top_k']
        if k is None or k > len(ordered_images):
            k = len(ordered_images)
        
        top_k = ordered_images[:k] if k > 0 else []
        
        # Get median mu for natural threshold
        all_mus = [img['mu'] for img in ordered_images]
        median_mu = statistics.median(all_mus) if all_mus else 1500.0
        
        # SHA256 list for stability tracking
        top_k_sha256s = [img['sha256'] for img in top_k]
        
        return {
            'k': k,
            'median_mu': median_mu,
            'top_k_sha256s': top_k_sha256s,
            'top_k_images': top_k
        }
    
    def _analyze_boundary_gap(self, ordered_images: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze boundary gap per algo-update.yaml boundary spec."""
        k = self.config['target_top_k']
        if k is None or k >= len(ordered_images):
            return {
                'boundary_gap': float('inf'),
                'boundary_sigmas': [0, 0],
                'max_boundary_sigma': 0,
                'k_image': None,
                'k_plus_1_image': None
            }
        
        k_image = ordered_images[k-1]  # k-th image (0-indexed)
        k_plus_1_image = ordered_images[k] if k < len(ordered_images) else None
        
        if k_plus_1_image is None:
            boundary_gap = float('inf')
            boundary_sigmas = [k_image['sigma'], 0]
        else:
            # boundary_gap = ci_lower(k) - ci_upper(k+1)
            boundary_gap = k_image['ci_lower'] - k_plus_1_image['ci_upper']
            boundary_sigmas = [k_image['sigma'], k_plus_1_image['sigma']]
        
        return {
            'boundary_gap': boundary_gap,
            'boundary_sigmas': boundary_sigmas,
            'max_boundary_sigma': max(boundary_sigmas),
            'k_image': k_image,
            'k_plus_1_image': k_plus_1_image
        }
    
    def _analyze_stability(self, current_round: int) -> Dict[str, Any]:
        """Analyze Top-K stability over window per algo-update.yaml stability spec."""
        window_rounds = self.config['stability_window_rounds']
        window_start = max(1, current_round - window_rounds + 1)
        
        # For now, return placeholder - full implementation would track historical Top-K
        # This would require storing Top-K snapshots per round
        return {
            'window_start': window_start,
            'window_end': current_round,
            'window_size': min(window_rounds, current_round),
            'top_k_swaps_in_window': 0,  # Placeholder - needs historical tracking
            'stability_attained': True  # Placeholder
        }
    
    def _evaluate_predicates(self, coverage: Dict[str, Any], top_k_data: Dict[str, Any], 
                           boundary: Dict[str, Any], stability: Dict[str, Any]) -> Dict[str, bool]:
        """Evaluate convergence predicates per algo-update.yaml predicates spec."""
        
        # coverage_complete: coverage_required -> unseen_count == 0 else true
        coverage_complete = (not self.config['coverage_required']) or coverage['coverage_complete']
        
        # exposures_floor_met: min(exposures in ranks [k-3..k+3]) >= min_exposures_per_image
        k = top_k_data['k']
        exposures_floor_met = True  # Placeholder - would check exposures around rank k
        
        # confidence_separation: boundary_gap >= min_boundary_gap AND max(boundary_sigmas) <= sigma_confident_max
        confidence_separation = (
            boundary['boundary_gap'] >= self.config['min_boundary_gap'] and
            boundary['max_boundary_sigma'] <= self.config['sigma_confident_max']
        )
        
        # stability_attained: topk_swaps_last_window <= max_rank_swaps_in_window
        stability_attained = (
            stability['top_k_swaps_in_window'] <= self.config['max_rank_swaps_in_window']
        )
        
        return {
            'coverage_complete': coverage_complete,
            'exposures_floor_met': exposures_floor_met,
            'confidence_separation': confidence_separation,
            'stability_attained': stability_attained
        }
    
    def _decide_auto_finish(self, predicates: Dict[str, bool]) -> Dict[str, Any]:
        """Decide auto-finish per algo-update.yaml decision rule."""
        # auto_finish: coverage_complete AND exposures_floor_met AND (confidence_separation OR stability_attained)
        auto_finish = (
            predicates['coverage_complete'] and
            predicates['exposures_floor_met'] and
            (predicates['confidence_separation'] or predicates['stability_attained'])
        )
        
        return {
            'should_auto_finish': auto_finish,
            'reason': self._get_finish_reason(predicates, auto_finish)
        }
    
    def _get_finish_reason(self, predicates: Dict[str, bool], auto_finish: bool) -> str:
        """Generate human-readable finish reason."""
        if auto_finish:
            separation = predicates['confidence_separation']
            stability = predicates['stability_attained']
            if separation and stability:
                return "Confidence separation and stability both achieved"
            elif separation:
                return "Confidence separation achieved"
            elif stability:
                return "Stability achieved"
        
        missing = []
        if not predicates['coverage_complete']:
            missing.append("coverage incomplete")
        if not predicates['exposures_floor_met']:
            missing.append("insufficient exposures")
        if not predicates['confidence_separation'] and not predicates['stability_attained']:
            missing.append("neither confidence nor stability achieved")
        
        return f"Not ready: {', '.join(missing)}"
    
    def get_portfolio_progress(self) -> Dict[str, Any]:
        """
        Calculate overall portfolio completion progress.
        
        Returns comprehensive progress metrics for UI display.
        """
        convergence_state = self.get_convergence_state()
        coverage = convergence_state['coverage']
        top_k_data = convergence_state['top_k']
        boundary = convergence_state['boundary']
        stability = convergence_state['stability']
        
        # Component progress calculations
        components = self._calculate_component_progress(coverage, top_k_data, boundary, stability)
        
        # Overall progress using weighted formula
        overall = (
            0.30 * components['coverage']['progress'] +
            0.25 * components['exposure']['progress'] + 
            0.25 * components['confidence']['progress'] +
            0.20 * components['stability']['progress']
        )
        
        # Estimates and milestones
        estimates = self._calculate_estimates(overall, coverage['total_count'])
        milestones = self._get_milestone_info(overall)
        
        return {
            'overall_progress': round(overall, 1),
            'components': components,
            'estimates': estimates,
            'milestones': milestones
        }
    
    def _calculate_component_progress(self, coverage: Dict, top_k_data: Dict, 
                                    boundary: Dict, stability: Dict) -> Dict[str, Any]:
        """Calculate progress for each component."""
        
        # Coverage Progress (30%): How many images have been seen
        coverage_progress = coverage['coverage_pct']
        
        # Exposure Progress (25%): Images with sufficient exposures
        ordered_images = self._get_ordered_images()
        well_exposed = sum(1 for img in ordered_images 
                          if img['exposures'] >= self.config['min_exposures_per_image'])
        exposure_progress = (well_exposed / max(1, len(ordered_images))) * 100
        
        # Confidence Progress (25%): Boundary separation and sigma reduction
        if boundary['boundary_gap'] == float('inf'):
            confidence_progress = 100.0
        else:
            gap_progress = min(100, (boundary['boundary_gap'] / self.config['min_boundary_gap']) * 100)
            sigma_progress = max(0, min(100, 
                (self.config['sigma_confident_max'] - boundary['max_boundary_sigma']) / 
                self.config['sigma_confident_max'] * 100))
            confidence_progress = (gap_progress + sigma_progress) / 2
        
        # Stability Progress (20%): Top-K consistency (placeholder implementation)
        stability_progress = 75.0 if stability['stability_attained'] else 40.0
        
        return {
            'coverage': {
                'progress': coverage_progress,
                'label': 'Images Seen',
                'value': coverage['seen_count'],
                'total': coverage['total_count']
            },
            'exposure': {
                'progress': exposure_progress,
                'label': 'Evaluation Depth',
                'value': well_exposed,
                'total': len(ordered_images)
            },
            'confidence': {
                'progress': confidence_progress,
                'label': 'Confidence Level',
                'value': boundary['boundary_gap'],
                'target': self.config['min_boundary_gap']
            },
            'stability': {
                'progress': stability_progress,
                'label': 'Ranking Stability',
                'value': stability['top_k_swaps_in_window'],
                'target': self.config['max_rank_swaps_in_window']
            }
        }
    
    def _calculate_estimates(self, overall_progress: float, total_images: int) -> Dict[str, Any]:
        """Calculate remaining comparisons and readiness."""
        
        # Base estimate: 5 comparisons per image for full evaluation
        base_comparisons = total_images * 5
        
        # Adjust based on current progress
        remaining_progress = 100 - overall_progress
        comparisons_remaining = max(0, int((remaining_progress / 100) * base_comparisons))
        
        # Portfolio readiness (85% threshold)
        portfolio_ready = overall_progress >= 85.0
        
        # Quality indicator
        if overall_progress >= 95:
            quality = "excellent"
        elif overall_progress >= 85:
            quality = "very good"
        elif overall_progress >= 70:
            quality = "good"
        elif overall_progress >= 50:
            quality = "fair"
        else:
            quality = "early"
        
        return {
            'comparisons_remaining': comparisons_remaining,
            'portfolio_ready': portfolio_ready,
            'quality_indicator': quality
        }
    
    def _get_milestone_info(self, progress: float) -> Dict[str, Any]:
        """Get next milestone information."""
        milestones = [
            (25, "Getting started"),
            (50, "Good progress"),
            (75, "Portfolio taking shape"),
            (85, "Ready to create portfolio"),
            (95, "Excellent results")
        ]
        
        next_milestone = None
        next_label = None
        
        for milestone_pct, label in milestones:
            if progress < milestone_pct:
                next_milestone = milestone_pct
                next_label = label
                break
        
        return {
            'next_milestone': next_milestone,
            'next_milestone_label': next_label,
            'current_milestone': max([m[0] for m in milestones if progress >= m[0]], default=0)
        }

    def _generate_ui_signals(self, boundary: Dict[str, Any], stability: Dict[str, Any]) -> Dict[str, Any]:
        """Generate UI progress meters per algo-update.yaml ui_signals spec."""
        return {
            'meters': [
                {
                    'name': 'Confidence gap',
                    'value': boundary['boundary_gap'],
                    'target': self.config['min_boundary_gap'],
                    'progress': min(100, boundary['boundary_gap'] / self.config['min_boundary_gap'] * 100)
                },
                {
                    'name': 'Uncertainty σ @ boundary',
                    'value': boundary['max_boundary_sigma'],
                    'target': self.config['sigma_confident_max'],
                    'progress': min(100, (self.config['sigma_confident_max'] - boundary['max_boundary_sigma']) / self.config['sigma_confident_max'] * 100)
                },
                {
                    'name': 'Stability (Top-K swaps)',
                    'value': stability['top_k_swaps_in_window'],
                    'target': self.config['max_rank_swaps_in_window'],
                    'progress': min(100, (self.config['max_rank_swaps_in_window'] - stability['top_k_swaps_in_window']) / max(1, self.config['max_rank_swaps_in_window']) * 100)
                }
            ]
        }