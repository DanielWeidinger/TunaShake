#!/usr/bin/env python3
"""
Quick test script to verify the exercise picker functionality
"""

import os
import sys

# Set the environment variable for testing
os.environ['EXERCISE_FILE'] = 'exercises.md'

# Import the exercise manager
from exercise_picker import ExerciseManager

def test_basic_functionality():
    """Test basic functionality of the exercise picker."""
    print("Testing Exercise Picker...")
    print("-" * 60)

    # Create manager
    manager = ExerciseManager('exercises.md')

    # Test statistics
    stats = manager.get_statistics()
    print(f"\n✓ Loaded {stats['total']} exercises")
    print(f"  - Completed: {stats['completed']}")
    print(f"  - Unsolved: {stats['unsolved']}")
    print(f"  - Completion rate: {stats['completion_rate']:.1f}%")

    # Test getting unsolved exercises
    unsolved = manager.get_unsolved_exercises()
    print(f"\n✓ Found {len(unsolved)} unsolved exercises")

    # Test getting random exercises
    print("\n✓ Random unsolved exercises:")
    for i in range(min(5, len(unsolved))):
        exercise = manager.get_random_unsolved()
        if exercise:
            print(f"  {i+1}. {exercise}")

    print("\n" + "-" * 60)
    print("✓ All tests passed!")
    print("\nTo run the interactive version, use:")
    print("  python exercise_picker.py")

if __name__ == '__main__':
    try:
        test_basic_functionality()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

