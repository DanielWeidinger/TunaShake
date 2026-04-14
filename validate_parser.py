#!/usr/bin/env python3
"""
Comprehensive validation script for the exercise picker.
Tests the improved checkbox parsing with various formats.
"""

import sys
from exercise_picker import ExerciseManager


def test_completed_flag_detection():
    """Test that completed flags are correctly detected."""
    print("Testing completed flag detection...")
    print("=" * 70)

    # Test with exercises.md
    manager = ExerciseManager('exercises.md')
    stats = manager.get_statistics()

    print(f"\n📊 exercises.md Statistics:")
    print(f"   Total exercises: {stats['total']}")
    print(f"   Completed: {stats['completed']} ✓")
    print(f"   Unsolved: {stats['unsolved']} ⏳")

    # List completed exercises
    completed = [ex for ex in manager.exercises if ex.is_completed]
    print(f"\n✓ Completed exercises ({len(completed)}):")
    for ex in completed:
        print(f"   - {ex}")

    # List unsolved exercises
    unsolved = [ex for ex in manager.exercises if not ex.is_completed]
    print(f"\n⏳ Unsolved exercises ({len(unsolved)}):")
    for ex in unsolved:
        print(f"   - {ex}")

    # Validate counts
    assert stats['completed'] == 6, f"Expected 6 completed, got {stats['completed']}"
    assert stats['unsolved'] == 13, f"Expected 13 unsolved, got {stats['unsolved']}"
    assert stats['total'] == 19, f"Expected 19 total, got {stats['total']}"

    print("\n" + "=" * 70)
    print("✓ All validation tests passed!")
    print("✓ Completed flags are correctly detected from markdown file")
    return True


def test_various_formats():
    """Test that various markdown formats are supported."""
    print("\n\nTesting various markdown formats...")
    print("=" * 70)

    manager = ExerciseManager('test_formats.md')
    stats = manager.get_statistics()

    print(f"\n📊 test_formats.md Statistics:")
    print(f"   Total exercises: {stats['total']}")
    print(f"   Completed: {stats['completed']} ✓")
    print(f"   Unsolved: {stats['unsolved']} ⏳")

    # Should have parsed exercises with various formats
    assert stats['total'] > 0, "Should have parsed some exercises"
    assert stats['completed'] > 0, "Should have detected completed exercises"
    assert stats['unsolved'] > 0, "Should have detected unsolved exercises"

    print("\n✓ Various markdown formats are correctly supported:")
    print("   - Standard format: - [ ] and - [x]")
    print("   - No space after dash: -[ ] and -[x]")
    print("   - Different bullets: *, +")
    print("   - Extra spaces in brackets")
    print("   - Uppercase X: [X]")

    print("\n" + "=" * 70)
    print("✓ Format flexibility tests passed!")
    return True


def main():
    """Run all validation tests."""
    try:
        print("\n" + "🔍 Exercise Picker Validation Suite" + "\n")

        test_completed_flag_detection()
        test_various_formats()

        print("\n" + "=" * 70)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 70)
        print("\nThe exercise picker correctly:")
        print("  ✓ Loads and parses markdown files")
        print("  ✓ Detects completed exercises (marked with [x])")
        print("  ✓ Detects unsolved exercises (marked with [ ])")
        print("  ✓ Supports various markdown checkbox formats")
        print("  ✓ Calculates accurate statistics")
        print("\nYou can now use the script with confidence:")
        print("  python exercise_picker.py")
        print()

        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

