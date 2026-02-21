"""Evaluation metrics framework"""

import numpy as np
from typing import Dict, List, Optional, Any
from collections import defaultdict

try:
    import scipy.stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

from ..decomposition import ProblemDecomposition, SubComponent


class DecompositionCoverageMetrics:
    """Measure how well decomposition covers problem aspects"""
    
    def calculate_coverage(
        self,
        decomposition: ProblemDecomposition,
        ground_truth_components: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """Calculate how well decomposition covers problem aspects.
        
        Args:
            decomposition: The decomposition to evaluate
            ground_truth_components: Optional list of expected component goals
            
        Returns:
            Dictionary with coverage metrics
        """
        metrics = {}
        
        # Basic statistics
        metrics['num_components'] = len(decomposition.sub_components)
        
        if decomposition.sub_components:
            metrics['avg_entities_per_component'] = np.mean([
                len(c.entities) for c in decomposition.sub_components.values()
            ])
            metrics['avg_dependencies_per_component'] = np.mean([
                len(c.dependencies) for c in decomposition.sub_components.values()
            ])
        else:
            metrics['avg_entities_per_component'] = 0.0
            metrics['avg_dependencies_per_component'] = 0.0
        
        # Entity coverage: extract unique entities from problem statement
        all_entities = set()
        for component in decomposition.sub_components.values():
            all_entities.update(component.entities)
        metrics['total_unique_entities'] = len(all_entities)
        
        # Coverage if ground truth available
        if ground_truth_components:
            extracted_goals = {c.goal.lower() for c in decomposition.sub_components.values()}
            expected_goals = {g.lower() for g in ground_truth_components}
            
            if expected_goals:
                metrics['goal_recall'] = len(extracted_goals & expected_goals) / len(expected_goals)
            else:
                metrics['goal_recall'] = 0.0
            
            if extracted_goals:
                metrics['goal_precision'] = len(extracted_goals & expected_goals) / len(extracted_goals)
            else:
                metrics['goal_precision'] = 0.0
            
            if metrics['goal_recall'] + metrics['goal_precision'] > 0:
                metrics['goal_f1'] = (
                    2 * metrics['goal_recall'] * metrics['goal_precision'] /
                    (metrics['goal_recall'] + metrics['goal_precision'])
                )
            else:
                metrics['goal_f1'] = 0.0
        
        return metrics
    
    def calculate_granularity(self, decomposition: ProblemDecomposition) -> Dict[str, float]:
        """Measure appropriate level of decomposition.
        
        Args:
            decomposition: The decomposition to analyze
            
        Returns:
            Dictionary with granularity metrics
        """
        if not decomposition.sub_components:
            return {
                'avg_component_size': 0.0,
                'max_dependency_depth': 0,
                'granularity_balance': 0.0,
            }
        
        # Component size (entities per component)
        component_sizes = [len(c.entities) for c in decomposition.sub_components.values()]
        avg_size = np.mean(component_sizes)
        std_size = np.std(component_sizes) if len(component_sizes) > 1 else 0.0
        
        # Dependency depth
        max_depth = 0
        for component in decomposition.sub_components.values():
            depth = self._calculate_component_depth(component, decomposition)
            max_depth = max(max_depth, depth)
        
        # Balance: lower std = more balanced
        balance = 1.0 / (1.0 + std_size) if std_size > 0 else 1.0
        
        return {
            'avg_component_size': avg_size,
            'std_component_size': std_size,
            'max_dependency_depth': max_depth,
            'granularity_balance': balance,
        }
    
    def _calculate_component_depth(
        self,
        component: SubComponent,
        decomposition: ProblemDecomposition,
        visited: Optional[set] = None
    ) -> int:
        """Calculate dependency depth of a component."""
        if visited is None:
            visited = set()
        
        if component.component_id in visited:
            return 0  # Circular dependency
        
        if not component.dependencies:
            return 0
        
        visited.add(component.component_id)
        max_dep_depth = 0
        
        for dep_id in component.dependencies:
            dep_component = decomposition.get_component(dep_id)
            if dep_component:
                dep_depth = self._calculate_component_depth(dep_component, decomposition, visited.copy())
                max_dep_depth = max(max_dep_depth, dep_depth)
        
        return max_dep_depth + 1
    
    def calculate_dependency_accuracy(
        self,
        decomposition: ProblemDecomposition,
        ground_truth_deps: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """Measure correctness of dependency relationships.
        
        Args:
            decomposition: The decomposition to evaluate
            ground_truth_deps: Optional dict mapping component_id -> expected dependencies
            
        Returns:
            Dictionary with dependency accuracy metrics
        """
        metrics = {}
        
        # Check for circular dependencies
        metrics['has_circular_deps'] = self._detect_circular_dependencies(decomposition)
        
        # Validate all dependencies exist
        all_ids = set(decomposition.sub_components.keys())
        invalid_deps = []
        for comp_id, component in decomposition.sub_components.items():
            for dep_id in component.dependencies:
                if dep_id not in all_ids:
                    invalid_deps.append((comp_id, dep_id))
        
        metrics['invalid_dependencies'] = len(invalid_deps)
        metrics['invalid_dependency_pairs'] = invalid_deps
        
        # Compare with ground truth if available
        if ground_truth_deps:
            correct_deps = 0
            total_predicted = 0
            total_expected = 0
            
            for comp_id, component in decomposition.sub_components.items():
                predicted_deps = set(component.dependencies)
                expected_deps = set(ground_truth_deps.get(comp_id, []))
                
                correct_deps += len(predicted_deps & expected_deps)
                total_predicted += len(predicted_deps)
                total_expected += len(expected_deps)
            
            if total_predicted > 0:
                metrics['dependency_precision'] = correct_deps / total_predicted
            else:
                metrics['dependency_precision'] = 0.0
            
            if total_expected > 0:
                metrics['dependency_recall'] = correct_deps / total_expected
            else:
                metrics['dependency_recall'] = 0.0
            
            if metrics['dependency_precision'] + metrics['dependency_recall'] > 0:
                metrics['dependency_f1'] = (
                    2 * metrics['dependency_precision'] * metrics['dependency_recall'] /
                    (metrics['dependency_precision'] + metrics['dependency_recall'])
                )
            else:
                metrics['dependency_f1'] = 0.0
        
        return metrics
    
    def _detect_circular_dependencies(self, decomposition: ProblemDecomposition) -> bool:
        """Detect if there are circular dependencies."""
        visited = set()
        rec_stack = set()
        
        def has_cycle(comp_id: str) -> bool:
            visited.add(comp_id)
            rec_stack.add(comp_id)
            
            component = decomposition.get_component(comp_id)
            if component:
                for dep_id in component.dependencies:
                    if dep_id not in visited:
                        if has_cycle(dep_id):
                            return True
                    elif dep_id in rec_stack:
                        return True
            
            rec_stack.remove(comp_id)
            return False
        
        for comp_id in decomposition.sub_components.keys():
            if comp_id not in visited:
                if has_cycle(comp_id):
                    return True
        
        return False


class WeightAccuracyMetrics:
    """Measure how well weights predict actual difficulty and impact"""
    
    def calculate_difficulty_correlation(
        self,
        decomposition: ProblemDecomposition,
        actual_difficulties: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate correlation between predicted and actual difficulties.
        
        Args:
            decomposition: The decomposition with predicted weights
            actual_difficulties: Dict mapping component_id -> actual difficulty (0-1)
            
        Returns:
            Dictionary with correlation metrics
        """
        correlations = {}
        
        predicted_diffs = []
        actual_diffs = []
        
        for comp_id, component in decomposition.sub_components.items():
            if comp_id in actual_difficulties:
                predicted_diffs.append(component.difficulty)
                actual_diffs.append(actual_difficulties[comp_id])
        
        if len(predicted_diffs) > 1:
            if SCIPY_AVAILABLE:
                pearson_r, pearson_p = scipy.stats.pearsonr(predicted_diffs, actual_diffs)
                spearman_r, spearman_p = scipy.stats.spearmanr(predicted_diffs, actual_diffs)
                
                correlations['pearson_correlation'] = pearson_r
                correlations['pearson_p_value'] = pearson_p
                correlations['spearman_correlation'] = spearman_r
                correlations['spearman_p_value'] = spearman_p
            else:
                # Fallback to numpy correlation
                correlations['pearson_correlation'] = np.corrcoef(predicted_diffs, actual_diffs)[0, 1]
                correlations['pearson_p_value'] = None
                correlations['spearman_correlation'] = None
                correlations['spearman_p_value'] = None
            
            correlations['mae'] = np.mean(np.abs(np.array(predicted_diffs) - np.array(actual_diffs)))
            correlations['rmse'] = np.sqrt(np.mean((np.array(predicted_diffs) - np.array(actual_diffs)) ** 2))
        else:
            correlations['pearson_correlation'] = 0.0
            correlations['pearson_p_value'] = None
            correlations['spearman_correlation'] = 0.0
            correlations['spearman_p_value'] = None
            correlations['mae'] = 0.0
            correlations['rmse'] = 0.0
        
        return correlations
    
    def calculate_ranking_accuracy(
        self,
        decomposition: ProblemDecomposition,
        optimal_order: List[str],
        weight_calculator: Any
    ) -> Dict[str, float]:
        """Measure if priority ordering matches optimal ordering.
        
        Args:
            decomposition: The decomposition
            optimal_order: List of component_ids in optimal solving order
            weight_calculator: WeightCalculator instance for priority scores
            
        Returns:
            Dictionary with ranking accuracy metrics
        """
        # Get predicted order by priority
        predicted_order = sorted(
            decomposition.sub_components.keys(),
            key=lambda cid: weight_calculator.get_priority_score(
                decomposition.get_component(cid)
            ),
            reverse=True
        )
        
        metrics = {}
        
        # Top-K accuracy
        for k in [1, 3, 5]:
            if len(optimal_order) >= k:
                top_k_optimal = set(optimal_order[:k])
                top_k_predicted = set(predicted_order[:k])
                metrics[f'top_{k}_accuracy'] = len(top_k_optimal & top_k_predicted) / k
            else:
                metrics[f'top_{k}_accuracy'] = 0.0
        
        # Kendall's tau if scipy available
        if SCIPY_AVAILABLE and len(optimal_order) == len(predicted_order):
            try:
                tau, p_value = scipy.stats.kendalltau(predicted_order, optimal_order)
                metrics['kendall_tau'] = tau
                metrics['kendall_p_value'] = p_value
            except:
                metrics['kendall_tau'] = None
                metrics['kendall_p_value'] = None
        else:
            metrics['kendall_tau'] = None
            metrics['kendall_p_value'] = None
        
        # Average position error
        position_errors = []
        for comp_id in optimal_order:
            if comp_id in predicted_order:
                optimal_pos = optimal_order.index(comp_id)
                predicted_pos = predicted_order.index(comp_id)
                position_errors.append(abs(optimal_pos - predicted_pos))
        
        if position_errors:
            metrics['avg_position_error'] = np.mean(position_errors)
            metrics['max_position_error'] = np.max(position_errors)
        else:
            metrics['avg_position_error'] = 0.0
            metrics['max_position_error'] = 0.0
        
        return metrics
    
    def calculate_impact_accuracy(
        self,
        decomposition: ProblemDecomposition,
        actual_failures: Dict[str, bool]
    ) -> Dict[str, float]:
        """Measure if failure impact weights predict actual failures.
        
        Args:
            decomposition: The decomposition
            actual_failures: Dict mapping component_id -> bool (did this component fail?)
            
        Returns:
            Dictionary with impact accuracy metrics
        """
        metrics = {}
        
        # Separate high and low impact components
        high_impact_threshold = 0.7
        high_impact_components = [
            comp_id for comp_id, comp in decomposition.sub_components.items()
            if comp.failure_impact >= high_impact_threshold
        ]
        low_impact_components = [
            comp_id for comp_id, comp in decomposition.sub_components.items()
            if comp.failure_impact < high_impact_threshold
        ]
        
        # Calculate failure rates
        if high_impact_components:
            high_impact_failures = sum(
                actual_failures.get(cid, False) for cid in high_impact_components
            )
            metrics['high_impact_failure_rate'] = high_impact_failures / len(high_impact_components)
        else:
            metrics['high_impact_failure_rate'] = 0.0
        
        if low_impact_components:
            low_impact_failures = sum(
                actual_failures.get(cid, False) for cid in low_impact_components
            )
            metrics['low_impact_failure_rate'] = low_impact_failures / len(low_impact_components)
        else:
            metrics['low_impact_failure_rate'] = 0.0
        
        # Impact difference (should be positive if weights are good)
        metrics['impact_difference'] = (
            metrics['high_impact_failure_rate'] - metrics['low_impact_failure_rate']
        )
        
        # Calculate AUC if scipy available
        if SCIPY_AVAILABLE:
            impacts = [comp.failure_impact for comp in decomposition.sub_components.values()]
            failures = [actual_failures.get(cid, False) for cid in decomposition.sub_components.keys()]
            
            if len(set(failures)) > 1:  # Need both True and False
                try:
                    from sklearn.metrics import roc_auc_score
                    metrics['impact_prediction_auc'] = roc_auc_score(failures, impacts)
                except ImportError:
                    metrics['impact_prediction_auc'] = None
            else:
                metrics['impact_prediction_auc'] = None
        else:
            metrics['impact_prediction_auc'] = None
        
        return metrics


class SolutionImprovementMetrics:
    """Measure improvement when using decomposition"""
    
    def calculate_accuracy_improvement(
        self,
        baseline_scores: List[float],
        decomposition_scores: List[float]
    ) -> Dict[str, float]:
        """Compare solution accuracy with/without decomposition guidance.
        
        Args:
            baseline_scores: List of scores without decomposition
            decomposition_scores: List of scores with decomposition
            
        Returns:
            Dictionary with improvement metrics
        """
        baseline_acc = np.mean(baseline_scores)
        decomp_acc = np.mean(decomposition_scores)
        
        baseline_std = np.std(baseline_scores)
        decomp_std = np.std(decomposition_scores)
        
        absolute_improvement = decomp_acc - baseline_acc
        
        if baseline_acc > 0:
            relative_improvement = absolute_improvement / baseline_acc
        else:
            relative_improvement = 0.0
        
        if baseline_acc < 1.0:
            error_reduction = absolute_improvement / (1.0 - baseline_acc)
        else:
            error_reduction = 0.0
        
        # Statistical significance if scipy available
        if SCIPY_AVAILABLE and len(baseline_scores) > 1 and len(decomposition_scores) > 1:
            try:
                t_stat, p_value = scipy.stats.ttest_ind(decomposition_scores, baseline_scores)
                is_significant = p_value < 0.05
            except:
                t_stat, p_value = None, None
                is_significant = False
        else:
            t_stat, p_value = None, None
            is_significant = False
        
        return {
            'baseline_accuracy': baseline_acc,
            'baseline_std': baseline_std,
            'decomposition_accuracy': decomp_acc,
            'decomposition_std': decomp_std,
            'absolute_improvement': absolute_improvement,
            'relative_improvement': relative_improvement,
            'error_reduction': error_reduction,
            't_statistic': t_stat,
            'p_value': p_value,
            'is_significant': is_significant,
        }
    
    def calculate_component_accuracy(
        self,
        component_scores: Dict[str, List[float]]
    ) -> Dict[str, Any]:
        """Measure accuracy at component level.
        
        Args:
            component_scores: Dict mapping component_id -> List[scores across problems]
            
        Returns:
            Dictionary with component-level metrics
        """
        metrics = {
            'per_component_accuracy': {},
            'avg_component_accuracy': 0.0,
            'component_failure_rate': {},
        }
        
        if not component_scores:
            return metrics
        
        per_component_acc = {}
        per_component_failure = {}
        
        for comp_id, scores in component_scores.items():
            if scores:
                acc = np.mean(scores)
                per_component_acc[comp_id] = acc
                per_component_failure[comp_id] = 1.0 - acc
        
        metrics['per_component_accuracy'] = per_component_acc
        metrics['component_failure_rate'] = per_component_failure
        
        if per_component_acc:
            metrics['avg_component_accuracy'] = np.mean(list(per_component_acc.values()))
            metrics['min_component_accuracy'] = np.min(list(per_component_acc.values()))
            metrics['max_component_accuracy'] = np.max(list(per_component_acc.values()))
        
        return metrics


class EvaluationMetrics:
    """Comprehensive evaluation metrics combining all metric classes"""
    
    def __init__(self):
        """Initialize evaluation metrics"""
        self.coverage_metrics = DecompositionCoverageMetrics()
        self.weight_metrics = WeightAccuracyMetrics()
        self.solution_metrics = SolutionImprovementMetrics()
    
    def evaluate_decomposition(
        self,
        decomposition: ProblemDecomposition,
        ground_truth_components: Optional[List[str]] = None,
        ground_truth_deps: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """Evaluate decomposition quality.
        
        Args:
            decomposition: The decomposition to evaluate
            ground_truth_components: Optional expected component goals
            ground_truth_deps: Optional expected dependencies
            
        Returns:
            Dictionary with all decomposition metrics
        """
        return {
            'coverage': self.coverage_metrics.calculate_coverage(
                decomposition, ground_truth_components
            ),
            'granularity': self.coverage_metrics.calculate_granularity(decomposition),
            'dependencies': self.coverage_metrics.calculate_dependency_accuracy(
                decomposition, ground_truth_deps
            ),
        }
    
    def evaluate_weights(
        self,
        decomposition: ProblemDecomposition,
        actual_difficulties: Optional[Dict[str, float]] = None,
        optimal_order: Optional[List[str]] = None,
        actual_failures: Optional[Dict[str, bool]] = None,
        weight_calculator: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Evaluate weight accuracy.
        
        Args:
            decomposition: The decomposition with weights
            actual_difficulties: Optional actual difficulty scores
            optimal_order: Optional optimal component ordering
            actual_failures: Optional actual failure outcomes
            weight_calculator: Optional WeightCalculator instance
            
        Returns:
            Dictionary with weight accuracy metrics
        """
        results = {}
        
        if actual_difficulties:
            results['difficulty_correlation'] = self.weight_metrics.calculate_difficulty_correlation(
                decomposition, actual_difficulties
            )
        
        if optimal_order and weight_calculator:
            results['ranking_accuracy'] = self.weight_metrics.calculate_ranking_accuracy(
                decomposition, optimal_order, weight_calculator
            )
        
        if actual_failures:
            results['impact_accuracy'] = self.weight_metrics.calculate_impact_accuracy(
                decomposition, actual_failures
            )
        
        return results
    
    def evaluate_solution_improvement(
        self,
        baseline_scores: List[float],
        decomposition_scores: List[float],
        component_scores: Optional[Dict[str, List[float]]] = None
    ) -> Dict[str, Any]:
        """Evaluate solution improvement.
        
        Args:
            baseline_scores: Scores without decomposition
            decomposition_scores: Scores with decomposition
            component_scores: Optional component-level scores
            
        Returns:
            Dictionary with improvement metrics
        """
        results = {
            'accuracy_improvement': self.solution_metrics.calculate_accuracy_improvement(
                baseline_scores, decomposition_scores
            ),
        }
        
        if component_scores:
            results['component_accuracy'] = self.solution_metrics.calculate_component_accuracy(
                component_scores
            )
        
        return results
