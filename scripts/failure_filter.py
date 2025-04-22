import json
import re

# filter rules

def is_timeout_empty(detail):
    bash_stdout_empty = detail.get("bash_stdout", "") == ""
    posix_stdout_empty = detail.get("posix_stdout", "") == ""
    bash_stderr = detail.get("bash_stderr", "")
    posix_stderr = detail.get("posix_stderr", "")
    bash_exit_code = detail.get("bash_exit_code", 0)
    posix_exit_code = detail.get("posix_exit_code", 0)
    if (bash_stdout_empty and posix_stdout_empty and
        bash_stderr == "" and posix_stderr.startswith("Command timed out after") and
        bash_exit_code == 0 and posix_exit_code == -1):
        return True
    if (bash_stdout_empty and posix_stdout_empty and
        posix_stderr == "" and bash_stderr.startswith("Command timed out after") and
        bash_exit_code == -1 and posix_exit_code == 0):
        return True
    return False

def is_value_too_great_base(detail):
    bash_stderr = detail.get("bash_stderr", "")
    if "value too great for base" in bash_stderr:
        return True
    return False 

def is_test_expr_error(detail):
    bash_stderr = detail.get("bash_stderr", "")
    posix_stderr = detail.get("posix_stderr", "")
    if "==: unexpected operator" in posix_stderr:
        return True
    if "[: Illegal number:" in posix_stderr:
        return True
    if re.search(r"\[: .*: unexpected operator", posix_stderr):
        return True
    if re.search(r"test: .*: unexpected operator", posix_stderr):
        return True
    return False

def is_built_in_error(detail):
    bash_stderr = detail.get("bash_stderr", "")
    posix_stderr = detail.get("posix_stderr", "")
    if "help: not found" in posix_stderr:
        return True
    if "read: arg count" in posix_stderr:
        return True
    return False

def is_pass_testcase(detail):
    # check array error chain problem
    bash_stdout = detail.get("bash_stdout", "") 
    posix_stdout = detail.get("posix_stdout", "")
    bash_stderr = detail.get("bash_stderr", "")
    posix_stderr = detail.get("posix_stderr", "")
    bash_exit_code = detail.get("bash_exit_code", 0)
    posix_exit_code = detail.get("posix_exit_code", 0)
    if (bash_stdout == posix_stdout and
        bash_stderr ==  posix_stderr and
        bash_exit_code != posix_exit_code):
        return True
    return False

# TODO: more rules
FILTER_RULES = [
    is_timeout_empty,
    is_value_too_great_base,
    is_test_expr_error,
    is_built_in_error,
    is_pass_testcase,
]

def should_filter(detail):
    return any(rule(detail) for rule in FILTER_RULES)

def filter_failures(data):
    original_failure_count = 0
    filtered_failure_count = 0
    new_failure_details = []

    for round_item in data["failure_details"]:
        new_failures = []
        for fail in round_item["failures"]:
            original_failure_count += len(fail["details"])
            new_details = [d for d in fail["details"] if not should_filter(d)]
            if new_details:
                fail_copy = dict(fail)
                fail_copy["details"] = new_details
                new_failures.append(fail_copy)
                filtered_failure_count += len(new_details)
        if new_failures:
            round_copy = dict(round_item)
            round_copy["failures"] = new_failures
            new_failure_details.append(round_copy)

    return {
        "total_rounds_analyzed": data.get("total_rounds_analyzed"),
        "rounds_with_failures": data.get("rounds_with_failures"),
        "original_failure_count": original_failure_count,
        "filtered_failure_count": filtered_failure_count,
        "failure_details": new_failure_details
    }


if __name__ == "__main__":
    input_path = "results/reports/failures_summary.json"
    output_path = "results/reports/failures_summary.filtered.json"
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    filtered = filter_failures(data)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(filtered, f, indent=2, ensure_ascii=False)


