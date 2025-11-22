"""
Test Runner - Runs all test suites

Usage:
    python tests/test_runner.py              # Run all tests
    python tests/test_runner.py --verbose    # Verbose output
    python tests/test_runner.py --quick      # Quick test subset
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_tests(test_suite_name, verbose=False):
    """Run a specific test suite"""
    if test_suite_name == "comprehensive":
        from test_bot_comprehensive import run_all_tests
        return run_all_tests()
    elif test_suite_name == "integration":
        from test_integration import run_integration_tests
        return run_integration_tests()
    elif test_suite_name == "blocklists":
        # Run blocklist tests using the interactive tester
        print("\n" + "="*70)
        print("BLOCKLIST FUNCTIONALITY TESTS")
        print("="*70)
        
        test_phrases = [
            ("dm me", "BAN", True),
            ("every few minutes", None, False),  # Should NOT match
            ("private message", "DELETE", True),  # Actually in DELETE, not MUTE
            ("if you are still holding", "DELETE", True),
            ("hello world", None, False),
        ]
        
        from test_blocklists import test_phrase
        all_passed = True
        
        for phrase, expected_action, should_match in test_phrases:
            result = test_phrase(phrase, verbose=False)
            
            if should_match:
                if not result["matched"]:
                    print(f"[FAIL] '{phrase}' should match but didn't")
                    all_passed = False
                elif result["action"] != expected_action:
                    print(f"[FAIL] '{phrase}' matched but action is {result['action']}, expected {expected_action}")
                    all_passed = False
                else:
                    print(f"[PASS] '{phrase}' correctly matched {expected_action}")
            else:
                if result["matched"]:
                    print(f"[FAIL] '{phrase}' should NOT match but did (matched {result['action']})")
                    all_passed = False
                else:
                    print(f"[PASS] '{phrase}' correctly did not match")
        
        print("="*70)
        return all_passed
    else:
        print(f"Unknown test suite: {test_suite_name}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run bot.py test suites")
    parser.add_argument(
        "--suite",
        choices=["all", "comprehensive", "integration", "blocklists"],
        default="all",
        help="Test suite to run (default: all)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick test subset (blocklists only)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("BOT.PY TEST SUITE")
    print("="*70)
    print(f"Running: {args.suite}")
    print("="*70 + "\n")
    
    if args.quick:
        suites = ["blocklists"]
    elif args.suite == "all":
        suites = ["comprehensive", "integration", "blocklists"]
    else:
        suites = [args.suite]
    
    results = {}
    for suite in suites:
        print(f"\n{'='*70}")
        print(f"Running {suite.upper()} tests...")
        print(f"{'='*70}\n")
        
        try:
            success = run_tests(suite, verbose=args.verbose)
            results[suite] = success
        except Exception as e:
            print(f"\n[ERROR] Running {suite} tests: {e}")
            import traceback
            traceback.print_exc()
            results[suite] = False
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for suite, success in results.items():
        status = "[PASSED]" if success else "[FAILED]"
        print(f"{suite:20s} {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n[SUCCESS] ALL TESTS PASSED")
        return 0
    else:
        print("\n[FAILURE] SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())

