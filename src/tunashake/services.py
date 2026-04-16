"""
Business logic — kept pure (no DB calls) for easy testing.
"""

import random
from typing import Callable

from tunashake.models import Exercise, Trial

# Type alias for any picking strategy.
StrategyFn = Callable[[list[Exercise], dict[int, list[Trial]]], "Exercise | None"]


def _latest_grade(trials: list[Trial]) -> int | None:
    """Return the grade of the most recent trial, or None if there are none."""
    if not trials:
        return None
    return sorted(trials, key=lambda t: t.timestamp)[-1].grade


def next_exercise(
    exercises: list[Exercise],
    trials_by_exercise: dict[int, list[Trial]],
) -> Exercise | None:
    """
    Deterministic pick — the exercise most in need of practice.

    Priority (ascending sort key, smallest = first pick):
    1. Higher exercise.priority first (negated so larger = smaller key).
    2. Untried exercises before tried ones.
    3. Fewest trials.
    4. Worst (highest) latest grade — grade 5 means hardest.
    5. Title for deterministic tie-breaking.
    """
    if not exercises:
        return None

    def sort_key(ex: Exercise) -> tuple:
        trials = sorted(
            trials_by_exercise.get(ex.id, []), key=lambda t: t.timestamp
        )
        if not trials:
            return (-ex.priority, 0, 0, 0, ex.title)
        latest = trials[-1].grade
        # Negate grade so grade-5 (worst) maps to -5 (smallest → first).
        return (-ex.priority, 1, len(trials), -latest, ex.title)

    return min(exercises, key=sort_key)


def weighted_grade(
    exercises: list[Exercise],
    trials_by_exercise: dict[int, list[Trial]],
) -> Exercise | None:
    """
    Weighted random pick — selection probability proportional to latest grade
    multiplied by (1 + priority).

    Grade 5 (hardest) is 5× more likely than grade 1 (easiest).
    Untried exercises use a neutral weight of 3.
    Priority multiplies the weight: priority=0 → ×1, priority=5 → ×6.
    """
    if not exercises:
        return None
    weights = [
        (_latest_grade(trials_by_exercise.get(ex.id, [])) or 3) * (1 + ex.priority)
        for ex in exercises
    ]
    return random.choices(exercises, weights=weights, k=1)[0]


def weighted_trials(
    exercises: list[Exercise],
    trials_by_exercise: dict[int, list[Trial]],
) -> Exercise | None:
    """
    Weighted random pick — selection probability inversely proportional to trial count.

    Weight = 1 / (trial_count + 1), so untried exercises (weight 1.0) are most
    likely and well-practiced ones fade into the background gradually.
    """
    if not exercises:
        return None
    weights = [
        1.0 / (len(trials_by_exercise.get(ex.id, [])) + 1)
        for ex in exercises
    ]
    return random.choices(exercises, weights=weights, k=1)[0]


# Registry of all available strategies. Keys are the CLI-facing names.
STRATEGIES: dict[str, StrategyFn] = {
    "priority":       next_exercise,
    "weighted-grade": weighted_grade,
    "weighted-trials": weighted_trials,
}


def course_stats(
    exercises: list[Exercise],
    trials_by_exercise: dict[int, list[Trial]],
) -> dict:
    """Return a stats dict for display by the CLI layer."""
    total = len(exercises)
    untried = sum(1 for ex in exercises if not trials_by_exercise.get(ex.id))
    all_trials = [t for ts in trials_by_exercise.values() for t in ts]
    total_trials = len(all_trials)
    avg_grade = (
        sum(t.grade for t in all_trials) / total_trials if all_trials else None
    )

    per_exercise = []
    for ex in exercises:
        trials = sorted(
            trials_by_exercise.get(ex.id, []), key=lambda t: t.timestamp
        )
        latest = trials[-1] if trials else None
        per_exercise.append(
            {
                "title": ex.title,
                "trial_count": len(trials),
                "latest_grade": latest.grade if latest else None,
            }
        )

    per_exercise.sort(key=lambda r: (r["latest_grade"] or 0), reverse=True)

    return {
        "total_exercises": total,
        "untried_exercises": untried,
        "total_trials": total_trials,
        "avg_grade": avg_grade,
        "per_exercise": per_exercise,
    }
