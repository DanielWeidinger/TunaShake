# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

TunaShake is a Python CLI tool that picks random exercises from a markdown checklist file. It runs an interactive REPL where the user rates their performance (1–5, worse = higher), marks exercises done, and the picker uses those ratings to weight future selections toward harder exercises.

## Running the app

```bash
# Install dependency
pip install -r requirements.txt

# Configure the exercises file path
cp .env.example .env
# Edit .env: EXERCISE_FILE=path/to/exercises.md

# Run the REPL
python run.py

# Diagnostic tool (if exercises aren't loading correctly)
python utils/analyze_file.py
```

## Architecture

The app has three layers:

**`shared/exercise.py`** — `Exercise` dataclass: `sheet`, `task`, `is_completed`, `rating` (default 3), `raw_line`. Task identifiers are normalized on load (whitespace stripped, `3 . 1` → `3.1`, `3 a)` → `3a)`).

**`exercise_manager.py`** — `ExerciseManager`: parses the markdown file on init, holds all exercises in memory. All mutations (`mark_as_completed`, `save_rating`) write directly back to the markdown file and then reload from disk. Weighted random selection groups exercises by top-level task number and weights by average group rating.

**`run.py`** — REPL loop. Commands: Enter/`next` (random exercise + prompt for rating), `done` (mark current as completed), `stats`, `list`, `pick` (select specific exercise by `Sheet - Task`), `quit`/`exit`/`q`. Rating 1 auto-marks the exercise as completed.

## Exercise file format

```markdown
- [ ] Sheet1 - 1a)
- [x] Sheet1 - 2 (Rating: 2)
- [ ] Sheet2 - 1.1
```

Bullet markers `-`, `*`, `+` all work. The parser is flexible with spacing inside `[ ]`. Ratings are appended inline as `(Rating: N)` and stripped/replaced on update.

## State persistence

There is no database. The markdown file is the source of truth. `ExerciseManager` matches lines by `raw_line` (with rating suffix stripped for comparison) to find which line to update in-place.
