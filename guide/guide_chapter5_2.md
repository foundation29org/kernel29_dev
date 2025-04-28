# Summary: dxGPT Asynchronous Differential Diagnosis Generation

## Overview

This module (`src.dxGPT`) provides functionality to generate differential diagnoses for clinical cases using various Large Language Models (LLMs). It leverages the `lapin` framework for asynchronous processing, configuration management, database interaction, and modularity, mirroring the structural patterns observed in other project components.

Key features:

-   **Asynchronous Processing**: Uses `lapin.utils.async_batch.process_all_batches` for efficient handling of multiple LLM API calls.
-   **Database Integration**: Fetches input cases from a database table (e.g., `CasesBench`) and stores generated diagnoses (raw response and parsed items) in relational tables (e.g.,`LlmDifferentialDiagnosis`, `DifferentialDiagnosis2Rank`).
-   **Configurable Models**: Supports multiple LLM backends through `lapin`'s configuration system (`models/dxGPT_models.py`).
-   **Modular Prompts**: Uses `lapin`'s `PromptBuilder` pattern (`prompts/dxGPT_prompts.py`) to define and manage different prompt strategies, selectable via configuration.
-   **Flexible Parsing**: Includes parsers (`parsers/dxGPT_parsers.py`) to extract structured diagnosis information from LLM responses.
-   **Structured Execution**: Follows a pattern where a simple runner script (`run_dxGPT_async.py`) invokes the main asynchronous logic (`dxGPT_async.py`).

## Core Components

1.  **`dxGPT_async.py`**: Contains the main asynchronous execution logic and helper functions.
    -   `set_settings()`: Initializes DB session, `AsyncModelHandler`, and the selected `PromptBuilder`.
    -   `retrieve_and_make_prompts()`: Fetches `CasesBench` records, builds prompt strings using the `PromptBuilder`, and prepares simple wrapper objects (`DxGPTInputWrapper`) containing the prompt text and necessary metadata for `process_all_batches`.
    -   `process_results()`: Takes the list of dictionaries returned by `process_all_batches`, extracts the original item data and the LLM response (or error), parses the response based on the original prompt used, and stores results in the database via `queries.dxGPT_queries.insert_differential_diagnoses`.
    -   `main_async()`: Orchestrates the overall process: loads config, calls `set_settings`, `retrieve_and_make_prompts`, `lapin.utils.async_batch.process_all_batches`, and `process_results`, handling setup and cleanup (like DB session closing).
    -   Includes a `if __name__ == '__main__'` block for direct testing/debugging.
2.  **`run_dxGPT_async.py`**: Command-line interface runner.
    -   Uses `argparse` to define arguments (`--model`, `--prompt_alias`, `--num_samples`, etc.).
    -   Sets up logging.
    -   Calls the `main_async()` function in `dxGPT_async.py`, passing the parsed arguments.
3.  **`models/dxGPT_models.py`**: Defines `lapin` configuration classes inheriting from framework base classes (e.g., `lapin.conf.openai_conf.OpenAIConfig`).
4.  **`prompts/dxGPT_prompts.py`**: Defines `PromptBuilder` classes (`lapin.prompt_builder.base.PromptBuilder`) registered with `lapin` (`@register_prompt`).
5.  **`parsers/dxGPT_parsers.py`**: Contains functions to parse LLM outputs (e.g., `universal_dif_diagnosis_parser`, `parse_top5_xml`). JSON parsing logic is currently within `process_results`.
6.  **`queries/dxGPT_queries.py`**: Provides database interaction functions:
    -   `get_model_id`: Retrieves model ID from alias.
    -   `fetch_cases_from_db`: Queries `CasesBench` table.
    -   `insert_differential_diagnoses`: Inserts results into `LlmDifferentialDiagnosis` and `DifferentialDiagnosis2Rank` tables.
7.  **`serialization/dxGPT_schemas.py`**: Defines Pydantic models for internal data structuring (used within `dxGPT_async.py` but not directly by the batch runner).

## Workflow

1.  **Execution**: The `run_dxGPT_async.py` script is executed with command-line arguments.
2.  **Argument Parsing**: The runner parses arguments (model, prompt, filters, etc.).
3.  **Main Logic Invocation**: The runner calls `main_async()` in `dxGPT_async.py`, passing the arguments.
4.  **Configuration Loading**: `main_async()` loads the `LapinConfig` using `lapin.core.config.load_config`, applying arguments as overrides.
5.  **Setup**: `main_async()` calls `set_settings()` to get a DB session, instantiate the `AsyncModelHandler`, and load the specified `PromptBuilder`.
6.  **Input Preparation**: `main_async()` calls `retrieve_and_make_prompts()` which:
    a.  Fetches cases from the DB using `queries.dxGPT_queries.fetch_cases_from_db`.
    b.  For each case, builds the prompt string using the loaded `PromptBuilder`.
    c.  Creates a list of `DxGPTInputWrapper` objects containing the final prompt text and necessary IDs.
7.  **Asynchronous Batch Processing**: `main_async()` calls `lapin.utils.async_batch.process_all_batches`, passing the list of input wrappers, the prompt builder instance (potentially redundant if handler uses config, TBC by lapin usage), the handler instance, model alias, and batching parameters.
8.  **Result Processing**: `main_async()` calls `process_results()` which iterates through the list of results returned by `process_all_batches`:
    a.  Extracts the raw LLM response and original input data.
    b.  Parses the response using the appropriate logic based on the `prompt_alias` stored in the input data.
    c.  Calls `queries.dxGPT_queries.insert_differential_diagnoses` to save the raw response and parsed diagnoses to the database.
9.  **Cleanup**: `main_async()` ensures the database session is closed in a `finally` block.
10. **Completion**: Logging indicates the number of successful operations and errors.

## Database Interaction

-   **Input**: Reads from `CasesBench` table (fields: `id`, `description`, `additional_info`, `hospital`, `case_identifier`). Also reads `Models` table.
-   **Output**:
    -   Creates a record in `LlmDifferentialDiagnosis` (fields: `cases_bench_id`, `model_id`, `prompt_identifier`, `raw_response`).
    -   Creates multiple linked records in `DifferentialDiagnosis2Rank` (fields: `differential_diagnosis_id`, `cases_bench_id`, `rank_position`, `predicted_diagnosis`, `reasoning`).

## Configuration

Configuration is managed by `lapin`. Key aspects:

-   **Model Config**: Defined in `models/dxGPT_models.py`, selected via `--model` argument.
-   **Prompt Builder**: Defined in `prompts/dxGPT_prompts.py`, selected via `--prompt_alias` argument, which sets `params.prompt_alias` in config.
-   **Parameters**: Runtime parameters (`num_samples`, filters, batching settings) passed via CLI arguments and merged into `config.params`.
-   API keys/secrets handled by `lapin` config loading. 