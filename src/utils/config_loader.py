"""
Configuration loading utilities
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a JSON file
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing configuration
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        logger.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        # Load environment variables for sensitive values like API keys
        if "llm" in config:
            if "api_key" not in config["llm"] or not config["llm"]["api_key"]:
                provider = config["llm"].get("provider", "").upper()
                env_var = f"{provider}_API_KEY"
                if env_var in os.environ:
                    config["llm"]["api_key"] = os.environ[env_var]
                    logger.info(f"Loaded API key from environment variable {env_var}")
                    
        return config
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {str(e)}")
        raise ValueError(f"Invalid JSON in configuration file: {str(e)}")
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        raise


from pathlib import Path
import json

class Config:
    def __init__(self, config_file: str):
        self.config_file = Path(config_file)
        self.config_data = self.load_config()

    def load_config(self) -> dict:
        if not self.config_file.exists():
            raise FileNotFoundError(f"Configuration file {self.config_file} does not exist.")
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_llm_config(self) -> dict:
        return self.config_data.get("llm", {})

    def get_feature_list(self) -> list:
        return self.config_data.get("features", [])

    def get_results_paths(self) -> dict:
        return self.config_data.get("results", {})

    def get_timeout(self) -> int:
        return self.config_data.get("timeout", 5)

    def get_validation_config(self) -> dict:
        return self.config_data.get("validation", {})

    def get_bash_path(self) -> str:
        return self.config_data.get("bash_path", "/bin/bash")

    def get_posix_path(self) -> str:
        return self.config_data.get("posix_path", "/bin/sh")