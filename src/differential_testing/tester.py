"""
Differential Testing module for comparing bash and POSIX shell script behavior
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.utils import execute_shell_command

logger = logging.getLogger(__name__)

class DifferentialTester:
    """
    Performs differential testing between bash and POSIX shell scripts
    """
    
    def __init__(self, bash_path: str = "/bin/bash", posix_path: str = "/bin/sh", timeout: int = 10):
        """
        Initialize the differential tester
        
        Args:
            bash_path: Path to bash executable
            posix_path: Path to POSIX shell executable
            timeout: Timeout for script execution in seconds
        """
        self.bash_path = bash_path
        self.posix_path = posix_path
        self.timeout = timeout
        
    def test(self, bash_file: str, posix_file: str, test_inputs: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Test a bash script against its POSIX equivalent
        
        Args:
            bash_file: Path to the bash script
            posix_file: Path to the POSIX shell script
            test_inputs: List of input strings to provide to the scripts
            
        Returns:
            Dictionary containing test results
        """
        logger.info(f"Testing {bash_file} against {posix_file}")
        
        bash_script = Path(bash_file)  # e.g., "test.sh"
        posix_script = Path(posix_file)
        
        if not bash_script.exists():
            raise FileNotFoundError(f"Bash file not found: {bash_file}")
        if not posix_script.exists():
            raise FileNotFoundError(f"POSIX file not found: {posix_file}")
            
        # Make sure scripts are executable
        bash_script.chmod(0o755)
        posix_script.chmod(0o755)
        
        # If no test inputs provided, run with empty input
        if test_inputs is None:
            test_inputs = [""]
            
        results = []
        
        # Run tests with each input
        for i, input_data in enumerate(test_inputs):
            input_desc = f"input {i+1}" if input_data else "no input"
            logger.debug(f"Running test with {input_desc}")
            
            # Execute bash script
            bash_result = execute_shell_command(
                [self.bash_path, str(bash_script)],
                input_text=input_data,
                timeout=self.timeout
            )
            
            # Execute posix script
            posix_result = execute_shell_command(
                [self.posix_path, str(posix_script)],
                input_text=input_data,
                timeout=self.timeout
            )
            
            # Check equivalence
            stdout_match = bash_result["stdout"].strip() == posix_result["stdout"].strip()
            stderr_match = bash_result["stderr"].strip() == posix_result["stderr"].strip()
            exit_code_match = bash_result["returncode"] == posix_result["returncode"]
            
            result = {
                "input": input_data,
                "bash_stdout": bash_result["stdout"],
                "posix_stdout": posix_result["stdout"],
                "bash_stderr": bash_result["stderr"],
                "posix_stderr": posix_result["stderr"],
                "bash_exit_code": bash_result["returncode"],
                "posix_exit_code": posix_result["returncode"],
                "stdout_match": stdout_match,
                "stderr_match": stderr_match,
                "exit_code_match": exit_code_match,
                "equivalent": stdout_match and exit_code_match  # stderr is less important
            }
            
            results.append(result)
            
        # Determine overall equivalence
        all_equivalent = all(r["equivalent"] for r in results)
        
        return {
            "bash_file": str(bash_script),
            "posix_file": str(posix_script),
            "test_count": len(results),
            "equivalent": all_equivalent,
            "details": results
        }
        
    def batch_test(self, test_cases: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Run multiple differential tests
        
        Args:
            test_cases: List of test cases, each with 'bash_file' and 'posix_file' keys
            
        Returns:
            List of test results
        """
        results = []
        
        for case in test_cases:
            try:
                result = self.test(case["bash_file"], case["posix_file"])
                results.append(result)
            except Exception as e:
                logger.error(f"Error testing {case['bash_file']}: {str(e)}")
                results.append({
                    "bash_file": case["bash_file"],
                    "posix_file": case["posix_file"],
                    "error": str(e),
                    "equivalent": False
                })
                
        return results