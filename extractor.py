"""LLM-based problem statement extractor"""

import json
import re
from typing import Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

import logging

logger = logging.getLogger(__name__)


class ProblemExtractor:
    """Extracts sub-components from problem statements using LLM-based parsing."""
    
    EXTRACTION_PROMPT = """You are a problem decomposition expert. Given a problem statement, extract the main goal and identify all 1-level deep sub-components.

Each sub-component should have:
- A goal (what needs to be achieved)
- Entities (objects/resources involved)
- Dependencies (other sub-components this depends on, if any)

Return your analysis as a JSON object with this structure:
{{
    "main_goal": "the overall goal of the problem",
    "sub_components": [
        {{
            "goal": "specific goal for this sub-component",
            "entities": ["entity1", "entity2"],
            "dependencies": []  // list of goals this depends on (empty if none)
        }}
    ]
}}

Guidelines:
- Extract only 1-level deep goals (immediate sub-goals, not nested deeper)
- Each sub-component should represent a distinct, actionable goal
- Dependencies should reference other sub-component goals by their goal text
- Be thorough but concise

Problem statement:
{problem_statement}

Return only valid JSON, no additional text."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """Initialize the extractor.
        
        Args:
            api_key: OpenAI API key (if None, will try to get from environment)
            model: Model to use for extraction
        """
        if OpenAI is None:
            raise ImportError(
                "openai package is required. Install with: pip install openai"
            )
        
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
        self.model = model
    
    def extract(self, problem_statement: str) -> dict:
        """Extract sub-components from a problem statement.
        
        Args:
            problem_statement: The problem statement to analyze
            
        Returns:
            Dictionary with 'main_goal' and 'sub_components' list
        """
        prompt = self.EXTRACTION_PROMPT.format(problem_statement=problem_statement)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a problem decomposition expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            logger.info(f"Extracted result: {result}")
            return result
            
        except json.JSONDecodeError as e:
            # Try to extract JSON from response if it's wrapped in markdown
            try:
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return result
            except:
                pass
            
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")
        except Exception as e:
            raise RuntimeError(f"Error during LLM extraction: {e}")
    
    def extract_to_decomposition(self, problem_statement: str):
        """Extract and convert to ProblemDecomposition object.
        
        Args:
            problem_statement: The problem statement to analyze
            
        Returns:
            ProblemDecomposition object with all sub-components
        """
        from .decomposition import ProblemDecomposition, SubComponent
        
        extracted = self.extract(problem_statement)
        
        decomposition = ProblemDecomposition(
            problem_statement=problem_statement,
            main_goal=extracted.get("main_goal", "")
        )
        
        # Create a mapping from goal text to component ID for dependency resolution
        goal_to_id = {}
        
        # First pass: create all components
        for idx, comp_data in enumerate(extracted.get("sub_components", [])):
            comp_id = f"comp_{idx}"
            component = SubComponent(
                component_id=comp_id,
                goal=comp_data.get("goal", ""),
                entities=comp_data.get("entities", []),
                dependencies=[]  # Will resolve in second pass
            )
            decomposition.add_component(component)
            goal_to_id[comp_data.get("goal", "")] = comp_id
        
        # Second pass: resolve dependencies
        for idx, comp_data in enumerate(extracted.get("sub_components", [])):
            comp_id = f"comp_{idx}"
            component = decomposition.get_component(comp_id)
            
            # Resolve dependency goals to component IDs
            dep_goals = comp_data.get("dependencies", [])
            for dep_goal in dep_goals:
                if dep_goal in goal_to_id:
                    component.dependencies.append(goal_to_id[dep_goal])
        
        return decomposition
