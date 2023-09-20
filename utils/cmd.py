import os
import cmd
import pandas as pd

TMP_FILE_SUFFIX = "_tmp.pckl"
TIME_FORMAT = '%Y-%m-%d %H:%M'


class InteractiveCmd(cmd.Cmd):

    def __init__(self, exercises_path, tmp_path):
        cmd.Cmd.__init__(self)
        self._init_exercises(exercises_path, tmp_path)
        self.prompt = ">>> "

    def _init_exercises(self, path, tmp_path):
        file_name = f"{os.path.splitext(os.path.basename(path))[0]}{TMP_FILE_SUFFIX}"
        self.full_tmp_file_path = os.path.join(tmp_path, file_name)

        df_exercises = pd.read_csv(path)
        df_exercises["Notes"] = ""
        df_exercises["Done"] = False
        df_exercises["Tries"] = 0
        df_exercises["Date"] = pd.Timestamp.now().strftime(
            TIME_FORMAT)  # of last try

        if os.path.exists(self.full_tmp_file_path):
            df_cached_exercises = pd.read_pickle(self.full_tmp_file_path)
            # Use cached exercies to set the ones already done
            matches = df_cached_exercises["Exercise"] == df_exercises["Exercise"]
            df_exercises.loc[matches, "Notes"] = df_cached_exercises["Notes"]
            df_exercises.loc[matches, "Done"] = df_cached_exercises["Done"]
            df_exercises.loc[matches, "Tries"] = df_cached_exercises["Tries"]
            df_exercises.loc[matches, "Date"] = df_cached_exercises["Date"]

        self.exercises = df_exercises

    def _give_random_exercise(self):
        undone_exercises = pd.DataFrame(
            self.exercises[~self.exercises["Done"]])
        if bool(undone_exercises.empty):
            return None

        redo_matches = (undone_exercises["Tries"] >= 1) & (pd.Timestamp.now(
        ) - pd.to_datetime(undone_exercises["Date"], format=TIME_FORMAT) > pd.Timedelta(days=3))
        if not bool(undone_exercises[redo_matches].empty):
            return undone_exercises[redo_matches].sample(n=1)

        priority_matches = undone_exercises["Priority"] == "*"
        if not bool(undone_exercises[priority_matches].empty):
            return undone_exercises[priority_matches].sample(n=1)

        # If there are no exercises with priority, do the residual ones
        return undone_exercises.sample(n=1)

    def _update_meta_info(self):
        self.exercises.loc[self.current_index,
                           "Date"] = pd.Timestamp.now().strftime(TIME_FORMAT)
        self.exercises.loc[self.current_index, "Tries"] += 1

    def _serialize_to_tmp(self):
        self.exercises.to_pickle(self.full_tmp_file_path)

    def _current_exercise(self):
        return self.exercises.loc[[self.current_index]]

    def do_next(self, arg):
        rnd_exercise = self._give_random_exercise()
        if rnd_exercise is None:
            print("All exercises done")
            return

        self.current_index = rnd_exercise.index[0]
        print(f"Next exercise\n")
        print(self._current_exercise().to_string(index=False))
        print("\n")

    def do_done(self, arg):
        if hasattr(self, 'current_index'):
            print(f"Setting exercise to done")
            self.exercises.loc[self.current_index, "Done"] = True
            self._update_meta_info()
            self._serialize_to_tmp()
            print(self._current_exercise().to_string(index=False))
        else:
            print("No exercise selected")

    def do_again(self, arg):
        if hasattr(self, 'current_index'):
            print(
                f"This was the {int(self._current_exercise()['Tries'].iloc[0])} try.\n")
            self.exercises.loc[self.current_index, "Notes"] = arg
            self._update_meta_info()
            self._serialize_to_tmp()
            print(self._current_exercise().to_string(index=False))
        else:
            print("No exercise selected")

    def do_note(self, arg):
        if hasattr(self, 'current_index'):
            print(f"Adding note to exercise")
            self.exercises.loc[self.current_index, "Notes"] = arg
            self._serialize_to_tmp()
        else:
            print("No exercise selected")

    def do_all(self, arg):
        print(self.exercises.to_string(index=False))

    def do_stats(self, arg):
        progess = self.exercises["Done"].sum() / len(self.exercises)
        progess_prio = self.exercises[self.exercises["Priority"] == "*"]["Done"].sum(
        ) / len(self.exercises[self.exercises["Priority"] == "*"])
        print(f"Progress: {progess*100:.2f} ({progess_prio*100:.2f} Priority)")

    def do_quit(self, arg):
        self._serialize_to_tmp()
        return True
