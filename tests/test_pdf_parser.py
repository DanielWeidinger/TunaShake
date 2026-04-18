"""
Tests for pdf_parser — unit tests for each style and integration tests against
the example PDFs.
"""

from tunashake.pdf_parser import (
    _parse_generic_style,
    _parse_qft_style,
    _parse_sh_style,
    detect_sheet_number,
    parse_exercises,
)

EXAMPLES = "examples"


# ── unit tests: _parse_qft_style ───────────────────────────────────────────────

class TestParseQftStyle:
    def test_basic(self):
        lines = ["1.1 Show that", "1.2 Compute", "2.1 Prove"]
        assert _parse_qft_style(lines, 3) == ["3.1.1", "3.1.2", "3.2.1"]

    def test_ignores_non_matching_lines(self):
        lines = ["Exercise 1 - Title", "Some text", "1.1 Sub"]
        assert _parse_qft_style(lines, 1) == ["1.1.1"]

    def test_empty_input(self):
        assert _parse_qft_style([], 1) == []

    def test_does_not_match_middle_of_line(self):
        lines = ["a lifetime of τ = 1.5 µs, they can be created"]
        assert _parse_qft_style(lines, 1) == []

    def test_does_not_match_ordinal_list_items(self):
        # "1. Text" has a space after the dot, not a digit → no match
        lines = ["1. What condition", "2. Find the form"]
        assert _parse_qft_style(lines, 1) == []


# ── unit tests: _parse_generic_style ──────────────────────────────────────────

class TestParseGenericStyle:
    def test_exercise_header_with_ordinal_subs(self):
        lines = [
            "Exercise 1 - Title",
            "1. First sub",
            "2. Second sub",
            "Exercise 2 - Another",
            "1. Only sub",
        ]
        assert _parse_generic_style(lines, 2) == ["2.1.1", "2.1.2", "2.2.1"]

    def test_problem_header_with_bracket_subs(self):
        lines = [
            "Problem 1 Title",
            "[a] First sub",
            "[b] Second sub",
            "Problem 2 No subs",
        ]
        assert _parse_generic_style(lines, 1) == ["1.1.a", "1.1.b", "1.2"]

    def test_problem_header_with_bare_letter_paren_subs(self):
        lines = [
            "Problem 2 Title",
            "a) First sub",
            "b) Second sub",
        ]
        assert _parse_generic_style(lines, 6) == ["6.2.a", "6.2.b"]

    def test_mixed_headers_across_blocks(self):
        # Exercise + Problem can appear on the same sheet (Sheet 6)
        lines = [
            "Exercise 1 - Title",
            "1. Sub one",
            "2. Sub two",
            "Problem 2 - Title",
            "a) Sub a",
            "b) Sub b",
        ]
        assert _parse_generic_style(lines, 6) == [
            "6.1.1", "6.1.2", "6.2.a", "6.2.b"
        ]

    def test_pattern_locked_per_block(self):
        # Once ordinal "1." is seen, nested "(a)" items in the same block
        # must NOT be captured as additional sub-exercises.
        lines = [
            "Exercise 1 - Title",
            "1. First sub",
            "2. Second sub",
            "(a) Nested inside sub 2 — should be ignored",
            "(b) Also nested — should be ignored",
        ]
        assert _parse_generic_style(lines, 2) == ["2.1.1", "2.1.2"]

    def test_exercise_without_sub_exercises(self):
        lines = ["Exercise 5 - No subs", "Some prose text"]
        assert _parse_generic_style(lines, 2) == ["2.5"]

    def test_returns_empty_without_header(self):
        # S/H-style content should not trigger this parser
        lines = ["S 1 Title", "(a) Sub", "(b) Sub"]
        assert _parse_generic_style(lines, 1) == []

    def test_ignores_subs_before_first_header(self):
        lines = ["1. Orphan ordinal", "Problem 1 Title", "1. Real sub"]
        assert _parse_generic_style(lines, 1) == ["1.1.1"]

    def test_deduplicates_repeated_sub_labels(self):
        lines = ["Problem 1 Title", "[a] First", "[a] Duplicate (PDF reflow)"]
        assert _parse_generic_style(lines, 1) == ["1.1.a"]

    def test_case_insensitive_header(self):
        lines = ["EXERCISE 1 Title", "1. Sub", "PROBLEM 2 Title", "a) Sub"]
        assert _parse_generic_style(lines, 1) == ["1.1.1", "1.2.a"]


# ── unit tests: _parse_sh_style ───────────────────────────────────────────────

class TestParseShStyle:
    def test_basic(self):
        lines = [
            "S 1 Title",
            "(a) How are",
            "(b) Does a",
            "H 1 Homework",
            "(a) Solve",
        ]
        assert _parse_sh_style(lines, 1) == ["1.1.a", "1.1.b", "1.2.a"]

    def test_empty_input(self):
        assert _parse_sh_style([], 1) == []


# ── integration tests: sheet number detection ─────────────────────────────────

class TestDetectSheetNumber:
    def test_sheet1(self):
        assert detect_sheet_number(f"{EXAMPLES}/sheet1.pdf") == 1

    def test_exercise_sheet_1(self):
        assert detect_sheet_number(f"{EXAMPLES}/Exercise_sheet_1.pdf") == 1

    def test_qft_sheet_2(self):
        assert detect_sheet_number(f"{EXAMPLES}/QFT_Exercise-Sheet_2.pdf") == 2

    def test_qft_sheet_3(self):
        assert detect_sheet_number(f"{EXAMPLES}/QFT_Exercise-Sheet_3.pdf") == 3

    def test_qft_sheet_4(self):
        assert detect_sheet_number(f"{EXAMPLES}/QFT_Exercise-Sheet_4.pdf") == 4

    def test_qft_sheet_6(self):
        assert detect_sheet_number(f"{EXAMPLES}/QFT_Exercise-Sheet_6.pdf") == 6


# ── integration tests: exercise parsing ───────────────────────────────────────

class TestParseExercises:
    def test_sheet1_problem_style(self):
        result = parse_exercises(f"{EXAMPLES}/sheet1.pdf", 1)
        assert result == [
            "1.1.a", "1.1.b",
            "1.2.a", "1.2.b",
            "1.3",
            "1.4",
            "1.5.a", "1.5.b", "1.5.c",
        ]

    def test_exercise_sheet_1_sh_style(self):
        result = parse_exercises(f"{EXAMPLES}/Exercise_sheet_1.pdf", 1)
        assert result[:4] == ["1.1.a", "1.1.b", "1.1.c", "1.1.d"]
        assert "1.2.a" in result
        assert "1.7.c" in result
        assert len(result) == 24

    def test_qft_sheet_2_exercise_list_style(self):
        result = parse_exercises(f"{EXAMPLES}/QFT_Exercise-Sheet_2.pdf", 2)
        assert result[:6] == ["2.1.1", "2.1.2", "2.1.3", "2.1.4", "2.1.5", "2.1.6"]
        assert "2.2.5" in result
        assert "2.3.7" in result
        assert "2.4.6" in result
        assert "2.5" in result
        # nested (a)/(b) inside Exercise 1 sub-6 must NOT appear
        assert "2.1.a" not in result
        assert "2.1.b" not in result

    def test_qft_sheet_3_qft_style(self):
        result = parse_exercises(f"{EXAMPLES}/QFT_Exercise-Sheet_3.pdf", 3)
        assert "3.1.1" in result
        assert "3.1.3" in result
        assert "3.3.1" in result
        assert "3.4.7" in result

    def test_qft_sheet_4_qft_style(self):
        result = parse_exercises(f"{EXAMPLES}/QFT_Exercise-Sheet_4.pdf", 4)
        assert "4.1.1" in result
        assert "4.5.9" in result
        assert "4.6.2" in result

    def test_qft_sheet_6_mixed_style(self):
        result = parse_exercises(f"{EXAMPLES}/QFT_Exercise-Sheet_6.pdf", 6)
        # Exercise 1: 5 numbered sub-exercises
        assert result[:5] == ["6.1.1", "6.1.2", "6.1.3", "6.1.4", "6.1.5"]
        # Problem 2: a) and b) letter-paren sub-exercises
        assert "6.2.a" in result
        assert "6.2.b" in result
        # Exercise 3: 4 numbered sub-exercises
        assert "6.3.1" in result
        assert "6.3.4" in result
        # Exercise 4: 5 numbered sub-exercises
        assert "6.4.1" in result
        assert "6.4.5" in result

    def test_deduplication(self):
        for f, s in [
            (f"{EXAMPLES}/sheet1.pdf", 1),
            (f"{EXAMPLES}/QFT_Exercise-Sheet_6.pdf", 6),
        ]:
            result = parse_exercises(f, s)
            assert len(result) == len(set(result)), f"Duplicates in {f}"
