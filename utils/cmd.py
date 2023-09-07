import os
import cmd
import pandas as pd

TMP_FILE_SUFFIX="_tmp.pckl"


class InteractiveCmd(cmd.Cmd):

    def __init__(self, exercises_path, tmp_path):
        cmd.Cmd.__init__(self)
        self._init_exercises(exercises_path, tmp_path)
        self.prompt = ">>> "
    def _init_exercises(self, path, tmp_path):
        file_name = f"{os.path.splitext(os.path.basename(path))[0]}{TMP_FILE_SUFFIX}"
        self.full_tmp_file_path = os.path.join(tmp_path, file_name)

        df_exercises = pd.read_csv(path)
        df_exercises["Done"] = False
        df_exercises["Notes"] = ""

        if os.path.exists(self.full_tmp_file_path):
            df_cached_exercises = pd.read_pickle(self.full_tmp_file_path)
            # Use cached exercies to set the ones already done
            matches = df_cached_exercises["Exercise"] == df_exercises["Exercise"]
            df_exercises.loc[matches,"Done"] = df_cached_exercises["Done"]
            df_exercises.loc[matches,"Notes"] = df_cached_exercises["Notes"]

        self.exercises = df_exercises

    def _give_random_exercise(self):
        if bool(self.exercises["Done"].all()):
            return None
        priority_matches = self.exercises["Priority"] == "*"
        if bool(self.exercises[priority_matches]["Done"].all()):
            return self.exercises[~self.exercises["Done"]].sample(n=1)
        return self.exercises[priority_matches & ~self.exercises["Done"]].sample(n=1)

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
        if self.current_index is not None:
            print(f"Setting exercise to done")
            self.exercises.loc[self.current_index, "Done"] = True
            self._serialize_to_tmp()
        print(self._current_exercise().to_string(index=False))

    def do_all(self, arg):
        print(self.exercises.to_string(index=False))

    def do_note(self, arg):
        if self.current_index is not None:
            print(f"Adding note to exercise")
            self.exercises.loc[self.current_index, "Notes"] = arg
            self._serialize_to_tmp()
        print(self.exercises.to_string(index=False))

    def do_quit(self, arg):
        self._serialize_to_tmp()
        return True
