import pandas as pd

from utils import DAYS_TILL_REPEAT, TIME_FORMAT


def give_random_exercise(exercises, only_new):
    undone_exercises = pd.DataFrame(
        exercises[~exercises["Done"]])
    if bool(undone_exercises.empty):
        return None

    extra_conditions = undone_exercises["Done"] == False
    if only_new:
        print("!Only new Mode!")
        extra_conditions = (undone_exercises["Tries"] == 0)

    redo_matches = (undone_exercises["Tries"] >= 1) & (pd.Timestamp.now(
    ) - pd.to_datetime(undone_exercises["Date"], format=TIME_FORMAT) > pd.Timedelta(days=DAYS_TILL_REPEAT)) & extra_conditions
    if not bool(undone_exercises[redo_matches].empty):
        return undone_exercises[redo_matches].sample(n=1)

    priority_matches = (
        undone_exercises["Priority"] == "*") & extra_conditions
    if not bool(undone_exercises[priority_matches].empty):
        return undone_exercises[priority_matches].sample(n=1)

    if not bool(undone_exercises[extra_conditions].empty):
        return undone_exercises[extra_conditions].sample(n=1)

    # If there are no exercises with priority, do the residual ones
    print("No exercises with extra conditions found. Using residual ones")
    return undone_exercises.sample(n=1)
