"""Solution verification framework"""

import re
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from ..decomposition import ProblemDecomposition, SubComponent


class SolutionVerifier(ABC):
    """Abstract base class for solution verification"""
    
    @abstractmethod
    def verify(self, decomposition: ProblemDecomposition, solution: str, problem_entry: Dict[str, Any], dataset: Any) -> Dict[str, Any]:
        """Verify a solution against a decomposition"""
        pass


class FinalAnswerVerifier(SolutionVerifier):
    """Option B: Simple final answer verification using reasoning-gym's score_answer.
    
    This is the default, fast verification method that uses reasoning-gym's built-in
    verification without requiring expensive LLM calls.
    """
    
    def verify(
        self, 
        decomposition: ProblemDecomposition, 
        solution: str, 
        problem_entry: Dict[str, Any], 
        dataset: Any
    ) -> Dict[str, Any]:
        """Verify final answer using reasoning-gym's score_answer method.
        
        Args:
            decomposition: The problem decomposition
            solution: The LLM's solution (final answer)
            problem_entry: The original problem entry from reasoning-gym
            dataset: The reasoning-gym dataset instance (has score_answer method)
            
        Returns:
            Dictionary with verification results:
            - final_score: float (0.0-1.0)
            - is_correct: bool
            - verification_method: str
        """
        # Use reasoning-gym's built-in verification
        final_score = dataset.score_answer(answer=solution, entry=problem_entry)
        
        return {
            'final_score': final_score,
            'is_correct': final_score >= 0.99,  # Consider 0.99+ as correct
            'verification_method': 'final_answer',
            'component_scores': None,  # Not available in Option B
        }
    
    def verify_batch(
        self,
        decompositions: List[ProblemDecomposition],
        solutions: List[str],
        problem_entries: List[Dict[str, Any]],
        dataset: Any
    ) -> List[Dict[str, Any]]:
        """Verify multiple solutions in batch.
        
        Args:
            decompositions: List of decompositions
            solutions: List of solutions
            problem_entries: List of problem entries
            dataset: The reasoning-gym dataset instance
            
        Returns:
            List of verification result dictionaries
        """
        results = []
        for decomp, solution, entry in zip(decompositions, solutions, problem_entries):
            result = self.verify(decomp, solution, entry, dataset)
            results.append(result)
        return results


class ComponentLevelVerifier(SolutionVerifier):
    """Option A: Component-level verification with intermediate step extraction.
    
    This is an expensive method that uses LLM calls to extract and verify
    intermediate steps. Use sparingly or for detailed analysis only.
    """
    
    INTERMEDIATE_EXTRACTION_PROMPT = """You solved this problem: "{problem_statement}"

Your solution was: "{solution}"

Please break down your solution into intermediate steps, showing how you solved each sub-component of the problem. For each step, indicate:
1. Which sub-goal you were addressing
2. What calculation or reasoning you performed
3. The intermediate result

Format your response as a JSON object with this structure:
{{
    "steps": [
        {{
            "component_goal": "description of sub-goal",
            "calculation": "what you did",
            "result": "intermediate result"
        }}
    ]
}}

Return only valid JSON, no additional text."""

    COMPONENT_VERIFICATION_PROMPT = """Given this problem component:
Goal: {goal}
Entities: {entities}
Dependencies: {dependencies}

And this intermediate solution step:
{step_description}

Does this step correctly solve the component goal? Consider:
- Does it address the right entities?
- Is the calculation/logic correct?
- Does it produce a reasonable result?

Respond with JSON:
{{
    "is_correct": true/false,
    "confidence": 0.0-1.0,
    "explanation": "brief explanation"
}}"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """Initialize component-level verifier.
        
        Args:
            api_key: OpenAI API key (if None, will try to get from environment)
            model: Model to use for verification
        """
        if OpenAI is None:
            raise ImportError(
                "openai package is required for component-level verification. "
                "Install with: pip install openai"
            )
        
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
        self.model = model
    
    def verify(
        self,
        decomposition: ProblemDecomposition,
        solution: str,
        problem_entry: Dict[str, Any],
        dataset: Any,
        extract_intermediate_steps: bool = True
    ) -> Dict[str, Any]:
        """Verify solution at component level with intermediate step extraction.
        
        Args:
            decomposition: The problem decomposition
            solution: The LLM's solution
            problem_entry: The original problem entry
            dataset: The reasoning-gym dataset instance
            extract_intermediate_steps: Whether to extract intermediate steps (expensive)
            
        Returns:
            Dictionary with verification results:
            - final_score: float (from reasoning-gym)
            - component_scores: Dict[component_id] -> float
            - intermediate_steps: List of extracted steps
            - verification_method: str
        """
        import json
        
        # First, get final answer score (fast)
        final_score = dataset.score_answer(answer=solution, entry=problem_entry)
        
        if not extract_intermediate_steps:
            # Return just final score if not extracting steps
            return {
                'final_score': final_score,
                'is_correct': final_score >= 0.99,
                'verification_method': 'component_level_no_extraction',
                'component_scores': None,
                'intermediate_steps': None,
            }
        
        # Extract intermediate steps (expensive LLM call)
        try:
            intermediate_steps = self._extract_intermediate_steps(
                problem_entry.get('question', ''),
                solution
            )
        except Exception as e:
            # If extraction fails, fall back to final answer only
            return {
                'final_score': final_score,
                'is_correct': final_score >= 0.99,
                'verification_method': 'component_level_extraction_failed',
                'component_scores': None,
                'intermediate_steps': None,
                'extraction_error': str(e),
            }
        
        # Map steps to components and verify each
        component_scores = self._verify_components(
            decomposition, intermediate_steps, problem_entry
        )
        
        return {
            'final_score': final_score,
            'is_correct': final_score >= 0.99,
            'verification_method': 'component_level',
            'component_scores': component_scores,
            'intermediate_steps': intermediate_steps,
        }
    
    def _extract_intermediate_steps(self, problem_statement: str, solution: str) -> List[Dict[str, Any]]:
        """Extract intermediate steps from solution using LLM.
        
        Args:
            problem_statement: The original problem statement
            solution: The LLM's solution
            
        Returns:
            List of step dictionaries
        """
        import json
        import re
        
        prompt = self.INTERMEDIATE_EXTRACTION_PROMPT.format(
            problem_statement=problem_statement,
            solution=solution
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a solution analyzer. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            return result.get('steps', [])
            
        except json.JSONDecodeError:
            # Try to extract JSON from response if wrapped
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    return result.get('steps', [])
                except:
                    pass
            
            return []
        except Exception as e:
            raise RuntimeError(f"Error extracting intermediate steps: {e}")
    
    def _verify_components(
        self,
        decomposition: ProblemDecomposition,
        intermediate_steps: List[Dict[str, Any]],
        problem_entry: Dict[str, Any]
    ) -> Dict[str, float]:
        """Verify each component against intermediate steps.
        
        Args:
            decomposition: The problem decomposition
            intermediate_steps: Extracted intermediate steps
            problem_entry: The problem entry
            
        Returns:
            Dictionary mapping component_id -> score (0.0-1.0)
        """
        component_scores = {}
        
        # Map steps to components by matching goals
        for component_id, component in decomposition.sub_components.items():
            # Find matching steps
            matching_steps = self._find_matching_steps(component, intermediate_steps)
            
            if not matching_steps:
                # No matching step found - component not addressed
                component_scores[component_id] = 0.0
                continue
            
            # Verify the step(s) for this component
            # For now, use simple heuristics (can be enhanced with LLM verification)
            score = self._verify_component_step(component, matching_steps, problem_entry)
            component_scores[component_id] = score
        
        return component_scores
    
    def _find_matching_steps(
        self,
        component: SubComponent,
        intermediate_steps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find intermediate steps that match a component.
        
        Args:
            component: The component to match
            intermediate_steps: List of intermediate steps
            
        Returns:
            List of matching steps
        """
        matching = []
        goal_keywords = set(component.goal.lower().split())
        
        for step in intermediate_steps:
            step_goal = step.get('component_goal', '').lower()
            step_keywords = set(step_goal.split())
            
            # Check if component entities are mentioned
            entity_match = any(
                entity.lower() in step.get('calculation', '').lower() or
                entity.lower() in str(step.get('result', '')).lower()
                for entity in component.entities
            )
            
            # Check if goals overlap
            goal_overlap = len(goal_keywords & step_keywords) > 0
            
            if entity_match or goal_overlap:
                matching.append(step)
        
        return matching
    
    def _verify_component_step(
        self,
        component: SubComponent,
        matching_steps: List[Dict[str, Any]],
        problem_entry: Dict[str, Any]
    ) -> float:
        """Verify if a component step is correct.
        
        Args:
            component: The component
            matching_steps: Steps that match this component
            problem_entry: The problem entry
            
        Returns:
            Score between 0.0 and 1.0
        """
        if not matching_steps:
            return 0.0
        
        # Simple heuristic verification
        # Can be enhanced with LLM-based verification for more accuracy
        
        # Check if result makes sense
        for step in matching_steps:
            result = step.get('result', '')
            calculation = step.get('calculation', '')
            
            # For arithmetic tasks, check if result is numeric
            if component.goal.lower() in ['count', 'calculate', 'sum', 'total']:
                try:
                    float(result)
                    return 1.0  # If numeric result exists, assume correct
                except:
                    pass
            
            # If calculation exists and mentions entities, give partial credit
            if calculation and any(entity.lower() in calculation.lower() for entity in component.entities):
                return 0.5
        
        return 0.0
    
    def verify_with_llm_check(
        self,
        decomposition: ProblemDecomposition,
        solution: str,
        problem_entry: Dict[str, Any],
        dataset: Any,
        component_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Verify a specific component using LLM (most expensive option).
        
        Use this sparingly for detailed analysis of specific components.
        
        Args:
            decomposition: The problem decomposition
            solution: The LLM's solution
            problem_entry: The problem entry
            dataset: The dataset instance
            component_id: Optional specific component to verify (if None, verifies all)
            
        Returns:
            Verification results with LLM-checked component scores
        """
        # First extract intermediate steps
        intermediate_steps = self._extract_intermediate_steps(
            problem_entry.get('question', ''),
            solution
        )
        
        # Then verify components with LLM
        component_scores = {}
        components_to_verify = (
            [decomposition.get_component(component_id)] if component_id
            else list(decomposition.sub_components.values())
        )
        
        for component in components_to_verify:
            matching_steps = self._find_matching_steps(component, intermediate_steps)
            if matching_steps:
                # Use LLM to verify this component
                score = self._verify_component_with_llm(component, matching_steps[0])
                component_scores[component.component_id] = score
            else:
                component_scores[component.component_id] = 0.0
        
        final_score = dataset.score_answer(answer=solution, entry=problem_entry)
        
        return {
            'final_score': final_score,
            'is_correct': final_score >= 0.99,
            'verification_method': 'component_level_llm_verified',
            'component_scores': component_scores,
            'intermediate_steps': intermediate_steps,
        }
    
    def _verify_component_with_llm(
        self,
        component: SubComponent,
        step: Dict[str, Any]
    ) -> float:
        """Verify a component using LLM (expensive).
        
        Args:
            component: The component to verify
            step: The intermediate step
            
        Returns:
            Score between 0.0 and 1.0
        """
        import json
        import re
        
        prompt = self.COMPONENT_VERIFICATION_PROMPT.format(
            goal=component.goal,
            entities=', '.join(component.entities),
            dependencies=', '.join(component.dependencies),
            step_description=f"{step.get('calculation', '')} -> {step.get('result', '')}"
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a solution verifier. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            if result.get('is_correct', False):
                return result.get('confidence', 1.0)
            else:
                return result.get('confidence', 0.0) * 0.5  # Partial credit even if wrong
            
        except Exception as e:
            # Fall back to heuristic if LLM verification fails
            return 0.5


# Convenience class that combines both methods
class HybridSolutionVerifier:
    """Combines fast Option B with optional expensive Option A."""
    
    def __init__(self, enable_component_verification: bool = False, **kwargs):
        """Initialize hybrid verifier.
        
        Args:
            enable_component_verification: Whether to enable expensive component-level verification
            **kwargs: Arguments passed to ComponentLevelVerifier if enabled
        """
        self.final_answer_verifier = FinalAnswerVerifier()
        self.component_verifier = None
        
        if enable_component_verification:
            try:
                self.component_verifier = ComponentLevelVerifier(**kwargs)
            except ImportError:
                print("Warning: Component-level verification not available. Install openai package.")
    
    def verify(
        self,
        decomposition: ProblemDecomposition,
        solution: str,
        problem_entry: Dict[str, Any],
        dataset: Any,
        use_component_verification: bool = False
    ) -> Dict[str, Any]:
        """Verify solution with optional component-level analysis.
        
        Args:
            decomposition: The problem decomposition
            solution: The LLM's solution
            problem_entry: The problem entry
            dataset: The dataset instance
            use_component_verification: Whether to use expensive component verification
            
        Returns:
            Verification results
        """
        # Always do fast final answer verification
        result = self.final_answer_verifier.verify(
            decomposition, solution, problem_entry, dataset
        )
        
        # Optionally add component-level verification
        if use_component_verification and self.component_verifier:
            component_result = self.component_verifier.verify(
                decomposition, solution, problem_entry, dataset,
                extract_intermediate_steps=True
            )
            # Merge results
            result.update({
                'component_scores': component_result.get('component_scores'),
                'intermediate_steps': component_result.get('intermediate_steps'),
                'verification_method': 'hybrid',
            })
        
        return result
