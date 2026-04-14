#!/usr/bin/env python3
"""
Random Exercise Picker
Reads a markdown TODO file and provides random unsolved exercises in a REPL loop.
"""

import random
import re
from pathlib import Path
from typing import List, Optional

from shared.exercise import Exercise


class ExerciseManager:
    """Manages exercises from a markdown TODO file."""

    def __init__(self, markdown_file_path: str):
        self.file_path = Path(markdown_file_path)
        self.exercises: List[Exercise] = []
        self._load_exercises()

    def _load_exercises(self):
        """Load and parse exercises from the markdown file."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {self.file_path}")

        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Pattern to match markdown checklist items
        # Matches: - [ ] or - [x] followed by content
        # More flexible pattern that handles various markdown styles:
        # - Supports -, *, + as bullet markers
        # - Handles optional spaces around the checkbox marker
        # - Case-insensitive for x/X
        pattern = re.compile(r"^[-*+]\s*\[\s*([xX\s])\s*\]\s*(.+)$", re.IGNORECASE)

        for line in lines:
            line = line.strip()
            match = pattern.match(line)

            if match:
                checkbox_state = match.group(1).strip()
                content = match.group(2).strip()
                is_completed = checkbox_state.lower() == "x"

                # Parse the content to extract sheet and task
                # Expected format: "<Sheet name> - <task details>"
                parts = content.split(" - ", 1)
                if len(parts) == 2:
                    sheet = parts[0].strip()
                    # Normalize exercise identifiers by removing spaces and handling various formats
                    task = re.sub(r"\s+", "", parts[1].strip())
                    task = re.sub(
                        r"(\d+)\s*\.\s*(\d+)", r"\1.\2", task
                    )  # Normalize 3 . 1 to 3.1
                    task = re.sub(
                        r"(\d+)\s*([a-zA-Z])\s*\)", r"\1\2)", task
                    )  # Normalize 3 a) to 3a)
                else:
                    # If format doesn't match, use the whole content as task
                    sheet = "Unknown"
                    task = re.sub(r"\s+", "", content)
                    task = re.sub(
                        r"(\d+)\s*\.\s*(\d+)", r"\1.\2", task
                    )  # Normalize 3 . 1 to 3.1
                    task = re.sub(
                        r"(\d+)\s*([a-zA-Z])\s*\)", r"\1\2)", task
                    )  # Normalize 3 a) to 3a)

                exercise = Exercise(
                    raw_line=line, is_completed=is_completed, sheet=sheet, task=task
                )
                self.exercises.append(exercise)

    def get_unsolved_exercises(self) -> List[Exercise]:
        """Return list of all unsolved exercises."""
        return [ex for ex in self.exercises if not ex.is_completed]

    def get_random_unsolved(self) -> Optional[Exercise]:
        """Return a random unsolved exercise, or None if all are completed, with preference given to those with higher (worse) ratings."""
        unsolved = self.get_unsolved_exercises()
        if not unsolved:
            return None

        # Group exercises by their sheet and main task identifier
        exercise_groups = {}
        for ex in unsolved:
            main_task = ex.task.split(".")[
                0
            ]  # Extract main task level, e.g., '3' from '3.1'
            if main_task not in exercise_groups:
                exercise_groups[main_task] = []
            exercise_groups[main_task].append(ex)

        # Calculate average ratings for each group
        weighted_groups = []
        for group in exercise_groups.values():
            avg_rating = sum(ex.rating for ex in group) / len(group)
            weighted_groups.append((group, avg_rating))

        # Create a weighted list based on average ratings
        weighted_exercises = [
            ex
            for group, avg_rating in weighted_groups
            for ex in group
            for _ in range(int(avg_rating))
        ]

        return random.choice(weighted_exercises)

    def get_statistics(self) -> dict:
        """Return statistics about exercises."""
        total = len(self.exercises)
        completed = sum(1 for ex in self.exercises if ex.is_completed)
        unsolved = total - completed

        return {
            "total": total,
            "completed": completed,
            "unsolved": unsolved,
            "completion_rate": (completed / total * 100) if total > 0 else 0,
        }

    def save_rating(self, exercise: Exercise) -> bool:
        """Save the rating for an exercise to the file without marking it as completed."""
        try:
            # Read the file
            with open(self.file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Find and update the line
            modified = False
            for i, line in enumerate(lines):
                stripped_line = line.strip()
                # Remove existing rating if present
                stripped_line_no_rating = re.sub(
                    r"\s*\(Rating:\s*\d+\)\s*$", "", stripped_line
                )
                exercise_line_no_rating = re.sub(
                    r"\s*\(Rating:\s*\d+\)\s*$", "", exercise.raw_line
                )

                if (
                    stripped_line_no_rating == exercise_line_no_rating
                    or stripped_line == exercise.raw_line
                ):
                    # Remove existing rating from the line if present
                    new_line = re.sub(r"\s*\(Rating:\s*\d+\)\s*$", "", line.rstrip())
                    # Append new rating to the end of the task line
                    new_line = new_line + f" (Rating: {exercise.rating})\n"
                    lines[i] = new_line
                    modified = True
                    break

            if not modified:
                return False

            # Write back to file
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            # Reload exercises
            self.exercises.clear()
            self._load_exercises()

            return True

        except Exception as e:
            print(f"Error saving rating: {e}")
            return False

    def mark_as_completed(self, exercise: Exercise) -> bool:
        """Mark an exercise as completed in the file and reload exercises."""
        if exercise.is_completed:
            return False  # Already completed

        try:
            # Read the file
            with open(self.file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Find and update the line
            modified = False
            for i, line in enumerate(lines):
                stripped_line = line.strip()
                # Remove existing rating if present for comparison
                stripped_line_no_rating = re.sub(
                    r"\s*\(Rating:\s*\d+\)\s*$", "", stripped_line
                )
                exercise_line_no_rating = re.sub(
                    r"\s*\(Rating:\s*\d+\)\s*$", "", exercise.raw_line
                )

                if (
                    stripped_line_no_rating == exercise_line_no_rating
                    or stripped_line == exercise.raw_line
                ):
                    # Replace [ ] with [x]
                    # Handle various formats: - [ ], -[ ], * [ ], etc.
                    new_line = re.sub(r"(\[-*\+\]\s*)\[\s*\]", r"\1[x]", line)
                    if new_line == line:
                        # Try more specific replacement
                        new_line = line.replace("[ ]", "[x]", 1)

                    # Remove existing rating if present
                    new_line = re.sub(
                        r"\s*\(Rating:\s*\d+\)\s*$", "", new_line.rstrip()
                    )
                    # Append rating to the end of the task line
                    new_line = new_line + f" (Rating: {exercise.rating})\n"

                    lines[i] = new_line
                    modified = True
                    break

            if not modified:
                return False

            # Write back to file
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            # Reload exercises
            self.exercises.clear()
            self._load_exercises()

            return True

        except Exception as e:
            print(f"Error marking exercise as completed: {e}")
            return False
