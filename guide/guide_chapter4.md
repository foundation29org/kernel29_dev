## CHAPTER 4: The Kernel29 Framework Architecture

### Framework Overview

Previous chapters detailed the significant hurdles in large-scale LLM experimentation: managing combinatorial complexity  and ad-hoc engineering practices(Chapter 1, Tables 1-4), ensuring robust data standardization (Chapter 2, `bat29`), and implementing meaningful evaluation metrics (Chapter 3). The sheer scale and intricacy demand a departure from unstructured approaches, which inevitably lead to the inefficiencies, irreproducibility, and scalability issues outlined previously.

**Kernel29** provides this essential architectural solution. It offers a structured environment specifically designed to tackle the interwoven engineering and data science demands of systematic LLM research and development. By establishing clear conventions and providing integrated core components, Kernel29 enables maintainable, reproducible, and scalable workflows. The framework is principally composed of:

1.  A standardized module architecture for task-specific code.
2.  The `lapin` library for unified LLM interaction, configuration, and execution.
3.  A central `db` component for structured, persistent storage of all experimental data, including inputs, configurations, LLM outputs, and evaluations.

### Core Components: `lapin` and `db`

Addressing the complexity and data management needs of large-scale LLM experimentation requires dedicated tooling. Kernel29 provides two foundational components for this purpose: `lapin` for managing LLM interactions and experimental orchestration, and `db` for ensuring data persistence and integrity.

#### `lapin`: LLM Interaction and Orchestration
Extensive LLM experimentation, demands a centralized solution capable of managing scale and complexity effectively. Otherwise, operational challenges (e.g. handle heterogeneous LLM API protocols) would dominate development effort, hindering research progress. 

`lapin` serves as this crucial infrastructural component within Kernel29. It encapsulates the necessary logic for handling API diversity, managing configurations via aliases, building prompts dynamically, and orchestrating asynchronous execution. By providing this standardized toolkit, `lapin` abstracts away operational challengues, enabling researchers and developers to focus on designing experiments, analyzing results, and advancing the core scientific objectives of the project.

**Key Features of `lapin`:**

| Feature                 | Description                                                                                                                               | Relevant `lapin` Modules/Classes                     |
| :---------------------- | :---------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------- |
| **API Abstraction**     | Provides unified handlers to interact with different LLM provider APIs, masking underlying differences.                                   | `lapin.handlers` (e.g., `AsyncModelHandler`)         |
| **Configuration**       | Defines and manages LLM configurations (model details, API keys, parameters) through dedicated objects and loading mechanisms.          | `lapin.core.config.LapinConfig`, `load_config`       |
| **Component Registry**  | Allows `LapinConfig` and `PromptBuilder` instances to be registered with unique string aliases for easy reference and loading.            | `@register_config`, `@register_prompt` decorators  |
| **Dynamic Loading**     | Enables runtime selection and instantiation of registered configurations and prompt builders based on their aliases, typically via CLI args. | Implicitly used by runner scripts via registration |
| **Prompt Engineering**  | Provides a structured way (`PromptBuilder`) to define, manage, and version different prompt strategies programmatically.             | `lapin.prompt_builder.base.PromptBuilder`            |
| **Batch Processing**    | Offers utilities for efficient, asynchronous batching of API requests to improve performance when processing large datasets.          | `lapin.utils.async_batch.process_all_batches`      |

#### `db`: Data Persistence and Integrity

A core principle of Kernel29 is a data-centric workflow, shifting from fragile file-based I/O to a structured, persistent database layer (`db`). This approach is crucial for ensuring the reproducibility, traceability, and analytical potential of experimental results. By centralizing inputs, outputs, configurations, and evaluations in a database (typically using SQLAlchemy), Kernel29 facilitates robust data management.

**Key Database Tables (Illustrative, based on Model Definitions):**

The database is organized into schemas (like `bench29`, `registry`, `llm`, `prompts`). Below are some important tables, primarily from the `bench29` schema, ordered by likely importance for core experimental workflows:

| SQLAlchemy Model Class                        | Description                                                                                                                               | Schema    |
| :-------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------- | :-------- |
| `CasesBench`                                    | Stores the primary clinical case data used as input for LLM tasks, including the original text and source metadata (e.g., hospital).    | `bench29` |
| `CasesBenchDiagnosis`                           | Stores the gold standard (correct) diagnosis associated with each case in `CasesBench`, used for evaluation.                              | `bench29` |
| `LlmDifferentialDiagnosis`                    | Records the raw output generated by a specific LLM (`Models`) using a specific prompt (`Prompt`) for a given case (`CasesBench`).         | `bench29` |
| `DifferentialDiagnosis2Rank`                | Parses the raw `LlmDifferentialDiagnosis` output into a ranked list of predicted diagnoses, storing each diagnosis, its rank, and reasoning. | `bench29` |
| `DifferentialDiagnosis2Severity`            | Stores severity judgments (linking to `SeverityLevels`) for each ranked diagnosis generated by an LLM or a judge.                         | `bench29` |
| `DifferentialDiagnosis2SemanticRelationship`  | Stores semantic relationship judgments vs gold (linking to `DiagnosisSemanticRelationship`) for each ranked diagnosis.                | `bench29` |
| `LlmAnalysis`                                 | An aggregation table combining case, LLM output, ranking, and judgment information for comprehensive analysis.                             | `bench29` |
| `CasesBenchMetadata`                          | Stores supplementary metadata about clinical cases, such as predicted complexity, specialty, or severity (links to `registry` tables). | `bench29` |
| `Models`                                        | Defines the LLM models used in experiments, including their registered `alias`, full `name`, and `provider`.                           | `llm`     |
| `Prompt`                                        | Defines the different prompt templates used, identified by `alias`, storing `content`, metadata, and linking to the creator (`User`). | `prompts` |
| `SeverityLevels`                              | Registry table defining possible severity levels (e.g., Low, Medium, High) used for case metadata and diagnosis judgments.           | `registry`|
| `DiagnosisSemanticRelationship`               | Registry table defining categories for comparing predicted vs gold diagnoses (e.g., Exact Match, Parent, Child).                        | `registry`|
| `ComplexityLevels`                            | Registry table defining possible complexity levels for clinical cases.                                                                  | `registry`|

*Note: This table list is illustrative and focuses on core experimental data. Additional tables like `PromptArguments`, `PromptRelationship`, etc., exist for more detailed tracking within the `prompts` schema.*

### Standardized Module Architecture

Building upon `lapin` and `db`, Kernel29 enforces a standardized structure for implementing specific LLM-driven tasks. Each task is encapsulated within its own module (e.g., `src/dxGPT` for diagnosis generation, `src/bench29` for evaluation). This modularity promotes separation of concerns, code reuse, and maintainability.

A standard module typically contains the following subdirectories, file types and functions:

**Standard Directories:**

| Directory       | Purpose                                                                                                                                                                                                                         |
| :-------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `models/`       | Contains `LapinConfig` subclass definitions specific to the module, registered with `lapin` via aliases.                                                                                                                      |
| `prompts/`      | Contains `PromptBuilder` implementations specific to the task, also registered via aliases.                                                                                                                                  |
| `parsers/`      | Includes functions responsible for parsing and structuring the raw outputs received from LLMs.                                                                                                                                |
| `queries/`      | Intended for complex, task-specific database interactions or refined query logic not suitable for the central query repository (`src/db/queries/`). *Note: Query logic may also be found directly within core logic files.* |
| `serialization/`| (Optional) May contain Pydantic models for data validation and clear data contracts.                                                                                                                                      |

**Standard File Patterns:**

| File Pattern / Type                 | Purpose                                                                                                                                                                                                                                                           | Example Filename(s)       |
| :---------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------ |
| `run_*_async.py`                    | The executable entry point for the module (Runner Script). Handles CLI arguments, setup, and orchestration via the Core Logic File.                                                                                                                                         | `run_dxGPT_async.py`    |
| `*_async.py`                        | Contains the main asynchronous functions (Core Logic) implementing the task's workflow (data fetching, prep, processing, storage). May currently contain embedded database query logic.                                                                               | `dxGPT_async.py`        |
| `*_models.py` inside `models/`      | Defines specific `LapinConfig` classes, typically inheriting from `lapin` base configs, to specify model parameters, endpoints, etc.                                                                                                                                        | `dxGPT_models.py`       |
| `*_prompts.py` inside `prompts/`    | Defines specific `PromptBuilder` classes, inheriting from `lapin.prompt_builder.base.PromptBuilder`, registered with `lapin`.                                                                                                                                        | `dxGPT_prompts.py`      |
| `*_parsers.py` inside `parsers/`    | Defines parsing functions responsible for extracting structured data from raw LLM text responses.                                                                                                                                                                           | `dxGPT_parsers.py`      |
| `*_queries.py` inside `queries/`    | Defines complex/specific database query functions for the module, potentially involving multiple tables or intricate logic beyond simple CRUD.                                                                                                                      | `dxGPT_queries.py`      |
| `src/db/queries/{get or post}/*.py`    | **Intended** location for reusable, general-purpose query functions (`get_*`, `add_*`) interacting with specific schemas, often grouped by operation type.                                                                                                                | (e.g., `get/cases.py`)  |
| `src/db/db_queries_{schema}.py`     | **Current/Legacy** location where many general query functions currently reside due to development history, often grouping queries by schema (e.g., bench29).                                                                                                               | `db_queries_bench29.py` |

**Common Function/Mode Conventions:**

| Convention Name / Pattern         | Purpose                                                                                                                                                                                                                                                                                                                                                                                          | Example Functions/Modes                   |
| :-------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------- |
| `main` / `main_async`             | Main orchestrator function within the Core Logic file, called by the Runner Script.                                                                                                                                                                                                                                                                                                          | `main`, `main_async`                    |
| `set_settings`                  | Initializes common resources like DB session, `lapin` handler, and prompt builder based on configuration/arguments.                                                                                                                                                                                                                                                                                 | `set_settings`                          |
| `retrieve_and_make_prompts`     | Fetches input data from the database (using query functions, wherever they reside), processes/transforms it, and formats it for batch processing via `lapin`.                                                                                                                                                                                                                                                  | `retrieve_and_make_prompts`             |
| `process_results`               | Takes the raw output from `lapin`'s batch processing, parses it using functions from `parsers/`, and prepares results for database storage (using query functions, wherever they reside).                                                                                                                                                                                                               | `process_results`                       |
| `get_*`                         | Functions responsible for retrieving data from the database. **Ideally centralized** in `src/db/queries/get/`, but **currently scattered** across various locations including legacy files (`src/db/db_queries_*.py`), the central query directory (`src/db/queries/get/`), module-specific query directories (`{module_root}/queries/`), and potentially embedded within core logic files or other utility directories. | `get_cases`, `get_model_id`             |
| `add_*`                         | Functions responsible for inserting or updating data in the database. **Ideally centralized** in `src/db/queries/post/`, but **currently scattered** across various locations including legacy files (`src/db/db_queries_*.py`), the central query directory (`src/db/queries/post/`), module-specific query directories (`{module_root}/queries/`), and potentially embedded within core logic files or other utility directories. | `add_semantic_results_to_db`, `add_differential_diagnoses` |
| `parse_*` (in `parsers/`)         | Module-specific functions dedicated to extracting structured information from LLM text responses.                                                                                                                                                                                                                                                                                             | `parse_judged_semantic`, `parse_top5_xml` |
| Endpoint Mode vs. Debug Mode    | Scripts often support execution via CLI arguments (Endpoint) for automation, or using hardcoded values (Debug) for development/testing.                                                                                                                                                                                                                                                            | Determined by presence of specific CLI args |

This consistent architecture ensures that different tasks within the Kernel29 project share a common structure, simplifying navigation, understanding, and extension of the codebase while leveraging the core `lapin` and `db` functionalities.




