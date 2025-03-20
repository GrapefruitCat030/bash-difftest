#!/usr/bin/env python3
"""
Shell Metamorphic Differential Testing Framework
Main entry point for the framework
"""

import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="tree_sitter")

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any

from src.mutator              import MutatorGenerator
from src.mutator              import MutatorValidator 
from src.mutation_chain       import MutationChain
from src.report               import TestReporter
from src.differential_testing import DifferentialTester
from src.utils                import load_config


def setup_logger():
    """Set up the logger for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("shell_testing.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("shell-metamorphic-testing")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Shell Metamorphic Differential Testing Framework")
    parser.add_argument("--mode", choices=["prepare", "testing"], required=True, help="Mode of operation: prepare mutators or run tests")
    parser.add_argument("--config",     type=str, default="configs/conf.json",help="Path to configuration file")
    parser.add_argument("--features",   type=str, nargs="+",                  help="Specific shell features to process (for prepare mode)")
    return parser.parse_args()


def prepare_mutators(config: Dict[str, Any]):
    """
    Prepare phase: Generate and validate mutators.
    """
    logger = logging.getLogger("prepare-mutators")
    logger.info("Starting mutator preparation phase")
    
    # Initialize components
    generator = MutatorGenerator(config.get("llm"), config.get("prompt_engine"))
    validator = MutatorValidator(config.get("validation"))
    
    # Get features to process
    feature_list = config.get("features")
    logger.info(f"Processing {len(feature_list)} features: {feature_list}")
    
    # Create output directory if it doesn't exist
    output_dir = config.get("results").get("mutators")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Process each feature
    for feature in feature_list:
        logger.info(f"Generating mutator for feature: {feature}")
        
        # Generate and validate mutator in an iterative process
        mutator_code = generator.generate_mutator(feature)
        valid, feedback = validator.validate(mutator_code, feature)
        
        attempts = 1
        max_attempts = config.get("validation").get("max_validation_attempts", 5)
        
        while not valid and attempts < max_attempts:
            logger.info(f"Mutator validation failed. Attempt {attempts}/{max_attempts}. Regenerating...")
            logger.debug(f"Validation feedback: {feedback}")
            
            # Regenerate with feedback
            mutator_code = generator.refine_mutator(feature, feedback, mutator_code)
            valid, feedback = validator.validate(mutator_code, feature)
            attempts += 1
            
        if valid:
            logger.info(f"Successfully validated mutator for {feature} (attempts: {attempts}), saving to {output_dir}")
        else:
            logger.error(f"Failed to validate mutator for {feature} after {max_attempts} attempts, requires manual correction! Feedback: {feedback}")
        # Save validated mutator
        generator.save_mutator(mutator_code, feature, output_dir)
        # Clear LLM history for next iteration
        generator.clear_history()

    logger.info("Mutator preparation phase completed")


def run_difftest(config):
    """
    Testing phase: Run differential tests using the prepared mutators
    """
   # ANSI escape sequences for colors
    GREEN = "\033[92m"
    RED = "\033[91m"
    RESET = "\033[0m"

    logger = logging.getLogger("differential-testing")
    logger.info("Starting differential testing phase")
    
    # Initialize components
    mutation_chain = MutationChain(config)
    diffTester = DifferentialTester(
        bash_path=config.get("bash_path"),
        posix_path=config("posix_path"),
        timeout=config.get("timeout", 10)
    )
    report_dir = config.get("results")("reports")
    reporter = TestReporter(report_dir)

    # Get all test seed files
    seed_dir = config.get("seeds")
    seed_files = list(Path(seed_dir).glob("*.sh"))
    logger.info(f"Found {len(seed_files)} test seed files")
    
    results = []
    
    # Process each test seed
    for seed_file in seed_files:
        logger.info(f"Processing test seed: {seed_file}")
        
        # Apply mutation chain to generate equivalent POSIX shell code
        try:
            posix_code = mutation_chain.convert(seed_file)
            posix_code_dir = config.get("results")("posix_code")
            posix_file = Path(posix_code_dir) / f"{seed_file.stem}2posix.sh"
            posix_file.write_text(posix_code)
            
            # Run differential test
            test_result = diffTester.test(str(seed_file), str(posix_file))
            results.append({
                "seed": str(seed_file),
                "posix": str(posix_file),
                "result": test_result
            })
            result_status = (GREEN + "PASS" + RESET) if test_result["equivalent"] else (RED + "FAIL" + RESET)
            logger.info(f"Test result for {seed_file.name}: {result_status}")
        
        except Exception as e:
            logger.error(f"Error processing {seed_file}: {str(e)}")
            results.append({
                "seed": str(seed_file),
                "error": str(e)
            })

    # Generate and save test reports with all reporting logic encapsulated in the reporter
    _, summary = reporter.generate_and_save(
        results=results,
        config=config,
        seed_files=seed_files
    )

    logger.info(f"Testing completed. Results saved to {report_dir}")
    
    # Return summary for command line output
    return summary


if __name__ == "__main__":
    logger = setup_logger()
    logger.info("Starting Shell Metamorphic Differential Testing Framework")
    
    args = parse_args()
    config = load_config(args.config)

    switcher = {
        "prepare": prepare_mutators,
        "testing": run_difftest
    }
    boot_func = switcher.get(args.mode)
    if boot_func is None:
        logger.error(f"Invalid mode: {args.mode}")
        sys.exit(1)
    boot_func(config)

    logger.info("Framework execution completed")