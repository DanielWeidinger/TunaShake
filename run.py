import sys
from utils.cmd import InteractiveCmd


arguments = sys.argv
path = arguments[1]

if __name__ == '__main__':
    if path is None:
        print("Please specify a path to the project")
        sys.exit(1)
    cmd = InteractiveCmd(path, "tmp")
    cmd.cmdloop()
