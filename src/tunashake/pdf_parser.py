"""
Parse exercise titles from PDF exercise sheets.

Supports three layouts (tried in order):

  QFT-style  (Sheets 3, 4, …)
    Exercise 1 - Title
    1.1 Sub-exercise text
    1.2 …

  Generic-style  (Sheets 2, 6, sheet1, …)
    Exercise N - Title   OR   Problem N - Title
    Sub-exercises in any of:
      "1. Text"   ordinal numbers
      "[a] Text"  bracket letters
      "(a) Text"  paren letters
      "a) Text"   bare letter-paren
    Exercises/Problems with no sub-items are emitted as sheet.N.

  S/H-style  (Exercise_sheet_1, …)
    S 1  Short question title
    (a) …
    H 1  Homework title
    (a) …
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

# QFT-style: inline "N.M" sub-exercise numbers (no header context needed)
_SUB_NUMERIC = re.compile(r'^(\d+)\.(\d+)\s')

# Generic-style: "Exercise N" or "Problem N" section headers
_GENERIC_HEADER = re.compile(r'^(?:Exercise|Problem)\s+(\d+)\b', re.IGNORECASE)

# Generic-style sub-exercise patterns (tried in order; first match wins)
_GENERIC_SUBS: list[re.Pattern[str]] = [
    re.compile(r'^(\d+)\.\s'),       # "1. Text"
    re.compile(r'^\[([a-z])\]\s'),   # "[a] Text"
    re.compile(r'^\(([a-z])\)\s'),   # "(a) Text"
    re.compile(r'^([a-z])\)\s'),     # "a) Text"
]

# S/H-style headers and sub-exercises
_SH_HEADER = re.compile(r'^([SH])\s+(\d+)\b')
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
    ``sheet.exercise[.sub]`` format parsed from *pdf_path*.

    Tries QFT-style first, then generic-style (Exercise/Problem headers),
    then S/H-style as a final fallback.
    """
    text = _extract_text(pdf_path)
    lines = text.splitlines()

    titles = _parse_qft_style(lines, sheet)
    if not titles:
        titles = _parse_generic_style(lines, sheet)
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
    """Collect 'N.M …' inline sub-exercise numbers (no header context needed).

    Used by QFT sheets where sub-exercises are already namespaced as e.g.
    '1.1', '3.2', so the exercise number is embedded in the sub-exercise line.
    """
    titles: list[str] = []
    for line in lines:
        line = line.strip()
        m = _SUB_NUMERIC.match(line)
        if m:
            ex = int(m.group(1))
            sub = int(m.group(2))
            titles.append(f"{sheet}.{ex}.{sub}")
    return titles


def _parse_generic_style(lines: list[str], sheet: int) -> list[str]:
    """Collect sub-exercises under 'Exercise N' or 'Problem N' headers.

    Recognises four sub-exercise syntaxes within each block:
      - ordinal  "1. …"
      - bracket  "[a] …"
      - paren    "(a) …"
      - bare     "a) …"

    The first syntax seen in a block locks in the pattern for that block.
    This prevents nested sub-sub-exercises (e.g. (a)/(b) inside sub-item 6)
    from being picked up as additional top-level sub-exercises.

    Exercises/Problems with no detected sub-items are emitted as ``sheet.N``.
    Returns an empty list if no Exercise/Problem header is found, so this
    parser silently passes through on sheets that use other layouts.
    """
    titles: list[str] = []
    current: int | None = None
    subs: list[str] = []
    locked_pat: int | None = None   # index into _GENERIC_SUBS; set on first hit
    found_any_header = False

    def _emit() -> None:
        if current is None:
            return
        if subs:
            for s in subs:
                titles.append(f"{sheet}.{current}.{s}")
        else:
            titles.append(f"{sheet}.{current}")

    for line in lines:
        line = line.strip()

        m = _GENERIC_HEADER.match(line)
        if m:
            _emit()
            current = int(m.group(1))
            subs = []
            locked_pat = None
            found_any_header = True
            continue

        if current is not None:
            for i, pat in enumerate(_GENERIC_SUBS):
                m = pat.match(line)
                if m:
                    if locked_pat is None:
                        locked_pat = i          # lock in on first hit
                    if i == locked_pat:
                        sub = str(m.group(1))
                        if sub not in subs:
                            subs.append(sub)
                    break                       # always stop at first match

    _emit()
    return titles if found_any_header else []


def _parse_sh_style(lines: list[str], sheet: int) -> list[str]:
    """Collect sub-exercises under 'S N' / 'H N' headers with '(a)' markers."""
    titles: list[str] = []
    seq = 0
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
