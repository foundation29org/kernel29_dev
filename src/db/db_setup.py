"""
Database setup module that handles the creation of all schemas and tables
by invoking individual model modules via direct script execution.
"""

import os
import sys
import subprocess

# Configuration flags for table creation
create_registry_tables = True
create_llm_tables = True
create_prompts_tables = True
create_bench29_tables = True
verbose = True

# Get the absolute path to the db directory
db_dir = os.path.dirname(os.path.abspath(__file__))

# Python executable
python_exe = "python"  # Use "python3" for systems where python refers to Python 2

# Registry tables
if create_registry_tables:
    registry_script = os.path.join(db_dir, "registry", "registry_models.py")
    command = f"{python_exe} {registry_script}"
    if verbose:
        print("Creating registry tables...")
        print(f"Script path: {registry_script}")
        print(f"Command: {command}")
    os.system(command)

# LLM tables
if create_llm_tables:
    llm_script = os.path.join(db_dir, "llm", "llm_models.py")
    command = f"{python_exe} {llm_script}"
    if verbose:
        print("Creating LLM tables...")
        print(f"Script path: {llm_script}")
        print(f"Command: {command}")
    os.system(command)

# Prompts tables
if create_prompts_tables:
    prompts_script = os.path.join(db_dir, "prompts", "prompts_models.py")
    command = f"{python_exe} {prompts_script}"
    if verbose:
        print("Creating prompts tables...")
        print(f"Script path: {prompts_script}")
        print(f"Command: {command}")
    os.system(command)

# Bench29 tables
if create_bench29_tables:
    bench29_script = os.path.join(db_dir, "bench29", "bench29_models.py")
    command = f"{python_exe} {bench29_script}"
    if verbose:
        print("Creating bench29 tables...")
        print(f"Script path: {bench29_script}")
        print(f"Command: {command}")
    os.system(command)

if verbose:
    print("Database setup completed successfully.")
