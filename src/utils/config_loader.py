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

def load_corpus_data(corpus_path: str, feature: str) -> Dict[str, Any]:
    """
    Load corpus data for a specific shell feature
    
    Args:
        corpus_path: Path to the corpus directory
        feature: Name of the feature
        
    Returns:
        Dictionary containing corpus data
    """
    feature_file = Path(corpus_path) / f"{feature}.json"
    
    if not feature_file.exists():
        logger.error(f"Corpus file not found for feature {feature}: {feature_file}")
        raise FileNotFoundError(f"Corpus file not found: {feature_file}")
        
    try:
        with open(feature_file, 'r') as f:
            corpus_data = json.load(f)
            
        return corpus_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in corpus file: {str(e)}")
        raise ValueError(f"Invalid JSON in corpus file: {str(e)}")
    except Exception as e:
        logger.error(f"Error loading corpus data: {str(e)}")
        raise