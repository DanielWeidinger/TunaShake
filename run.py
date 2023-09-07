import pandas as pd
from utils.cmd import InteractiveCmd

df_exercises = pd.read_csv('data/ana2.csv')
df_exercises.head()


if __name__ == '__main__':
    cmd = InteractiveCmd("data/ana2.csv", "tmp")
    cmd.cmdloop()
