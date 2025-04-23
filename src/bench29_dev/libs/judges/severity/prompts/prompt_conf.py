"""
Configuration settings for severity judge prompts.
Defines default templates, sections, and formatting strings.
"""


# Configuration dictionary for severity judge prompts
SEVERITY_PROMPT_CONFIG = {
    # Default templates for each prompt section
    "defaults": {
        "intro": """You are a medical expert evaluating the severity of diseases in a differential diagnosis. 
Please analyze the following differential diagnosis and evaluate the severity of each proposed disease.""",

        "classification": """For each disease in the differential diagnosis, evaluate its severity based on the following criteria:
1. Mild: The disease generally has minor symptoms that do not significantly affect daily activities.
2. Moderate: The disease has noticeable symptoms requiring medical intervention but is not life-threatening.
3. Severe: The disease has serious symptoms that significantly impact health and may require hospitalization.
4. Critical: The disease is life-threatening and requires immediate medical intervention.

For each disease, consider its typical presentation, potential complications, and impact on the patient's quality of life.""",

        "json_format": """Please structure your response as a JSON object with the following format:
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
    },

    # List of section placeholders that can be used in prompt_string
    "prompt_sections": [
        "intro",
        "differential_diagnosis",
        "classification",
        "json_format"
    ],

    # The template string for formatting the complete prompt
    "prompt_metatemplate": "{intro}\n\nDifferential Diagnosis:\n{differential_diagnosis}\n\n{classification}\n\n{json_format}"
}



SEVERITY_PROMPT_SOURCES ={
            "intro": {"from_prompt_db": False, "from_local_json": False, "from_default": True ....add all},
            "classification": {"from_db": False, ...},
            ...
        }
    