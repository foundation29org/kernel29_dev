"""
Severity prompt template builder module.

This module defines builders for creating severity assessment prompt templates.
"""

from typing import Dict, Any, Optional
from abc import abstractmethod

from src.PromptTemplateBuilder.base import PromptTemplateBuilder


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


class SeverityTemplateBuilder(PromptTemplateBuilder):
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
        self.load_section_from_default("intro", self._get_intro())
        
        # Load JSON format section
        self.load_section_from_default("json_format", self._get_json_format())
        
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
        return """Please structure your response as a JSON object with the following format:
```json
{
  "case_id": {case_id},
  "severity_evaluations": [
    {
      "disease": "Disease name",
      "rank": 1,
      "severity": "mild|moderate|severe|critical",
      "reasoning": "Brief explanation for this severity assessment"
    },
    {
      "disease": "Another disease",
      "rank": 2,
      "severity": "mild|moderate|severe|critical",
      "reasoning": "Brief explanation for this severity assessment"
    }
  ],
  "overall_assessment": "Brief summary of the overall severity profile of this differential diagnosis"
}
```
Provide only the JSON response without additional text."""
    
    def _get_template_string(self) -> str:
        """Get the template string."""
        return "{intro}\n\nDifferential Diagnosis:\n{differential_diagnosis}\n\n{severity_levels}\n\n{json_format}"


class StandardSeverityTemplateBuilder(SeverityTemplateBuilder):
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
        self.load_section_from_default("intro", self._get_intro())
        
        # Load classification from defaults instead of database
        self.load_section_from_default("severity_levels", self._get_classification())
        
        # Load JSON format section
        self.load_section_from_default("json_format", self._get_json_format())
        
        # Set the template
        self.set_template(self._get_template_string())
        
        # Build the template
        self.build_template()
        
        return self
    
    def _get_classification(self) -> str:
        """Get the classification section text."""
        return """For each disease in the differential diagnosis, evaluate its severity based on the following criteria:
1. Mild: The disease generally has minor symptoms that do not significantly affect daily activities.
2. Moderate: The disease has noticeable symptoms requiring medical intervention but is not life-threatening.
3. Severe: The disease has serious symptoms that significantly impact health and may require hospitalization.
4. Critical: The disease is life-threatening and requires immediate medical intervention.

For each disease, consider its typical presentation, potential complications, and impact on the patient's quality of life."""
