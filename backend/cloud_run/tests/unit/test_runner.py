#!/usr/bin/env python3
"""
Unit test runner for The Intaker Flask API.
Provides convenient test execution with coverage reporting and detailed output.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_unit_tests(
    pattern: str = None,
    coverage: bool = True,
    verbose: bool = True,
    parallel: bool = False,
    html_report: bool = False,
    xml_report: bool = False
):
    """
    Run unit tests with optional coverage reporting.
    
    Args:
        pattern: Test file pattern to match
        coverage: Whether to generate coverage report
        verbose: Whether to use verbose output
        parallel: Whether to run tests in parallel
        html_report: Whether to generate HTML coverage report
        xml_report: Whether to generate XML coverage report for CI
    """
    
    # Change to the project root directory
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    # Base pytest command
    cmd = ['python', '-m', 'pytest']
    
    # Test directory
    test_dir = 'tests/unit'
    if pattern:
        test_dir = f'{test_dir}/*{pattern}*'
    cmd.append(test_dir)
    
    # Pytest options
    if verbose:
        cmd.extend(['-v', '--tb=short'])
    
    # Parallel execution
    if parallel:
        cmd.extend(['-n', 'auto'])
    
    # Coverage options
    if coverage:
        cmd.extend([
            '--cov=.',
            '--cov-report=term-missing',
            '--cov-config=.coveragerc'
        ])
        
        if html_report:
            cmd.append('--cov-report=html:tests/coverage/html')
        
        if xml_report:
            cmd.append('--cov-report=xml:tests/coverage/coverage.xml')
    
    # Additional pytest options
    cmd.extend([
        '--strict-markers',
        '--disable-warnings',
        '-p', 'no:cacheprovider'  # Disable cache for clean runs
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    print("-" * 80)
    
    # Run the tests
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def run_specific_test_categories():
    """Run specific categories of tests."""
    
    categories = {
        'auth': 'Authentication and authorization tests',
        'patients': 'Patient management endpoint tests', 
        'documents': 'Document management endpoint tests',
        'schemas': 'Schema validation tests',
        'errors': 'Error handling tests',
        'rate_limiting': 'Rate limiting tests',
        'openapi': 'OpenAPI documentation tests',
        'health': 'Health check endpoint tests'
    }
    
    print("Available test categories:")
    for category, description in categories.items():
        print(f"  {category}: {description}")
    
    category = input("\nEnter category to run (or 'all' for all tests): ").strip().lower()
    
    if category == 'all':
        return run_unit_tests()
    elif category in categories:
        return run_unit_tests(pattern=category)
    else:
        print(f"Invalid category: {category}")
        return 1


def check_test_environment():
    """Check that the test environment is properly set up."""
    
    print("Checking test environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8+ is required")
        return False
    
    print(f"✓ Python version: {sys.version}")
    
    # Check required packages
    required_packages = [
        'pytest', 'pytest-cov', 'flask', 'marshmallow',
        'google-cloud-firestore', 'flask-limiter', 'flask-smorest'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} (missing)")
    
    if missing_packages:
        print(f"\nERROR: Missing required packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r requirements.txt")
        return False
    
    # Check test directory structure
    test_dirs = [
        'tests/unit',
        'tests/unit/test_auth.py',
        'tests/unit/test_patients.py',
        'tests/unit/conftest.py'
    ]
    
    project_root = Path(__file__).parent.parent.parent
    
    for test_path in test_dirs:
        full_path = project_root / test_path
        if full_path.exists():
            print(f"✓ {test_path}")
        else:
            print(f"✗ {test_path} (missing)")
    
    print("\nTest environment check complete.")
    return True


def generate_test_report():
    """Generate a comprehensive test report."""
    
    print("Generating comprehensive test report...")
    
    # Run tests with full coverage and reporting
    return run_unit_tests(
        coverage=True,
        verbose=True,
        html_report=True,
        xml_report=True
    )


def main():
    """Main entry point for the test runner."""
    
    parser = argparse.ArgumentParser(description='Unit test runner for The Intaker API')
    parser.add_argument('--pattern', '-p', help='Test file pattern to match')
    parser.add_argument('--no-coverage', action='store_true', help='Disable coverage reporting')
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet output')
    parser.add_argument('--parallel', action='store_true', help='Run tests in parallel')
    parser.add_argument('--html', action='store_true', help='Generate HTML coverage report')
    parser.add_argument('--xml', action='store_true', help='Generate XML coverage report')
    parser.add_argument('--check-env', action='store_true', help='Check test environment')
    parser.add_argument('--categories', action='store_true', help='Run specific test categories')
    parser.add_argument('--report', action='store_true', help='Generate comprehensive report')
    
    args = parser.parse_args()
    
    if args.check_env:
        success = check_test_environment()
        return 0 if success else 1
    
    if args.categories:
        return run_specific_test_categories()
    
    if args.report:
        return generate_test_report()
    
    # Run tests with specified options
    return run_unit_tests(
        pattern=args.pattern,
        coverage=not args.no_coverage,
        verbose=not args.quiet,
        parallel=args.parallel,
        html_report=args.html,
        xml_report=args.xml
    )


if __name__ == '__main__':
    sys.exit(main()) 