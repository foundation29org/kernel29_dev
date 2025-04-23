import os
import sys

ROOT_DIR_LEVEL = 1
parent_dir = "../" * ROOT_DIR_LEVEL
path2add = os.path.join(os.path.dirname(os.path.abspath(__file__)), parent_dir)
# print(path2add)
sys.path.append(path2add)
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../'))

