import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.db_conf import Base
from db.registry.registry_models import DiagnosisSemanticRelationship, SeverityLevels

def get_session():
    """Create and return a database session"""
    DATABASE_URL = "postgresql://dummy_user:dummy_password_42@localhost/bench29"
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    print("Tables created successfully!")
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

def preload_semantic_relationships(session):
    """Preload semantic relationship data"""
    relationships = [
        {
            "semantic_relationship": "Exact Synonym",
            "description": """The AI-generated diagnosis is an exact match to the reference diagnosis, differing only in wording but maintaining the same medical meaning. 
             Examples: "Myocardial infarction" vs. "Heart attack", "Varicella" vs. "Chickenpox", "Hypertension" vs. "High blood pressure".
             Not applicable when: "Myocardial infarction" vs. "Heart failure" (reverse case), "Acute myocardial infarction" vs. "Chronic heart disease", "Hypertension" vs. "Hypotension"."""
        },
        {
            "semantic_relationship": "Broad Synonym",
            "description": """The AI-generated diagnosis is a synonym but represents a broader concept than the reference diagnosis.
             Examples: "Viral infection" for "Influenza", "Neoplasm" for "Lung cancer", "Dementia" for "Alzheimer disease".
             Not applicable when: "Lung cancer" for "Neoplasm" (reverse case), "Influenza" for "Bacterial pneumonia", "Dementia" for "Cognitive impairment due to depression"."""
        },
        {
            "semantic_relationship": "Exact Group of Diseases",
            "description": """The AI-generated diagnosis belongs to the same well-defined disease category as the reference diagnosis.
             Examples: "Type 1 Diabetes" for "Diabetes mellitus", "Hepatitis B" for "Hepatitis", "Non-Hodgkin Lymphoma" for "Lymphoma".
             Not applicable when: "Diabetes mellitus" for "Type 1 Diabetes" (reverse case), "Hepatitis B" for "Autoimmune hepatitis", "Lymphoma" for "Leukemia"."""
        },
        {
            "semantic_relationship": "Broad Group of Diseases",
            "description": """The AI-generated diagnosis belongs to a larger disease family but lacks specificity regarding the reference diagnosis.
             Examples: "Respiratory disease" for "Pneumonia", "Cardiac disease" for "Arrhythmia", "Neurological disorder" for "Multiple sclerosis".
             Not applicable when: "Pneumonia" for "Respiratory disease" (reverse case), "Cardiac disease" for "Pulmonary embolism", "Neurological disorder" for "Psychiatric disorder"."""
        },
        {
            "semantic_relationship": "Related Disease Group",
            "description": """The AI-generated diagnosis belongs to a different disease group but has overlapping symptoms, risk factors, or diagnostic considerations with the reference diagnosis.
             Examples: "Chronic kidney disease" for "Diabetic nephropathy", "Rheumatoid arthritis" for "Psoriatic arthritis", "Gastroesophageal reflux disease (GERD)" for "Hiatal hernia".
             Not applicable when: "Psoriatic arthritis" for "Rheumatoid arthritis" (reverse case), "Chronic kidney disease" for "Liver cirrhosis", "GERD" for "Irritable bowel syndrome"."""
        },
        {
            "semantic_relationship": "Not Related Disease",
            "description": """The AI-generated diagnosis is completely unrelated to the reference diagnosis, meaning no significant pathophysiological, etiological, or symptomatic connection exists between them.
             Examples: "Asthma" for "Osteoporosis", "Multiple sclerosis" for "Acute pancreatitis", "Colon cancer" for "Schizophrenia".
             Not applicable when: "Asthma" for "Chronic obstructive pulmonary disease" (related but different), "Multiple sclerosis" for "Parkinson disease", "Colon cancer" for "Inflammatory bowel disease"."""
        }
    ]
    
    relationships_added = 0
    for relationship_data in relationships:
        existing = session.query(DiagnosisSemanticRelationship).filter_by(
            semantic_relationship=relationship_data["semantic_relationship"]
        ).first()
        
        if not existing:
            relationship = DiagnosisSemanticRelationship(
                semantic_relationship=relationship_data["semantic_relationship"],
                description=relationship_data["description"]
            )
            session.add(relationship)
            relationships_added += 1
            print(f"Added semantic relationship: {relationship_data['semantic_relationship']}")
    
    if relationships_added > 0:
        session.commit()
        print(f"Added {relationships_added} semantic relationships")
    else:
        print("No new semantic relationships added")

def preload_severity_levels(session):
    """Preload severity level data"""
    severities = [
        {
            "name": "mild",
            "description": "The clinical case has minor symptoms that do not significantly affect the patient's daily activities and typically resolve on their own or with minimal treatment."
        },
        {
            "name": "moderate",
            "description": "The patient experiences noticeable symptoms that may require medical intervention but are not life-threatening."
        },
        {
            "name": "severe",
            "description": "The case involves serious symptoms that significantly impact the patient's health and may require hospitalization."
        },
        {
            "name": "critical",
            "description": "Life-threatening condition requiring immediate medical intervention, often involving intensive care."
        },
        {
            "name": "rare",
            "description": "The case involves a rare disease or condition, which may require specialized diagnosis and treatment. If a disease is identified as rare, do not consider any other severity category."
        }
    ]
    
    severities_added = 0
    for severity_data in severities:
        existing = session.query(SeverityLevels).filter_by(name=severity_data["name"]).first()
        
        if not existing:
            severity = SeverityLevels(
                name=severity_data["name"],
                description=severity_data["description"]
            )
            session.add(severity)
            severities_added += 1
            print(f"Added severity level: {severity_data['name']}")
    
    if severities_added > 0:
        session.commit()
        print(f"Added {severities_added} severity levels")
    else:
        print("No new severity levels added")

def main():
    """Preload registry data"""
    session = get_session()
    
    try:
        print("\nPreloading semantic relationships...")
        preload_semantic_relationships(session)
        
        print("\nPreloading severity levels...")
        preload_severity_levels(session)
        
        print("\nSetup completed successfully.")
    finally:
        session.close()

if __name__ == "__main__":
    main()
