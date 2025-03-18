"""
Shell utilities for executing shell commands
"""

import logging
import subprocess
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

def execute_shell_command(
    command: List[str],
    input_text: Optional[str] = None,
    timeout: int = 10,
    env: Optional[Dict[str, str]] = None
) -> Dict:
    """
    Execute a shell command and return the results
    
    Args:
        command: List of command arguments
        input_text: Optional input text to provide to the command
        timeout: Timeout in seconds
        env: Optional environment variables
        
    Returns:
        Dictionary with stdout, stderr, and return code
    """
    logger.debug(f"Executing command: {' '.join(command)}")
    
    input_bytes = None
    if input_text is not None:
        input_bytes = input_text.encode('utf-8')
    
    try:
        process = subprocess.run(
            command,
            input=input_bytes,
            capture_output=True,
            timeout=timeout,
            env=env,
            text=False  # We'll decode manually to handle errors better
        )
        
        # Decode stdout and stderr, replacing invalid characters
        stdout = process.stdout.decode('utf-8', errors='replace')
        stderr = process.stderr.decode('utf-8', errors='replace')
        
        result = {
            "stdout": stdout,
            "stderr": stderr,
            "returncode": process.returncode
        }
        
        logger.debug(f"Command completed with return code {process.returncode}")
        return result
        
    except subprocess.TimeoutExpired:
        logger.warning(f"Command timed out after {timeout} seconds: {' '.join(command)}")
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
            "returncode": -1
        }
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        return {
            "stdout": "",
            "stderr": f"Error: {str(e)}",
            "returncode": -1
        }