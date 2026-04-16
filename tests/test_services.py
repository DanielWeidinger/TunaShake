from datetime import datetime, timezone

import pytest

from tunashake.models import Exercise, Trial
from tunashake.services import STRATEGIES, next_exercise, weighted_grade, weighted_trials, course_stats


def make_exercise(eid: int, title: str) -> Exercise:
    return Exercise(id=eid, course_id=1, title=title)


def make_trial(tid: int, exercise_id: int, grade: int, ts_offset: int = 0) -> Trial:
    ts = datetime(2024, 1, 1, 0, ts_offset, tzinfo=timezone.utc)
    return Trial(id=tid, exercise_id=exercise_id, grade=grade, timestamp=ts)


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

    def test_title_tiebreaker(self):
        ex1 = make_exercise(1, "1.2.a")
        ex2 = make_exercise(2, "1.1.a")
        trials = {
            1: [make_trial(1, 1, 3)],
            2: [make_trial(2, 2, 3)],
        }
        result = next_exercise([ex1, ex2], trials)
        assert result is ex2  # "1.1.a" < "1.2.a"

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
