#!/usr/bin/env python3
"""Debug script to test the markdown parsing."""

import re

# Test lines from the markdown file
test_lines = [
    "- [ ] 1 Blatt - 1 1",
    "- [ ] 1 Blatt - 2",
    "- [x] 2 Blatt - 1 a)",
    "- [x] 2 Blatt - 1 b) 1",
    "- [ ] 2 Blatt - 2 a)",
]

# Current pattern from the script
pattern = re.compile(r'^-\s+\[([x\s])\]\s+(.+)$', re.IGNORECASE)

print("Testing markdown parsing:")
print("=" * 70)

for line in test_lines:
    match = pattern.match(line)
    if match:
        checkbox_state = match.group(1).strip()
        content = match.group(2).strip()
        is_completed = checkbox_state.lower() == 'x'

        print(f"\nLine: {line}")
        print(f"  Checkbox state: '{checkbox_state}' (raw: '{match.group(1)}')")
        print(f"  Is completed: {is_completed}")
        print(f"  Content: {content}")
    else:
        print(f"\nLine: {line}")
        print(f"  NO MATCH!")

print("\n" + "=" * 70)

# Now test with actual file
print("\nReading from exercises.md:")
print("=" * 70)

with open('exercises.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

completed_count = 0
unsolved_count = 0

for line in lines:
    line = line.strip()
    match = pattern.match(line)

    if match:
        checkbox_state = match.group(1).strip()
        content = match.group(2).strip()
        is_completed = checkbox_state.lower() == 'x'

        if is_completed:
            completed_count += 1
            print(f"✓ COMPLETED: {content}")
        else:
            unsolved_count += 1
            print(f"○ UNSOLVED:  {content}")

print("\n" + "=" * 70)
print(f"Summary: {completed_count} completed, {unsolved_count} unsolved")

