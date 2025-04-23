"""
Severity prompt template builder module.

This module defines builders for creating severity assessment prompt templates.
"""

from typing import Dict, Any, Optional
from lapin.prompt_builder.base import PromptBuilder




def get_severity_levels(severity_levels_table, verbose: bool = False):
    """
    Get severity levels from database table.
    
    Args:
        severity_levels_table: SQLAlchemy table object for severity levels
        verbose: Whether to print status information
        
    Returns:
        List of severity level objects
    """
    if verbose:
        print("Getting severity levels from database")
    
    from db.utils.db_utils import get_session
    session = get_session()
    
    severity_levels = session.query(severity_levels_table).all()
    session.close()
    
    return severity_levels


def severity_levels2text(severity_levels, verbose: bool = False) -> str:
    """
    Transform severity levels into text description.
    
    Args:
        severity_levels: List of severity level objects
        verbose: Whether to print status information
        
    Returns:
        Text representation of severity levels
    """
    if verbose:
        print("Transforming severity levels to text")
    
    # Format severity levels as text
    level_texts = []
    for level in severity_levels:
        level_texts.append(f"- {level.name}: {level.description}")
    
    return "\n".join(level_texts)


def get_and_transform_levels(table, verbose: bool = False) -> str:
    """
    Get severity levels from database table and transform them to text.
    
    Args:
        table: SQLAlchemy table object for severity levels
        verbose: Whether to print status information
        
    Returns:
        Text representation of severity levels
    """
    # First get the levels from database
    levels = get_severity_levels(table, verbose=verbose)
    
    # Then transform them to text
    text = severity_levels2text(levels, verbose=verbose)
    
    return text


class SeverityBuilder(PromptBuilder):       
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
        self.meta_template = """{intro}\n\nDifferential Diagnosis:\n{differential_diagnosis}\n\n{severity_levels}\n\n{json_format}"""
        self.initialize()
    
    def load_severity_levels(self, backward: bool = True):
        """
        Load severity levels from the database.
        
        Args:
            backward: Whether to use backward-compatible tables
            
        Returns:
            Self for method chaining
        """
        if self.verbose:
            print("Loading severity levels from database")
            
        # Import the correct table class
        if backward:
            from db.backward_comp_models import SeverityLevels as severity_table
        else:
            from db.registry.registry_models import SeverityLevels as severity_table
            
        # Load severity levels into classification section
        return self.load_section_from_table(
            "severity_levels", 
            severity_table, 
            get_and_transform_levels
        )
    
    def initialize(self):
        """
        Initialize with standard configuration.
        
        Returns:
            Self for method chaining
        """
        if self.verbose:
            print("Initializing Severity Template Builder")
        
        # Load intro section
        self.load_section_from_text("intro", self._get_intro())
        
        # Load JSON format section
        self.load_section_from_text("json_format", self._get_json_format())
        
        # By default, load classification from the database
        self.load_severity_levels()
        
        # Set the template
        self.set_template(self._get_template_string())
        
        # Build the template
        self.build_template()
        
        return self
    
    def _get_intro(self) -> str:
        """Get the intro section text."""
        return """You are a medical expert evaluating the severity of diseases in a differential diagnosis. 
Please analyze the following differential diagnosis and evaluate the severity of each proposed disease."""
    
    def _get_json_format(self) -> str:
        """Get the JSON format section text."""
        return """Please structure your response as a JSON object with the following structure. 
        Replace the placeholders with real data.


```json
{{
  "severity_evaluations": [
    {{
      "disease": "{{disease_name}}",
      "severity": "{{mild|moderate|severe|critical|rare}}"
    }},
    {{
      "disease": "Another disease",
      "severity": "mild|moderate|severe|critical|rare"
    }}
  ]
}}
```

Final remarks:
- "disease" string must match **exactly** one of the diseases provided in the list of differential diagnoses
- "severity" string must match **exactly** one of the severity levels provided in the list of severity levels
- Ensure that you evaluate all diseases in the differential diagnosis. No disease should be left out.
Remember that if a disease is rare, it should be labeled as "rare" and not any other severity category. 
Rare diseases include congenital syndromes, rare cancers, rare genetic disorders, congenital diseases or anomalies etc.
Provide only the JSON response without additional text. 
Ensure that the output is a valid JSON object. 
Do not include any text outside of the JSON or include formatting marks. like ``` or ```json. """










    def _get_json_format_old(self) -> str:
        """Get the JSON format section text."""
        return """Please structure your response as a JSON object with the following format:
```json
{{
  "severity_evaluations": [
    {{
      "disease": "{{disease_name}}",
      "rank": {{rank}},
      "severity": "{{severity_level}}",
      "reasoning": "{{reasoning_text}}"
    }},
    {{
      "disease": "Another disease",
      "rank": 2,
      "severity": "mild|moderate|severe|critical",
      "reasoning": "Brief explanation for this severity assessment"
    }}
  ],
  "overall_assessment": "Brief summary of the overall severity profile of this differential diagnosis"
}}
```
Provide only the JSON response without additional text."""




    def _get_meta_template(self) -> str:
        """Get the template string."""
        return self.meta_template


class prompt_1(SeverityBuilder):
    """
    Standard severity template builder with classification from defaults.
    
    This version overrides the classification section to use default text
    instead of loading from the database.
    """
    
    def initialize(self):
        """
        Initialize with standard configuration but using default classification.
        
        Returns:
            Self for method chaining
        """
        if self.verbose:
            print("Initializing Standard Severity Template Builder")
        
        # Load intro section
        self.load_section_from_text("intro", self._get_intro())
        
        # Load classification from defaults instead of database
        self.load_section_from_text("severity_levels", self._get_classification())
        
        # Load JSON format section
        self.load_section_from_text("json_format", self._get_json_format())
        
        # Set the template
        # self.set_meta_template(self._get_meta_template())
        # print(self.template)
        verbose = True
        if verbose:
            print("prompt_1 is going to build the template")
        # Build the template
        self.build_template()
        if verbose:
            print("prompt_1 has built the template")
        
        return self
    
    def _get_classification_old(self) -> str:
        """Get the classification section text."""
        return """For each disease in the differential diagnosis, evaluate its severity based on the following criteria:
1. Mild: The disease generally has minor symptoms that do not significantly affect daily activities.
2. Moderate: The disease has noticeable symptoms requiring medical intervention but is not life-threatening.
3. Severe: The disease has serious symptoms that significantly impact health and may require hospitalization.
4. Critical: The disease is life-threatening and requires immediate medical intervention.

For each disease, consider its typical presentation, potential complications, and impact on the patient's quality of life."""


    def _get_classification(self) -> str:
        """Get the classification section text."""
        return """For each disease in the differential diagnosis, evaluate its severity based on the following criteria:
- mild: The disease has minor symptoms that do not significantly affect daily activities and typically resolves on its own or with minimal treatment.
- moderate: The disease has noticeable symptoms that may require medical intervention but is not life-threatening.
- severe: The disease presents serious symptoms that significantly impact health and may require hospitalization.
- critical: The disease is life-threatening and requires immediate medical intervention, often involving intensive care.
- rare: The disease is internationally recognized as rare disease. Most rare diseases are congenital syndromes, rare cancers, rare genetic disorders, congenital diseases or anomalies etc. Rare diseases are usually the result of a mutation in a gene , few genes or abnormalities in the genome. If a disease is identified as rare, do not consider any other severity category.

Rules:
- For each disease, consider its typical presentation, potential complications, and impact on the patient's quality of life.
- If a disease is rare, label it 'rare' and ignore all other categories.
- Assign only one category (never combine, e.g., no “mild to moderate”).
- If you are unsure between multiple severities, choose the single most severe one, except if the disease is rare.
- The main task is to detect rare diseases and label them as 'rare', if you detect a rare disease, do not consider any other severity category.
- if something similar to "congenital" is mentioned, it is a rare disease, label it as 'rare'.
-if the disease has a genetic origin, it is a rare disease, label it as 'rare'.
-usually the word type followed by a number, for example type 1, type 2 ... denotes a disease name. Double check if it is a rare disease.
-multiple endrocrine neoplasia MEN1 is a rare disease, label it as 'rare'.
-Myasthenia gravis is a rare disease, label it as 'rare'.
-usually the word syndrome in disease name denotes a rare disease. Double check if it is a rare disease.
If you identify a disease as rare, label it “rare” and do not consider any other severity category. 
If you are unsure between multiple severities, choose the one that represents the highest level of severity. 
Never use combined or partial categories (such as “mild to moderate”)


"""








# class prompt_2(SeverityBuilder):
#     """
#     This version builds a prompt for classifying how a set of differential diagnoses 
#     relate to a golden diagnosis, using diagnostic relationship categories.
#     """

#     def initialize(self):
#         """
#         Initialize with the sections necessary to build the prompt.
        
#         Returns:
#             Self for method chaining
#         """
#         if self.verbose:
#             print("Initializing prompt_2 for relationship classification.")

#         # Load prompt parts
#         self.load_section_from_text("intro", self._get_intro())
#         self.load_section_from_text("relationship_categories", self._get_relationship_categories())
#         self.load_section_from_text("json_format", self._get_json_format())

#         # Build final template
#         self.build_template()

#         if self.verbose:
#             print("prompt_2 has built the template.")

#         return self

#     def _get_intro(self) -> str:
#         return """You are building a structured dataset for diagnostic reasoning.

# You are given:

# A golden diagnosis: {{{{GOLDEN_DIAGNOSIS}}}}

# A set of differential diagnoses: {{{{DIFFERENTIAL_DIAGNOSES}}}}

# For each differential, determine how it relates to the golden diagnosis as a medical or diagnostic entity. Use the defined categories below."""

#     def _get_relationship_categories(self) -> str:
#         return """Each category is defined by:

# A code (1–6)  
# A label (must match exactly)  
# A short justification explaining the relationship

# Categories:
# 1) Exact synonym → Same diagnosis, different name  
# 2) Broad synonym → More general version of the same condition  
# 3) Exact group of diseases → Same clinical group  
# 4) Broad group of diseases → Same system/category  
# 5) Related disease group → Not same group, but with overlap  
# 6) Not related disease → No connection"""

#     def _get_json_format(self) -> str:
#         return """JSON output only:
