import pytest
from tunashake.validation import validate_course_name, validate_grade, validate_title


class TestValidateTitle:
    def test_valid_titles(self):
        for t in ["1.3.a", "4.12.b", "2.5.1", "10.1.abc", "1.1.A"]:
            assert validate_title(t) == t

    def test_rejects_missing_subexercise(self):
        with pytest.raises(ValueError, match="Invalid title"):
            validate_title("1.3")

    def test_rejects_non_integer_sheet(self):
        with pytest.raises(ValueError):
            validate_title("a.3.b")

    def test_rejects_spaces(self):
        with pytest.raises(ValueError):
            validate_title("1. 3.a")

    def test_rejects_empty(self):
        with pytest.raises(ValueError):
            validate_title("")

    def test_rejects_extra_dots(self):
        with pytest.raises(ValueError):
            validate_title("1.3.a.b")


class TestValidateGrade:
    def test_valid_grades(self):
        for g in [1, 2, 3, 4, 5]:
            assert validate_grade(g) == g

    def test_rejects_zero(self):
        with pytest.raises(ValueError):
            validate_grade(0)

    def test_rejects_six(self):
        with pytest.raises(ValueError):
            validate_grade(6)

    def test_rejects_bool(self):
        with pytest.raises(TypeError):
            validate_grade(True)

    def test_rejects_negative(self):
        with pytest.raises(ValueError):
            validate_grade(-1)


class TestValidateCourseName:
    def test_valid_name(self):
        assert validate_course_name("Course QFT") == "Course QFT"

    def test_strips_whitespace(self):
        assert validate_course_name("  Physics  ") == "Physics"

    def test_rejects_empty(self):
        with pytest.raises(ValueError):
            validate_course_name("")

    def test_rejects_whitespace_only(self):
        with pytest.raises(ValueError):
            validate_course_name("   ")
