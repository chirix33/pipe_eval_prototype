"""Analyze and compare evaluation results"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import statistics


class ResultsAnalyzer:
    """Analyze evaluation results and generate comparison reports"""
    
    def __init__(self, results_dir: str = "data/results"):
        """Initialize results analyzer.
        
        Args:
            results_dir: Directory containing result JSON files
        """
        self.results_dir = Path(results_dir)
    
    def load_results(self, filename: str) -> Dict:
        """Load results from JSON file.
        
        Args:
            filename: Name of results file
            
        Returns:
            Loaded results dictionary
        """
        filepath = self.results_dir / filename
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def analyze_domain_results(self, domain_results: Dict) -> Dict:
        """Analyze results for a single domain.
        
        Args:
            domain_results: Domain evaluation results
            
        Returns:
            Analysis dictionary
        """
        if not domain_results.get("success", False):
            return {"error": "Domain evaluation failed"}
        
        baseline_scores = [
            r["score"] for r in domain_results.get("baseline_results", [])
            if r.get("success", False)
        ]
        decomp_scores = [
            r["score"] for r in domain_results.get("decomposition_results", [])
            if r.get("success", False)
        ]
        
        if not baseline_scores or not decomp_scores:
            return {"error": "Insufficient data"}
        
        analysis = {
            "domain": domain_results.get("domain"),
            "task": domain_results.get("task"),
            "num_problems": len(baseline_scores),
            "baseline": {
                "mean": statistics.mean(baseline_scores),
                "median": statistics.median(baseline_scores),
                "std": statistics.stdev(baseline_scores) if len(baseline_scores) > 1 else 0,
                "min": min(baseline_scores),
                "max": max(baseline_scores),
            },
            "decomposition": {
                "mean": statistics.mean(decomp_scores),
                "median": statistics.median(decomp_scores),
                "std": statistics.stdev(decomp_scores) if len(decomp_scores) > 1 else 0,
                "min": min(decomp_scores),
                "max": max(decomp_scores),
            },
            "improvement": {
                "absolute": statistics.mean(decomp_scores) - statistics.mean(baseline_scores),
                "relative": (
                    (statistics.mean(decomp_scores) - statistics.mean(baseline_scores)) /
                    statistics.mean(baseline_scores) * 100
                    if statistics.mean(baseline_scores) > 0 else 0
                ),
            },
            "structural_clarity": domain_results.get("avg_decomposition_quality", {}),
        }
        
        return analysis
    
    def analyze_cross_domain(self, results_file: str = "cross_domain_results.json") -> Dict:
        """Analyze cross-domain results.
        
        Args:
            results_file: Name of cross-domain results file
            
        Returns:
            Cross-domain analysis
        """
        results = self.load_results(results_file)
        
        domain_analyses = {}
        for domain_name, domain_results in results.get("results", {}).items():
            domain_analyses[domain_name] = self.analyze_domain_results(domain_results)
        
        # Aggregate statistics
        improvements = [
            a["improvement"]["absolute"]
            for a in domain_analyses.values()
            if "improvement" in a
        ]
        
        analysis = {
            "experiment_info": {
                "timestamp": results.get("experiment_timestamp"),
                "domains": results.get("domains_evaluated", []),
                "problems_per_task": results.get("problems_per_task"),
            },
            "domain_analyses": domain_analyses,
            "aggregate": {
                "avg_improvement": statistics.mean(improvements) if improvements else 0,
                "total_domains": len(domain_analyses),
            },
        }
        
        return analysis
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate text report from results.
        
        Args:
            output_file: Optional file to save report
            
        Returns:
            Report text
        """
        analysis = self.analyze_cross_domain()
        
        lines = []
        lines.append("=" * 80)
        lines.append("CROSS-DOMAIN EVALUATION REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        lines.append(f"Experiment Date: {analysis['experiment_info']['timestamp']}")
        lines.append(f"Domains Evaluated: {', '.join(analysis['experiment_info']['domains'])}")
        lines.append(f"Problems per Task: {analysis['experiment_info']['problems_per_task']}")
        lines.append("")
        
        for domain_name, domain_analysis in analysis["domain_analyses"].items():
            if "error" in domain_analysis:
                continue
            
            lines.append("-" * 80)
            lines.append(f"Domain: {domain_name.upper()} ({domain_analysis.get('task', 'N/A')})")
            lines.append("-" * 80)
            lines.append(f"Problems Evaluated: {domain_analysis['num_problems']}")
            lines.append("")
            
            lines.append("Baseline Performance:")
            lines.append(f"  Mean Accuracy: {domain_analysis['baseline']['mean']:.3f}")
            lines.append(f"  Std Dev: {domain_analysis['baseline']['std']:.3f}")
            lines.append("")
            
            lines.append("Decomposition-Guided Performance:")
            lines.append(f"  Mean Accuracy: {domain_analysis['decomposition']['mean']:.3f}")
            lines.append(f"  Std Dev: {domain_analysis['decomposition']['std']:.3f}")
            lines.append("")
            
            lines.append("Improvement:")
            lines.append(f"  Absolute: {domain_analysis['improvement']['absolute']:+.3f}")
            lines.append(f"  Relative: {domain_analysis['improvement']['relative']:+.2f}%")
            lines.append("")
            
            if "structural_clarity" in domain_analysis:
                sc = domain_analysis["structural_clarity"]
                lines.append("Structural Clarity (Decomposition Quality):")
                lines.append(f"  Avg Components: {sc.get('avg_components', 'N/A'):.2f}")
                lines.append("")
        
        lines.append("=" * 80)
        lines.append("AGGREGATE RESULTS")
        lines.append("=" * 80)
        lines.append(f"Average Improvement Across Domains: {analysis['aggregate']['avg_improvement']:+.3f}")
        lines.append("")
        
        report_text = "\n".join(lines)
        
        if output_file:
            output_path = self.results_dir / output_file
            with open(output_path, 'w') as f:
                f.write(report_text)
            print(f"Report saved to: {output_path}")
        
        return report_text


def main():
    """Generate analysis report"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze evaluation results")
    parser.add_argument("--results-dir", default="data/results", help="Results directory")
    parser.add_argument("--output", default="analysis_report.txt", help="Output report file")
    
    args = parser.parse_args()
    
    analyzer = ResultsAnalyzer(results_dir=args.results_dir)
    report = analyzer.generate_report(output_file=args.output)
    print(report)


if __name__ == "__main__":
    main()
