"""
Mutator Generator module for generating code mutators using LLM
"""

import logging
from typing import Dict, Any, Optional

from src.llm.api_client import LLMClient

logger = logging.getLogger(__name__)

class MutatorGenerator:
    """Generates code mutators using LLM"""
    
    def __init__(self, llm_client: LLMClient, prompt_engine_config: Dict[str, Any]):
        """
        Initialize the mutator generator
        
        Args:
            llm_client: LLM client for API calls
            prompt_engine_config: Configuration for the prompt engine
        """
        self.llm_client = llm_client
        self.prompt_engine_config = prompt_engine_config
        # Dynamically import the prompt engine from your existing code
        self.prompt_engine = self._load_prompt_engine()
        
    def generate_mutator(self, feature: str, corpus_data: Dict) -> str:
        """
        Generate a mutator for a specific shell feature
        
        Args:
            feature: The shell feature name
            corpus_data: Corpus data for the feature
            
        Returns:
            Generated mutator code as a string
        """
        logger.info(f"Generating mutator for feature: {feature}")
        
        # Generate prompt using your existing prompt engine
        prompt = self.prompt_engine.generate_prompt(
            feature=feature, 
            corpus_data=corpus_data
        )
        
        # Set up context for the LLM
        context = {
            "system_message": "You are an expert shell script converter. "
                             "Your task is to write a Python function that transforms Bash code to "
                             "POSIX-compliant shell code while preserving functionality."
        }
        
        # Generate the mutator code
        mutator_code = self.llm_client.generate_code(prompt, context)
        
        return self._format_mutator_code(mutator_code, feature, corpus_data)
        
    def refine_mutator(self, feature: str, corpus_data: Dict, feedback: str, previous_code: str) -> str:
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
            corpus_data=corpus_data,
            feedback=feedback,
            previous_code=previous_code
        )
        
        # Generate refined code
        refined_code = self.llm_client.refine_code(
            prompt=refinement_prompt,
            code=previous_code,
            feedback=feedback
        )
        
        return self._format_mutator_code(refined_code, feature, corpus_data)
        
    def _load_prompt_engine(self):
        """
        Load the prompt engine from your existing code
        
        This is a placeholder - you'll need to import your actual prompt engine
        """
        # Import your existing prompt engine here
        from src.prompt.engine import PromptEngine
        
        return PromptEngine(self.prompt_engine_config)
        
    def _format_mutator_code(self, code: str, feature: str, corpus_data: Dict) -> str:
        """Format the generated code into a complete mutator module"""
        # Extract the transform_code function if it exists
        if "def transform_code" in code:
            # The code might already be properly formatted
            if "def get_feature_name" in code and "def get_description" in code:
                return code
                
            # Otherwise, add the missing functions
            feature_desc = corpus_data.get("description", f"Converts {feature} from bash to POSIX")
            
            # Add required functions if they don't exist
            additional_code = ""
            
            if "def get_feature_name" not in code:
                additional_code += f"""
def get_feature_name():
    \"\"\"Return the name of the shell feature this mutator handles\"\"\"
    return "{feature}"
"""
            
            if "def get_description" not in code:
                additional_code += f"""
def get_description():
    \"\"\"Return a description of what this mutator does\"\"\"
    return \"\"\"{feature_desc}\"\"\"
"""
            
            return code + additional_code
        else:
            # The code doesn't contain a transform_code function
            # This is unexpected, but we'll try to wrap it in a proper function
            logger.warning(f"Generated code for {feature} is missing transform_code function")
            
            feature_desc = corpus_data.get("description", f"Converts {feature} from bash to POSIX")
            
            return f"""
def transform_code(bash_code):
    \"\"\"
    Transform bash code to POSIX shell code
    
    Args:
        bash_code: String containing bash code
        
    Returns:
        String containing equivalent POSIX shell code
    \"\"\"
    # Generated transformation logic
{code.replace('^', '    ')}
    
    return bash_code  # Default to returning input if transformation didn't happen

def get_feature_name():
    \"\"\"Return the name of the shell feature this mutator handles\"\"\"
    return "{feature}"

def get_description():
    \"\"\"Return a description of what this mutator does\"\"\"
    return \"\"\"{feature_desc}\"\"\"
"""