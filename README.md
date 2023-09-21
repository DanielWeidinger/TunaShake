# TunaShake

TunaShake is a command-line tool designed to help you select and track exercises. The tool uses the concept of interleaving, a learning technique that involves mixing different kinds of situations or problems to be practiced, instead of focusing on just one type. This way, you can become a bodybuilder of the mind!

## How to Run

To run TunaShake, navigate to the project directory and run the following command:

```bash
python run.py <path_to_csv>
```

Replace `<path_to_csv>` with the path to your project.

## Commands

TunaShake supports the following commands:

- `next`: Get a random exercise.
- `done`: Mark an exercise as done.
- `again`: Mark an exercise as done and add a note.
- `note`: Add a note to the exercise.
- `only <arg>`: This command has an argument `<arg>`. When `<arg>` is set to `new`, the command will only show new exercises.
- `all`: Show all exercises.
- `stats`: Show statistics.
- `quit`: Quit the program.

## Data

TunaShake uses a CSV file as input. Each exercise has the following fields:

- `Exercise`: The name of the exercise
- `Priority`: Whether the exercise is a priority. Can only be \* or blank

The CSV file will be read everytime you start the script, and exercises which have already been edited will be loaded from the tmp cache

## Temporary Files

TunaShake creates temporary files to store the current state of the exercises. These files are updated each time you run a command.
Per default the tmp folder will be created in the project root.
