"""
Mutator validation module for validating generated mutators
"""

import importlib.util
import logging
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

from src.utils.shell import execute_shell_command

logger = logging.getLogger(__name__)

class MutatorValidator:
    """Validates mutators by testing them against reference examples"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the validator
        
        Args:
            config: Configuration dictionary
                - validate_examples_dir: Directory containing test examples
                - bash_path: Path to bash executable
                - posix_path: Path to POSIX shell executable
        """
        self.validate_examples_dir = Path(config.get("validate_examples_dir"))
        self.bash_path = config.get("bash_path", "/bin/bash")
        self.posix_path = config.get("posix_path", "/bin/sh")
        self.timeout = config.get("timeout", 5)
        
    def validate(self, mutator_code: str, feature: str) -> Tuple[bool, str]:
        """
        Validate a generated mutator
        
        Args:
            mutator_code: The Python code for the mutator
            feature: The shell feature being tested
        Returns:
            Tuple of (is_valid, feedback)
        """
        logger.info(f"Validating mutator for feature: {feature}")
        
        # Basic validation checks
        syntax_valid, syntax_feedback = self._validate_python_syntax(mutator_code)
        if not syntax_valid:
            return False, f"Python syntax validation failed: {syntax_feedback}"
            
        # Load the mutator module
        mutator = self._load_mutator_module(mutator_code)
        if mutator is None:
            return False, "Failed to load mutator module"
        
        # Check if the mutator has the required interface
        interface_valid, interface_feedback = self._validate_interface(mutator)
        if not interface_valid:
            return False, f"Interface validation failed: {interface_feedback}"
        
        # Test the mutator with examples
        examples_valid, examples_feedback = self._validate_with_examples(
            mutator, feature,
        )
        if not examples_valid:
            return False, f"Example validation failed: {examples_feedback}"
            
        return True, "Mutator successfully validated"
        
    def _validate_python_syntax(self, code: str) -> Tuple[bool, str]:
        """Validate Python syntax of the mutator code"""
        try:
            compile(code, "<string>", "exec")
            return True, "Syntax is valid"
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"
            
    def _load_mutator_module(self, code: str) -> Optional[Any]:
        """Load mutator code as a Python module"""
        try:
            # Create a temporary file for the module
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(code.encode('utf-8'))
                
            # Import the module from the temporary file
            module_name = Path(temp_path).stem
            spec = importlib.util.spec_from_file_location(module_name, temp_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Clean up the temporary file
            Path(temp_path).unlink()
            
            return module
            
        except Exception as e:
            logger.error(f"Error loading mutator module: {str(e)}")
            logger.debug(traceback.format_exc())
            return None
            
    def _validate_interface(self, module: Any) -> Tuple[bool, str]:
        """Validate that the mutator module has the required interface"""
        required_attributes = ["transform", "apply_patches"]
        missing_attributes = [attr for attr in required_attributes if not hasattr(module, attr)]
        
        if missing_attributes:
            return False, f"Missing required attributes: {', '.join(missing_attributes)}"
            
        # Check that transform is callable and has the right signature
        transform_func = getattr(module, "transform")
        if not callable(transform_func):
            return False, "transforme is not callable"
            
        return True, "Interface is valid"
        
    def _validate_with_examples(self, module: Any, feature: str) -> Tuple[bool, str]:
        """Validate the mutator using examples from the corpus"""
            
        bash_code_path = self.validate_examples_dir / f"{feature}_bash.sh"
        with open(bash_code_path, "r", encoding="utf-8") as f:
            bash_code = f.read() 
        posix_code_path = self.validate_examples_dir / f"{feature}_posix.sh"
        with open(posix_code_path, "r", encoding="utf-8") as f:
            posix_code = f.read()

        # Transform bash code to posix using the mutator
        try:
            posix_code = module.transform(bash_code)
            # Check for syntactic correctness of the output
            posix_valid, posix_feedback = self._check_shell_syntax(posix_code, self.posix_path)
            if not posix_valid:
                return False, f"Generated POSIX code has syntax error: {posix_feedback}"
            
        except Exception as e:
            return False, f"Error during validation: {str(e)}"
            
    def _check_shell_syntax(self, code: str, shell_path: str) -> Tuple[bool, str]:
        """Check if shell code has valid syntax"""
        with tempfile.NamedTemporaryFile(suffix=".sh", delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(code.encode('utf-8'))
            
        try:
            result = execute_shell_command(
                [shell_path, "-n", temp_path], # -n for syntax check
                timeout=self.timeout
            )
            
            Path(temp_path).unlink()  # Clean up
            
            if result["returncode"] == 0:
                return True, "Syntax is valid"
            else:
                return False, result["stderr"]
                
        except Exception as e:
            Path(temp_path).unlink()  # Clean up
            return False, str(e)
            