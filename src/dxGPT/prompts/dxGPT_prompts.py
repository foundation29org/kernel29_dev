"""
Prompt builders for the dxGPT diagnosis generation task.
Follows the lapin PromptBuilder pattern using meta-templates and sections.
"""
from typing import Dict, Any

# Assuming lapin provides these base components
try:
    from lapin.prompt_builder.base import PromptBuilder, register_prompt
except ImportError:
    # Dummy implementations if lapin is not fully available
    class PromptBuilder:
        def __init__(self, verbose: bool = False):
            self.verbose = verbose
            self.template = ""
            self.sections = {}
            self.meta_template = "" # Must be defined by subclasses

        def load_section_from_text(self, name: str, text: str):
            self.sections[name] = text
            if self.verbose: print(f"Loaded section '{name}'")

        def build_template(self):
            """Builds the main template string from sections and meta_template."""
            try:
                self.template = self.meta_template.format(**self.sections)
                if self.verbose: print("Template built successfully.")
            except KeyError as e:
                print(f"[ERROR] Missing section key in meta_template: {e}")
                self.template = f"Error: Missing section {e}"
        
        def build(self, **kwargs) -> str:
            """Builds the final prompt string using the loaded template and provided kwargs."""
            # Assumes self.template is already built by build_template()
            try:
                return self.template.format(**kwargs)
            except KeyError as e:
                 print(f"[ERROR] Missing key in kwargs during final prompt build: {e}")
                 return f"Error: Missing build key {e}"

    def register_prompt(cls):
        # Dummy decorator
        return cls

# --- Specific Prompt Builders --- 

@register_prompt
class StandardDxGPTPrompt(PromptBuilder):
    """Builds the standard diagnosis prompt."""
    @classmethod
    def alias(cls) -> str:
        return "dxgpt_standard"

    def __init__(self, verbose: bool = False):
        super().__init__(verbose=verbose)
        # Define meta template with placeholder for dynamic description
        self.meta_template = """
{intro}
Symptoms:{description}
"""
        self._initialize() # Load sections and build template

    def _initialize(self):
        intro_text = "Behave like a hypotethical doctor who has to do a diagnosis for a patient. Give me a list of potential diseases with a short description. Shows for each potential diseases always with '\n\n+' and a number, starting with '\n\n+1', for example '\n\n+23.' (never return \n\n-), the name of the disease and finish with ':'. Dont return '\n\n-', return '\n\n+' instead. You have to indicate which symptoms the patient has in common with the proposed disease and which symptoms the patient does not have in common. The text is"
        self.load_section_from_text("intro", intro_text)
        self.build_template() # Build the template after loading static sections

    # build() method is inherited from base class

@register_prompt
class RareDxGPTPrompt(PromptBuilder):
    """Builds the rare disease focused diagnosis prompt."""
    @classmethod
    def alias(cls) -> str:
        return "dxgpt_rare"

    def __init__(self, verbose: bool = False):
        super().__init__(verbose=verbose)
        self.meta_template = """
{intro}
Symptoms:{description}
"""
        self._initialize()

    def _initialize(self):
        intro_text = "Behave like a hypotethical doctor who has to do a diagnosis for a patient. Give me a list of potential rare diseases with a short description. Shows for each potential rare diseases always with '\n\n+' and a number, starting with '\n\n+1', for example '\n\n+23.' (never return \n\n-), the name of the disease and finish with ':'. Dont return '\n\n-', return '\n\n+' instead. You have to indicate which symptoms the patient has in common with the proposed disease and which symptoms the patient does not have in common. The text is"
        self.load_section_from_text("intro", intro_text)
        self.build_template()

@register_prompt
class ImprovedDxGPTPrompt(PromptBuilder):
    """Builds the improved diagnosis prompt with thinking step and XML tags."""
    @classmethod
    def alias(cls) -> str:
        return "dxgpt_improved"

    def __init__(self, verbose: bool = False):
        super().__init__(verbose=verbose)
        self.meta_template = """
<prompt> As an AI-assisted diagnostic tool, your task is to analyze the given patient symptoms and generate a list of the top 5 potential diagnoses. Follow these steps:
Carefully review the patient's reported symptoms.
In the <thinking></thinking> tags, provide a detailed analysis of the patient's condition: a. Highlight any key symptoms or combinations of symptoms that stand out. b. Discuss possible diagnoses and why they might or might not fit the patient's presentation. c. Suggest any additional tests or information that could help narrow down the diagnosis.
In the <top5></top5> tags, generate a list of the 5 most likely diagnoses that match the given symptoms: a. Assign each diagnosis a number, starting from 1 (e.g., "\n\n+1", "\n\n+2", etc.). b. Provide the name of the condition, followed by a colon (":"). c. Indicate which of the patient's symptoms are consistent with this diagnosis. d. Mention any key symptoms of the condition that the patient did not report, if applicable.
Remember:

Do not use "\n\n-" in your response. Only use "\n\n+" when listing the diagnoses.
The <thinking> section should come before the <top5> section.
Patient Symptoms:
<patient_description>
{description}
</patient_description>
</prompt>
"""
        self._initialize()

    def _initialize(self):
        prompt_structure_text = """
<prompt> As an AI-assisted diagnostic tool, your task is to analyze the given patient symptoms and generate a list of the top 5 potential diagnoses. Follow these steps:
Carefully review the patient's reported symptoms.
In the <thinking></thinking> tags, provide a detailed analysis of the patient's condition: a. Highlight any key symptoms or combinations of symptoms that stand out. b. Discuss possible diagnoses and why they might or might not fit the patient's presentation. c. Suggest any additional tests or information that could help narrow down the diagnosis.
In the <top5></top5> tags, generate a list of the 5 most likely diagnoses that match the given symptoms: a. Assign each diagnosis a number, starting from 1 (e.g., "\n\n+1", "\n\n+2", etc.). b. Provide the name of the condition, followed by a colon (":"). c. Indicate which of the patient's symptoms are consistent with this diagnosis. d. Mention any key symptoms of the condition that the patient did not report, if applicable.
Remember:

Do not use "\n\n-" in your response. Only use "\n\n+" when listing the diagnoses.
The <thinking> section should come before the <top5> section.
Patient Symptoms:
<patient_description>
{description}
</patient_description>
</prompt>
"""
        self.load_section_from_text("prompt_structure", prompt_structure_text)
        self.build_template()

@register_prompt
class JSONDxGPTPrompt(PromptBuilder):
    """Builds the diagnosis prompt requesting JSON output."""
    @classmethod
    def alias(cls) -> str:
        return "dxgpt_json"

    def __init__(self, verbose: bool = False):
        super().__init__(verbose=verbose)
        self.meta_template = """
{intro}
{format_instructions}
Here is the patient description:
<patient_description>
{description}
</patient_description>
"""
        self._initialize()

    def _initialize(self):
        intro_text = "Behave like a hypothetical doctor tasked with providing 5 hypothesis diagnosis for a patient based on their description. Your goal is to generate a list of 5 potential diseases, each with a short description, and indicate which symptoms the patient has in common with the proposed disease and which symptoms the patient does not have in common."
        format_instructions_text = """
Carefully analyze the patient description and consider various potential diseases that could match the symptoms described. For each potential disease:
1. Provide a brief description of the disease
2. List the symptoms that the patient has in common with the disease
3. List the symptoms that the patient has that are not in common with the disease

Present your findings in a JSON format within XML tags. The JSON should contain the following keys for each of the 5 potential disease:
- "diagnosis": The name of the potential disease
- "description": A brief description of the disease
- "symptoms_in_common": An array of symptoms the patient has that match the disease
- "symptoms_not_in_common": An array of symptoms the patient has that are not in common with the disease

Here's an example of how your output should be structured:

<5_diagnosis_output>
[
{{
    "diagnosis": "some disease 1",
    "description": "some description",
    "symptoms_in_common": ["symptom1", "symptom2", "symptomN"],
    "symptoms_not_in_common": ["symptom1", "symptom2", "symptomN"]
}},
...
{{
    "diagnosis": "some disease 5",
    "description": "some description",
    "symptoms_in_common": ["symptom1", "symptom2", "symptomN"],
    "symptoms_not_in_common": ["symptom1", "symptom2", "symptomN"]
}}
]
</5_diagnosis_output>

Present your final output within <5_diagnosis_output> tags as shown in the example above.
"""
        self.load_section_from_text("intro", intro_text)
        self.load_section_from_text("format_instructions", format_instructions_text)
        self.build_template()

@register_prompt
class JSONRiskDxGPTPrompt(PromptBuilder):
    """Builds the diagnosis prompt requesting JSON output with risk handling."""
    @classmethod
    def alias(cls) -> str:
        return "dxgpt_json_risk"

    def __init__(self, verbose: bool = False):
        super().__init__(verbose=verbose)
        # Reuse the JSON prompt meta template
        self.meta_template = """
{intro}
{format_instructions}
{risk_handling}
Here is the patient description:
<patient_description>
{description}
</patient_description>
"""
        self._initialize()

    def _initialize(self):
        # Reuse sections from JSON prompt
        intro_text = "Behave like a hypothetical doctor tasked with providing 5 hypothesis diagnosis for a patient based on their description. Your goal is to generate a list of 5 potential diseases, each with a short description, and indicate which symptoms the patient has in common with the proposed disease and which symptoms the patient does not have in common."
        format_instructions_text = """
Carefully analyze the patient description and consider various potential diseases that could match the symptoms described. For each potential disease:
1. Provide a brief description of the disease
2. List the symptoms that the patient has in common with the disease
3. List the symptoms that the patient has that are not in common with the disease

Present your findings in a JSON format within XML tags. The JSON should contain the following keys for each of the 5 potential disease:
- "diagnosis": The name of the potential disease
- "description": A brief description of the disease
- "symptoms_in_common": An array of symptoms the patient has that match the disease
- "symptoms_not_in_common": An array of symptoms the patient has that are not in common with the disease

Here's an example of how your output should be structured:

<5_diagnosis_output>
[
{{
    "diagnosis": "some disease 1",
    "description": "some description",
    "symptoms_in_common": ["symptom1", "symptom2", "symptomN"],
    "symptoms_not_in_common": ["symptom1", "symptom2", "symptomN"]
}},
...
{{
    "diagnosis": "some disease 5",
    "description": "some description",
    "symptoms_in_common": ["symptom1", "symptom2", "symptomN"],
    "symptoms_not_in_common": ["symptom1", "symptom2", "symptomN"]
}}
]
</5_diagnosis_output>

Present your final output within <5_diagnosis_output> tags as shown in the example above.
"""
        risk_handling_text = """
If there are no symptoms in the description or it is not related to a patient's clinic, return an empty list like this:

<diagnosis_output>
[]
</diagnosis_output>
"""
        
        self.load_section_from_text("intro", intro_text)
        self.load_section_from_text("format_instructions", format_instructions_text)
        self.load_section_from_text("risk_handling", risk_handling_text)
        self.build_template()

# Removed PROMPT_ALIAS_MAP as registration handles alias mapping now.
