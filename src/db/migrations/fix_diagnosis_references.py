import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, ForeignKeyConstraint, text

def fix_tables():
    """Drop and recreate tables with correct references"""
    DATABASE_URL = "postgresql://dummy_user:dummy_password_42@localhost/bench29"
    engine = create_engine(DATABASE_URL)
    
    # Create MetaData instance
    metadata = MetaData(schema='bench29')
    
    # Drop existing tables using with context
    with engine.connect() as connection:
        # Drop tables
        connection.execute(text("""
            DROP TABLE IF EXISTS bench29.differential_diagnosis_to_severity CASCADE;
            DROP TABLE IF EXISTS bench29.differential_diagnosis_to_semantic_relationship CASCADE;
        """))
        connection.commit()
        
        # Create new tables with correct references
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS bench29.differential_diagnosis_to_severity (
                id SERIAL PRIMARY KEY,
                cases_bench_id INTEGER NOT NULL,
                rank_id INTEGER NOT NULL,
                severity_levels_id INTEGER NOT NULL,
                FOREIGN KEY (cases_bench_id) REFERENCES bench29.cases_bench(id) ON DELETE CASCADE,
                FOREIGN KEY (rank_id) REFERENCES bench29.differential_diagnosis_to_rank(id) ON DELETE CASCADE,
                FOREIGN KEY (severity_levels_id) REFERENCES registry.severity_levels(id) ON DELETE CASCADE
            );
        """))
        
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS bench29.differential_diagnosis_to_semantic_relationship (
                id SERIAL PRIMARY KEY,
                cases_bench_id INTEGER NOT NULL,
                rank_id INTEGER NOT NULL,
                differential_diagnosis_semantic_relationship_id INTEGER NOT NULL,
                FOREIGN KEY (cases_bench_id) REFERENCES bench29.cases_bench(id) ON DELETE CASCADE,
                FOREIGN KEY (rank_id) REFERENCES bench29.differential_diagnosis_to_rank(id) ON DELETE CASCADE,
                FOREIGN KEY (differential_diagnosis_semantic_relationship_id) 
                    REFERENCES registry.diagnosis_semantic_relationship(id) ON DELETE CASCADE
            );
        """))
        
        connection.commit()
        print("Tables recreated successfully with correct references")

if __name__ == "__main__":
    fix_tables() 