# Random Exercise Picker

A Python script that reads a markdown TODO file and provides random unsolved exercises in an interactive REPL loop.

## Features

- 📝 Parse markdown checklist format
- 🎲 Get random unsolved exercises
- 📊 View statistics (total, completed, unsolved)
- 📋 List all unsolved exercises
- 🔄 Interactive REPL loop

## Installation

1. Install Python 3.6 or higher

2. Install required dependencies:
```bash
pip install python-dotenv
```

## Setup

1. Create a `.env` file in the same directory as the script:
```bash
cp .env.example .env
```

2. Edit the `.env` file to point to your markdown file:
```
EXERCISE_FILE=exercises.md
```

3. Create your exercises markdown file with the following format:
```markdown
- [ ] 1 Blatt - 1 1
- [ ] 1 Blatt - 2
- [x] 2 Blatt - 1 a)
- [ ] 2 Blatt - 2 a)
```

Where:
- `- [ ]` indicates an unsolved exercise
- `- [x]` indicates a completed exercise
- Format: `<Sheet name> - <Exercise details>`

**Note:** The parser is flexible and supports various markdown checkbox formats:
- Different bullet markers: `-`, `*`, `+`
- Optional spaces: `-[ ]`, `- [ ]`, `-[x]`, `- [x]`
- Extra spaces in brackets: `- [ x]`, `- [x ]`
- Case-insensitive: `[x]` or `[X]`

## Usage

Run the script:
```bash
python exercise_picker.py
```

Or make it executable:
```bash
chmod +x exercise_picker.py
./exercise_picker.py
```

## Commands

Once the script is running, you can use the following commands:

- **[Enter]** or **next** - Get a random unsolved exercise
- **stats** - Show statistics about your progress
- **list** - List all unsolved exercises
- **quit**, **exit**, or **q** - Exit the program
- **Ctrl+C** - Exit the program

## Example Session

```


## Diagnostic Tool

If you're experiencing issues with exercises not loading or not being marked as completed, use the diagnostic tool:

```bash
python analyze_file.py
```

This will show you:
- Total exercises found in your file
- How many are marked as completed vs unsolved
- Sample lines from your file
- Helpful suggestions

## Troubleshooting

### Not all exercises are being loaded

**Problem:** You have 75 exercises but only 68 are loaded.

**Solution:** Run the diagnostic tool:
```bash
python analyze_file.py
```

Common causes:
- Lines without checkbox format (`- [ ]` or `- [x]`) are ignored
- Empty lines or headers don't count as exercises
- Lines must start with `-`, `*`, or `+` followed by `[ ]` or `[x]`

### Completed exercises not showing as completed

**Problem:** Exercises marked as done aren't being recognized.

**Solution:** Make sure you're using the correct format:

✗ **Wrong** (unchecked):
```markdown
- [ ] Exercise name
```

✓ **Correct** (checked/completed):
```markdown
- [x] Exercise name
```

The script recognizes these as completed:
- `- [x]` or `- [X]` (dash with lowercase or uppercase X)
- `* [x]` or `* [X]` (asterisk bullet)
- `+ [x]` or `+ [X]` (plus bullet)

Run the diagnostic to verify:
```bash
python analyze_file.py
```

### "python-dotenv not installed" warning

Install the required dependency:
```bash
pip install python-dotenv
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

### "EXERCISE_FILE environment variable not set"

Create a `.env` file with:
```
EXERCISE_FILE=/path/to/your/exercises.md
```

Or set it directly:
```bash
export EXERCISE_FILE=/path/to/your/exercises.md
python exercise_picker.py
```

### "Markdown file not found"

Make sure:
1. The file path in `.env` is correct
2. The file actually exists
3. You have permission to read the file

Check your `.env` file:
```bash
cat .env
```

Then verify the file exists:
```bash
ls -la /path/from/env/file
```

## License

This script is provided as-is for educational purposes.
