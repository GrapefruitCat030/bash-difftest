"""
Test Reporter module for generating and saving test reports
"""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class TestReporter:
    """
    Generates and saves test reports from differential testing results
    """
    
    def __init__(self, output_dir: str = "results/tests"):
        """
        Initialize the test reporter
        
        Args:
            output_dir: Base directory to store generated reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.all_rounds_summary = {
            "rounds": 0,
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
        }

        
    def _get_shell_version(self, shell_path: str) -> str:
        """Get version information of a shell executable"""
        try:
            result = subprocess.run(
                [shell_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Unknown ({shell_path})"
        except Exception as e:
            return f"Error getting version: {str(e)}"
            
    def _count_mutators(self, mutators_dir: str) -> int:
        """Count the number of mutator files"""
        try:
            return len(list(Path(mutators_dir).glob("*.py")) - 1) # Exclude __init__.py
        except Exception:
            return 0
            
    def _get_mutators_applied(self, mutators_dir: str) -> List[str]:
        """Get list of features being tested based on mutator filenames"""
        try:
            return [f.stem for f in Path(mutators_dir).glob("*.py") if f.stem != "__init__"]
        except Exception:
            return []

    def _generate_results_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of test results
        
        Args:
            results: List of test results, each is a dictionary with:
                - seed_name: Name of the test seed
                - test_count: int
                - pass_num: int
                - details: List of dictionaries with detail for each test input
        Returns:
            Summary dictionary
        """
        total = sum(r.get("test_count", 0) for r in results)
        passed = sum(r.get("pass_num", 0) for r in results)
        failed = total - passed

        # Calculate success rate
        success_rate = (passed / total * 100) if total > 0 else 0
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "success_rate": f"{success_rate:.2f}%"
        }

    def _save_json_report(self, report: Dict[str, Any], filename: str) -> str:
        """Save report in JSON format"""
        if not filename.endswith(".json"):
            filename += ".json"
            
        file_path = self.output_dir / filename
        
        with open(file_path, "w") as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"JSON report saved to: {file_path}")
        return str(file_path)
        
    def _save_text_report(self, report: Dict[str, Any], filename: str) -> str:
        """Save report in text format"""
        if not filename.endswith(".txt"):
            filename += ".txt"
            
        file_path = self.output_dir / filename
        
        with open(file_path, "w") as f:
            f.write(f"Shell Metamorphic Differential Testing Report\n")
            f.write(f"Generated: {report['timestamp']}\n")
            f.write(f"\n== Summary ==\n")
            f.write(f"Total tests: {report['summary']['total_tests']}\n")
            f.write(f"Passed: {report['summary']['passed']}\n")
            f.write(f"Failed: {report['summary']['failed']}\n")
            f.write(f"Errors: {report['summary']['errors']}\n")
            f.write(f"Success rate: {report['summary']['success_rate']}\n")
            
            f.write(f"\n== Failure Analysis ==\n")
            for reason, count in report.get("failure_analysis", {}).items():
                f.write(f"{reason}: {count}\n")
                
            if "metadata" in report:
                f.write(f"\n== Metadata ==\n")
                for key, value in report["metadata"].items():
                    if isinstance(value, dict):
                        f.write(f"{key}:\n")
                        for k, v in value.items():
                            f.write(f"  {k}: {v}\n")
                    else:
                        f.write(f"{key}: {value}\n")
                    
            f.write(f"\n== Test Details ==\n")
            for i, result in enumerate(report["details"]):
                f.write(f"\nTest {i+1}:\n")
                if "seed" in result:
                    f.write(f"  Seed file: {result['seed']}\n")
                if "posix" in result:
                    f.write(f"  POSIX file: {result['posix']}\n")
                    
                if "error" in result:
                    f.write(f"  ERROR: {result['error']}\n")
                elif "result" in result:
                    status = "PASS" if result["result"].get("equivalent", False) else "FAIL"
                    f.write(f"  Status: {status}\n")
                    
                    # Include limited details of failures to keep report readable
                    if status == "FAIL" and "details" in result["result"]:
                        for detail in result["result"]["details"]:
                            if not detail.get("equivalent", True):
                                f.write(f"  Failure details:\n")
                                if not detail.get("stdout_match", True):
                                    f.write(f"    - stdout mismatch\n")
                                if not detail.get("stderr_match", True):
                                    f.write(f"    - stderr mismatch\n")
                                if not detail.get("exit_code_match", True):
                                    f.write(f"    - exit code mismatch\n")
                                break
            
        logger.info(f"Text report saved to: {file_path}")
        return str(file_path)

    def _generate_report(self,
                        metadata: Optional[Dict[str, Any]] = None,
                        results: List[Dict[str, Any]] = []) -> Dict[str, Any]:
        """
        Generate a structured test report from test results
        
        Args:
            metadata: Additional metadata to include in the report
            results: List of testcase result from this round (each testcase result struct see tester.py)
            
        Returns:
            Dictionary containing the structured report
        """
        # Generate summary statistics
        summary = self._generate_results_summary(results)
        
        # Group failures by type
        failure_types = {}
        for r in results:
            test_count = r.get("test_count", 0)
            pass_num = r.get("pass_num", 0)
            
            if pass_num == test_count:
                continue  # Test passed
            
            for detail in r.get("details", []):
                if not detail.get("equivalent", True):
                    # Determine failure reason
                    reasons = {
                        "stdout_mismatch":      not detail.get("stdout_match", True),
                        "exit_code_mismatch":   not detail.get("exit_code_match", True),
                        "stderr_mismatch":      not detail.get("stderr_match", True),
                    }
                    reason = next((k for k, v in reasons.items() if v), "unknown")
                    failure_types[reason] = failure_types.get(reason, 0) + 1
        
        # Build the report
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report = {
            "timestamp": timestamp,
            "summary": summary,
            "failure_analysis": failure_types,
            "results_details": results,
        }
        
        if metadata:
            report["metadata"] = metadata
            
        return report
        
    def _save_report(self, 
                    report: Dict[str, Any], 
                    file_format: str = "json", 
                    filename: Optional[str] = None) -> str:
        """
        Save the test report to a file
        
        Args:
            report: The report data to save
            file_format: Report format (json, text)
            filename: Optional custom filename
            
        Returns:
            Path to the saved report file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}"
            
        if file_format == "json":
            return self._save_json_report(report, filename)
        elif file_format == "text":
            return self._save_text_report(report, filename)
        else:
            raise ValueError(f"Unsupported report format: {file_format}")
    
    def generate_round_report(self, round_num: int, round_results: list) -> Dict[str, Any]:
        """
        process the test results of a round and generate a report
        
        Args:
            round_num: Current round number
            round_results: List of testcase result from this round (each testcase result struct see tester.py)
            config: Configuration dictionary
            seed_files: List of test seed files

        Returns:
            Summary of the round report
        """
        
        # generate round report
        report = self._generate_report(
            metadata={
                "round_num": round_num,
            },
            results=round_results
        )
        
        # update global summary
        self.all_rounds_results.extend(round_results)
        summary = report["summary"]
        self.all_rounds_summary["rounds"] = max(self.all_rounds_summary["rounds"], round_num) # idiot code ^^
        self.all_rounds_summary["total_tests"] += summary["total_tests"]
        self.all_rounds_summary["passed"] += summary["passed"]
        self.all_rounds_summary["failed"] += summary["failed"]
        
        # save round report
        saved_files = {}
        for file_format in ["json", "text"]:
            try:
                filename = f"round_{round_num}_report"
                saved_files[file_format] = self._save_report(report, file_format, filename)
            except Exception as e:
                logger.error(f"Error saving {file_format} report: {str(e)}")
        
        return summary
    
    def generate_summary_report(self, config: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """
        Generate a summary report of all rounds
        Args:
            config: Configuration dictionary
        Returns:
            Tuple of saved files and global summary
        """
        metadata = {
            "bash_version": self._get_shell_version(config.get("bash_binpath", "/bin/bash")),
            "posix_version": self._get_shell_version(config.get("posix_binpath", "/bin/sh")),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_rounds": self.all_rounds_summary["rounds"],
            "configuration": {
                "timeout":          config.get("timeout", 10),
                "mutators_count":   self._count_mutators(config.get("results").get("mutators")),
                "mutators_applied": self._get_mutators_applied(config.get("results").get("mutators")),
            }
        }
        report = {
            "metadata": metadata,
        }
        
        # global summary
        success_rate = (self.all_rounds_summary["passed"] / self.all_rounds_summary["total_tests"] * 100) \
                      if self.all_rounds_summary["total_tests"] > 0 else 0
        report["global_summary"] = {
            "total_rounds": self.all_rounds_summary["rounds"],
            "total_tests": self.all_rounds_summary["total_tests"],
            "passed": self.all_rounds_summary["passed"],
            "failed": self.all_rounds_summary["failed"],
            "success_rate": f"{success_rate:.2f}%"
        }
        
        # save summary report
        saved_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for file_format in ["json", "text"]:
            try:
                filename = f"summary_report_{timestamp}"
                saved_files[file_format] = self._save_report(report, file_format, filename)
            except Exception as e:
                logger.error(f"Error saving {file_format} summary report: {str(e)}")
                
        return saved_files, report["global_summary"]

