"""
tunashake CLI — built with Typer.

Command hierarchy:
  tunashake course  create / list
  tunashake exercise add / list / show / next / open-solution / open-source / import
  tunashake trial   add
  tunashake stats   show
  tunashake repl    interactive study session
"""

import subprocess
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from tunashake.db import get_connection
from tunashake.repository import (
    create_course,
    create_exercise,
    create_trial,
    get_course_by_name,
    get_exercise,
    get_trials_for_course,
    get_trials_for_exercise,
    list_courses,
    list_exercises,
    set_exercise_priority,
    set_exercise_solution,
    set_exercise_source,
)
from tunashake.services import STRATEGIES, course_stats, next_exercise
from tunashake.validation import validate_course_name, validate_grade, validate_title

console = Console()

app = typer.Typer(
    name="tunashake",
    help="Local CLI study tool for math and physics exercises.",
    no_args_is_help=True,
)
course_app = typer.Typer(help="Manage courses.", no_args_is_help=True)
exercise_app = typer.Typer(help="Manage exercises.", no_args_is_help=True)
trial_app = typer.Typer(help="Manage trials.", no_args_is_help=True)
stats_app = typer.Typer(help="Show statistics.", no_args_is_help=True)
db_app = typer.Typer(help="Raw database access.", no_args_is_help=True)

app.add_typer(course_app, name="course")
app.add_typer(exercise_app, name="exercise")
app.add_typer(trial_app, name="trial")
app.add_typer(stats_app, name="stats")
app.add_typer(db_app, name="db")


# ── helpers ────────────────────────────────────────────────────────────────────

def _abort(msg: str) -> None:
    console.print(f"[red]Error:[/red] {msg}")
    raise typer.Exit(1)


def _xdg_open(path: str) -> None:
    """Open a path or URL with xdg-open, printing errors gracefully."""
    console.print(f"Opening: {path}")
    try:
        result = subprocess.run(
            ["xdg-open", path], check=False, capture_output=True, text=True
        )
        if result.returncode != 0:
            console.print(f"[red]xdg-open failed (exit {result.returncode}):[/red] {result.stderr.strip()}")
    except FileNotFoundError:
        console.print("[red]xdg-open not found. Are you on a Linux desktop?[/red]")


def _require_course(name: str):
    conn = get_connection()
    course = get_course_by_name(conn, name)
    if not course:
        conn.close()
        _abort(f"Course '{name}' not found. Create it with: tunashake course create \"{name}\"")
    return conn, course


# ── course commands ────────────────────────────────────────────────────────────

@course_app.command("create")
def course_create(name: str = typer.Argument(..., help="Course name")):
    """Create a new course."""
    try:
        name = validate_course_name(name)
    except ValueError as e:
        _abort(str(e))

    conn = get_connection()
    try:
        course = create_course(conn, name)
        console.print(f"[green]Created course:[/green] {course.name} (id={course.id})")
    except Exception as e:
        if "UNIQUE" in str(e):
            _abort(f"Course '{name}' already exists.")
        _abort(str(e))
    finally:
        conn.close()


@course_app.command("list")
def course_list():
    """List all courses."""
    conn = get_connection()
    courses = list_courses(conn)
    conn.close()

    if not courses:
        console.print("No courses yet. Create one with: tunashake course create NAME")
        return

    table = Table("ID", "Name", show_header=True)
    for c in courses:
        table.add_row(str(c.id), c.name)
    console.print(table)


# ── exercise commands ──────────────────────────────────────────────────────────

@exercise_app.command("add")
def exercise_add(
    course: str = typer.Option(..., "--course", "-c", help="Course name"),
    title: str = typer.Option(..., "--title", "-t", help="Title (Sheet.Number.Subexercise)"),
    solution_path: Optional[str] = typer.Option(None, "--solution-path", "-s", help="Path or URL to solution"),
    source_path: Optional[str] = typer.Option(None, "--source-path", "-p", help="Path or URL to exercise source"),
    priority: int = typer.Option(0, "--priority", help="A-priori priority (higher = picked sooner)"),
):
    """Add an exercise to a course."""
    try:
        title = validate_title(title)
    except ValueError as e:
        _abort(str(e))

    conn, c = _require_course(course)
    try:
        ex = create_exercise(conn, c.id, title, solution_path, source_path, priority)
        console.print(f"[green]Added exercise:[/green] {ex.title} (id={ex.id})")
    except Exception as e:
        if "UNIQUE" in str(e):
            _abort(f"Exercise '{title}' already exists in course '{course}'.")
        _abort(str(e))
    finally:
        conn.close()


@exercise_app.command("list")
def exercise_list(
    course: str = typer.Option(..., "--course", "-c", help="Course name"),
):
    """List all exercises in a course."""
    conn, c = _require_course(course)
    exercises = list_exercises(conn, c.id)
    trials_map = get_trials_for_course(conn, c.id)
    conn.close()

    if not exercises:
        console.print(f"No exercises in '{course}' yet.")
        return

    table = Table("Title", "Pri", "Trials", "Latest Grade", "Source", "Solution", show_header=True)
    for ex in exercises:
        trials = trials_map.get(ex.id, [])
        latest = trials[-1].grade if trials else "-"
        src = ex.source_path or "-"
        sol = ex.solution_path or "-"
        table.add_row(ex.title, str(ex.priority), str(len(trials)), str(latest), src, sol)
    console.print(table)


@exercise_app.command("show")
def exercise_show(
    course: str = typer.Option(..., "--course", "-c", help="Course name"),
    title: str = typer.Option(..., "--title", "-t", help="Exercise title"),
):
    """Inspect an exercise and its trial history."""
    conn, c = _require_course(course)
    ex = get_exercise(conn, c.id, title)
    if not ex:
        conn.close()
        _abort(f"Exercise '{title}' not found in course '{course}'.")

    trials = get_trials_for_exercise(conn, ex.id)
    conn.close()

    console.print(f"\n[bold]Exercise:[/bold] {ex.title}")
    console.print(f"[bold]Course:[/bold]   {course}")
    console.print(f"[bold]Priority:[/bold] {ex.priority}")
    if ex.source_path:
        console.print(f"[bold]Source:[/bold]   {ex.source_path}")
    else:
        console.print("[bold]Source:[/bold]   (none)")
    if ex.solution_path:
        console.print(f"[bold]Solution:[/bold] {ex.solution_path}")
    else:
        console.print("[bold]Solution:[/bold] (none)")

    if not trials:
        console.print("\nNo trials yet.")
        return

    console.print(f"\n[bold]Trials ({len(trials)}):[/bold]")
    table = Table("#", "Grade", "Timestamp", "Note", show_header=True)
    for i, t in enumerate(trials, 1):
        ts = t.timestamp.strftime("%Y-%m-%d %H:%M")
        table.add_row(str(i), str(t.grade), ts, t.note or "")
    console.print(table)


_STRATEGY_NAMES = ", ".join(STRATEGIES)


@exercise_app.command("next")
def exercise_next(
    course: str = typer.Option(..., "--course", "-c", help="Course name"),
    strategy: str = typer.Option(
        "priority", "--strategy", "-s",
        help=f"Picking strategy: {_STRATEGY_NAMES}",
    ),
):
    """Recommend the next exercise to practice."""
    if strategy not in STRATEGIES:
        _abort(f"Unknown strategy '{strategy}'. Choose from: {_STRATEGY_NAMES}")

    conn, c = _require_course(course)
    exercises = list_exercises(conn, c.id)
    trials_map = get_trials_for_course(conn, c.id)
    conn.close()

    if not exercises:
        console.print(f"No exercises in '{course}' yet.")
        return

    ex = STRATEGIES[strategy](exercises, trials_map)
    if not ex:
        console.print("All exercises done!")
        return

    trials = trials_map.get(ex.id, [])
    console.print(f"\n[bold green]Next exercise:[/bold green] {ex.title}")
    console.print(f"  Trials so far: {len(trials)}")
    if trials:
        console.print(f"  Latest grade:  {trials[-1].grade}")
    if ex.solution_path:
        console.print(f"  Solution:      {ex.solution_path}")


@exercise_app.command("open-solution")
def exercise_open_solution(
    course: str = typer.Option(..., "--course", "-c", help="Course name"),
    title: str = typer.Option(..., "--title", "-t", help="Exercise title"),
):
    """Open the solution for an exercise using xdg-open."""
    conn, c = _require_course(course)
    ex = get_exercise(conn, c.id, title)
    conn.close()

    if not ex:
        _abort(f"Exercise '{title}' not found in course '{course}'.")
    if not ex.solution_path:
        _abort(f"Exercise '{title}' has no solution path.")

    _xdg_open(ex.solution_path)


@exercise_app.command("open-source")
def exercise_open_source(
    course: str = typer.Option(..., "--course", "-c", help="Course name"),
    title: str = typer.Option(..., "--title", "-t", help="Exercise title"),
):
    """Open the source for an exercise using xdg-open."""
    conn, c = _require_course(course)
    ex = get_exercise(conn, c.id, title)
    conn.close()

    if not ex:
        _abort(f"Exercise '{title}' not found in course '{course}'.")
    if not ex.source_path:
        _abort(f"Exercise '{title}' has no source path.")

    _xdg_open(ex.source_path)


@exercise_app.command("set-priority")
def exercise_set_priority(
    course: str = typer.Option(..., "--course", "-c", help="Course name"),
    title: str = typer.Option(None, "--title", "-t", help="Exercise title (omit to set for all exercises in the course)"),
    priority: int = typer.Option(..., "--priority", "-p", help="New priority value (higher = picked sooner)"),
    like: str = typer.Option(None, "--like", "-l", help="Title pattern (SQL LIKE, e.g. '1.5.%%')"),
):
    """Set the priority of one or more exercises."""
    conn, c = _require_course(course)

    if title:
        ex = get_exercise(conn, c.id, title)
        if not ex:
            conn.close()
            _abort(f"Exercise '{title}' not found in course '{course}'.")
        set_exercise_priority(conn, ex.id, priority)
        conn.close()
        console.print(f"[green]Priority set to {priority}[/green] for {title}")
    elif like:
        rows = conn.execute(
            "SELECT id, title FROM exercises WHERE course_id = ? AND title LIKE ?",
            (c.id, like),
        ).fetchall()
        if not rows:
            conn.close()
            _abort(f"No exercises matching '{like}' in course '{course}'.")
        for row in rows:
            set_exercise_priority(conn, row["id"], priority)
        conn.close()
        console.print(f"[green]Priority set to {priority}[/green] for {len(rows)} exercise(s) matching '{like}'")
    else:
        exercises = list_exercises(conn, c.id)
        for ex in exercises:
            set_exercise_priority(conn, ex.id, priority)
        conn.close()
        console.print(f"[green]Priority set to {priority}[/green] for all {len(exercises)} exercise(s) in '{course}'")


@exercise_app.command("import")
def exercise_import(
    pdf: str = typer.Argument(..., help="Path to the exercise sheet PDF"),
    course: str = typer.Option(..., "--course", "-c", help="Course name"),
    sheet: Optional[int] = typer.Option(
        None, "--sheet", "-n",
        help="Sheet number (auto-detected from PDF if omitted)",
    ),
    solution_path: Optional[str] = typer.Option(
        None, "--solution-path", "-s",
        help="Path or URL to the solution (applied to all imported exercises)",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview parsed exercises without inserting them",
    ),
):
    """Bulk import exercises from a PDF exercise sheet.

    The PDF path is stored as the source for every imported exercise.
    Use --solution-path to also record where solutions can be found.
    """
    from pathlib import Path
    from tunashake.pdf_parser import detect_sheet_number, parse_exercises

    pdf_path = Path(pdf).resolve()
    if not pdf_path.exists():
        _abort(f"File not found: {pdf}")

    # Resolve sheet number.
    resolved_sheet = sheet
    if resolved_sheet is None:
        resolved_sheet = detect_sheet_number(str(pdf_path))
    if resolved_sheet is None:
        _abort(
            "Could not detect sheet number from the PDF. "
            "Provide it explicitly with --sheet N."
        )

    titles = parse_exercises(str(pdf_path), resolved_sheet)
    if not titles:
        _abort("No exercises found in the PDF. Check the file or provide --sheet manually.")

    # Preview table.
    console.print(f"\n[bold]PDF:[/bold]   {pdf_path}")
    console.print(f"[bold]Sheet:[/bold] {resolved_sheet}  [bold]Exercises found:[/bold] {len(titles)}\n")
    table = Table("Title", "Source", "Solution", show_header=True)
    for t in titles:
        table.add_row(t, str(pdf_path), solution_path or "-")
    console.print(table)

    if dry_run:
        console.print("\n[dim]Dry run — nothing imported.[/dim]")
        return

    # Confirm before inserting.
    confirm = typer.confirm(f"\nImport {len(titles)} exercise(s) into course '{course}'?")
    if not confirm:
        console.print("[dim]Aborted.[/dim]")
        return

    conn, c = _require_course(course)
    added = skipped = 0
    try:
        for t in titles:
            try:
                create_exercise(conn, c.id, t, solution_path, str(pdf_path))
                added += 1
            except Exception as e:
                if "UNIQUE" in str(e):
                    skipped += 1
                else:
                    raise
    finally:
        conn.close()

    console.print(f"\n[green]Imported {added} exercise(s).[/green]", end="")
    if skipped:
        console.print(f"  [dim]{skipped} already existed, skipped.[/dim]")
    else:
        console.print()


# CSV columns accepted by import-csv (order doesn't matter, header is required).
_CSV_COLUMNS = ["title", "solution_path", "source_path", "priority"]
_CSV_EXAMPLE = "title,solution_path,source_path,priority\n1.1.a,/path/to/solutions.pdf,/path/to/sheet.pdf,0\n1.1.b,,,5\n"


@exercise_app.command("csv-template")
def exercise_csv_template():
    """Print an example CSV that import-csv accepts."""
    console.print(_CSV_EXAMPLE, end="")


@exercise_app.command("import-csv")
def exercise_import_csv(
    csv_file: str = typer.Argument(..., help="Path to the CSV file"),
    course: str = typer.Option(..., "--course", "-c", help="Course name"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview rows without inserting them",
    ),
):
    """Bulk import exercises from a CSV file.

    Required column: title.
    Optional columns: solution_path, source_path, priority (default 0).

    Run 'tunashake exercise csv-template' to see the expected format.
    """
    import csv
    from pathlib import Path

    csv_path = Path(csv_file).resolve()
    if not csv_path.exists():
        _abort(f"File not found: {csv_file}")

    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None or "title" not in reader.fieldnames:
            _abort("CSV must have a 'title' column.")
        rows = list(reader)

    if not rows:
        _abort("CSV file contains no data rows.")

    # Parse and validate rows.
    exercises: list[dict] = []
    errors: list[str] = []
    for i, row in enumerate(rows, start=2):  # row 1 is the header
        title = row.get("title", "").strip()
        if not title:
            errors.append(f"Row {i}: missing title.")
            continue
        try:
            title = validate_title(title)
        except ValueError as e:
            errors.append(f"Row {i}: {e}")
            continue

        raw_priority = row.get("priority", "").strip()
        try:
            priority = int(raw_priority) if raw_priority else 0
        except ValueError:
            errors.append(f"Row {i}: priority must be an integer, got '{raw_priority}'.")
            continue

        exercises.append({
            "title": title,
            "solution_path": row.get("solution_path", "").strip() or None,
            "source_path": row.get("source_path", "").strip() or None,
            "priority": priority,
        })

    if errors:
        for e in errors:
            console.print(f"[red]{e}[/red]")
        _abort(f"{len(errors)} validation error(s). Nothing imported.")

    # Preview table.
    console.print(f"\n[bold]CSV:[/bold] {csv_path}  [bold]Rows:[/bold] {len(exercises)}\n")
    table = Table("Title", "Pri", "Source", "Solution", show_header=True)
    for ex in exercises:
        table.add_row(
            ex["title"],
            str(ex["priority"]),
            ex["source_path"] or "-",
            ex["solution_path"] or "-",
        )
    console.print(table)

    if dry_run:
        console.print("\n[dim]Dry run — nothing imported.[/dim]")
        return

    confirm = typer.confirm(f"\nImport {len(exercises)} exercise(s) into course '{course}'?")
    if not confirm:
        console.print("[dim]Aborted.[/dim]")
        return

    conn, c = _require_course(course)
    added = skipped = 0
    try:
        for ex in exercises:
            try:
                create_exercise(
                    conn, c.id,
                    ex["title"], ex["solution_path"], ex["source_path"], ex["priority"],
                )
                added += 1
            except Exception as e:
                if "UNIQUE" in str(e):
                    skipped += 1
                else:
                    raise
    finally:
        conn.close()

    console.print(f"\n[green]Imported {added} exercise(s).[/green]", end="")
    if skipped:
        console.print(f"  [dim]{skipped} already existed, skipped.[/dim]")
    else:
        console.print()


# ── repl ───────────────────────────────────────────────────────────────────────

@app.command()
def repl(
    course: str = typer.Option(..., "--course", "-c", help="Course name"),
    strategy: str = typer.Option(
        "priority", "--strategy", "-s",
        help=f"Picking strategy: {', '.join(STRATEGIES)}",
    ),
):
    """
    Interactive study session: get an exercise, grade it, repeat.

    Commands at the prompt:
      1-5        record a trial with that grade and move to next exercise
      s / skip   skip this exercise (no trial recorded)
      o / open   open the solution with xdg-open (then still grade/skip)
      p / source open the exercise source with xdg-open (then still grade/skip)
      q / quit   exit the session
    """
    if strategy not in STRATEGIES:
        _abort(f"Unknown strategy '{strategy}'. Choose from: {', '.join(STRATEGIES)}")

    pick = STRATEGIES[strategy]

    conn, c = _require_course(course)
    conn.close()

    console.print(f"\n[bold]Course:[/bold] {course}  [dim](strategy: {strategy})[/dim]")
    console.print("[dim]Grade 1–5 · (s)kip · (o)pen · (p)source · src <path> · sol <path> · sel <title> · (q)uit[/dim]\n")

    forced: "Exercise | None" = None  # set by 'sel' to override the picker

    while True:
        # Re-fetch each iteration so grades recorded this session affect future picks.
        conn = get_connection()
        exercises = list_exercises(conn, c.id)
        trials_map = get_trials_for_course(conn, c.id)
        conn.close()

        if forced is not None:
            ex = forced
            forced = None
        else:
            ex = pick(exercises, trials_map)

        if ex is None:
            console.print("[green]No exercises available.[/green]")
            break

        trials = trials_map.get(ex.id, [])
        trial_info = (
            f"[dim]({len(trials)} trial(s), last grade: {trials[-1].grade})[/dim]"
            if trials else "[dim](never attempted)[/dim]"
        )
        console.print(f"[bold yellow]{ex.title}[/bold yellow]  {trial_info}")
        if ex.source_path:
            console.print(f"  [dim]source: {ex.source_path}[/dim]")

        # Inner loop: stay on this exercise until graded, skipped, or quit.
        while True:
            try:
                raw = input(">>> ").strip()
            except (EOFError, KeyboardInterrupt):
                console.print("\n[dim]Bye![/dim]")
                return

            cmd = raw.lower()

            if cmd in ("q", "quit", "exit"):
                console.print("[dim]Bye![/dim]")
                return

            if cmd in ("s", "skip"):
                console.print("[dim]Skipped.[/dim]\n")
                break  # next exercise

            if cmd in ("o", "open"):
                if ex.solution_path:
                    _xdg_open(ex.solution_path)
                else:
                    console.print("[yellow]No solution path set for this exercise.[/yellow]")
                continue

            if cmd in ("p", "source"):
                if ex.source_path:
                    _xdg_open(ex.source_path)
                else:
                    console.print("[yellow]No source path set for this exercise.[/yellow]")
                continue

            if cmd.startswith("src "):
                path = raw[4:].strip()
                if not path:
                    console.print("[red]Usage: src <path>[/red]")
                    continue
                conn = get_connection()
                ex_db = get_exercise(conn, c.id, ex.title)
                if ex_db:
                    set_exercise_source(conn, ex_db.id, path)
                    ex = ex_db
                    ex.source_path = path
                conn.close()
                console.print(f"[green]Source set:[/green] {path}")
                continue

            if cmd.startswith("sol "):
                path = raw[4:].strip()
                if not path:
                    console.print("[red]Usage: sol <path>[/red]")
                    continue
                conn = get_connection()
                ex_db = get_exercise(conn, c.id, ex.title)
                if ex_db:
                    set_exercise_solution(conn, ex_db.id, path)
                    ex = ex_db
                    ex.solution_path = path
                conn.close()
                console.print(f"[green]Solution set:[/green] {path}")
                continue

            if cmd.startswith("sel "):
                title = raw[4:].strip()
                if not title:
                    console.print("[red]Usage: sel <title>[/red]")
                    continue
                conn = get_connection()
                selected = get_exercise(conn, c.id, title)
                conn.close()
                if not selected:
                    # Try a case-insensitive partial match.
                    matches = [e for e in exercises if title.lower() in e.title.lower()]
                    if len(matches) == 1:
                        selected = matches[0]
                    elif len(matches) > 1:
                        console.print(f"[yellow]Ambiguous — matches: {', '.join(e.title for e in matches)}[/yellow]")
                        continue
                    else:
                        console.print(f"[red]Exercise '{title}' not found.[/red]")
                        continue
                forced = selected
                console.print("[dim]Skipped.[/dim]\n")
                break  # jump to forced exercise

            try:
                grade = validate_grade(int(cmd))
            except (ValueError, TypeError):
                console.print("[red]Enter 1–5, (s)kip, (o)pen, (p)source, src <path>, sol <path>, sel <title>, or (q)uit.[/red]")
                continue

            conn = get_connection()
            ex_db = get_exercise(conn, c.id, ex.title)
            if ex_db:
                create_trial(conn, ex_db.id, grade)
            conn.close()
            console.print(f"[green]Grade {grade} recorded.[/green]\n")
            break  # next exercise


# ── trial commands ─────────────────────────────────────────────────────────────

@trial_app.command("add")
def trial_add(
    course: str = typer.Option(..., "--course", "-c", help="Course name"),
    title: str = typer.Option(..., "--title", "-t", help="Exercise title"),
    grade: int = typer.Option(..., "--grade", "-g", help="Grade 1 (easy) to 5 (hard)"),
    note: Optional[str] = typer.Option(None, "--note", "-n", help="Optional note"),
):
    """Record a trial for an exercise."""
    try:
        grade = validate_grade(grade)
    except (ValueError, TypeError) as e:
        _abort(str(e))

    conn, c = _require_course(course)
    ex = get_exercise(conn, c.id, title)
    if not ex:
        conn.close()
        _abort(f"Exercise '{title}' not found in course '{course}'.")

    trial = create_trial(conn, ex.id, grade, note or None)
    conn.close()

    ts = trial.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    console.print(f"[green]Trial recorded:[/green] grade={trial.grade}  at {ts}")
    if trial.note:
        console.print(f"  Note: {trial.note}")


# ── stats commands ─────────────────────────────────────────────────────────────

@stats_app.command("show")
def stats_show(
    course: str = typer.Option(..., "--course", "-c", help="Course name"),
):
    """Show statistics for a course."""
    conn, c = _require_course(course)
    exercises = list_exercises(conn, c.id)
    trials_map = get_trials_for_course(conn, c.id)
    conn.close()

    stats = course_stats(exercises, trials_map)

    console.print(f"\n[bold]Stats for:[/bold] {course}")
    console.print(f"  Total exercises:    {stats['total_exercises']}")
    console.print(f"  Never attempted:    {stats['untried_exercises']}")
    console.print(f"  Total trials:       {stats['total_trials']}")
    if stats["avg_grade"] is not None:
        console.print(f"  Average grade:      {stats['avg_grade']:.2f}  (1=easy, 5=hard)")
    else:
        console.print("  Average grade:      n/a")

    if stats["per_exercise"]:
        console.print("\n[bold]Per exercise (hardest first):[/bold]")
        table = Table("Title", "Trials", "Latest Grade", show_header=True)
        for row in stats["per_exercise"]:
            lg = str(row["latest_grade"]) if row["latest_grade"] is not None else "-"
            table.add_row(row["title"], str(row["trial_count"]), lg)
        console.print(table)


# ── db commands ────────────────────────────────────────────────────────────────

@db_app.command("query")
def db_query(
    sql: str = typer.Argument(..., help="SQL statement to execute"),
):
    """Execute a raw SQL query and print results as a table."""
    conn = get_connection()
    try:
        cur = conn.execute(sql)
        conn.commit()
    except Exception as e:
        conn.close()
        _abort(str(e))

    rows = cur.fetchall()
    if not rows:
        console.print("[dim]No rows returned.[/dim]")
        conn.close()
        return

    col_names = [d[0] for d in cur.description]
    table = Table(*col_names, show_header=True)
    for row in rows:
        table.add_row(*[str(v) if v is not None else "" for v in row])
    console.print(table)
    conn.close()


@db_app.command("path")
def db_path():
    """Print the path to the SQLite database file."""
    from tunashake.db import get_db_path
    console.print(str(get_db_path()))


@db_app.command("shell")
def db_shell():
    """Open an interactive SQLite shell for the database."""
    import subprocess
    from tunashake.db import get_db_path
    path = str(get_db_path())
    try:
        subprocess.run(["sqlite3", path], check=False)
    except FileNotFoundError:
        _abort("sqlite3 not found. Install it or use 'tunashake db query' instead.")
