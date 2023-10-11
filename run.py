import sys
from utils import DEFAULT_TMP_PATH
from utils.cmd import InteractiveCmd


arguments = sys.argv
path = arguments[1]

if __name__ == '__main__':
    if path is None:
        print("Please specify the path the exercises csv file")
        sys.exit(1)
    cmd = InteractiveCmd(path, DEFAULT_TMP_PATH)
    cmd.cmdloop()
