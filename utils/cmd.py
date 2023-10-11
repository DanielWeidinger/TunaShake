import os
import cmd
import pandas as pd


from utils import TIME_FORMAT, TMP_FILE_SUFFIX
from utils.exercise_selection import give_random_exercise


class InteractiveCmd(cmd.Cmd):

    def __init__(self, exercises_path, tmp_path):
        cmd.Cmd.__init__(self)
        self.exercise_path = exercises_path
        self.tmp_path = tmp_path
        self._init_exercises(exercises_path, tmp_path)
        self.prompt = ">>> "

    def _init_exercises(self, path, tmp_path):
        self.only_new = False

        file_name = f"{os.path.splitext(os.path.basename(path))[0]}{TMP_FILE_SUFFIX}"
        self.full_tmp_file_path = os.path.join(tmp_path, file_name)

        df_exercises = pd.read_csv(path)
        if "float" in str(df_exercises["Exercise"].dtype):
            df_exercises["Exercise"] = df_exercises["Exercise"].astype(str).str.rstrip(
                ".0")
        else:
            df_exercises["Exercise"] = df_exercises["Exercise"].astype(str)
        df_exercises["Link"] = df_exercises["Link"].astype(
            str) if "Link" in df_exercises.columns else "nan"
        df_exercises["Notes"] = ""
        df_exercises["Done"] = False
        df_exercises["Tries"] = 0
        df_exercises["Date"] = pd.Timestamp.now().strftime(
            TIME_FORMAT)  # of last try

        if os.path.exists(self.full_tmp_file_path):
            df_cached_exercises = pd.read_pickle(self.full_tmp_file_path)

            # Use cached exercies to set the ones already done
            for _, row in df_cached_exercises.iterrows():
                matches = df_exercises["Exercise"] == row["Exercise"]
                if matches.sum() > 1:
                    raise Exception(
                        "Multiple Matches for single Exercise in cache found")
                if matches.sum() == 1:
                    # print("Setting: " + str(row))
                    df_exercises.loc[matches, "Notes"] = row["Notes"]
                    df_exercises.loc[matches, "Done"] = row["Done"]
                    df_exercises.loc[matches, "Tries"] = row["Tries"]
                    df_exercises.loc[matches, "Date"] = row["Date"]

            # print(df_cached_exercises["Exercise"])
            # matches = df_exercises["Exercise"].apply(
            #     lambda x: x in list(df_cached_exercises["Exercise"]))
            # print(matches)
            # df_exercises.loc[matches, "Notes"] = df_cached_exercises["Notes"]
            # df_exercises.loc[matches, "Done"] = df_cached_exercises["Done"]
            # df_exercises.loc[matches, "Tries"] = df_cached_exercises["Tries"]
            # df_exercises.loc[matches, "Date"] = df_cached_exercises["Date"]

        self.exercises = df_exercises

    def _update_meta_info(self, no_update=False):
        self.exercises.loc[self.current_index,
                           "Date"] = pd.Timestamp.now().strftime(TIME_FORMAT)
        self.exercises.loc[self.current_index,
                           "Tries"] += 1 if not no_update else 0

    def _serialize_to_tmp(self):
        self.exercises.to_pickle(self.full_tmp_file_path)

    def _current_exercise(self):
        return self.exercises.loc[[self.current_index]]

    def do_next(self, arg):
        rnd_exercise = give_random_exercise(self.exercises, self.only_new)
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

    def do_undone(self, arg):
        if hasattr(self, 'current_index') and self._current_exercise()["Done"].iloc[0]:
            print(f"Setting exercise to not done")
            self.exercises.loc[self.current_index, "Done"] = False
            self._update_meta_info(no_update=True)
            self._serialize_to_tmp()
            print(self._current_exercise().to_string(index=False))
        else:
            print("No exercise selected or exercise not done")

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

    def do_only(self, arg):
        if arg == "":
            print("No argument given")
            return
        if arg == "new":
            self.only_new = True

    def do_select(self, arg):
        if arg == "":
            print("No argument given")
            return
        matches = self.exercises["Exercise"].str.contains(
            arg, case=False)

        if matches.sum() == 0:
            print("No matching exercise found")
        elif matches.sum() == 1:
            self.current_index = self.exercises[matches].index[0]
            print(f"Selected exercise\n")
            print(self._current_exercise().to_string(index=False))
            print("\n")
        else:
            print("Multiple matching exercises found")
            print(pd.DataFrame(
                self.exercises[["Exercise"]][matches]).to_string(index=False))

    def do_reset(self, arg):
        print("Resetting ")
        del self.only_new
        self._init_exercises(self.exercise_path, self.tmp_path)

    def do_all(self, arg):
        print(self.exercises.to_string(index=False))

    def do_stats(self, arg):
        progess = self.exercises["Done"].sum() / len(self.exercises)
        if len(self.exercises[self.exercises["Priority"] == "*"]) == 0:
            progess_prio = 0
        else:
            progess_prio = self.exercises[self.exercises["Priority"] == "*"]["Done"].sum(
            ) / len(self.exercises[self.exercises["Priority"] == "*"])
        tried = len(self.exercises[self.exercises["Tries"]
                                   != 0]) / len(self.exercises)
        print(f"""
        Progress: {progess*100:.2f}% ({progess_prio*100:.2f}% Priority)
        Tried: {tried*100:.2f}%
              """)

    def do_open(self, arg):
        if hasattr(self, 'current_index'):
            link = self._current_exercise()["Link"].iloc[0]
            if link != "nan":
                if ";" in link:
                    links = link.split(";")
                    for link in links:
                        os.system(f"xdg-open {link}")
                os.system(f"xdg-open {link}")
            else:
                print("No link available")
        else:
            print("No exercise selected")

    def do_help(self, arg):
        print("""
        next: Get a random exercise
        done: Mark exercise as done
        again: Mark exercise as done and add a note
        note: Add a note to the exercise
        all: Show all exercises
        stats: Show statistics
        only <arg>:
              * new: Only show new exercises
        select <arg>: Select an exercise by name
        quit: Quit the program
        """)

    def do_quit(self, arg):
        self._serialize_to_tmp()
        return True
