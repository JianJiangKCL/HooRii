#!/usr/bin/env python3
"""
Test runner script for the Smart Home AI Assistant
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type="all", verbose=False):
    """Run tests based on type"""
    project_root = Path(__file__).parent
    test_dir = project_root / "tests"

    # Build pytest command
    cmd = ["python", "-m", "pytest"]

    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    # Add coverage if available
    cmd.extend(["--cov=src", "--cov-report=term-missing"])

    # Select test directory
    if test_type == "unit":
        cmd.append(str(test_dir / "unit"))
    elif test_type == "integration":
        cmd.append(str(test_dir / "integration"))
    elif test_type == "all":
        cmd.append(str(test_dir))
    else:
        print(f"Unknown test type: {test_type}")
        return 1

    # Add color output
    cmd.append("--color=yes")

    print(f"Running {test_type} tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print("\nError: pytest not found. Install it with: pip install pytest pytest-cov pytest-asyncio")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Run tests for Smart Home AI Assistant")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "all"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install test dependencies first"
    )

    args = parser.parse_args()

    if args.install_deps:
        print("Installing test dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "pytest", "pytest-cov", "pytest-asyncio", "pytest-mock"
        ])
        print()

    return run_tests(args.type, args.verbose)


if __name__ == "__main__":
    sys.exit(main())