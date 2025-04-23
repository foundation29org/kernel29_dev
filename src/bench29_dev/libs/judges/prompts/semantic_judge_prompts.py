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



    def _get_semantic_levels_old(self) -> str:
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


    def _get_semantic_levels(self) -> str:
        return """code: 1. label: **Exact Synonym**

    **Definition:**  
    The differential diagnosis is the exact same disease entity as the golden diagnosis, simply referred to by a different name (e.g., regional, historical, eponymous, or technical variation). There is no difference in etiology, pathophysiology, diagnostic criteria, or treatment.

    **When to use it:**  
    Use this category when the two terms are fully interchangeable in all clinical, research, and educational contexts.

    **When NOT to use it:**  
    Do not use this category if one diagnosis is a subtype of the other, or if they differ in mechanism, severity, or presentation.

    **Examples:**
    - Golden: Amyotrophic Lateral Sclerosis  
      Differential: Lou Gehrig’s Disease → Exact Synonym  
    - Golden: Trisomy 21  
      Differential: Down Syndrome → Exact Synonym  
    - Golden: Varicella  
      Differential: Chickenpox → Exact Synonym  

    ---

    code: 2. label: **Broad Synonym**

    **Definition:**  
    The differential diagnosis is a broader or umbrella term that includes the golden diagnosis as one of its subtypes, forms, or variants. It may include other diseases as well, and is often more general or imprecise in its use.

    **When to use it:**  
    Use this category when the golden diagnosis is fully contained within the broader label, but the broader label includes additional, different conditions. The broader label may reflect a category, syndrome, or umbrella disease.

    **When NOT to use it:**  
    Do not use this category if the two diagnoses are parallel subtypes or variants (use "Exact Disease Group" instead), or if the broader term is not generally used to include the golden diagnosis.

    **Examples:**
    - Golden: Type 1 Diabetes Mellitus  
      Differential: Diabetes Mellitus → Broad Synonym  
    - Golden: Bardet-Biedl Syndrome Type 2  
      Differential: Bardet-Biedl Syndrome → Broad Synonym  
    - Golden: Mucopolysaccharidosis Type I (Hurler Syndrome)  
      Differential: Mucopolysaccharidosis → Broad Synonym  
    - Golden: Marfan Syndrome due to FBN1 mutation  
      Differential: Marfan Syndrome → Broad Synonym  

    ---

    code: 3. label: **Exact Disease Group**

    **Definition:**  
    The differential diagnosis and the golden diagnosis are different diseases, but both belong to the same narrowly defined disease group. This group is characterized by a **shared mechanism, pathophysiology, and diagnostic framework**, such as mutations in related enzymes, deficiencies in the same metabolic pathway, or loss of function in a common biological process. The two diagnoses are **distinct but parallel** entities within a **mechanistically cohesive family**.

    **When to use it:**  
    Use this category when both diagnoses are members of a **clearly defined clinical, biochemical, or genetic group**, and the relationship is horizontal — that is, neither diagnosis contains the other.

    **When NOT to use it:**  
    Do not use this category if one diagnosis is a subtype of the other (use "Broad Synonym" instead). Also avoid this category for conditions that share only broad clinical similarities but not a common mechanism (those go in "Broad Disease Group").

    **Examples:**
    - Golden: Hemophilia A (Factor VIII deficiency)  
      Differential: Hemophilia B (Factor IX deficiency) → Exact Disease Group  
    - Golden: Glutaric Acidemia Type I  
      Differential: Methylmalonic Acidemia → Exact Disease Group  
    - Golden: Hereditary Spherocytosis  
      Differential: Hereditary Elliptocytosis → Exact Disease Group  
    - Golden: Factor VII deficiency  
      Differential: Factor X deficiency → Exact Disease Group  

    ---

    code: 4. label: **Broad Disease Group**

    **Definition:**  
    A diagnosis that does not share a direct mechanistic, genetic, or taxonomic relationship with the golden diagnosis, but is frequently considered alongside it in clinical practice due to similar presentation. These diseases may look alike at the bedside, especially during the early stages of evaluation, and often require similar first-line tests to distinguish. The relationship is based on clinical confusability, not biological connection.
    T
    **When to use it:**  
    Use this category when the two conditions are **clinically related** — often co-considered in the same differential diagnosis — but are **not mechanistically related** or taxonomically close. Both diagnoses often share presenting symptoms and are commonly discussed together in teaching, guidelines, or diagnostic algorithms.

    **When NOT to use it:**  
    Do not use this category if the diagnoses are part of a clearly defined, mechanistically unified group (those go in "Exact Disease Group"). Also do not use this if the conditions are clearly unrelated (use "Not Related").

    **Examples:**
    - Golden: Aicardi-Goutières Syndrome  
      Differential: Krabbe Disease → Broad Disease Group  
    - Golden: Crohn’s Disease  
      Differential: Ulcerative Colitis → Broad Disease Group  
    - Golden: Familial Mediterranean Fever  
      Differential: TNF Receptor-Associated Periodic Syndrome (TRAPS) → Broad Disease Group  
    - Golden: Systemic Lupus Erythematosus  
      Differential: Mixed Connective Tissue Disease → Broad Disease Group  

    ---

    code: 5. label: **Not Related**

    **Definition:**  
    The differential diagnosis has no clinically meaningful overlap with the golden diagnosis in terms of pathophysiology, anatomy, clinical presentation, or diagnostic reasoning. The two conditions are not considered together in real-world clinical practice.

    **When to use it:**  
    Use this category when the conditions are **anatomically, mechanistically, and diagnostically unrelated**. They affect different systems, have different etiologies, and would not realistically be confused or co-considered in a differential diagnosis.

    **When NOT to use it:**  
    Do not use this category if there is any significant overlap in symptoms, systems involved, patient populations, or diagnostic workup — even if the mechanisms differ.

    **Examples:**
    - Golden: Turner Syndrome  
      Differential: Tuberculosis → Not Related  
    - Golden: Asthma  
      Differential: Epilepsy → Not Related  
    - Golden: Phenylketonuria  
      Differential: Irritable Bowel Syndrome → Not Related  
    - Golden: Hemophilia A  
      Differential: Ankylosing Spondylitis → Not Related  """











    def _get_json_format_old(self) -> str:
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






    def _get_json_format(self) -> str:
        return """Your output must be a valid JSON object with the following structure. Replace the placeholders with real data.

You must include:
- The golden diagnosis under the field "golden_diagnosis"
- A list of differential diagnoses under the field "differential_diagnoses"
- For each differential:
    - A "diagnosis" string that must match **exactly** one of the diseases provided in the list of differential diagnoses
    - A "reasoning" field: a short explanation that justifies the relationship. It should focus on why the diagnosis fits the selected category, based on criteria such as name equivalence, subtype structure, shared pathophysiology, clinical similarity, or complete lack of relation.
   
    - A "category" object containing:
        - A "code" field (integer from 1 to 6)
        - A "label" field (must match **exactly** one of the predefined category names)
-You should classify all differential diagnoses.

Do not generate new diagnoses or modify the names. Use each differential diagnosis exactly as it appears in the list.

Return only the JSON object. Do not include any explanations or formatting around it.

Example:

{{
  "golden_diagnosis": "Parkinson's Disease",
  "differential_diagnoses": [
    {{
      "diagnosis": "Idiopathic Parkinsonism",
      "reasoning": "Parkinson's Disease and Idiopathic Parkinsonism are often used interchangeably in clinical settings when no secondary cause is identified, indicating they refer to the same condition.",
      "category": {{
        "code": 1,
        "label": "Exact synonym"
      }}
    }},
    {{
      "diagnosis": "Parkinson’s Disease with dementia",
      "reasoning": "Parkinson's Disease and Parkinson’s Disease with dementia describe related stages of the same condition, where the latter represents a subtype involving cognitive decline.",
      "category": {{
        "code": 2,
        "label": "Broad synonym"
      }}
    }},
    {{
      "diagnosis": "Multiple System Atrophy",
      "reasoning": "Parkinson's Disease and Multiple System Atrophy are often grouped as atypical parkinsonian syndromes due to overlapping motor symptoms and neurodegeneration, placing them in the same disease group.",
      "category": {{
        "code": 3,
        "label": "Exact disease group"
      }}
    }},
    {{
      "diagnosis": "Alzheimer’s Disease",
      "reasoning": "Parkinson's Disease and Alzheimer's Disease are both neurodegenerative conditions that can share cognitive symptoms and are often evaluated together in elderly patients, despite distinct underlying pathologies.",
      "category": {{
        "code": 4,
        "label": "Broad disease group"
      }}
    }},
    {{
      "diagnosis": "Asthma",
      "reasoning": "Parkinson's Disease and Asthma affect completely different organ systems with no clinical, anatomical, or pathophysiological connection, and are not considered related.",
      "category": {{
        "code": 5,
        "label": "Not related"
      }}
    }}
  ]
}}



Do not include any text outside of the JSON.


The most important aspect of your output is the accuracy and clinical depth of the reasoning behind each classification. For every differential diagnosis, you must justify why the selected category is the most appropriate based on the definitions provided — considering factors like clinical presentation, pathophysiological mechanism, diagnostic process, and context of use.

When you are about to assign the category "Not related disease", **pause and challenge your decision**. You can extend your reasoning to make more precise classification. Before finalizing that label, ask yourself:

1. Could these two conditions share overlapping clinical features (e.g., symptoms, timing, course)?
2. Are these diagnoses commonly considered together in clinical differential diagnoses or diagnostic workups?
3. Might these conditions be confused in real-world cases, especially early in the diagnostic process?
4. If a patient presented with an unknown condition resembling the golden diagnosis, would this differential be a **reasonable clinical hypothesis** to explore — even if ultimately incorrect?

Remember that Broad group of diseases focus on clinical similarity of shared symptoms between conditions, not biological connection.
If the answer to any of these is yes, then consider whether "Broad group of diseases" might be more appropriate than "Not related disease".  
**Do not choose "Not related disease" by default**. Only assign it after deliberately evaluating why the other categories — especially "Broad group of diseases" — do not fit.

Always include this reflective process in your reasoning if the category is "Not related disease" or "Broad group of diseases". you can extend your reasoning to justify a wrong classification.

Finally, ensure that the output is a valid JSON object. Do not include any text outside of the JSON or include formatting marks. like ``` or ```json. """
