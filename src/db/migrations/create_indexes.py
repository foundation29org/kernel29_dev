import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))

from sqlalchemy import create_engine, text

def create_indexes():
    """Create indexes for better query performance"""
    DATABASE_URL = "postgresql://dummy_user:dummy_password_42@localhost/bench29"
    engine = create_engine(DATABASE_URL)
    
    indexes = [
        # cases_bench indexes
        """CREATE INDEX IF NOT EXISTS idx_cases_bench_hospital 
           ON bench29.cases_bench(hospital)""",
        
        """CREATE INDEX IF NOT EXISTS idx_cases_bench_processed_date 
           ON bench29.cases_bench(processed_date)""",
        
        # cases_bench_metadata indexes
        """CREATE INDEX IF NOT EXISTS idx_metadata_disease_type 
           ON bench29.cases_bench_metadata(disease_type)""",
        
        """CREATE INDEX IF NOT EXISTS idx_metadata_primary_specialty 
           ON bench29.cases_bench_metadata(primary_medical_specialty)""",
        
        # llm_differential_diagnosis indexes
        """CREATE INDEX IF NOT EXISTS idx_differential_diagnosis_timestamp 
           ON bench29.llm_differential_diagnosis(timestamp)""",
        
        """CREATE INDEX IF NOT EXISTS idx_differential_diagnosis_model 
           ON bench29.llm_differential_diagnosis(model_id)""",
        
        # differential_diagnosis_to_rank indexes
        """CREATE INDEX IF NOT EXISTS idx_rank_position 
           ON bench29.differential_diagnosis_to_rank(rank_position)""",
        
        # New indexes optimized for the specific query pattern
        """CREATE INDEX IF NOT EXISTS idx_diff_diagnosis_rank_case_id 
           ON bench29.differential_diagnosis_to_rank(cases_bench_id)""",
        
        """CREATE INDEX IF NOT EXISTS idx_diff_diagnosis_rank_diff_id 
           ON bench29.differential_diagnosis_to_rank(differential_diagnosis_id)""",
        
        """CREATE INDEX IF NOT EXISTS idx_llm_diff_diagnosis_id 
           ON bench29.llm_differential_diagnosis(id)""",
        
        # Composite indexes for the specific join conditions
        """CREATE INDEX IF NOT EXISTS idx_cases_bench_hospital_id 
           ON bench29.cases_bench(hospital, id)""",
        
        """CREATE INDEX IF NOT EXISTS idx_llm_diff_diagnosis_model_id 
           ON bench29.llm_differential_diagnosis(model_id, id)""",
        
        # Composite indexes for frequently joined tables
        """CREATE INDEX IF NOT EXISTS idx_differential_diagnosis_case_model 
           ON bench29.llm_differential_diagnosis(cases_bench_id, model_id)""",
        
        """CREATE INDEX IF NOT EXISTS idx_rank_case_diagnosis 
           ON bench29.differential_diagnosis_to_rank(cases_bench_id, differential_diagnosis_id)""",
        
        # Text search index for diagnosis
        """CREATE INDEX IF NOT EXISTS idx_predicted_diagnosis_gin 
           ON bench29.differential_diagnosis_to_rank 
           USING gin(to_tsvector('english', predicted_diagnosis))"""
    ]
    
    try:
        for index in indexes:
            engine.execute(text(index))
            print(f"Created index: {index.split('CREATE INDEX IF NOT EXISTS')[1].split('ON')[0].strip()}")
        
        print("\nAll indexes created successfully!")
        print("\nNote: Run analyze_tables.py to update database statistics for optimal query performance")
        
    except Exception as e:
        print(f"Error creating indexes: {str(e)}")

if __name__ == "__main__":
    create_indexes() 