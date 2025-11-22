import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Blocklist file paths (relative to project root)
BLOCKLIST_DIR = Path(__file__).parent.parent / "blocklists"
BAN_PHRASES_FILE = BLOCKLIST_DIR / "ban_phrases.txt"
MUTE_PHRASES_FILE = BLOCKLIST_DIR / "mute_phrases.txt"
DELETE_PHRASES_FILE = BLOCKLIST_DIR / "delete_phrases.txt"

# Load blocklist/whitelisted words/phrases from files
def load_phrases(file_path):
    """Load phrases from a file, similar to bot.py"""
    if not file_path.exists():
        print(f"Warning: Blocklist file not found: {file_path}")
        return []
    
    with open(file_path, 'r', encoding='utf-8') as file:
        phrases = [line.strip().lower() for line in file.readlines() if line.strip()]
    return phrases

# Load all blocklists
BAN_PHRASES = load_phrases(BAN_PHRASES_FILE)
MUTE_PHRASES = load_phrases(MUTE_PHRASES_FILE)
DELETE_PHRASES = load_phrases(DELETE_PHRASES_FILE)

def test_phrase(phrase: str, verbose: bool = True) -> dict:
    """
    Test a phrase against all blocklists.
    
    Returns a dict with:
    - matched: bool
    - action: str | None ("BAN", "MUTE", "DELETE", or None)
    - matched_phrase: str | None
    - reasoning: str
    """
    import re
    
    # Normalize the message (same as bot.py does)
    normalized = phrase.strip().lower()
    original = phrase
    
    result = {
        "matched": False,
        "action": None,
        "matched_phrase": None,
        "reasoning": "No match found in any blocklist.",
        "original_phrase": original,
        "normalized_phrase": normalized
    }
    
    # Check in order: BAN → MUTE → DELETE (same priority as bot.py)
    # Check for banned phrases (word boundary match - same as bot.py)
    for ban_phrase in BAN_PHRASES:
        pattern = r'\b' + re.escape(ban_phrase) + r'\b'
        if re.search(pattern, normalized, re.IGNORECASE):
            result["matched"] = True
            result["action"] = "BAN"
            result["matched_phrase"] = ban_phrase
            result["reasoning"] = f"Matched BAN phrase: '{ban_phrase}'. User would be BANNED and message DELETED."
            return result
    
    # Check for muted phrases (word boundary match - same as bot.py)
    for mute_phrase in MUTE_PHRASES:
        pattern = r'\b' + re.escape(mute_phrase) + r'\b'
        if re.search(pattern, normalized, re.IGNORECASE):
            result["matched"] = True
            result["action"] = "MUTE"
            result["matched_phrase"] = mute_phrase
            result["reasoning"] = f"Matched MUTE phrase: '{mute_phrase}'. User would be MUTED for 3 days and message would trigger mute notification."
            return result
    
    # Check for deleted phrases (word boundary match - same as bot.py)
    for delete_phrase in DELETE_PHRASES:
        pattern = r'\b' + re.escape(delete_phrase) + r'\b'
        if re.search(pattern, normalized, re.IGNORECASE):
            result["matched"] = True
            result["action"] = "DELETE"
            result["matched_phrase"] = delete_phrase
            result["reasoning"] = f"Matched DELETE phrase: '{delete_phrase}'. Message would be DELETED."
            return result
    
    return result

def print_result(result: dict, verbose: bool = True):
    """Print test result in a readable format"""
    print("\n" + "="*70)
    print(f"Original phrase: {result['original_phrase']}")
    print(f"Normalized:      {result['normalized_phrase']}")
    print("-"*70)
    
    if result["matched"]:
        action_symbol = {
            "BAN": "[BAN]",
            "MUTE": "[MUTE]",
            "DELETE": "[DELETE]"
        }
        symbol = action_symbol.get(result["action"], "[MATCH]")
        print(f"{symbol} MATCHED: {result['action']}")
        print(f"Matched phrase: '{result['matched_phrase']}'")
        print(f"Reasoning: {result['reasoning']}")
    else:
        print("[PASS] NO MATCH - Message would pass through (assuming user is not admin)")
    
    print("="*70)

def test_interactive():
    """Interactive mode - test phrases one by one"""
    print("\n" + "="*70)
    print("BLOCKLIST TESTER - Interactive Mode")
    print("="*70)
    print(f"Loaded {len(BAN_PHRASES)} BAN phrases")
    print(f"Loaded {len(MUTE_PHRASES)} MUTE phrases")
    print(f"Loaded {len(DELETE_PHRASES)} DELETE phrases")
    print("\nEnter phrases to test (or 'quit' to exit):")
    print("-"*70)
    
    while True:
        try:
            phrase = input("\n> ").strip()
            if not phrase:
                continue
            if phrase.lower() in ['quit', 'exit', 'q']:
                print("Exiting...")
                break
            
            result = test_phrase(phrase, verbose=True)
            print_result(result)
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except EOFError:
            print("\n\nExiting...")
            break

def test_batch(phrases: list):
    """Test multiple phrases at once"""
    print("\n" + "="*70)
    print("BLOCKLIST TESTER - Batch Mode")
    print("="*70)
    print(f"Testing {len(phrases)} phrases...")
    print("-"*70)
    
    results = []
    for phrase in phrases:
        result = test_phrase(phrase, verbose=False)
        results.append(result)
        print_result(result, verbose=True)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    matched_count = sum(1 for r in results if r["matched"])
    action_counts = {"BAN": 0, "MUTE": 0, "DELETE": 0}
    for r in results:
        if r["action"]:
            action_counts[r["action"]] += 1
    
    print(f"Total phrases tested: {len(results)}")
    print(f"Matched: {matched_count} ({matched_count/len(results)*100:.1f}%)")
    print(f"No match: {len(results) - matched_count}")
    print(f"\nActions:")
    for action, count in action_counts.items():
        if count > 0:
            print(f"  {action}: {count}")
    print("="*70)
    
    return results

def test_from_file(file_path: str):
    """Load phrases from a file and test them"""
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File not found: {file_path}")
        return
    
    with open(path, 'r', encoding='utf-8') as f:
        phrases = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    
    if not phrases:
        print(f"Error: No phrases found in file: {file_path}")
        return
    
    test_batch(phrases)

def show_all_phrases():
    """Show all phrases in each blocklist"""
    print("\n" + "="*70)
    print("ALL BLOCKLIST PHRASES")
    print("="*70)
    
    print(f"\n📋 BAN PHRASES ({len(BAN_PHRASES)}):")
    print("-"*70)
    for i, phrase in enumerate(BAN_PHRASES, 1):
        print(f"{i:3d}. {phrase}")
    
    print(f"\n📋 MUTE PHRASES ({len(MUTE_PHRASES)}):")
    print("-"*70)
    for i, phrase in enumerate(MUTE_PHRASES, 1):
        print(f"{i:3d}. {phrase}")
    
    print(f"\n📋 DELETE PHRASES ({len(DELETE_PHRASES)}):")
    print("-"*70)
    for i, phrase in enumerate(DELETE_PHRASES, 1):
        print(f"{i:3d}. {phrase}")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test phrases against ban/mute/delete blocklists",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python tests/test_blocklists.py
  
  # Test a single phrase
  python tests/test_blocklists.py -p "please dm me"
  
  # Test multiple phrases
  python tests/test_blocklists.py -p "dm me" -p "airdrop" -p "hello world"
  
  # Test from file
  python tests/test_blocklists.py -f tests/test_phrases.txt
  
  # Show all blocklist phrases
  python tests/test_blocklists.py --show-all
        """
    )
    
    parser.add_argument(
        "-p", "--phrase",
        action="append",
        help="Phrase(s) to test (can be used multiple times)"
    )
    parser.add_argument(
        "-f", "--file",
        help="File containing phrases to test (one per line, # for comments)"
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Show all phrases in all blocklists"
    )
    
    args = parser.parse_args()
    
    if args.show_all:
        show_all_phrases()
    elif args.file:
        test_from_file(args.file)
    elif args.phrase:
        test_batch(args.phrase)
    else:
        test_interactive()

