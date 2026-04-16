# tunashake

A local CLI study tool for math and physics exercises.

Track exercises by course, record attempt grades, open solutions, and always know which exercise to practice next.

---

## Installation

```bash
pip install -e ".[dev]"
```

---

## Usage

```bash
# Create a course
tunashake course create "Course QFT"
tunashake course list

# Add exercises
tunashake exercise add --course "Course QFT" --title 1.3.a
tunashake exercise add --course "Course QFT" --title 2.1.b --solution-path file:///home/user/sol.pdf
tunashake exercise list --course "Course QFT"

# Inspect an exercise
tunashake exercise show --course "Course QFT" --title 1.3.a

# Record an attempt
tunashake trial add --course "Course QFT" --title 1.3.a --grade 4 --note "Needed one hint"

# Open solution
tunashake exercise open-solution --course "Course QFT" --title 2.1.b

# Get next recommended exercise
tunashake exercise next --course "Course QFT"

# Course statistics
tunashake stats show --course "Course QFT"
```

---

## Data model

| Entity   | Fields                                                  |
|----------|---------------------------------------------------------|
| Course   | id, name (unique)                                       |
| Exercise | id, course_id, title (unique per course), solution_path |
| Trial    | id, exercise_id, grade (1–5), timestamp, note           |

**Exercise title format:** `Sheet.Number.Subexercise`  
Examples: `1.3.a`, `4.12.b`, `2.5.1`

**Grade scale:** 1 = very easy, 5 = very hard / couldn't do it.

Data is stored in `~/.local/share/tunashake/tunashake.db` (SQLite).  
Override with `TUNASHAKE_DB=/path/to/file.db tunashake ...`.

---

## Next-exercise logic

The `exercise next` command recommends the exercise most in need of practice using this priority:

1. **Untried exercises first** — if you've never attempted it, it goes to the top.
2. **Fewest trials** — prefer exercises you've attempted less.
3. **Worst latest grade** — among exercises with equal trial counts, prefer the one you found hardest most recently (grade 5 = hardest).
4. **Title** — alphabetical, for deterministic tie-breaking.

The logic lives in `src/tunashake/services.py:next_exercise` and is fully pure (no DB calls), making it easy to test and reason about.

---

## Running tests

```bash
pytest
```
