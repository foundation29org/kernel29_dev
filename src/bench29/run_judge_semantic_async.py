import subprocess
import sys
import os

# Imports needed for the optional block below


from lapin.handlers.async_base_handler import AsyncModelHandler

if __name__ == "__main__":
    # Hardcoded settings for this specific run configuration
    verbose = True
    semantic_judge = "llama3-70b"      # Renamed from batch_model
    differential_diagnosis_model = 'llama2_7b' # Example: choose one for the run
    batch_size = 5
    max_diagnoses = None
    rpm_limit = 1000
    min_batch_interval = 25.0
    test_name = "ramedis"             # Renamed from hospital
    prompt_name = "Semantic_prompt" 
    
    # --- Optional: Add checks or setup using imported functions --- 
    # Example: Check available models or DB models if needed before running
    # handler = AsyncModelHandler()
    # all_models = handler.list_available_models()
    # print("Available API models:", all_models)
    # from db.db_queries_bench29 import get_model_names_from_differential_diagnosis
    # models_tested_for_differential_diagnosis = get_model_names_from_differential_diagnosis()
    # print("\nModels in the differential diagnosis table:", models_tested_for_differential_diagnosis)
    # --- End Optional Setup ---

    # List of differential diagnosis models (previously commented out)
    models = [
        'c3opus',
        'llama2_7b',
        'gpt4turbo1106',
        'geminipro',
        'mixtralmoe',
        'mistral7b',
        'cohere_cplus',
        'gpt4_0613',
        # 'c3opus', # Duplicate removed
        'llama3_70b',
        'gpt4turbo0409',
        'c3sonnet',
        'mixtralmoe_big',
        'llama3_8b'
    ]

    # Empty prompts list
    prompts = []

    # TODO: Potentially loop through 'models' or use them in some way?
    # Currently, only the hardcoded 'differential_diagnosis_model' is used.
    print(f"Defined models list: {models}")
    print(f"Defined prompts list: {prompts}")

    # Construct the command to run judge_semantic_async.py
    # It will always run in Endpoint mode because we include --semantic_judge
    script_path = os.path.join(os.path.dirname(__file__), 'judge_semantic_async.py')
    command = [sys.executable, script_path]

    # Add arguments based on hardcoded settings
    if verbose:
        command.append("--verbose")
    if semantic_judge: # Use renamed variable
        command.extend(["--semantic_judge", semantic_judge]) # Use renamed argument and variable
    if differential_diagnosis_model:
        command.extend(["--differential_diagnosis_model", differential_diagnosis_model])
    if batch_size is not None:
        command.extend(["--batch_size", str(batch_size)])
    if max_diagnoses is not None:
        command.extend(["--max_diagnoses", str(max_diagnoses)])
    if rpm_limit is not None:
        command.extend(["--rpm_limit", str(rpm_limit)])
    if min_batch_interval is not None:
        command.extend(["--min_batch_interval", str(min_batch_interval)])
    if test_name: # Use renamed variable
        command.extend(["--test_name", test_name]) # Use renamed argument and variable
    if prompt_name:
        command.extend(["--prompt_name", prompt_name]) 

    print(f"Running command: {' '.join(command)}")

    # Execute the command (without try...except block)
    # Using Popen for potentially long-running process, stream output
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)
    
    print("--- judge_semantic_async.py Output ---")
    # Stream stdout
    for line in process.stdout:
        print(line, end='')
    
    # Stream stderr
    stderr_output = ""
    for line in process.stderr:
        stderr_output += line
        print(line, end='', file=sys.stderr) # Print errors to stderr as they come

    process.wait() # Wait for the subprocess to finish
    print("--- End Output ---")
    
    if process.returncode != 0:
         print(f"\nError: judge_semantic_async.py exited with code {process.returncode}", file=sys.stderr)
    if stderr_output:
         print("--- judge_semantic_async.py Errors Summary ---", file=sys.stderr)
         print(stderr_output, file=sys.stderr)
         print("--- End Errors Summary ---", file=sys.stderr)
