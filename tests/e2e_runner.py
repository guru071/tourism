#!/usr/bin/env python3
"""
E2E Test Suite Runner for AI Tourism Ecosystem (Phase 0).
Can be executed directly via:
    python tests/e2e_runner.py
    python tests/e2e_runner.py --tier 1
    python tests/e2e_runner.py --tier 2
    python tests/e2e_runner.py --tier 3
    python tests/e2e_runner.py --tier 4
    python tests/e2e_runner.py --json-report test_report.json
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Set up paths
TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))


def run_with_pytest(tier: str = "all", verbose: bool = True, json_report: str = None) -> int:
    """Run tests using pytest with full reporting."""
    try:
        import pytest
    except ImportError:
        print("[ERROR] pytest is not installed. Fallback to unittest.", file=sys.stderr)
        return run_with_unittest(tier, verbose)

    args = []
    if verbose:
        args.append("-v")

    # Add warnings filter
    args.extend(["-W", "ignore::DeprecationWarning"])

    test_files_map = {
        "1": str(TESTS_DIR / "test_cases" / "test_tier1_features.py"),
        "2": str(TESTS_DIR / "test_cases" / "test_tier2_boundaries.py"),
        "3": str(TESTS_DIR / "test_cases" / "test_tier3_combinations.py"),
        "4": str(TESTS_DIR / "test_cases" / "test_tier4_scenarios.py"),
    }

    if tier in test_files_map:
        args.append(test_files_map[tier])
    else:
        args.append(str(TESTS_DIR / "test_cases"))

    print(f"\n========================================================")
    print(f" AI Tourism Ecosystem E2E Test Suite (Phase 0)")
    print(f" Target Tier: {tier.upper()}")
    print(f" Working Directory: {PROJECT_ROOT}")
    print(f"========================================================\n")

    start_time = time.time()
    exit_code = pytest.main(args)
    duration = time.time() - start_time

    print(f"\n--------------------------------------------------------")
    print(f" Execution completed in {duration:.2f} seconds")
    print(f" Exit Code: {exit_code}")
    print(f"--------------------------------------------------------\n")

    if json_report:
        report_data = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "tier": tier,
            "duration_seconds": round(duration, 3),
            "exit_code": int(exit_code),
            "status": "PASSED" if exit_code == 0 else "FAILED",
        }
        with open(json_report, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        print(f"[INFO] Saved test execution report to: {json_report}")

    return exit_code


def run_with_unittest(tier: str = "all", verbose: bool = True) -> int:
    """Fallback runner using standard library unittest."""
    import unittest

    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    tier_files = {
        "1": "test_tier1_features.py",
        "2": "test_tier2_boundaries.py",
        "3": "test_tier3_combinations.py",
        "4": "test_tier4_scenarios.py",
    }

    pattern = tier_files.get(tier, "test_*.py")
    suite = loader.discover(
        start_dir=str(TESTS_DIR / "test_cases"),
        pattern=pattern,
        top_level_dir=str(TESTS_DIR)
    )

    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


def main():
    parser = argparse.ArgumentParser(
        description="E2E Test Runner for AI Tourism Ecosystem (Phase 0)"
    )
    parser.add_argument(
        "--tier",
        type=str,
        default="all",
        choices=["all", "1", "2", "3", "4"],
        help="Specific test tier to run (default: all)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=True,
        help="Enable verbose output"
    )
    parser.add_argument(
        "--json-report",
        type=str,
        default=None,
        help="Optional path to output JSON summary report"
    )

    args = parser.parse_args()
    code = run_with_pytest(
        tier=args.tier,
        verbose=args.verbose,
        json_report=args.json_report
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
