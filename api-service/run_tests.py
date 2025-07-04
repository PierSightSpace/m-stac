#!/usr/bin/env python3
"""
Test runner script for the STAC API
"""

import subprocess
import sys
import argparse
import os


def run_command(command):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Run STAC API tests")
    parser.add_argument("--category", choices=["all", "unit", "integration", "catalog", "collections", "search", "items", "rate-limit"], 
                       default="all", help="Test category to run")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--debug", action="store_true", help="Debug mode with output")
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd = ["pytest"]
    
    if args.category == "unit":
        cmd.extend(["-m", "not integration"])
    elif args.category == "integration":
        cmd.extend(["-m", "integration"])
    elif args.category == "catalog":
        cmd.extend(["tests/test_catalog.py"])
    elif args.category == "collections":
        cmd.extend(["tests/test_collections.py"])
    elif args.category == "search":
        cmd.extend(["tests/test_search.py"])
    elif args.category == "items":
        cmd.extend(["tests/test_items.py"])
    elif args.category == "rate-limit":
        cmd.extend(["tests/test_rate_limiting.py"])
    
    if args.coverage:
        cmd.extend(["--cov=.", "--cov-report=term-missing", "--cov-report=html"])
    
    if args.parallel:
        cmd.extend(["-n", "auto"])
    
    if args.verbose:
        cmd.append("-v")
    
    if args.debug:
        cmd.append("-s")
    
    # Convert list to string for subprocess
    command = " ".join(cmd)
    
    print(f"Running: {command}")
    print("=" * 50)
    
    # Run the command
    if args.debug:
        # For debug mode, run without capture
        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)
    else:
        result = run_command(command)
        if result:
            print(result)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main() 