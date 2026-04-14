class Exercise:
    """Represents a single exercise from the markdown file."""

    def __init__(
        self, raw_line: str, is_completed: bool, sheet: str, task: str, rating: int = 3
    ):
        self.raw_line = raw_line
        self.is_completed = is_completed
        self.sheet = sheet
        self.task = task
        self.rating = rating

    def __str__(self):
        return f"{self.sheet} - {self.task}"

    def __repr__(self):
        return f"Exercise(sheet='{self.sheet}', task='{self.task}', completed={self.is_completed})"
