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
import pkgutil
import importlib
import inspect
import traceback
import signal
from pathlib import Path
from typing import Dict, Any

from src.mutator              import MutatorGenerator
from src.mutator              import MutatorValidator 
from src.mutation_chain       import MutatorChain
from src.report               import TestReporter
from src.differential_testing import DifferentialTester
import src.utils as utils


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


def register_all_mutators(chain: MutatorChain) -> MutatorChain:
    from src.mutation_chain import mutators
    from src.mutation_chain import BaseMutator

    for _, module_name, _ in pkgutil.iter_modules(mutators.__path__, mutators.__name__ + "."):
        module = importlib.import_module(module_name)
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # 判断是否是BaseMutator的子类
            if issubclass(obj, BaseMutator) and obj != BaseMutator:
                chain.register(obj())
    return chain


class GracefulExit(Exception):
    pass

# TODO: add a detect thread to control the memory and disk usage, interrupt the process if it exceeds the limit
def graceful_exit_handler(signum, frame):
    raise GracefulExit()


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
    
    # init mutator chain
    mutation_chain = MutatorChain()
    register_all_mutators(mutation_chain)
    mutation_chain.set_debug()

    # init differential tester and test reporter
    diffTester = DifferentialTester(
        bash_binpath=config.get("bash_binpath"),
        posix_binpath=config.get("posix_binpath"),
        timeout=config.get("timeout", 10)
    )
    report_dir = config.get("results").get("reports")
    reporter = TestReporter(report_dir)

    
    # infinite loop for testing
    round_num = 0 
    signal.signal(signal.SIGINT, graceful_exit_handler) 

    try:
        round_results = []
        while True:
            round_num += 1
            logger.info(f"Staring Round [{round_num}] .")

            # generate test seeds
            base_seed_dir = config.get("seeds")
            round_seed_dir = Path(base_seed_dir) / f"round_{round_num}"
            round_seed_dir.mkdir(parents=True, exist_ok=True)

            utils.generate_seed_scripts(round_seed_dir, 10, 100)

            # get all test seed files
            seed_files = list(Path(round_seed_dir).glob("*.sh"))
            
            # process each test seed file
            for seed_file in seed_files:
                
                # apply mutation chain to generate equivalent POSIX shell code
                try:
                    bash_code = seed_file.read_text()
                    posix_code = mutation_chain.transform(bash_code)
                    posix_code_dir = Path(config.get("results").get("posix_code")) / f"round_{round_num}"
                    posix_code_dir.mkdir(parents=True, exist_ok=True)
                    posix_file = posix_code_dir / f"{seed_file.stem}_posix.sh"
                    posix_file.write_text(posix_code)
                    
                    # Run differential test
                    test_result = diffTester.test(seed_file, posix_file)
                    round_results.append(test_result)
                
                except Exception as e:
                    err_stack = traceback.format_exc()
                    logger.error(f"Error processing {seed_file}: {str(e)}\n{err_stack}")
                    # TODO: hold the errors
                    round_results.append({
                        "seed_name": str(seed_file),
                        "error": str(e)
                    })

            # generate and save test reports in this round
            round_summary = reporter.generate_round_report(round_num, round_results)
            logger.info(f"End Round [{round_num}]. Round summary: Tests: {round_summary['total_tests']}, " 
                        f"Passed: {round_summary['passed']}, Failed: {round_summary['failed']}, ")
            logger.info(f"Report saved to {report_dir}/round_{round_num}")
            
            # clear round results
            round_results.clear()

    except GracefulExit:
        logger.info("Graceful exit triggered. generate summary report and exit.")
        if round_num <= 0:
            logger.info("No rounds completed. Exiting.")
            return
        # process the last round
        if round_results:
            round_summary = reporter.generate_round_report(round_num, round_results)
            logger.info(f"End Round [{round_num}]. Round summary: Tests: {round_summary['total_tests']}, " 
                        f"Passed: {round_summary['passed']}, Failed: {round_summary['failed']}, ")
            logger.info(f"Report saved to {report_dir}/round_{round_num}") 
            round_results.clear()
        # summarize all rounds 
        saved_files, summary = reporter.generate_summary_report(config)
        logger.info(f"Testing complete. Summary:")
        logger.info(f"Saved files: {saved_files}")
        logger.info(f"Total rounds: {summary['total_rounds']}")
        logger.info(f"Total tests:  {summary['total_tests']}")
        logger.info(f"Total passed: {summary['total_passed']}")
        logger.info(f"Total failed: {summary['total_failed']}")
        logger.info(f"Total errors: {summary['total_errors']}")
        logger.info(f"Success rate: {summary['success_rate']:.2f}%")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        traceback.print_exc()
    finally:
        # do nothing
        pass


if __name__ == "__main__":
    logger = setup_logger()
    logger.info("Starting Shell Metamorphic Differential Testing Framework")
    
    args = parse_args()
    config = utils.load_config(args.config)

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