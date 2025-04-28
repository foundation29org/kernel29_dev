# CHAPTER 8: Dynamic Prompt Engineering with `lapin.prompt_builder`

## Introduction

Effective Large Language Model (LLM) interaction hinges significantly on prompt engineering. As highlighted in Chapter 1 (Table 4), hardcoding prompts or scattering prompt logic across application code leads to inflexibility, poor maintainability, and difficulty in systematic experimentation. `lapin` addresses this challenge through its `prompt_builder` component, providing a structured and dynamic approach to defining, managing, and utilizing prompt strategies.

This chapter delves into the technical implementation of the `lapin.prompt_builder`, focusing on the `PromptBuilder` base class found in `lapin/prompt_builder/base.py`. We will examine how it enables the separation of prompt construction logic from core application code, facilitates the assembly of prompts from various sources, and integrates with the `lapin` registry system for dynamic selection of prompt strategies at runtime.

## Core Concept: The `PromptBuilder` Base Class

The foundation of the system is the abstract base class `lapin.prompt_builder.base.PromptBuilder`. Subclasses inheriting from `PromptBuilder` encapsulate the logic for constructing a specific type of prompt.

**Key Characteristics and Methods:**

1.  **Section-Based Composition**: `PromptBuilder` allows prompts to be built from distinct named "sections". These sections represent reusable parts of a prompt (e.g., instructions, context definitions, examples, output format specifications).
2.  **Flexible Section Loading**: The base class provides methods to load content for these sections from various sources during the builder's initialization:
    *   `load_section_from_db(...)`: Fetches section content stored in a database (likely via `bench29.libs.prompt_libs.get_prompt`).
    *   `load_section_from_file(...)`: Loads section content from a file path.
    *   `load_section_from_table(...)`: Loads and transforms data from a database table.
    *   `load_section_from_text(...)`: Uses a provided string directly (e.g., for default instructions).
    *   `set_section(...)`: Directly assigns content to a section.
    Loaded section content is stored in the `self.sections` dictionary.
3.  **Meta Template (`set_meta_template`)**: Each builder defines a main template string (`self.meta_template`). This string uses standard Python f-string/`.format()` style placeholders (`{placeholder_name}`) to indicate where:
    *   Static section content (`self.sections`) should be inserted.
    *   Dynamic, runtime arguments (like the specific input text or case details) should be placed.
4.  **Initialization Logic (`initialize`)**: This is an **abstract method** that *must* be implemented by each specific `PromptBuilder` subclass. The `initialize` method is responsible for:
    *   Calling `set_meta_template` to define the prompt's overall structure.
    *   Calling the various `load_section_*` methods to populate `self.sections` with the required static content for that specific prompt strategy.
5.  **Template Building (`build_template`)**: This internal method orchestrates the first stage of prompt construction. It calls `build_partial_template`, which substitutes the static content from `self.sections` into the `self.meta_template`. The result (`self.prompt_template`) is a template string where static parts are filled in, but placeholders for dynamic runtime arguments remain.
6.  **Runtime Formatting (`to_prompt`)**: This is the **primary method called by application code** to generate the final, fully formatted prompt string. It performs the following:
    *   Ensures `build_template` has been called (if not, it calls it).
    *   Takes the dynamic runtime data as input. This can be a single `text` argument (if only one dynamic placeholder like `{input_text}` remains in `self.prompt_template`) or a `kwargs` dictionary for multiple dynamic placeholders (`{case_narrative}`, `{patient_age}`, etc.).
    *   Uses Python's string `.format(**kwargs)` method on `self.prompt_template` to insert the dynamic runtime values into the remaining placeholders.
    *   Returns the final, complete prompt string ready to be sent to the LLM via a `lapin` Handler.

## The Prompt Registry (`@register_prompt`)

Similar to how model configurations are managed (Chapter 7), `lapin` employs a registry for `PromptBuilder` subclasses. 

1.  **Registration**: The `@register_prompt("alias_name")` decorator associates a unique string alias (e.g., `dxgpt_standard`, `judge_semantic_v1`) with a specific `PromptBuilder` subclass.
2.  **Dynamic Loading**: During the `set_settings` phase of a Kernel29 module (Chapter 5), the prompt alias provided via CLI arguments (e.g., `--prompt_alias dxgpt_standard`) is used to look up the corresponding `PromptBuilder` class in the registry.
3.  **Instantiation & Initialization**: An instance of the selected `PromptBuilder` subclass is created, and its `initialize()` method is called. This prepares the builder by loading its sections and setting its meta-template according to its specific strategy.

This registry mechanism allows users to easily switch between different, potentially complex prompt strategies at runtime simply by changing a command-line argument, facilitating systematic experimentation.

## Integration with Kernel29 Workflow

The initialized `PromptBuilder` instance plays a crucial role within the standard Kernel29 module workflow (Chapter 5), typically within the `retrieve_and_make_prompts` function or similar data preparation steps:

1.  **Data Fetching**: Input data (e.g., clinical cases from `CasesBench`) is retrieved from the database.
2.  **Prompt Generation**: For each data item, the relevant dynamic information is extracted and passed to the `prompt_builder.to_prompt(kwargs=dynamic_data)` method. This generates the final prompt string.
3.  **Wrapping**: The generated prompt string, along with necessary metadata, is wrapped in an input object (e.g., `DxGPTInputWrapper`) ready for batch processing.

In the context of asynchronous batching (`lapin.utils.async_batch`), the `process_all_batches` function utilizes the `prompt_template` object (which is the initialized `PromptBuilder` instance) within its `async_prompt_processing` helper to call `prompt_template.to_prompt(text)` for each item before passing the result to the `AsyncModelHandler`.

## Advantages of the `PromptBuilder` Approach

This structured approach to prompt management offers significant technical advantages:

*   **Separation of Concerns**: Prompt design and logic (defining templates, loading sections) are cleanly separated from the core application logic (data fetching, LLM interaction orchestration, result processing).
*   **Reusability**: Common prompt sections (e.g., standard instructions, safety guidelines) can be defined once (in files or DB) and loaded by multiple `PromptBuilder` subclasses.
*   **Consistency**: Ensures prompts for a given strategy are constructed identically every time, following the logic defined in the specific `PromptBuilder` subclass.
*   **Experimentation Agility**: Switching between fundamentally different prompt strategies (e.g., zero-shot vs. few-shot, XML vs. JSON output format) is achieved by simply changing the `--prompt_alias` argument, without altering application code.
*   **Maintainability**: Modifying or updating a specific prompt strategy only requires changes within the corresponding `PromptBuilder` subclass and its associated sections/meta-template.
*   **Readability**: Complex prompt logic involving multiple parts and conditional formatting is encapsulated within the builder, making the main application code cleaner.

## Conclusion

The `lapin.prompt_builder` component provides a robust and flexible system for managing prompt engineering within the Kernel29 framework. By combining a section-based loading mechanism, meta-templates, a clear initialization and formatting lifecycle (`initialize`, `build_template`, `to_prompt`), and integration with a dynamic registry (`@register_prompt`), it effectively decouples prompt logic from application code. This facilitates easier maintenance, promotes consistency, and enables rapid experimentation with different prompt strategies, complementing the configuration and execution capabilities of the `lapin` handlers and callers described in Chapter 7. 