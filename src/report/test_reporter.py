"""
Test Reporter module for generating and saving test reports
"""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)

class TestReporter:
    """
    Generates and saves test reports from differential testing results
    """
    
    def __init__(self, output_dir: str = "results/tests"):
        """
        Initialize the test reporter
        
        Args:
            output_dir: Directory to store generated reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_metadata(self, config: Dict[str, Any], seed_files: List[Path]) -> Dict[str, Any]:
        """
        Generate metadata for test reports
        
        Args:
            config: Configuration dictionary
            seed_files: List of test seed files
            
        Returns:
            Dictionary of metadata
        """
        return {
            "bash_version": self._get_shell_version(config.get("bash_path", "/bin/bash")),
            "posix_version": self._get_shell_version(config.get("posix_path", "/bin/sh")),
            "test_seed_count": len(seed_files),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "configuration": {
                # Include relevant config parameters, excluding sensitive data
                "timeout": config.get("timeout", 10),
                "mutators_count": self._count_mutators(config.get("mutators_dir", "")),
                "features_tested": self._get_features_tested(config.get("mutators_dir", ""))
            }
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
            return len(list(Path(mutators_dir).glob("*_mutator.py")))
        except Exception:
            return 0
            
    def _get_features_tested(self, mutators_dir: str) -> List[str]:
        """Get list of features being tested based on mutator filenames"""
        try:
            return [p.stem.replace("_mutator", "") 
                   for p in Path(mutators_dir).glob("*_mutator.py")]
        except Exception:
            return []
            
    def generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of test results
        
        Args:
            results: List of test results
            
        Returns:
            Summary dictionary
        """
        total = len(results)
        passed = sum(1 for r in results if "result" in r and r["result"].get("equivalent", False))
        failed = sum(1 for r in results if "result" in r and not r["result"].get("equivalent", False))
        errors = sum(1 for r in results if "error" in r)
        
        # Calculate success rate
        success_rate = (passed / total * 100) if total > 0 else 0
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "success_rate": f"{success_rate:.2f}%"
        }
        
    def generate_report(self, results: List[Dict[str, Any]], 
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a structured test report from test results
        
        Args:
            results: List of test results from differential testing
            metadata: Additional metadata to include in the report
            
        Returns:
            Dictionary containing the structured report
        """
        # Generate summary statistics
        summary = self.generate_summary(results)
        
        # Group failures by type
        failure_types = {}
        for r in results:
            if "result" in r and not r["result"].get("equivalent", False):
                details = r["result"].get("details", [])
                for detail in details:
                    if not detail.get("equivalent", True):
                        # Determine failure reason
                        if not detail.get("stdout_match", True):
                            reason = "stdout_mismatch"
                        elif not detail.get("exit_code_match", True):
                            reason = "exit_code_mismatch"
                        elif not detail.get("stderr_match", True):
                            reason = "stderr_mismatch"
                        else:
                            reason = "unknown"
                            
                        failure_types[reason] = failure_types.get(reason, 0) + 1
        
        # Build the report
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = {
            "timestamp": timestamp,
            "summary": summary,
            "failure_analysis": failure_types,
            "details": results
        }
        
        # Include metadata if provided
        if metadata:
            report["metadata"] = metadata
            
        return report
        
    def save_report(self, report: Dict[str, Any], 
                   format: str = "json", 
                   filename: Optional[str] = None) -> str:
        """
        Save the test report to a file
        
        Args:
            report: The report data to save
            format: Report format (json, text)
            filename: Optional custom filename
            
        Returns:
            Path to the saved report file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}"
            
        if format == "json":
            return self._save_json_report(report, filename)
        elif format == "text":
            return self._save_text_report(report, filename)
        else:
            raise ValueError(f"Unsupported report format: {format}")
            
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
        
    def generate_and_save(self, results: List[Dict[str, Any]], 
                         config: Dict[str, Any],
                         seed_files: List[Path],
                         formats: List[str] = ["json", "text"]) -> Dict[str, str]:
        """
        Generate and save test reports in multiple formats
        
        Args:
            results: List of test results
            config: Configuration dictionary for metadata
            seed_files: List of test seed files
            formats: List of formats to generate
            
        Returns:
            Dictionary mapping format to file path
        """
        # Generate metadata
        metadata = self.generate_metadata(config, seed_files)
        
        # Generate the report
        report = self.generate_report(results, metadata)
        saved_files = {}
        
        # Save in each requested format
        for format in formats:
            try:
                saved_files[format] = self.save_report(report, format)
            except Exception as e:
                logger.error(f"Error saving {format} report: {str(e)}")
                
        return saved_files, report["summary"]