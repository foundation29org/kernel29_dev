# Refactoring Rationale: `batch_diagnosis_SJD.py` to Modular Framework

## Introduction: From Standalone Scripts to Modular Framework

The previous approach to tasks like differential diagnosis generation or evaluation, exemplified by scripts found in the `dxgpt_testing-main` directory (e.g., `batch_diagnosis_SJD.py`, `batch_diagnosis_v2.py`, `HM_diagnoses_analisis.py`), suffered from several drawbacks common to rapidly developed standalone tools:

*   **Monolithic Structure and Duplication:** Core logic, data handling, API interactions, prompt definitions, parsing, and execution control were often tightly coupled within single large files. Generating variations for different datasets or models frequently involved duplicating entire scripts (`batch_diagnosis_*.py`), leading to significant code redundancy and maintenance challenges.
*   **Mixed Concerns:** A single script might handle data loading from various sources (CSV, Excel, DOCX), interact with multiple LLM APIs using different methods (direct SDKs, `langchain`), contain hardcoded prompts, implement basic parsing (e.g., regex), and manage file output.
*   **Inflexible and Scattered Configuration:** Configuration relied on hardcoded paths, commented-out code blocks, environment variables for secrets, and basic script arguments. This made managing different experimental setups difficult and lacked a unified configuration system.
*   **File-Based I/O:** The primary workflow involved reading from and writing to intermediate files (CSVs, Excel), hindering data integrity, querying capabilities, and integration with a centralized data store.
*   **Lack of Standardization and Clarity:** The absence of a common framework or architectural pattern made the codebase harder to understand, maintain, or extend collaboratively. The proliferation of similar scripts obscured the overall workflow and the specific roles of generation vs. evaluation.
*   **Limited Testability:** The intertwined nature of the code made unit testing individual components challenging.

The refactoring addresses these issues by migrating functionality into dedicated modules (like `src.dxGPT` and `src.bench29`) that leverage the `lapin` framework and adhere to a standardized architecture. This results in modular, database-centric, configurable, and maintainable components integrated within the larger project structure, adopting established patterns for consistency and robustness.

## Key Architectural Principles of `dxGPT` and `bench29`

The migration to dedicated modules (`src.dxGPT`, `src.bench29`) leverages the `lapin` framework and adopts a common architecture, offering significant improvements. The core principles are:

1.  **Addressing Monolithic Code and Separation of Concerns:**
    *   Functionality is broken down into distinct, reusable components following a consistent structure:
        *   **Runner Scripts (`run_*_async.py`):** Serve as the command-line entry points (e.g., `run_dxGPT_async.py`, `run_judge_severity_async.py`). They handle argument parsing, setup logging, load configurations, and orchestrate the overall workflow by calling the main asynchronous logic.
        *   **Core Logic Files (`*_async.py`):** Contain the main asynchronous functions and helper utilities for data preparation, processing results, and interacting with other components (e.g., `dxGPT_async.py`, `judge_severity_async.py`).
        *   **Configuration (`models/`):** Houses `LapinConfig` subclasses defining specific LLM configurations.
        *   **Prompts (`prompts/`):** Contains `PromptBuilder` implementations specific to the module's task.
        *   **Parsing (`parsers/`):** Includes functions dedicated to extracting structured information from potentially unstructured LLM responses.
        *   **Database Interactions (`queries/`):** Encapsulates all SQL queries and database operations, interacting with the defined data models (often using SQLAlchemy).
        *   **Data Contracts (`serialization/`):** Defines Pydantic schemas for validating and structuring data passed between components or used in database interactions.
    *   **Benefits:** This separation enhances code **reusability**, simplifies **maintenance** (changes are localized), and significantly improves **testability** (individual components can be unit-tested).
    *   **Standardized Naming Conventions:** Consistency in naming helps understand the codebase structure and component roles:
        *   **Module Entry Points:** Follow the `run_*_async.py` pattern.
        *   **Core Logic:** Follow the `*_async.py` pattern.
        *   **Database Query Functions (`queries/`):** Adhere to a convention where functions retrieving data are prefixed with `get_*` (e.g., `get_model_id`) and functions inserting or updating data are prefixed with `add_*` (e.g., `add_severity_judgements`, `add_semantic_judgements`). This pattern is established in `bench29` and will be followed by `dxGPT`.

2.  **Orchestrating LLM Variations: API, Prompts, and Configuration**
    *   **The Challenge:** Running experiments across numerous LLMs, prompts, datasets, and evaluation criteria (like different "judge" models) creates a significant combinatorial challenge. Testing 10 generator models with 5 prompts across 10 datasets results in 500 unique configurations. Adding 3 distinct judge models to evaluate these outputs increases this to 1500 combinations. The previous approach, exemplified by scripts like `batch_diagnosis_Ruber.py` or `HM_diagnoses_analisis.py`, often handled this through extensive code duplication (e.g., separate initialization functions for each API), hardcoded parameters scattered throughout scripts, and complex manual setup. This made experiments difficult to manage, reproduce, scale, and analyze efficiently, necessitating database integration for tracking results.
    *   **The Solution (`lapin` Framework):** `dxGPT` and `bench29` leverage the `lapin` framework to manage this complexity effectively:
        *   **Unified API Interaction:** Abstracts differences between various LLM APIs through `lapin.handlers.async_base_handler.AsyncModelHandler`, eliminating the need for numerous, model-specific initialization functions seen previously.
        *   **Centralized & Dynamic Configuration:** Uses `lapin.core.config.LapinConfig` and configuration files (e.g., in `dxGPT/models/`) managed by `lapin.core.config.load_config`. This replaces scattered, hardcoded settings and allows models and their parameters to be selected dynamically at runtime (e.g., by alias via command-line arguments).
        *   **Modular Components via Registration:** Leverages `lapin`'s registration mechanism (`@register_config`, `@register_prompt`) to discover and instantiate components like model configurations (see `dxGPT/models/dxGPT_models.py`) and prompt builders (see `dxGPT/prompts/dxGPT_prompts.py`) simply by using their alias. This avoids duplicating entire scripts just to change the model or prompt.
        *   **Prompt Abstraction:** Implements the `lapin.prompt_builder.base.PromptBuilder` pattern (in `prompts/`) for consistent, reusable prompt definition and construction, facilitating easy swapping of different prompt strategies.
        *   **Standardized Asynchronicity:** Employs `lapin.utils.async_batch.process_all_batches` for efficient, concurrent API calls, providing a consistent and scalable execution mechanism regardless of the specific model or prompt combination being tested.
    *   **Example (`judge_semantic_async.py`):** The `judge_semantic_async.py` script demonstrates this orchestration. It uses command-line arguments to dynamically specify the `semantic_judge` model, the `differential_diagnosis_model` (whose outputs are being evaluated), and the `prompt_name`. The script then seamlessly integrates these selected components using the underlying `lapin` framework mechanisms, retrieving configurations and prompts by their registered aliases and executing the task via the standardized batch processing. This approach offers significant flexibility and scalability compared to the substantial code modifications or duplications that would be required in the older scripts to achieve the same outcome.

3.  **Database-Centric Workflow:**
    *   Modules interact directly with a central database, moving away from intermediate file I/O (like CSVs).
    *   **Input:** Data required for processing (e.g., clinical cases, items to be judged) is fetched from database tables using functions within the `queries/` directory (e.g., `queries.dxGPT_queries.fetch_cases_from_db`).
    *   **Output:** Results, including raw LLM responses and parsed/structured data, are written back to dedicated database tables atomically (e.g., `queries.dxGPT_queries.insert_differential_diagnoses`, `queries.judge_severity_queries.add_severity_judgements`).
    *   **Benefits:** Ensures data integrity through database constraints and transactions, facilitates easier data querying and analysis, and provides a single source of truth.

4.  **Scalability and Extensibility:**
    *   The asynchronous nature (`process_all_batches`) provides inherent scalability for handling large volumes of API calls.
    *   The modular design and `lapin`'s registration system make extending the modules straightforward – adding support for new LLMs, prompt strategies, or parsing logic typically involves creating new classes or functions in the appropriate directory without major modifications to the core workflow.

In conclusion, transitioning to modules like `dxGPT` and `bench29` built upon these principles results in robust, maintainable, and integrated components within the `lapin` ecosystem. This standardized architecture directly addresses the limitations of the previous standalone, duplicated, and file-centric scripts, providing a much more reliable and extensible system. 