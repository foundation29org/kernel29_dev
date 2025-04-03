import os
import json
import re
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_models_working import Base, CasesBench, Models, Prompts, LlmDiagnosis

def get_session():
    DATABASE_URL = "postgresql://dummy_user:dummy_password_42@localhost/bench29"
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    print("Tables created successfully!")
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

def extract_model_prompt(dirname):
    """Extract model and prompt from directory name."""
    pattern = r"(.+)_diagnosis(?:_(.+))?"
    match = re.match(pattern, dirname)
    if match:
        model_name = match.group(1)
        prompt_name = match.group(2) if match.group(2) else "standard"
        return model_name, prompt_name
    return None, None

def get_model_id(session, model_name):
    """Get model ID from database."""
    model = session.query(Models).filter(Models.alias == model_name).first()
    if model:
        return model.id
    return None

def get_prompt_id(session, prompt_name):
    """Get prompt ID from database."""
    prompt = session.query(Prompts).filter(Prompts.alias == prompt_name).first()
    if prompt:
        return prompt.id
    return None

def get_files(dirname):
    print("listing directories")
    dirs = [d for d in os.listdir(dirname) if os.path.isdir(os.path.join(dirname, d))]
    
    print(f"Found {len(dirs)} directories")
    return dirs




def process_directory(session, base_dir, dir_name):
    """Process a single model-prompt directory."""
    # Extract model and prompt
    model_name, prompt_name = extract_model_prompt(dir_name)
    if not model_name or not prompt_name:
        print(f"  Could not extract model and prompt from {dir_name}, skipping")
        return 0
    
    # Get or create model and prompt
    model_id = get_model_id(session, model_name)
    prompt_id = get_prompt_id(session, prompt_name)
    
    print(f"  Using model: {model_name} (ID: {model_id}), prompt: {prompt_name} (ID: {prompt_id})")
    
    # Build directory path
    dir_path = os.path.join(base_dir, dir_name)
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        print(f"  Directory not found: {dir_path}, skipping")
        return 0
    
    # Process each JSON file
    files_processed = 0
    diagnoses_added = 0
    
    # Get all JSON files
    json_files = [f for f in os.listdir(dir_path) if f.endswith('.json') and f.startswith('patient_')]
    
    for filename in json_files:
        # Extract patient number
        print(filename)
        # patient_number = filename.split('.')[0].split('_')[-1]
        # for case in session.query(CasesBench).all():
        #     print (case.source_file_path) 
        # # Find corresponding case in database
        # case_path = f"patient_{patient_number}"
        case = session.query(CasesBench).filter(
            CasesBench.source_file_path == filename
        ).first()
        if not case:
            print(f"    Case not found for {filename}, skipping")
            continue
        print (f"procesing {filename}")    

        
        # Read the prediction
        file_path = os.path.join(dir_path, filename)
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
        except Exception as e:
            print(f"    Error processing {filename}: {str(e)}")  

        # input()
        predict_diagnosis = data.get("predict_diagnosis", "")
        if not predict_diagnosis:
            print(f"    No predict_diagnosis in {filename}, skipping")
            files_processed += 1
            continue
        
        #Add to database
        llm_diagnosis = LlmDiagnosis(
            cases_bench_id=case.id,
            model_id=model_id,
            prompt_id=prompt_id,
            diagnosis=predict_diagnosis,
            timestamp=datetime.datetime.now()
        )
        session.add(llm_diagnosis)
        session.commit()
        
        print(f"    Added diagnosis for {filename}")
        diagnoses_added += 1
        

        
        files_processed += 1
    
    print(f"  Completed directory {dir_name}. Processed {files_processed} files, added {diagnoses_added} diagnoses.")
    return diagnoses_added

def main(dirname):
    """Process all model-prompt directories."""
    session = get_session()
    
    # Get all directories
    directories = get_files(dirname)
    
    # Process each directory
    total_diagnoses_added = 0
    
    for dir_name in directories:
        print(f"Processing directory: {dir_name}")
        diagnoses_added = process_directory(session, dirname, dir_name)
        total_diagnoses_added += diagnoses_added
    
    print(f"All directories processed. Total diagnoses added: {total_diagnoses_added}")

if __name__ == "__main__":
    dirname = "../../data/prompt_comparison_results/prompt_comparison_results"  # Change this to your directory path
    main(dirname)
    # Total diagnoses added: 2250