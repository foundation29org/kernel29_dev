## CHAPTER 3: Modularity, Standardization & Data-Centric Approach

### Introduction

Initial script-based LLM experimentation (e.g., `dxgpt-testing-main`) is effective for rapid tests but scales poorly. Adapting via script duplication rather than refactoring leads to operational inefficiencies, poor reproducibility, and difficulties in managing configurations scattered across large, divergent codebases. Reliance on file-based I/O hinders data integrity and analysis, while lack of modularity (e.g., duplicated API logic) and standardization complicates integration and comparison (See table 4) .

### Approach
Kernel29 addreses these issues by adhering to a standardized architecture to interact whit LLMs whatever the task whit clear separation of concerns (see below). In addition, it has been introduced:

*   **`lapin`:** Abstracts LLM API differences, providing a standard interaction layer.
*   **`lapin.PromptBuilder`:** Enables systematic, programmatic prompt management and tracking.
*   **`db` (SQLAlchemy):** Implements a robust database backend for structured input/output capture. This ensures data integrity, facilitates analysis, and streamlines potential integration with web applications (e.g., throgout integration whit FastAPI and a frontend).

#### Standardized architecture to interact whit LLMs 

