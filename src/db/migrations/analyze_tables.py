import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))

from sqlalchemy import create_engine, text

def analyze_tables():
    """Update database statistics for query optimization"""
    DATABASE_URL = "postgresql://dummy_user:dummy_password_42@localhost/bench29"
    engine = create_engine(DATABASE_URL)
    
    tables = [
        'cases_bench',
        'cases_bench_metadata',
        'cases_bench_gold_diagnosis',
        'cases_bench_diagnosis',
        'llm_differential_diagnosis',
        'differential_diagnosis_to_rank',
        'differential_diagnosis_to_severity',
        'differential_diagnosis_to_semantic_relationship',
        'llm_analysis'
    ]
    
    try:
        print("Updating database statistics...")
        with engine.connect() as connection:
            for table in tables:
                connection.execute(text(f"ANALYZE bench29.{table}"))
                print(f"Updated statistics for bench29.{table}")
            
            # Also analyze registry tables that are frequently joined
            registry_tables = [
                'severity_levels',
                'diagnosis_semantic_relationship'
            ]
            
            for table in registry_tables:
                connection.execute(text(f"ANALYZE registry.{table}"))
                print(f"Updated statistics for registry.{table}")
            
            connection.commit()
            print("\nAll database statistics updated successfully!")
            
    except Exception as e:
        print(f"Error updating database statistics: {str(e)}")

if __name__ == "__main__":
    analyze_tables() 