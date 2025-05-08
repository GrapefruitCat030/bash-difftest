"""
Mutator Generator module for generating code mutators using LLM
"""

import logging
from typing import Dict, Any
from pathlib import Path

from src.llm import LLMClient
from src.prompt import PromptEngine

logger = logging.getLogger(__name__)

class MutatorGenerator:
    """Generates code mutators using LLM"""
    
    def __init__(self, llm_client_config: Dict[str, Any], prompt_engine_config: Dict[str, Any]):
        """
        Initialize the mutator generator
        
        Args:
            llm_client: LLM client for API calls
            prompt_engine_config: Configuration for the prompt engine
        """
        self.llm_client = LLMClient(llm_client_config)
        self.prompt_engine = PromptEngine(prompt_engine_config)
        
    def generate_mutator(self, feature: str) -> str:
        """
        Generate a mutator for a specific shell feature
        
        Args:
            feature: The shell feature name
        Returns:
            Generated mutator code as a string
        """
        logger.info(f"Generating mutator for feature: {feature}")
        # Generate prompt using your existing prompt engine
        prompt = self.prompt_engine.generate_mutator_prompt(feature=feature)
        # Generate the mutator code
        mutator_code = self.llm_client.generate_response(prompt)
        
        return mutator_code
        
    def refine_mutator(self, feature: str, feedback: str, previous_code: str) -> str:
        """
        Refine a mutator based on validation feedback
        
        Args:
            feature: The shell feature name
            corpus_data: Corpus data for the feature
            feedback: Validation feedback
            previous_code: Previously generated code
            
        Returns:
            Refined mutator code as a string
        """
        logger.info(f"Refining mutator for feature: {feature}")
        
        # Generate refinement prompt
        refinement_prompt = self.prompt_engine.generate_refinement_prompt(
            feature=feature,
            feedback=feedback,
            previous_code=previous_code
        )
        
        # Generate refined code
        refined_code = self.llm_client.generate_response(refinement_prompt)
        
        return refined_code

    def save_mutator(mutator_code, feature, output_dir):
        """Save a validated mutator to file"""
        output_file = Path(output_dir) / f"{feature}_mutator.py"
        output_file.write_text(mutator_code)

    def clear_history(self):
        self.llm_client.clear_history()
