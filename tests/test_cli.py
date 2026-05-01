import pytest
from typer.testing import CliRunner

from tunashake.cli import app

runner = CliRunner()


def test_course_create_and_list():
    result = runner.invoke(app, ["course", "create", "Linear Algebra"])
    assert result.exit_code == 0
    assert "Linear Algebra" in result.output

    result = runner.invoke(app, ["course", "list"])
    assert result.exit_code == 0
    assert "Linear Algebra" in result.output


def test_course_create_duplicate():
    runner.invoke(app, ["course", "create", "QFT"])
    result = runner.invoke(app, ["course", "create", "QFT"])
    assert result.exit_code == 1
    assert "already exists" in result.output


def test_exercise_add_and_list():
    runner.invoke(app, ["course", "create", "Mechanics"])
    result = runner.invoke(app, ["exercise", "add", "--course", "Mechanics", "--title", "1.3.a"])
    assert result.exit_code == 0
    assert "1.3.a" in result.output

    result = runner.invoke(app, ["exercise", "list", "--course", "Mechanics"])
    assert result.exit_code == 0
    assert "1.3.a" in result.output


def test_exercise_add_invalid_title():
    runner.invoke(app, ["course", "create", "Mechanics"])
    result = runner.invoke(app, ["exercise", "add", "--course", "Mechanics", "--title", "bad-title"])
    assert result.exit_code == 1
    assert "Invalid title" in result.output


def test_exercise_show():
    runner.invoke(app, ["course", "create", "Mechanics"])
    runner.invoke(app, ["exercise", "add", "--course", "Mechanics", "--title", "2.1.b",
                        "--solution-path", "file:///tmp/sol.pdf"])
    result = runner.invoke(app, ["exercise", "show", "--course", "Mechanics", "--title", "2.1.b"])
    assert result.exit_code == 0
    assert "2.1.b" in result.output
    assert "file:///tmp/sol.pdf" in result.output


def test_trial_add_and_show():
    runner.invoke(app, ["course", "create", "Mechanics"])
    runner.invoke(app, ["exercise", "add", "--course", "Mechanics", "--title", "1.1.a"])
    result = runner.invoke(app, [
        "trial", "add", "--course", "Mechanics", "--title", "1.1.a",
        "--grade", "4", "--note", "Needed one hint"
    ])
    assert result.exit_code == 0
    assert "grade=4" in result.output

    result = runner.invoke(app, ["exercise", "show", "--course", "Mechanics", "--title", "1.1.a"])
    assert result.exit_code == 0
    assert "Needed one hint" in result.output


def test_trial_invalid_grade():
    runner.invoke(app, ["course", "create", "Mechanics"])
    runner.invoke(app, ["exercise", "add", "--course", "Mechanics", "--title", "1.1.a"])
    result = runner.invoke(app, [
        "trial", "add", "--course", "Mechanics", "--title", "1.1.a", "--grade", "6"
    ])
    assert result.exit_code == 1
    assert "Grade" in result.output


def test_next_exercise():
    runner.invoke(app, ["course", "create", "QFT"])
    runner.invoke(app, ["exercise", "add", "--course", "QFT", "--title", "1.1.a"])
    runner.invoke(app, ["exercise", "add", "--course", "QFT", "--title", "1.2.a"])
    result = runner.invoke(app, ["exercise", "next", "--course", "QFT"])
    assert result.exit_code == 0
    assert "Next exercise" in result.output


@pytest.mark.parametrize("strategy", ["priority", "weighted-grade", "weighted-trials"])
def test_next_exercise_strategies(strategy):
    runner.invoke(app, ["course", "create", "QFT"])
    runner.invoke(app, ["exercise", "add", "--course", "QFT", "--title", "1.1.a"])
    result = runner.invoke(app, ["exercise", "next", "--course", "QFT", "--strategy", strategy])
    assert result.exit_code == 0
    assert "Next exercise" in result.output


def test_next_exercise_unknown_strategy():
    runner.invoke(app, ["course", "create", "QFT"])
    result = runner.invoke(app, ["exercise", "next", "--course", "QFT", "--strategy", "bogus"])
    assert result.exit_code == 1
    assert "Unknown strategy" in result.output


def test_stats_show():
    runner.invoke(app, ["course", "create", "QFT"])
    runner.invoke(app, ["exercise", "add", "--course", "QFT", "--title", "1.1.a"])
    runner.invoke(app, ["trial", "add", "--course", "QFT", "--title", "1.1.a", "--grade", "3"])
    result = runner.invoke(app, ["stats", "show", "--course", "QFT"])
    assert result.exit_code == 0
    assert "Total exercises" in result.output
    assert "Average grade" in result.output


def test_course_not_found():
    result = runner.invoke(app, ["exercise", "list", "--course", "Nonexistent"])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_exercise_not_found():
    runner.invoke(app, ["course", "create", "QFT"])
    result = runner.invoke(app, ["exercise", "show", "--course", "QFT", "--title", "9.9.z"])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_repl_skip_records_skipped_trial():
    runner.invoke(app, ["course", "create", "SkipTest"])
    runner.invoke(app, ["exercise", "add", "--course", "SkipTest", "--title", "1.1.a"])
    result = runner.invoke(app, ["repl", "--course", "SkipTest"], input="s\nq\n")
    assert result.exit_code == 0
    assert "Skipped" in result.output

    result = runner.invoke(app, ["exercise", "show", "--course", "SkipTest", "--title", "1.1.a"])
    assert result.exit_code == 0
    assert "skipped" in result.output


def test_repl_like_shows_in_header():
    runner.invoke(app, ["course", "create", "LikeTest"])
    runner.invoke(app, ["exercise", "add", "--course", "LikeTest", "--title", "1.1.a"])
    result = runner.invoke(app, ["repl", "--course", "LikeTest", "--like", "3.%%"], input="q\n")
    assert result.exit_code == 0
    assert "(like: 3.%%)" in result.output


def test_repl_like_restricts_to_matching_exercises():
    runner.invoke(app, ["course", "create", "LikeTest2"])
    runner.invoke(app, ["exercise", "add", "--course", "LikeTest2", "--title", "2.1.a"])
    runner.invoke(app, ["exercise", "add", "--course", "LikeTest2", "--title", "3.1.a"])
    runner.invoke(app, ["exercise", "add", "--course", "LikeTest2", "--title", "3.2.b"])
    runner.invoke(app, ["exercise", "add", "--course", "LikeTest2", "--title", "4.1.a"])
    result = runner.invoke(app, ["repl", "--course", "LikeTest2", "--like", "3.%%"], input="q\n")
    assert result.exit_code == 0
    assert "3.1.a" in result.output or "3.2.b" in result.output
    assert "2.1.a" not in result.output
    assert "4.1.a" not in result.output


def test_repl_like_and_tag_work_together():
    runner.invoke(app, ["course", "create", "LikeTagTest"])
    runner.invoke(app, ["exercise", "add", "--course", "LikeTagTest", "--title", "1.1.a"])
    runner.invoke(app, ["exercise", "add", "--course", "LikeTagTest", "--title", "2.1.a", "--tag", "hard"])
    runner.invoke(app, ["exercise", "add", "--course", "LikeTagTest", "--title", "3.1.a", "--tag", "hard"])
    result = runner.invoke(
        app, ["repl", "--course", "LikeTagTest", "--like", "3.%%", "--tag", "hard"], input="q\n"
    )
    assert result.exit_code == 0
    assert "(like: 3.%%)" in result.output
    assert "(tag: hard)" in result.output
    assert "3.1.a" in result.output
    assert "1.1.a" not in result.output
    assert "2.1.a" not in result.output
