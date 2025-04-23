import os, sys

ROOT_DIR_LEVEL = 1
parent_dir = "../" * ROOT_DIR_LEVEL
abs_path = os.path.abspath(__file__)
dir_path = os.path.dirname(abs_path)
path2add = os.path.join(dir_path, parent_dir)
print(path2add)
sys.path.append(path2add)