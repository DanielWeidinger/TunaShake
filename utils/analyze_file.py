#!/usr/bin/env python3
"""
Enhanced diagnostic tool to help users understand their markdown file parsing.
"""

import os
import sys


def analyze_file(filepath):
    """Provide detailed analysis of the markdown file."""
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        print(f"\nPlease check that the path in your .env file is correct.")
        return False

    print("=" * 80)
    print(f"📋 ANALYZING: {filepath}")
    print("=" * 80)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.splitlines()

    # Count different checkbox states
    unchecked_count = content.count('- [ ]')
    checked_lowercase = content.count('- [x]')
    checked_uppercase = content.count('- [X]')
    checked_total = checked_lowercase + checked_uppercase

    # Count alternative formats
    unchecked_asterisk = content.count('* [ ]')
    checked_asterisk_lower = content.count('* [x]')
    checked_asterisk_upper = content.count('* [X]')
    
    unchecked_plus = content.count('+ [ ]')
    checked_plus_lower = content.count('+ [x]')
    checked_plus_upper = content.count('+ [X]')

    total_checkboxes = (unchecked_count + checked_total + 
                       unchecked_asterisk + checked_asterisk_lower + checked_asterisk_upper +
                       unchecked_plus + checked_plus_lower + checked_plus_upper)

    print(f"\n📊 FILE STATISTICS:")
    print(f"   Total lines: {len(lines)}")
    print(f"   Total checkboxes found: {total_checkboxes}")
    print()
    print(f"   Dash format (-):")
    print(f"      Unchecked [ ]: {unchecked_count}")
    print(f"      Checked [x]:   {checked_lowercase}")
    print(f"      Checked [X]:   {checked_uppercase}")
    
    if unchecked_asterisk + checked_asterisk_lower + checked_asterisk_upper > 0:
        print(f"   Asterisk format (*):")
        print(f"      Unchecked [ ]: {unchecked_asterisk}")
        print(f"      Checked [x]:   {checked_asterisk_lower}")
        print(f"      Checked [X]:   {checked_asterisk_upper}")
    
    if unchecked_plus + checked_plus_lower + checked_plus_upper > 0:
        print(f"   Plus format (+):")
        print(f"      Unchecked [ ]: {unchecked_plus}")
        print(f"      Checked [x]:   {checked_plus_lower}")
        print(f"      Checked [X]:   {checked_plus_upper}")

    print("\n" + "=" * 80)
    print("📝 INTERPRETATION:")
    print("=" * 80)

    if checked_total == 0:
        print("\n⚠️  NO COMPLETED EXERCISES FOUND!")
        print()
        print("   Your file currently has NO exercises marked as completed.")
        print("   All exercises are marked with [ ] (unchecked).")
        print()
        print("   To mark an exercise as completed, change:")
        print("      - [ ] Exercise name")
        print("   to:")
        print("      - [x] Exercise name")
        print()
        print("   The script will then recognize it as completed.")
    else:
        print(f"\n✓ Found {checked_total} completed exercise(s)")
        print(f"  Found {unchecked_count} unsolved exercise(s)")

    # Check if user expects more exercises
    if total_checkboxes < 75:
        print(f"\n💡 NOTE:")
        print(f"   You mentioned having 75 exercises, but only {total_checkboxes} were found.")
        print(f"   This could mean:")
        print(f"      1. Some exercises are on lines without checkbox format")
        print(f"      2. Some exercises use a different format")
        print(f"      3. The file was recently edited")
        print()
        print(f"   Lines without checkboxes will be ignored by the script.")

    print("\n" + "=" * 80)
    print("🔍 SAMPLE LINES:")
    print("=" * 80)
    
    # Show first few checkbox lines
    checkbox_lines = [line for line in lines if '[' in line and ']' in line]
    print(f"\nFirst 5 checkbox lines:")
    for i, line in enumerate(checkbox_lines[:5], 1):
        status = "✓" if '[x]' in line.lower() else "○"
        print(f"   {status} {line}")

    if len(checkbox_lines) > 5:
        print(f"\nLast 5 checkbox lines:")
        for i, line in enumerate(checkbox_lines[-5:], len(checkbox_lines)-4):
            status = "✓" if '[x]' in line.lower() else "○"
            print(f"   {status} {line}")

    print("\n" + "=" * 80)
    return True


def main():
    """Main entry point."""
    
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        # Try to load from .env
        try:
            from dotenv import load_dotenv
            load_dotenv()
            filepath = os.getenv('EXERCISE_FILE')
            if not filepath:
                print("❌ No file specified and EXERCISE_FILE not set in .env")
                print("\nUsage:")
                print("   python analyze_file.py <path-to-markdown-file>")
                print("   OR set EXERCISE_FILE in your .env file")
                return 1
        except ImportError:
            filepath = 'exercises.md'

    print()
    success = analyze_file(filepath)
    print()
    
    if success:
        print("✓ Analysis complete!")
        print()
        print("To use the exercise picker:")
        print("   python exercise_picker.py")
        print()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

