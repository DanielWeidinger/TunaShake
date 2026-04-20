from datetime import datetime, timezone

import pytest

from tunashake.models import Exercise, Trial
from tunashake.services import STRATEGIES, _exercise_parent, next_exercise, weighted_grade, weighted_trials, course_stats


def make_exercise(eid: int, title: str) -> Exercise:
    return Exercise(id=eid, course_id=1, title=title)


def make_trial(tid: int, exercise_id: int, grade: int, ts_offset: int = 0) -> Trial:
    ts = datetime(2024, 1, 1, 0, ts_offset, tzinfo=timezone.utc)
    return Trial(id=tid, exercise_id=exercise_id, grade=grade, timestamp=ts)


class TestExerciseParent:
    def test_three_part_title(self):
        assert _exercise_parent("1.1.a") == "1.1"
        assert _exercise_parent("2.3.1") == "2.3"

    def test_two_part_title(self):
        assert _exercise_parent("1.1") == "1.1"

    def test_four_part_title(self):
        assert _exercise_parent("1.1.a.i") == "1.1"


class TestNextExercise:
    def test_returns_none_for_empty_list(self):
        assert next_exercise([], {}) is None

    def test_prefers_untried(self):
        ex1 = make_exercise(1, "1.1.a")
        ex2 = make_exercise(2, "1.2.a")
        trials = {1: [make_trial(1, 1, 3)]}
        result = next_exercise([ex1, ex2], trials)
        assert result is ex2

    def test_prefers_fewer_trials(self):
        ex1 = make_exercise(1, "1.1.a")
        ex2 = make_exercise(2, "1.2.a")
        trials = {
            1: [make_trial(1, 1, 2), make_trial(2, 1, 2)],
            2: [make_trial(3, 2, 2)],
        }
        result = next_exercise([ex1, ex2], trials)
        assert result is ex2

    def test_prefers_worse_grade_among_equal_trials(self):
        ex1 = make_exercise(1, "1.1.a")
        ex2 = make_exercise(2, "1.2.a")
        trials = {
            1: [make_trial(1, 1, 2)],
            2: [make_trial(2, 2, 4)],
        }
        result = next_exercise([ex1, ex2], trials)
        assert result is ex2  # grade 4 is worse

    def test_sub_exercise_ordering(self):
        """1.1.a must always be picked before 1.1.b when they are tied."""
        ex_a = make_exercise(1, "1.1.a")
        ex_b = make_exercise(2, "1.1.b")
        # Run many times to confirm determinism despite internal randomisation.
        for _ in range(20):
            result = next_exercise([ex_a, ex_b], {})
            assert result is ex_a

    def test_untried_picks_deterministically_by_title(self):
        """With no trials, always pick the smallest title — no randomisation."""
        ex_11a = make_exercise(1, "1.1.a")
        ex_12a = make_exercise(2, "1.2.a")
        for _ in range(20):
            assert next_exercise([ex_11a, ex_12a], {}) is ex_11a

    def test_randomises_across_exercise_groups_when_tried(self):
        """Once exercises have trials, randomise at the parent-exercise level."""
        ex_11a = make_exercise(1, "1.1.a")
        ex_12a = make_exercise(2, "1.2.a")
        trials = {
            1: [make_trial(1, 1, 3)],
            2: [make_trial(2, 2, 3)],
        }
        seen = set()
        for _ in range(200):
            r = next_exercise([ex_11a, ex_12a], trials)
            assert r is not None
            seen.add(r.id)
        assert seen == {1, 2}

    def test_latest_trial_is_used_not_first(self):
        """If a student improves over time, use the most recent grade."""
        ex1 = make_exercise(1, "1.1.a")
        ex2 = make_exercise(2, "1.2.a")
        # ex1: started hard (5), then got easier (1) → latest grade 1
        # ex2: always grade 3
        trials = {
            1: [make_trial(1, 1, 5, ts_offset=0), make_trial(2, 1, 1, ts_offset=1)],
            2: [make_trial(3, 2, 3)],
        }
        result = next_exercise([ex1, ex2], trials)
        assert result is ex2  # ex2 latest grade 3 is worse than ex1 latest grade 1

    def test_single_exercise(self):
        ex = make_exercise(1, "1.1.a")
        assert next_exercise([ex], {}) is ex


class TestCourseStats:
    def test_empty(self):
        stats = course_stats([], {})
        assert stats["total_exercises"] == 0
        assert stats["untried_exercises"] == 0
        assert stats["total_trials"] == 0
        assert stats["avg_grade"] is None

    def test_counts(self):
        ex1 = make_exercise(1, "1.1.a")
        ex2 = make_exercise(2, "1.2.a")
        trials = {1: [make_trial(1, 1, 4), make_trial(2, 1, 2)]}
        stats = course_stats([ex1, ex2], trials)
        assert stats["total_exercises"] == 2
        assert stats["untried_exercises"] == 1
        assert stats["total_trials"] == 2
        assert stats["avg_grade"] == 3.0


class TestWeightedStrategies:
    def test_weighted_grade_returns_exercise(self):
        exercises = [make_exercise(1, "1.1.a"), make_exercise(2, "1.2.a")]
        result = weighted_grade(exercises, {})
        assert result in exercises

    def test_weighted_grade_returns_none_for_empty(self):
        assert weighted_grade([], {}) is None

    def test_weighted_grade_single_exercise(self):
        ex = make_exercise(1, "1.1.a")
        assert weighted_grade([ex], {}) is ex

    def test_weighted_trials_returns_exercise(self):
        exercises = [make_exercise(1, "1.1.a"), make_exercise(2, "1.2.a")]
        result = weighted_trials(exercises, {})
        assert result in exercises

    def test_weighted_trials_returns_none_for_empty(self):
        assert weighted_trials([], {}) is None

    def test_weighted_trials_single_exercise(self):
        ex = make_exercise(1, "1.1.a")
        assert weighted_trials([ex], {}) is ex

    def test_strategies_registry_contains_all(self):
        assert "priority" in STRATEGIES
        assert "weighted-grade" in STRATEGIES
        assert "weighted-trials" in STRATEGIES

    def test_strategies_registry_are_callable(self):
        ex = make_exercise(1, "1.1.a")
        for name, fn in STRATEGIES.items():
            result = fn([ex], {})
            assert result is ex, f"Strategy '{name}' failed"
