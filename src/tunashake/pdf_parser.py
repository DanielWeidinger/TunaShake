"""
Parse exercise titles from PDF exercise sheets.

Supports two common layouts:

  QFT-style
    Exercise 1 - Some Title
    1.1 Do this thing ...
    1.2 Do another thing ...

  S/H-style (short/homework sections)
    S 1  Probability Distribution Functions
    (a) How are ...
    (b) Does a ...
    H 1  Some Homework
    (a) ...
"""

import re

try:
    import pdfplumber
except ImportError as e:
    raise ImportError(
        "pdfplumber is required for PDF import. "
        "Install it with: pip install pdfplumber"
    ) from e


_SHEET_PATTERNS = [
    re.compile(r'[Ss]heet\s+0*(\d+)', re.IGNORECASE),
    re.compile(r'[Ee]xercise\s+[Ss]heet\s+(\d+)', re.IGNORECASE),
    re.compile(r'[Bb]latt\s+0*(\d+)', re.IGNORECASE),
]

# QFT-style: "Exercise 1", "Exercise 1 - Title", "Exercise 1: Title"
_EXERCISE_HEADER = re.compile(r'^Exercise\s+(\d+)\s*[-:–]?\s*', re.IGNORECASE)
# QFT-style sub-exercise: "1.1 ...", "1.12 ..."
_SUB_NUMERIC = re.compile(r'^(\d+)\.(\d+)\s')
# S/H-style header: "S 1 Title", "H 2 Title"
_SH_HEADER = re.compile(r'^([SH])\s+(\d+)\b')
# S/H-style sub-exercise: "(a) ...", "(b) ..."
_SUB_LETTER = re.compile(r'^\(([a-z])\)\s')


def _extract_text(pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def detect_sheet_number(pdf_path: str) -> int | None:
    """Return the sheet number detected in the PDF, or None if not found."""
    text = _extract_text(pdf_path)
    for pat in _SHEET_PATTERNS:
        m = pat.search(text)
        if m:
            return int(m.group(1))
    return None


def parse_exercises(pdf_path: str, sheet: int) -> list[str]:
    """
    Return a deduplicated, ordered list of exercise titles in
    ``sheet.exercise.sub`` format parsed from *pdf_path*.

    Tries the QFT-style layout first; falls back to S/H-style if nothing
    is found.
    """
    text = _extract_text(pdf_path)
    lines = text.splitlines()

    titles = _parse_qft_style(lines, sheet)
    if not titles:
        titles = _parse_sh_style(lines, sheet)

    # Deduplicate while preserving order.
    seen: set[str] = set()
    result: list[str] = []
    for t in titles:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result


def _parse_qft_style(lines: list[str], sheet: int) -> list[str]:
    """Handle 'Exercise N' headers with 'N.M' sub-exercises."""
    titles: list[str] = []
    for line in lines:
        line = line.strip()
        m = _SUB_NUMERIC.match(line)
        if m:
            ex = int(m.group(1))
            sub = int(m.group(2))
            titles.append(f"{sheet}.{ex}.{sub}")
    return titles


def _parse_sh_style(lines: list[str], sheet: int) -> list[str]:
    """Handle 'S N' / 'H N' headers with '(a)' '(b)' sub-exercises."""
    titles: list[str] = []
    seq = 0               # sequential exercise counter across S and H groups
    current: int | None = None

    for line in lines:
        line = line.strip()

        m = _SH_HEADER.match(line)
        if m:
            seq += 1
            current = seq
            continue

        m = _SUB_LETTER.match(line)
        if m and current is not None:
            sub = m.group(1)
            titles.append(f"{sheet}.{current}.{sub}")

    return titles
