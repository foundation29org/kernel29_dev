import sys
import os


ROOT_DIR_LEVEL = 1  # Number of parent directories to go up
parent_dir = "..\\" * ROOT_DIR_LEVEL + "src"
path2add = os.path.join(os.path.dirname(os.path.abspath(__file__)), parent_dir)
# print("lel")
# print(path2add)
sys.path.append(path2add)