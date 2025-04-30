import subprocess
import sys
import os

# --- Optional Imports (Keep if needed for future setup/checks) ---
# import __init__ # Might be needed depending on dxGPT_async.py's imports
# from lapin.handlers.async_base_handler import AsyncModelHandler
# from db.utils.db_utils import get_session
# from db.queries.get.get_llm import get_models
# --- End Optional Imports ---

if __name__ == "__main__":
    # --- Hardcoded Settings (Adapt from original Debug mode or set new values) ---
    verbose = True
    model_alias = "dxgpt_debug"      # Model alias (e.g., 'llama3_70b', 'dxgpt_debug')
    prompt_alias = "dxgpt_improved" # Prompt alias (e.g., 'dxgpt_standard', 'dxgpt_improved')
    hospital_name = "test_PUMCH_ADM"  # Hospital/Dataset filter ('all', 'ramedis', 'test_PUMCH_ADM')
    num_samples = 5               # Max number of cases (None for all)
    batch_size = 5                # Batch size for API calls
    rpm_limit = 1000              # Requests Per Minute limit
    min_batch_interval = 10.0      # Minimum seconds between batches
    # config_path = "config/lapin_config.yaml" # Uncomment if dxGPT_async.py needs it via CLI
    # --- End Hardcoded Settings ---

    # --- Optional: Add checks or setup using imported functions here if needed ---
    # Example:
    # try:
    #     handler = AsyncModelHandler()
    #     all_models = handler.list_available_models()
    #     print("Available API models:", all_models)
    #     if model_alias not in all_models and model_alias != "dxgpt_debug": # Example check
    #         print(f"Warning: Specified model_alias '{model_alias}' might not be available via API.")
    # except Exception as e:
    #     print(f"Could not initialize AsyncModelHandler or list models: {e}")
    # --- End Optional Setup ---

    # Construct the command to run dxGPT_async.py
    # Assumes dxGPT_async.py is in the same directory as this runner script
    script_path = os.path.join(os.path.dirname(__file__), 'dxGPT_async.py')
    if not os.path.exists(script_path):
        print(f"Error: Could not find script to run at '{script_path}'", file=sys.stderr)
        sys.exit(1)
        
    command = [sys.executable, script_path]

    # Add arguments based on hardcoded settings
    # dxGPT_async.py expects these arguments for its Endpoint mode
    if verbose:
        command.append("--verbose")
    if model_alias: # dxGPT_async.py requires --model for Endpoint mode
        command.extend(["--model", model_alias])
    if prompt_alias: # dxGPT_async.py requires --prompt_alias for Endpoint mode
        command.extend(["--prompt_alias", prompt_alias])
    if hospital_name:
        command.extend(["--hospital", hospital_name])
    if num_samples is not None:
        command.extend(["--num_samples", str(num_samples)])
    if batch_size is not None:
        command.extend(["--batch_size", str(batch_size)])
    if rpm_limit is not None:
        command.extend(["--rpm_limit", str(rpm_limit)])
    if min_batch_interval is not None:
        command.extend(["--min_batch_interval", str(min_batch_interval)])
    # if config_path: # Add if dxGPT_async.py accepts --config_path
    #     command.extend(["--config_path", config_path])

    print(f"Running command: {' '.join(command)}")

    # Execute the command using subprocess.Popen
    try:
        # Using Popen for potentially long-running process, stream output
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1, # Line buffered
            universal_newlines=True,
            # Set cwd if necessary, but should default correctly if run from src/dxGPT
            # cwd=os.path.dirname(script_path) 
        )
        
        print(f"--- Starting execution of {os.path.basename(script_path)} ---")
        
        # Stream stdout
        stdout_output = ""
        if process.stdout:
            for line in process.stdout:
                print(line, end='') # Print line by line as it arrives
                stdout_output += line
        
        # Capture stderr separately
        stderr_output = ""
        if process.stderr:
             stderr_output = process.stderr.read()

        process.wait() # Wait for the subprocess to finish
        print(f"--- Finished execution of {os.path.basename(script_path)} ---")
        
        # Check return code and print stderr if there was an error
        if process.returncode != 0:
            print(f"Error: {os.path.basename(script_path)} exited with code {process.returncode}", file=sys.stderr)
        if stderr_output:
            print(f"--- {os.path.basename(script_path)} Errors/Warnings ---", file=sys.stderr)
            print(stderr_output, file=sys.stderr)
            print("--- End Errors/Warnings ---", file=sys.stderr)

    except FileNotFoundError:
        print(f"Error: The Python interpreter '{sys.executable}' or the script '{script_path}' was not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while trying to run the subprocess: {e}", file=sys.stderr)
        sys.exit(1)

    print("--- Runner Script Finished ---")
