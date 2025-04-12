"""
Differential Testing module for comparing bash and POSIX shell script behavior
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import src.utils as utils

logger = logging.getLogger(__name__)

class DifferentialTester:
    """
    Performs differential testing between bash and POSIX shell scripts
    """
    
    def __init__(self, bash_binpath: str = "/bin/bash", posix_binpath: str = "/bin/sh", timeout: int = 5):
        """
        Initialize the differential tester
        
        Args:
            bash_binpath: Path to bash executable
            posix_binpath: Path to POSIX shell executable
            timeout: Timeout for script execution in seconds
        """
        self.bash_binpath = bash_binpath
        self.posix_binpath = posix_binpath
        self.timeout = timeout
        
    def test(self, bash_script: Path, posix_script: Path, test_inputs: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Test a bash script against its POSIX equivalent
        
        Args:
            bash_file: Path to the bash script
            posix_file: Path to the POSIX shell script
            test_inputs: List of input strings to provide to the scripts
            
        Returns:
            a dictionary with test results:
            - seed_name: Name of the test seed
            - test_count: Number of tests run with different inputs
            - pass_num: Number of tests that passed
            - details: List of dictionaries with detail for each test input
        """
        
        # if no test inputs provided, run with empty input
        if test_inputs is None:
            test_inputs = [""]
            
        details = []
        
        # Run tests with each input
        for i, input_data in enumerate(test_inputs):
            input_desc = f"input {i+1}" if input_data else "no input"
            logger.debug(f"Running test with {input_desc}")
            
            # Execute bash script
            bash_result = utils.execute_shell_command(
                [self.bash_binpath, str(bash_script)],
                input_text=input_data,
                timeout=self.timeout
            )
            
            # Execute posix script
            posix_result = utils.execute_shell_command(
                [self.posix_binpath, str(posix_script)],
                input_text=input_data,
                timeout=self.timeout
            )
            
            # Check equivalence
            stdout_match = bash_result["stdout"].strip() == posix_result["stdout"].strip()
            stderr_match = bash_result["stderr"].strip() == posix_result["stderr"].strip()
            exit_code_match = bash_result["exitcode"] == posix_result["exitcode"]

            status = "SUCCESS"
            if not exit_code_match:
                status = "FAILURE"
            elif not stdout_match and not stderr_match:
                status = "WARNING"

            result = {
                "status": status,
                "input": input_data,
                "bash_stdout": bash_result["stdout"],
                "posix_stdout": posix_result["stdout"],
                "bash_stderr": bash_result["stderr"],
                "posix_stderr": posix_result["stderr"],
                "bash_exit_code": bash_result["exitcode"],
                "posix_exit_code": posix_result["exitcode"],
            }
            
            details.append(result)
            
        return {
            "seed_name":    str(bash_script),
            "test_count":   len(details),
            "pass_num":     sum(1 for d in details if d["status"] == "SUCCESS"),
            "fail_num":     sum(1 for d in details if d["status"] == "FAILURE"),
            "warning_num":  sum(1 for d in details if d["status"] == "WARNING"),
            "details":      details
        }
