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
                - test_examples_dir: Directory containing test examples
                - bash_path: Path to bash executable
                - posix_path: Path to POSIX shell executable
        """
        self.test_examples_dir = Path(config["test_examples_dir"])
        self.bash_path = config.get("bash_path", "/bin/bash")
        self.posix_path = config.get("posix_path", "/bin/sh")
        self.timeout = config.get("timeout", 5)
        
    def validate(self, mutator_code: str, feature: str, corpus_data: Dict) -> Tuple[bool, str]:
        """
        Validate a generated mutator
        
        Args:
            mutator_code: The Python code for the mutator
            feature: The shell feature being tested
            corpus_data: Corpus data for the feature
            
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
            mutator, feature, corpus_data
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
        required_attributes = ["transform_code", "get_feature_name", "get_description"]
        missing_attributes = [attr for attr in required_attributes if not hasattr(module, attr)]
        
        if missing_attributes:
            return False, f"Missing required attributes: {', '.join(missing_attributes)}"
            
        # Check that transform_code is callable and has the right signature
        transform_func = getattr(module, "transform_code")
        if not callable(transform_func):
            return False, "transform_code is not callable"
            
        return True, "Interface is valid"
        
    def _validate_with_examples(self, module: Any, feature: str, corpus_data: Dict) -> Tuple[bool, str]:
        """Validate the mutator using examples from the corpus"""
        examples = corpus_data.get("examples", [])
        if not examples:
            logger.warning(f"No examples found for feature: {feature}")
            return True, "No examples to validate against"
            
        passed_examples = 0
        failures = []
        
        for i, example in enumerate(examples):
            bash_code = example.get("bash")
            expected_posix = example.get("posix")
            
            if not bash_code or not expected_posix:
                logger.warning(f"Example {i} is missing bash or posix code")
                continue
                
            # Transform bash code to posix using the mutator
            try:
                actual_posix = module.transform_code(bash_code)
                
                # Check for syntactic correctness of the output
                posix_valid, posix_feedback = self._check_shell_syntax(actual_posix, self.posix_path)
                if not posix_valid:
                    failures.append(f"Example {i}: Generated POSIX code has syntax error: {posix_feedback}")
                    continue
                    
                # Check for behavioral equivalence
                equivalent, equivalence_feedback = self._check_behavioral_equivalence(
                    bash_code, actual_posix
                )
                if not equivalent:
                    failures.append(f"Example {i}: Behavioral equivalence check failed: {equivalence_feedback}")
                    continue
                    
                passed_examples += 1
                
            except Exception as e:
                failures.append(f"Example {i}: Error during transformation: {str(e)}")
                
        # Validation passes if at least 75% of examples pass
        if examples and passed_examples / len(examples) >= 0.75:
            return True, f"Passed {passed_examples}/{len(examples)} examples"
        else:
            failure_details = "\n".join(failures[:5])  # Limit to first 5 failures
            if len(failures) > 5:
                failure_details += f"\n... and {len(failures) - 5} more failures"
            return False, f"Failed examples: {passed_examples}/{len(examples)}\n{failure_details}"
            
    def _check_shell_syntax(self, code: str, shell_path: str) -> Tuple[bool, str]:
        """Check if shell code has valid syntax"""
        with tempfile.NamedTemporaryFile(suffix=".sh", delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(code.encode('utf-8'))
            
        try:
            result = execute_shell_command(
                [shell_path, "-n", temp_path],
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
            
    def _check_behavioral_equivalence(
        self, bash_code: str, posix_code: str
    ) -> Tuple[bool, str]:
        """
        Check if bash code and posix code are behaviorally equivalent
        
        This runs both scripts with the same inputs and compares outputs
        """
        # Create temporary files for both scripts
        with tempfile.NamedTemporaryFile(suffix=".sh", delete=False) as bash_file:
            bash_path = bash_file.name
            bash_file.write(bash_code.encode('utf-8'))
            
        with tempfile.NamedTemporaryFile(suffix=".sh", delete=False) as posix_file:
            posix_path = posix_file.name
            posix_file.write(posix_code.encode('utf-8'))
            
        try:
            # Make both files executable
            Path(bash_path).chmod(0o755)
            Path(posix_path).chmod(0o755)
            
            # Execute bash script
            bash_result = execute_shell_command(
                [self.bash_path, bash_path],
                timeout=self.timeout
            )
            
            # Execute posix script
            posix_result = execute_shell_command(
                [self.posix_path, posix_path],
                timeout=self.timeout
            )
            
            # Clean up
            Path(bash_path).unlink()
            Path(posix_path).unlink()
            
            # Compare return codes
            if bash_result["returncode"] != posix_result["returncode"]:
                return False, (f"Return codes differ: bash={bash_result['returncode']}, "
                              f"posix={posix_result['returncode']}")
                
            # Compare outputs (stdout)
            if bash_result["stdout"].strip() != posix_result["stdout"].strip():
                return False, "Outputs differ"
                
            return True, "Behaviorally equivalent"
            
        except Exception as e:
            # Clean up
            if Path(bash_path).exists():
                Path(bash_path).unlink()
            if Path(posix_path).exists():
                Path(posix_path).unlink()
                
            return False, f"Error during equivalence check: {str(e)}"