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


def _exercise_parent(title: str) -> str:
    """Return the parent key (sheet.exercise), stripping any sub-exercise suffix.

    Titles with 3+ dot-separated parts (e.g. '1.1.a', '2.3.1') have a
    sub-exercise; the parent is the first two parts ('1.1', '2.3').
    Titles with 2 parts (e.g. '1.1') have no sub-exercise and are their own parent.
    """
    parts = title.split(".")
    if len(parts) >= 3:
        return f"{parts[0]}.{parts[1]}"
    return title


def next_exercise(
    exercises: list[Exercise],
    trials_by_exercise: dict[int, list[Trial]],
) -> Exercise | None:
    """
    Priority pick — randomised at the exercise level, ordered within sub-exercises.

    Priority (ascending sort key, smallest = first pick):
    1. Higher exercise.priority first (negated so larger = smaller key).
    2. Untried exercises before tried ones.
    3. Fewest trials.
    4. Worst (highest) latest grade — grade 5 means hardest.

    Among all tied candidates a random *parent exercise* (sheet.exercise) is
    chosen uniformly, then the first sub-exercise of that parent in title order
    is returned.  This ensures 1.1.a is always picked before 1.1.b while still
    randomising across different exercises.
    """
    if not exercises:
        return None

    def sort_key(ex: Exercise) -> tuple:
        trials = sorted(
            trials_by_exercise.get(ex.id, []), key=lambda t: t.timestamp
        )
        if not trials:
            return (-ex.priority, 0, 0, 0)
        latest = trials[-1].grade
        # Negate grade so grade-5 (worst) maps to -5 (smallest → first).
        return (-ex.priority, 1, len(trials), -latest)

    best_key = min(sort_key(ex) for ex in exercises)
    candidates = [ex for ex in exercises if sort_key(ex) == best_key]

    untried = best_key[1] == 0
    if untried:
        # No trial data yet — pick deterministically by title so exercises are
        # always introduced in a consistent order.
        return min(candidates, key=lambda ex: ex.title)

    # Group candidates by parent exercise, then pick a random parent.
    groups: dict[str, list[Exercise]] = {}
    for ex in candidates:
        parent = _exercise_parent(ex.title)
        groups.setdefault(parent, []).append(ex)

    chosen_group = random.choice(list(groups.values()))
    # Within the group always take the first sub-exercise in title order.
    return min(chosen_group, key=lambda ex: ex.title)


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
