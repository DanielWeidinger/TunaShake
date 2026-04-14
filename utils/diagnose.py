#!/usr/bin/env python3
"""
Diagnostic tool to analyze markdown file parsing issues.
This will show exactly which lines are being parsed and which are being skipped.
"""

import os
import re
import sys


def diagnose_file(filepath):
    """Analyze a markdown file and show detailed parsing information."""

    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return

    print("=" * 80)
    print(f"DIAGNOSTIC REPORT FOR: {filepath}")
    print("=" * 80)

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"\n📄 Total lines in file: {len(lines)}")

    # Current pattern
    pattern = re.compile(r'^[-*+]\s*\[\s*([xX\s])\s*\]\s*(.+)$', re.IGNORECASE)

    matched_lines = []
    unmatched_checkbox_lines = []
    completed_count = 0
    unsolved_count = 0

    print("\n" + "=" * 80)
    print("LINE-BY-LINE ANALYSIS:")
    print("=" * 80)

    for line_num, line in enumerate(lines, 1):
        original_line = line
        line = line.strip()

        # Skip empty lines and headers
        if not line or line.startswith('#'):
            continue

        # Check if it looks like a checkbox line
        if '[' in line and ']' in line:
            match = pattern.match(line)

            if match:
                checkbox_state = match.group(1).strip()
                content = match.group(2).strip()
                is_completed = checkbox_state.lower() == 'x'

                if is_completed:
                    completed_count += 1
                    status_icon = "✓"
                    status_text = "COMPLETED"
                else:
                    unsolved_count += 1
                    status_icon = "○"
                    status_text = "UNSOLVED"

                matched_lines.append((line_num, line, is_completed))
                print(f"{line_num:3}. {status_icon} {status_text:10} | {line}")
            else:
                # Line has brackets but doesn't match pattern
                unmatched_checkbox_lines.append((line_num, line))
                print(f"{line_num:3}. ✗ NOT MATCHED  | {line}")
                print(f"     └─ Raw bytes: {line.encode('utf-8')}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    print(f"✓ Matched lines (parsed successfully): {len(matched_lines)}")
    print(f"  - Completed: {completed_count}")
    print(f"  - Unsolved: {unsolved_count}")
    print(f"✗ Unmatched checkbox lines: {len(unmatched_checkbox_lines)}")
    print(f"📊 Total checkbox items found: {len(matched_lines) + len(unmatched_checkbox_lines)}")

    if unmatched_checkbox_lines:
        print("\n" + "=" * 80)
        print("UNMATCHED LINES (Need attention):")
        print("=" * 80)
        for line_num, line in unmatched_checkbox_lines:
            print(f"\nLine {line_num}: {line}")
            print(f"  Raw: {repr(line)}")
            print(f"  Bytes: {line.encode('utf-8')}")

            # Try to figure out why it didn't match
            if not line.startswith(('-', '*', '+')):
                print(f"  Issue: Line doesn't start with -, *, or +")
            elif '[' not in line or ']' not in line:
                print(f"  Issue: Missing [ or ]")
            else:
                # Check bracket content
                start = line.find('[')
                end = line.find(']')
                if start >= 0 and end > start:
                    bracket_content = line[start+1:end]
                    print(f"  Bracket content: '{bracket_content}' (repr: {repr(bracket_content)})")
                    if bracket_content not in [' ', 'x', 'X']:
                        print(f"  Issue: Bracket contains unexpected character: '{bracket_content}'")

    # Test pattern variations
    print("\n" + "=" * 80)
    print("PATTERN TESTING:")
    print("=" * 80)
    print(f"Current pattern: {pattern.pattern}")

    if unmatched_checkbox_lines:
        print("\nTrying alternative patterns on unmatched lines:")

        alternative_patterns = [
            (r'^[-*+]\s*\[(.?)\]\s*(.+)$', "Any single char in brackets"),
            (r'^[-*+]?\s*\[(.?)\]\s*(.+)$', "Optional bullet marker"),
            (r'^\s*[-*+]\s*\[(.?)\]\s*(.+)$', "Leading whitespace allowed"),
            (r'^.*\[(.?)\](.+)$', "Very permissive"),
        ]

        for alt_pattern_str, description in alternative_patterns:
            alt_pattern = re.compile(alt_pattern_str, re.IGNORECASE)
            matches = 0
            for line_num, line in unmatched_checkbox_lines:
                if alt_pattern.match(line):
                    matches += 1
            if matches > 0:
                print(f"  ✓ Pattern '{description}' would match {matches} more lines")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        # Try to get from environment
        filepath = os.getenv('EXERCISE_FILE', 'exercises.md')

    print(f"\nAnalyzing: {filepath}\n")
    diagnose_file(filepath)

