# CHAPTER 5: Generating and Evaluating LLM Diagnostics within the Kernel29 Framework

## Introduction

Previous chapters established the necessity of standardized data processing (`bat29`, Chapter 2) and a robust architectural framework (`Kernel29`, `lapin`, `db`, Chapter 4) for managing the inherent complexities of large-scale Large Language Model (LLM) experimentation. This chapter details the practical application of this framework to the central task of generating differential diagnoses from clinical cases and subsequently evaluating the quality of these diagnoses using LLM-as-judge methodologies.

Leveraging the standardized clinical cases prepared by `bat29` and stored in the central database (`CasesBench` table), the Kernel29 framework orchestrates a multi-stage workflow. Initially, a target LLM processes the clinical cases to generate ranked lists of potential diagnoses along with supporting reasoning (Stage 1: `dxGPT`). Following generation, the diagnostic outputs undergo evaluation. First, a dedicated LLM "judge" assesses the semantic relationship (e.g., synonym, related, unrelated) between each LLM-generated diagnosis and the corresponding gold-standard diagnosis (Stage 2: Semantic Evaluation). Second, another LLM "judge" evaluates the clinical severity (e.g., mild, severe, critical) attributed to each generated diagnosis (Stage 3: Severity Evaluation). This chapter elucidates the purpose, technical design, and core logic of the software modules responsible for each stage, emphasizing the consistent architectural patterns employed and the integral roles of the `lapin` orchestration library and the `db` data persistence component.

## General Technical Architecture: A Modular and Standardized Workflow

The diagnostic generation and evaluation process utilizes three distinct logical stages, implemented as software modules typically residing within the `src/` directory: `dxGPT` for initial diagnosis generation, and components within a `bench29` module for the evaluation stages (Semantic and Severity Judgment). Although functionally distinct, these modules adhere rigorously to the standardized Kernel29 architectural template detailed in Chapter 4.

This workflow heavily leverages the **`lapin` library** (introduced in Chapter 4) for orchestrating LLM interactions. `lapin` handles configuration management, unified model interaction via `AsyncModelHandler`, asynchronous batch processing using `process_all_batches`, and systematic prompt management via the `PromptBuilder` pattern. This allows different models (e.g., `--model llama3_70b`) and prompt strategies (e.g., `--prompt_alias dxgpt_standard`) to be selected at runtime via command-line arguments.

The stages follow the standard operational pattern established in Chapter 4: a command-line runner script (`run_*_async.py`) invokes the core asynchronous logic in a `*_async.py` file. This core module typically contains:

1.  **`set_settings`**: Initializes the DB session, `lapin` handler, and prompt builder.
2.  **`retrieve_and_make_prompts`**: Fetches and transforms data, uses the `PromptBuilder` to create prompts, and prepares wrapper objects for batching. The specific data sources and transformations vary significantly by stage.
3.  **`process_results`**: Parses the raw LLM outputs from `lapin` and structures the data for storage, using stage-specific parsing logic.
4.  **Database Storage**: Uses query functions to persist the structured results.

While the overall structure relies on `lapin` and the `db` component, the implementation details within `retrieve_and_make_prompts` and `process_results` are tailored to the specific task of each stage.

## Stage 1: Differential Diagnosis Generation (`dxGPT`)

### Purpose

The `dxGPT` module serves as the initial stage, responsible for generating differential diagnoses based on clinical case descriptions. It processes standardized clinical cases fetched from the database (`CasesBench` table), utilizing a user-specified LLM (e.g., `llama3_70b`, `gpt4o`, selected via the `--model` argument) and a chosen prompt strategy (e.g., `dxgpt_standard`, `dxgpt_json`, selected via `--prompt_alias`). The output consists of a ranked list of potential diagnoses, often accompanied by justifications comparing case features to diagnostic criteria, which is then stored back into the database.

### Detailed Technical Implementation

Following the standard pattern, the `dxGPT` process is initiated by `run_dxGPT_async.py`, which calls the core logic in `dxGPT_async.py`. The key steps involved are:

1.  **Setup (`set_settings`)**: Initializes the DB session, the `lapin` `AsyncModelHandler` for the target LLM (`--model`), and the `dxGPT` `PromptBuilder` (`--prompt_alias`).
2.  **Input Preparation (`retrieve_and_make_prompts`)**: This function fetches specified `CasesBench` records, uses the loaded `PromptBuilder` to format the clinical narrative for each case according to the chosen strategy, and creates `DxGPTInputWrapper` objects containing the prompt text and necessary metadata (`case_id`, `model_id`, etc.) for `lapin`.
3.  **Asynchronous Processing (`process_all_batches`)**: `lapin` manages the asynchronous dispatch of the wrapped prompts to the configured LLM API, returning a list of results.
4.  **Result Processing (`process_results`)**: This function iterates through the `lapin` results. For each, it extracts the raw LLM response and metadata, selects the appropriate parser (based on `prompt_alias`, often from a `dxGPT/parsers` module) to structure the ranked diagnoses, and calls a database function (e.g., `insert_differential_diagnoses` from a `dxGPT` query module) to store the raw output (e.g., in `LlmDifferentialDiagnosis`) and the parsed rankings (e.g., in `DifferentialDiagnosis2Rank`).

Key internal software dependencies for this stage include the specific model configurations, prompt builders, parsers, and query functions defined within the `dxGPT` module. The primary database tables involved are `CasesBench` and `Models` (for reading input and model details) and `LlmDifferentialDiagnosis` and `DifferentialDiagnosis2Rank` (for writing the generated outputs).

## Stage 2: Semantic Relationship Evaluation

### Purpose

Following the generation and storage of differential diagnoses (in the `DifferentialDiagnosis2Rank` table), the subsequent stage focuses on evaluating the semantic relevance of each proposed diagnosis relative to the established gold-standard diagnosis for the case. This evaluation is performed by a dedicated script (e.g., `run_judge_semantic_async.py`), executing core logic typically found in a corresponding asynchronous module (e.g., `judge_semantic_async.py` within a `bench29` or similar evaluation module). It employs a designated LLM, configured as a "semantic judge", to classify the relationship (e.g., Exact Synonym, Broader Term, Related Condition, Unrelated) between the LLM-generated diagnosis and the gold standard.

### Detailed Technical Implementation

The semantic evaluation process follows the standard architectural pattern, initiated via `run_judge_semantic_async.py`, but with distinct logic in data preparation and result processing.

1.  **Execution**: The runner script takes arguments like the semantic judge model (`--semantic_judge`), the generation model being evaluated (`--differential_diagnosis_model`), and dataset identifiers (`--test_name`).
2.  **Setup (`set_settings`)**: Initializes the DB session, the `AsyncModelHandler` for the specified semantic judge LLM, and the appropriate semantic `PromptBuilder`.
3.  **Input Preparation (`retrieve_and_make_prompts`)**: **This function's logic is tailored to the semantic comparison task.**
    *   Fetches relevant `DifferentialDiagnosis2Rank` records and the corresponding gold-standard diagnoses using database queries.
    *   **Groups** the flat `DifferentialDiagnosis2Rank` records into nested dictionaries per case/model (e.g., using `create_nested_diagnosis_dict`).
    *   **Formats** the data for the semantic judge: Transforms each grouped diagnosis set into a single text prompt containing *both* the gold-standard diagnosis *and* the target LLM's ranked list. This combined text is mapped to a composite key (e.g., `f"{case_id}_{model_id}_{diff_diag_id}"`) in a flat dictionary (e.g., using `dif_diagnosis_dict2plain_text_dict_with_real_diagnosis`).
    *   **Creates an intermediate mapping**: Generates a dictionary mapping the composite keys back to original rank details (e.g., using `nested_dict2rank_dict`), crucial for correlating results later.
    *   **Wraps** the flat dictionary of prompts into `DiagnosisTextWrapper` objects for `lapin`.
    *   **Returns** the list of wrapper objects and the intermediate mapping dictionary.
4.  **Asynchronous Processing (`process_all_batches`)**: `lapin` sends the prompts (containing gold standard + ranked list) to the semantic judge LLM.
5.  **Result Processing (`process_results`)**: This function receives the raw results and the intermediate mapping dictionary.
    *   For each result, it calls a specific parser (e.g., `parse_judged_semantic`) which uses the mapping dictionary to extract the semantic relationship category for *each* ranked diagnosis compared in the prompt.
    *   Separates successful parses from failures.
    *   **Returns** the list of successful parses and failures.
6.  **Database Storage**: Calls a specific database function (e.g., `add_semantic_results_to_db`) to insert the successfully parsed judgments into the target table (e.g., `DifferentialDiagnosis2SemanticRelationship`).

Internal dependencies involve prompt builders, parsers, and utility functions within the evaluation module (`bench29`), common and specific query functions within the `db` component, and core `lapin` and `db.utils` components. Database interaction involves reading from `DifferentialDiagnosis2Rank`, `CasesBenchDiagnosis`, `CasesBench`, and `Models`, and writing the evaluation results to `DifferentialDiagnosis2SemanticRelationship`.

## Stage 3: Severity Evaluation

### Purpose

As a complementary evaluation, this stage assesses the clinical severity associated with each *individual* diagnosis proposed by the initial diagnosis-generating LLM. This helps understand if the LLM suggests appropriately severe conditions. The process is managed by a script (e.g., `run_judge_severity_async.py`), executing core logic in a corresponding asynchronous module (e.g., `judge_severity_async.py` within `bench29`). It uses a designated LLM configured as a "severity judge".

### Detailed Technical Implementation

The severity evaluation follows the standard pattern initiated by `run_judge_severity_async.py`, differing from the semantic stage primarily in prompt content and parsing.

1.  **Execution**: The runner script takes arguments like the severity judge model (`--severity_judge`), the model being evaluated (`--differential_diagnosis_model`), and dataset identifiers (`--test_name`).
2.  **Setup (`set_settings`)**: Initializes the DB session, the `AsyncModelHandler` for the specified severity judge LLM, and the appropriate severity `PromptBuilder`.
3.  **Input Preparation (`retrieve_and_make_prompts`)**: **Logic focuses on preparing individual diagnoses for severity assessment.**
    *   Fetches relevant `DifferentialDiagnosis2Rank` records.
    *   **Groups** records into nested dictionaries per case/model (e.g., using `create_nested_diagnosis_dict`).
    *   **Formats** data for the severity judge: Transforms each nested dictionary into a text string containing *only* the target LLM's ranked diagnosis list (gold standard is *not* included). Maps this text to a composite key in a flat dictionary (e.g., using `dif_diagnosis_dict2plain_text_dict`).
    *   **Creates the intermediate mapping**: Generates a dictionary mapping composite keys back to original rank details (e.g., using `nested_dict2rank_dict`).
    *   **Wraps** the flat dictionary into `DiagnosisTextWrapper` objects for `lapin`.
    *   **Returns** the list of wrapper objects and the intermediate mapping dictionary.
4.  **Asynchronous Processing (`process_all_batches`)**: `lapin` sends the prompts (containing only the ranked diagnoses list) to the severity judge LLM.
5.  **Result Processing (`process_results`)**: Receives raw results and the intermediate mapping dictionary.
    *   For each result, calls a specific severity parser (e.g., `parse_judged_severity`) which uses the mapping dictionary to extract the severity level for each diagnosis.
    *   Separates successful parses from failures.
    *   **Returns** the list of successful parses and failures.
6.  **Database Storage**: Calls a specific database function (e.g., `add_severity_results_to_db`) to insert the successfully parsed severity judgments into the target table (e.g., `DifferentialDiagnosis2Severity`).

Internal dependencies involve prompt builders, parsers, and utility functions within the evaluation module (`bench29`), common and specific query functions within the `db` component, and core `lapin` and `db.utils` components. Database access includes reading `DifferentialDiagnosis2Rank`, `CasesBench`, and `Models`, and writing the evaluation results to `DifferentialDiagnosis2Severity`.

## Conclusion

This chapter illustrated the application of the Kernel29 framework to orchestrate a sophisticated, multi-stage workflow for generating and evaluating LLM-based differential diagnoses. By adhering to the standardized module structures and leveraging the `lapin` library for LLM interaction and the `db` component for data persistence (as detailed in Chapter 4), the framework facilitates systematic and scalable experimentation. Each stage (`dxGPT`, Semantic Judgment, Severity Judgment) follows the established architectural pattern.

While maintaining structural consistency, the framework accommodates the unique requirements of each stage through tailored implementations within the `retrieve_and_make_prompts` and `process_results` functions, alongside stage-specific prompt builders and parsers. This highlights the framework's flexibility, demonstrated by the differing logic for prompt preparation (e.g., including gold standard for semantics vs. not for severity) and result parsing.

This modular, data-centric architecture enables robust assessment of LLM performance in clinical diagnosis. The structured capture of results in the database (`DifferentialDiagnosis2Rank`, `DifferentialDiagnosis2SemanticRelationship`, `DifferentialDiagnosis2Severity` tables) provides a foundation for the quantitative analyses and comparative evaluations discussed in subsequent phases.
