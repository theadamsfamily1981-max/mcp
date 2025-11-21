#!/usr/bin/env python3
"""
Comprehensive Test Runner for PC Parts Scraper

Runs all test suites and generates detailed reports:
- TIER 1 unit tests (stealth, anomaly detection, reputation)
- TIER 2 unit tests (image verification, trends, alerts, scheduler, DOM)
- Integration tests (full pipeline)

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py --tier1      # Run only TIER 1 tests
    python run_tests.py --tier2      # Run only TIER 2 tests
    python run_tests.py --integration # Run only integration tests
    python run_tests.py --verbose    # Verbose output
"""

import sys
import argparse
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def print_banner(text):
    """Print formatted banner"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def print_section(text):
    """Print section header"""
    print("\n" + "-"*70)
    print(f"  {text}")
    print("-"*70)


def run_tier1_tests():
    """Run TIER 1 unit tests"""
    print_section("TIER 1 UNIT TESTS")
    from tests.test_tier1 import run_all_tier1_tests
    return run_all_tier1_tests()


def run_tier2_tests():
    """Run TIER 2 unit tests"""
    print_section("TIER 2 UNIT TESTS")
    from tests.test_tier2 import run_all_tier2_tests
    return run_all_tier2_tests()


def run_integration_tests():
    """Run integration tests"""
    print_section("INTEGRATION TESTS")
    from tests.test_integration import run_all_integration_tests
    return run_all_integration_tests()


def generate_summary_report(results):
    """Generate comprehensive test summary"""
    print_banner("TEST SUMMARY REPORT")

    total_passed = sum(r['passed'] for r in results.values())
    total_failed = sum(r['failed'] for r in results.values())
    total_tests = total_passed + total_failed

    # Per-suite breakdown
    print("📊 RESULTS BY TEST SUITE:\n")
    for suite_name, result in results.items():
        passed = result['passed']
        failed = result['failed']
        total = passed + failed
        success_rate = (passed / total * 100) if total > 0 else 0

        status_icon = "✅" if failed == 0 else "⚠️"
        print(f"{status_icon} {suite_name}:")
        print(f"   Passed: {passed}/{total} ({success_rate:.1f}%)")
        if failed > 0:
            print(f"   ❌ Failed: {failed}")
        print()

    # Overall summary
    print("-"*70)
    print(f"\n📈 OVERALL RESULTS:\n")
    print(f"   Total tests: {total_tests}")
    print(f"   Passed: {total_passed} ✅")
    print(f"   Failed: {total_failed} {'❌' if total_failed > 0 else ''}")

    overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    print(f"   Success rate: {overall_success_rate:.1f}%")

    # Final verdict
    print("\n" + "="*70)
    if total_failed == 0:
        print("🎉 ALL TESTS PASSED! System is ready for deployment.")
    else:
        print(f"⚠️  {total_failed} TEST(S) FAILED. Please review and fix.")
    print("="*70 + "\n")

    return total_failed == 0


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(
        description="Run PC Parts Scraper test suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --tier1            # Run only TIER 1 tests
  python run_tests.py --tier2            # Run only TIER 2 tests
  python run_tests.py --integration      # Run only integration tests
  python run_tests.py --verbose          # Verbose output
        """
    )

    parser.add_argument('--tier1', action='store_true',
                        help='Run only TIER 1 unit tests')
    parser.add_argument('--tier2', action='store_true',
                        help='Run only TIER 2 unit tests')
    parser.add_argument('--integration', action='store_true',
                        help='Run only integration tests')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    parser.add_argument('--quick', action='store_true',
                        help='Quick test (skip slow tests)')

    args = parser.parse_args()

    # Determine which tests to run
    run_all = not (args.tier1 or args.tier2 or args.integration)

    print_banner("PC PARTS SCRAPER - TEST SUITE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test mode: {'ALL TESTS' if run_all else 'SELECTIVE'}")

    if args.quick:
        print("⚡ Quick mode enabled (skipping slow tests)")

    start_time = time.time()
    results = {}

    try:
        # Run TIER 1 tests
        if run_all or args.tier1:
            try:
                passed, failed = run_tier1_tests()
                results['TIER 1 Unit Tests'] = {'passed': passed, 'failed': failed}
            except Exception as e:
                print(f"❌ TIER 1 tests crashed: {e}")
                import traceback
                traceback.print_exc()
                results['TIER 1 Unit Tests'] = {'passed': 0, 'failed': 999}

        # Run TIER 2 tests
        if run_all or args.tier2:
            try:
                passed, failed = run_tier2_tests()
                results['TIER 2 Unit Tests'] = {'passed': passed, 'failed': failed}
            except Exception as e:
                print(f"❌ TIER 2 tests crashed: {e}")
                import traceback
                traceback.print_exc()
                results['TIER 2 Unit Tests'] = {'passed': 0, 'failed': 999}

        # Run integration tests
        if run_all or args.integration:
            try:
                passed, failed = run_integration_tests()
                results['Integration Tests'] = {'passed': passed, 'failed': failed}
            except Exception as e:
                print(f"❌ Integration tests crashed: {e}")
                import traceback
                traceback.print_exc()
                results['Integration Tests'] = {'passed': 0, 'failed': 999}

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user (Ctrl+C)")
        sys.exit(1)

    # Calculate duration
    duration = time.time() - start_time

    # Generate summary
    all_passed = generate_summary_report(results)

    print(f"⏱️  Total duration: {duration:.2f} seconds")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Exit code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
