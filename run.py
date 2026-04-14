import os
from dotenv import load_dotenv

from exercise_manager import ExerciseManager


def print_banner():
    """Print welcome banner."""
    print("=" * 60)
    print("  Random Exercise Picker")
    print("=" * 60)
    print()


def print_statistics(stats: dict):
    """Print exercise statistics."""
    print(f"\n📊 Statistics:")
    print(f"   Total exercises: {stats['total']}")
    print(f"   Completed: {stats['completed']} ✓")
    print(f"   Unsolved: {stats['unsolved']} ⏳")
    print(f"   Completion rate: {stats['completion_rate']:.1f}%")
    print()


def repl_loop(manager: ExerciseManager):
    """Run the interactive REPL loop."""
    print_banner()

    stats = manager.get_statistics()
    print_statistics(stats)

    if stats["unsolved"] == 0:
        print("🎉 Congratulations! All exercises are completed!")
        return

    print("Commands:")
    print("  [Enter] - Get a random unsolved exercise")
    print("  'done'  - Mark the current exercise as completed")
    print("  'stats' - Show statistics")
    print("  'list'  - List all unsolved exercises")
    print("  'pick'  - Pick a specific exercise by name")
    print("  'quit' or 'exit' - Exit the program")
    print()

    current_exercise = None  # Track the currently displayed exercise

    while True:
        try:
            user_input = input(">>> ").strip().lower()

            if user_input in ["quit", "exit", "q"]:
                print("\n👋 Goodbye! Good luck with your exercises!")
                break

            elif user_input == "stats":
                stats = manager.get_statistics()
                print_statistics(stats)

            elif user_input == "done":
                if current_exercise is None:
                    print(
                        "\n⚠️  No exercise to mark as done. Get an exercise first by pressing [Enter]."
                    )
                    print()
                elif current_exercise.is_completed:
                    print("\n✓ This exercise is already marked as completed.")
                    print()
                else:
                    # Mark as completed (rating was already saved when exercise was shown)
                    success = manager.mark_as_completed(current_exercise)
                    if success:
                        print(f"\n✅ Marked as completed: {current_exercise}")
                        current_exercise = None  # Reset current exercise

                        # Show updated statistics
                        stats = manager.get_statistics()
                        if stats["unsolved"] == 0:
                            print("🎉 Congratulations! All exercises are completed!")
                            break
                        else:
                            print(f"   {stats['unsolved']} exercise(s) remaining.")
                            print()
                    else:
                        print("\n❌ Failed to mark exercise as completed.")
                        print()

            elif user_input == "list":
                unsolved = manager.get_unsolved_exercises()
                if not unsolved:
                    print("\n🎉 All exercises are completed!")
                else:
                    print(f"\n📝 Unsolved exercises ({len(unsolved)}):")
                    for i, ex in enumerate(unsolved, 1):
                        print(f"   {i}. {ex}")
                print()

            elif user_input == "" or user_input == "next":
                # Get random unsolved exercise
                exercise = manager.get_random_unsolved()
                if exercise:
                    current_exercise = exercise  # Store the current exercise
                    print(f"\n🎯 Next exercise: {exercise}")
                    print()

                    # Prompt for rating every time an exercise is shown
                    while True:
                        try:
                            rating_input = input(
                                "Rate your performance on this exercise (1-5, where 5 is the worst): "
                            ).strip()
                            rating = int(rating_input)
                            if 1 <= rating <= 5:
                                current_exercise.rating = rating
                                # Save rating immediately
                                if rating == 1:
                                    # Auto-mark as completed if rated 1
                                    manager.mark_as_completed(current_exercise)
                                    print(
                                        f"✅ Automatically marked as completed (Rating: 1)"
                                    )
                                    current_exercise = None
                                else:
                                    # Just save the rating
                                    manager.save_rating(current_exercise)
                                    print(f"💾 Rating saved: {rating}")
                                break
                            else:
                                print(
                                    "Invalid input. Please enter a number between 1 and 5."
                                )
                        except ValueError:
                            print("Invalid input. Please enter a valid number.")
                    print()
                else:
                    print("\n🎉 All exercises are completed!")
                    break

            elif user_input == "pick":
                exercise_input = input("Enter the exercise (Sheet - Task): ").strip()
                unsolved = manager.get_unsolved_exercises()
                # Split input into sheet and task
                if " - " in exercise_input:
                    sheet_name, task_name = exercise_input.split(" - ", 1)
                    found_exercises = [
                        ex
                        for ex in unsolved
                        if ex.sheet.lower() == sheet_name.strip().lower()
                        and ex.task == task_name.strip()
                    ]
                else:
                    found_exercises = []
                if found_exercises:
                    current_exercise = found_exercises[0]
                    print(f"\n🎯 Picked exercise: {current_exercise}")
                    print()

                    # Prompt for rating after exercise is picked
                    while True:
                        try:
                            rating_input = input(
                                "Rate your performance on this exercise (1-5, where 5 is the worst): "
                            ).strip()
                            rating = int(rating_input)
                            if 1 <= rating <= 5:
                                current_exercise.rating = rating
                                # Save rating immediately
                                if rating == 1:
                                    # Auto-mark as completed if rated 1
                                    manager.mark_as_completed(current_exercise)
                                    print(
                                        f"✅ Automatically marked as completed (Rating: 1)"
                                    )
                                    current_exercise = None
                                else:
                                    # Just save the rating
                                    manager.save_rating(current_exercise)
                                    print(f"💾 Rating saved: {rating}")
                                break
                            else:
                                print(
                                    "Invalid input. Please enter a number between 1 and 5."
                                )
                        except ValueError:
                            print("Invalid input. Please enter a valid number.")
                    print()
                else:
                    print(f"\n❌ Exercise '{exercise_input}' not found.")
                    print()

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Good luck with your exercises!")
            break
        except EOFError:
            print("\n\n👋 Goodbye! Good luck with your exercises!")
            break


def main():
    """Main entry point."""
    # Load environment variables from .env file
    try:
        load_dotenv()
    except Exception as e:
        print(f"Error loading .env file: {e}")

    # Get markdown file path from environment variable
    markdown_file = os.getenv("EXERCISE_FILE")

    if not markdown_file:
        print("❌ Error: EXERCISE_FILE environment variable not set!")
        print("\nPlease create a .env file with:")
        print("  EXERCISE_FILE=path/to/your/exercises.md")
        print("\nOr set the environment variable directly:")
        print("  export EXERCISE_FILE=path/to/your/exercises.md")
        return 1

    try:
        manager = ExerciseManager(markdown_file)
        repl_loop(manager)
        return 0

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
