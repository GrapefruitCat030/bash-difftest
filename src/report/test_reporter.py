"""
Test Reporter module for generating and saving test reports
"""

import json
import logging
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class TestReporter:
    """
    Generates and saves test reports from differential testing results
    """
    
    def __init__(self, output_dir: str = "results/reports"):
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
            "warnings": 0,
            "errors": 0,
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
            results: List of testcase result, each is a dictionary with:
                - seed_name: Name of the test seed
                - test_count: int
                - pass_num: int
                - fail_num: int
                - waring_num: int
                - details: List of dictionaries with detail for each test input
            or  
                - seed_name: Name of the test seed
                - tool_error: str(e)
        Returns:
            Summary dictionary
        """
        total   = sum(r.get("test_count", 0) for r in results)
        passed  = sum(r.get("pass_num", 0) for r in results)
        failed  = sum(r.get("fail_num", 0) for r in results)
        warnings= sum(r.get("warning_num", 0) for r in results)
        errors  = sum(r.get("tool_error", 0) for r in results)
        effective_rate = ((passed + warnings) / total * 100) if total > 0 else 0
        success_rate = (passed / total * 100) if total > 0 else 0
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "errors": errors,
            "effective_rate": f"{effective_rate:.2f}%",
            "success_rate": f"{success_rate:.2f}%",
        }

    def _save_json_report(self, report: Dict[str, Any], filename: str) -> str:
        """Save report in JSON format"""
        if not filename.endswith(".json"):
            filename += ".json"
            
        file_path = self.output_dir / filename
        
        with open(file_path, "w") as f:
            json.dump(report, f, indent=2)
            
        logger.debug(f"JSON report saved to: {file_path}")
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
        
        warning_analysis = [] 
        failure_analysis = []
        for testcase_result in results:
            seed_name = testcase_result.get("seed_name", "unknown_seed")
            test_count = testcase_result.get("test_count", 0)
            pass_num = testcase_result.get("pass_num", 0)
            
            if pass_num == test_count:
                continue  # Testcase passed

            if testcase_result.get("tool_error"):
                failure_analysis.append({"seed_name": seed_name, "error": testcase_result["tool_error"]})
                continue # Testcase Tool error

            warning_num = testcase_result.get("warning_num", 0)
            failure_num = testcase_result.get("fail_num", 0)
            if warning_num > 0:
                warning_analysis.append({
                    "seed_name": seed_name,
                    "warnings_num": warning_num,
                })
            if failure_num > 0:
                failure_analysis.append({
                    "seed_name": seed_name,
                    "failures_num": failure_num,
                })
        
        # Build the report
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report = {
            "timestamp": timestamp,
            "summary": summary,
            "warning_testcases": warning_analysis,
            "failure_testcases": failure_analysis,
            "result_details_of_testcases": results,
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
        summary = report["summary"]
        self.all_rounds_summary["rounds"] = max(self.all_rounds_summary["rounds"], round_num) # idiot code ^^
        self.all_rounds_summary["total_tests"] += summary["total_tests"]
        self.all_rounds_summary["passed"] += summary["passed"]
        self.all_rounds_summary["failed"] += summary["failed"]
        self.all_rounds_summary["warnings"] += summary["warnings"]
        self.all_rounds_summary["errors"] += summary["errors"]
        
        # save round report
        saved_files = {}
        file_format = "json"  # default format
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
        effective_rate = ((self.all_rounds_summary["passed"] + self.all_rounds_summary["warnings"]) / self.all_rounds_summary["total_tests"] * 100) \
                            if self.all_rounds_summary["total_tests"] > 0 else 0
        success_rate = (self.all_rounds_summary["passed"] / self.all_rounds_summary["total_tests"] * 100) \
                      if self.all_rounds_summary["total_tests"] > 0 else 0
        report["global_summary"] = {
            "total_rounds": self.all_rounds_summary["rounds"],
            "total_tests": self.all_rounds_summary["total_tests"],
            "passed": self.all_rounds_summary["passed"],
            "failed": self.all_rounds_summary["failed"],
            "warnings": self.all_rounds_summary["warnings"],
            "errors": self.all_rounds_summary["errors"],
            "effective_rate": f"{effective_rate:.2f}%",
            "success_rate": f"{success_rate:.2f}%"
        }
        
        # save summary report
        saved_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_format = "json"  # default format
        try:
            filename = f"summary_report_{timestamp}"
            saved_files[file_format] = self._save_report(report, file_format, filename)
        except Exception as e:
            logger.error(f"Error saving {file_format} summary report: {str(e)}")
                
        return saved_files, report["global_summary"]

    def clear_reports(self):
        """
        Clear all reports in the output directory
        """
        if not self.output_dir.exists() or not self.output_dir.is_dir():
            logger.warning(f"Output directory {self.output_dir} does not exist or is not a directory")
            return

        # backup
        files_to_backup = [file for file in self.output_dir.iterdir() if file.is_file() and file.name != ".gitkeep"]
        if files_to_backup:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.output_dir / f"reports_backup_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            for file in files_to_backup:
                shutil.copy2(file, backup_dir / file.name)
            logger.info(f"Backed up {len(files_to_backup)} report files to {backup_dir}")
        else:
            logger.info("No files to back up and clear")
            return
    
        # clear
        for file in self.output_dir.iterdir():
            if file.is_file() and file.name != ".gitkeep":
                file.unlink()
        logger.info(f"Cleared all reports in {self.output_dir}")

    def collect_failure_reports(self) -> str:
        """
        Collect and summarize all failure reports from round files
        """
        all_failures = []
        round_files = sorted(list(self.output_dir.glob("round_*_report.json")))
        
        for report_file in round_files:
            try:
                with open(report_file, 'r') as f:
                    report_data = json.load(f)
                    
                round_num = report_data.get("metadata", {}).get("round_num", "unknown")
                
                failures = []
                for result in report_data.get("result_details_of_testcases", []):
                    seed_name = result.get("seed_name", "unknown_seed")
                    
                    if "tool_error" in result:
                        failures.append({
                            "seed_name": seed_name,
                            "error_type": "tool_error",
                            "error": result["tool_error"]
                        })
                        continue
                    
                    fail_num = result.get("fail_num", 0)
                    if fail_num > 0:
                        failure_details = []
                        for detail in result.get("details", []):
                            if detail.get("status") == "FAILURE":
                                failure_details.append(detail)                        
                        
                        failures.append({
                            "seed_name": seed_name,
                            "failure_count": fail_num,
                            "details": failure_details
                        })
                
                if failures:
                    all_failures.append({
                        "round": round_num,
                        "failures": failures
                    })
                    
            except Exception as e:
                logger.error(f"Error processing report file {report_file}: {str(e)}")
        
        summary_report = {
            "total_rounds_analyzed": len(round_files),
            "rounds_with_failures": len(all_failures),
            "failure_details": all_failures
        }
        
        filename = f"failures_summary.json"
        file_path = self.output_dir / filename
        
        with open(file_path, "w") as f:
            json.dump(summary_report, f, indent=2)
            
        logger.info(f"Failures summary report saved to: {file_path}")
        return str(file_path)
