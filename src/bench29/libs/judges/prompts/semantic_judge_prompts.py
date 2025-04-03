"""
Severity prompt template builder module.

This module defines builders for creating severity assessment prompt templates.
"""

from typing import Dict, Any, Optional
from lapin.prompt_builder.base import PromptBuilder






class Semantic_prompt(PromptBuilder):       
    """
    Base class for severity assessment prompt template builders.
    
    This class provides common functionality for severity assessment prompts,
    including loading severity levels from the database.
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the SeverityTemplateBuilder.
        
        Args:
            verbose: Whether to print status information
        """
        super().__init__(verbose=verbose)
        self.meta_template = """{intro}\n\n{differential_diagnosis}\n\n{semantic_levels}\n\n{json_format}"""
        self.initialize()
    

    
    def initialize(self):
        """
        Initialize with standard configuration.
        
        Returns:
            Self for method chaining
        """
        if self.verbose:
            print("Initializing Semw     Template Builder")
        
        # Load intro section
        self.load_section_from_text("intro", self._get_intro())
        
        self.load_section_from_text("semantic_levels", self._get_semantic_levels())
        self.load_section_from_text("json_format", self._get_json_format())
        
        verbose = True
        if verbose:
            print("prompt_1 is going to build the template")
        # Build the template
        self.build_template()
        if verbose:
            print("prompt_1 has built the template")
        
        # Build the template
        # self.build_template()
        
        return self


    def _get_meta_template(self) -> str:
        """Get the template string."""
        return self.meta_template


    def _get_intro(self) -> str:
        """Get the intro section text."""
        return """You are a medical expert evaluating diagnostic reasoning of clinicians. 
Each clinician where given a clinical case for which they provided a differential diagnosis consisting of several predicted diseases. 
Each case has a golden diagnosis that represents the correct diagnosis.
Please analyze the following differential diagnosis and evaluate the semantic relationship between the differential diagnosis and the golden diagnosis.

# You are given:

# A golden diagnosis: """



    def _get_semantic_levels(self) -> str:
        return """For each disease appearing in differential, determine how it relates to the golden diagnosis as a medical or diagnostic entity. Use the defined categories below.
Each category is defined by:
A code (1–6)  
A label (must match exactly)  


Categories:
- Exact synonym : Same diagnosis, different name  
- Broad synonym : More general version of the same condition  
- Exact group of diseases : Same clinical group  
- Broad group of diseases : Same system/category  
- Related disease group : Not same group, but with overlap  
- Not related disease : No connection"""
    def _get_json_format(self) -> str:
        return """Your output must be a valid JSON object with the following structure. Replace the placeholders with real data.

You must include:
- The golden diagnosis under the field "golden_diagnosis"
- A list of differential diagnoses under the field "differential_diagnoses"
- For each differential:
    - A "diagnosis" string that must match **exactly** one of the diseases provided in the list of differential diagnoses
    - A "category" object containing:
        - A "code" field (integer from 1 to 6)
        - A "label" field (must match **exactly** one of the predefined category names)
-You should classify all differential diagnoses.

Do not generate new diagnoses or modify the names. Use each differential diagnosis exactly as it appears in the list.

Return only the JSON object. Do not include any explanations or formatting around it.

Example:
```json
{{
  "golden_diagnosis": "Myocardial infarction",
  "differential_diagnoses": [
    {{
      "diagnosis": "Heart attack",
      "category": {{
        "code": 1,
        "label": "Exact synonym"
      }}
    }},
    {{
      "diagnosis": "Coronary artery disease",
      "category": {{
        "code": 2,
        "label": "Broad synonym"
      }}
    }}
  ]
}} Do not include any text outside of the JSON.```  """
