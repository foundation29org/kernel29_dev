from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, ForeignKeyConstraint
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class CasesBench(Base):
    __tablename__ = 'cases_bench'

    id = Column(Integer, primary_key=True)
    hospital = Column(String(255))  # Corrected
    original_text = Column(Text)
    meta_data =Column(JSON)
    processed_date = Column(DateTime)
    source_type = Column(String(255))
    source_file_path = Column(Text)


class CasesBenchMetadata(Base):
    __tablename__ = 'cases_bench_metadata'

    id = Column(Integer, primary_key=True)
    cases_bench_id = Column(Integer)
    __table_args__ = (ForeignKeyConstraint(['cases_bench_id'], ['cases_bench.id'], ondelete='CASCADE'),)
    disease_type = Column(String(255))
    primary_medical_specialty = Column(String(255))
    sub_medical_specialty = Column(String(255))
    alternative_medical_specialty = Column(String(255))
    comments = Column(Text)
    complexity = Column(String(255)) #TODO: add severity_levels_id  foreign key
    #TODO: check medical_specialty from ramedis paper


class CasesBenchGoldDiagnosis(Base):
    __tablename__ = 'cases_bench_gold_diagnosis'

    id = Column(Integer, primary_key=True)

    cases_bench_id = Column(Integer)
    __table_args__ = (ForeignKeyConstraint(['cases_bench_id'], ['cases_bench.id'], ondelete='CASCADE'),)
    diagnosis_type_tag = Column(String(255))
    alternative = Column(String)
    further = Column(String)


class LlmDiagnosis(Base):
    __tablename__ = 'llm_diagnosis'

    id = Column(Integer, primary_key=True)

    cases_bench_id = Column(Integer)
    __table_args__ = (ForeignKeyConstraint(['cases_bench_id'], ['cases_bench.id'], ondelete='CASCADE'),)

    model_id = Column(Integer)
    __table_args__ = (ForeignKeyConstraint(['model_id'], ['models.id'], ondelete='CASCADE'),)

    prompt_id = Column(Integer)
    __table_args__ = (ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='CASCADE'),)

    diagnosis = Column(Text)
    timestamp = Column(DateTime)


class LlmDiagnosisRank(Base):
    __tablename__ = 'llm_diagnosis_rank'

    id = Column(Integer, primary_key=True)
 
    cases_bench_id = Column(Integer)
    __table_args__ = (ForeignKeyConstraint(['cases_bench_id'], ['cases_bench.id'], ondelete='CASCADE'),)

    llm_diagnosis_id = Column(Integer)
    __table_args__ = (ForeignKeyConstraint(['llm_diagnosis_id'], ['llm_diagnosis.id'], ondelete='CASCADE'),)

    rank_position = Column(Integer)
    predicted_diagnosis = Column(String(255))
    reasoning = Column(Text)


class LlmDiagnosisBySeverity(Base):
    __tablename__ = 'llm_diagnosis_by_severity'

    id = Column(Integer, primary_key=True)

    cases_bench_id = Column(Integer)
    __table_args__ = (ForeignKeyConstraint(['cases_bench_id'], ['cases_bench.id'], ondelete='CASCADE'),)

    llm_diagnosis_id = Column(Integer)
    __table_args__ = (ForeignKeyConstraint(['llm_diagnosis_id'], ['llm_diagnosis.id'], ondelete='CASCADE'),)

    severity_levels_id = Column(Integer)
    __table_args__ = (ForeignKeyConstraint(['severity_levels_id'], ['severity_levels.id'], ondelete='CASCADE'),)


class LlmDiagnosisBySemanticRelationship(Base):
    __tablename__ = 'llm_diagnosis_by_semantic_relationship'

    id = Column(Integer, primary_key=True)

    cases_bench_id = Column(Integer)
    __table_args__ = (ForeignKeyConstraint(['cases_bench_id'], ['cases_bench.id'], ondelete='CASCADE'),)

    llm_diagnosis_id = Column(Integer)
    __table_args__ = (ForeignKeyConstraint(['llm_diagnosis_id'], ['llm_diagnosis.id'], ondelete='CASCADE'),)

    diagnosis_semantic_relationship_id = Column(Integer)
    __table_args__ = (ForeignKeyConstraint(['diagnosis_semantic_relationship_id'], ['diagnosis_semantic_relationship.id'], ondelete='CASCADE'),)

class SeverityLevels(Base):
    __tablename__ = 'severity_levels'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(Text)


class DiagnosisSemanticRelationship(Base):
    __tablename__ = 'diagnosis_semantic_relationship'

    id = Column(Integer, primary_key=True)
    semantic_relationship = Column(String(255))
    description = Column(Text)


class Models(Base):
    __tablename__ = 'models'

    id = Column(Integer, primary_key=True)
    alias = Column(String(255))
    name = Column(String(255))
    provider = Column(String(255))


class Prompts(Base):
    __tablename__ = 'prompts'

    id = Column(Integer, primary_key=True)
    alias = Column(String(255))
    description = Column(Text)


class LlmAnalysis(Base):
    __tablename__ = 'llm_analysis'

    id = Column(Integer, primary_key=True)
    cases_bench_id = Column(Integer)
    llm_diagnosis_id = Column(Integer)
    predicted_rank = Column(Integer)
    diagnosis_semantic_relationship_id = Column(Integer)
    severity_levels_id = Column(Integer) #TODO: change for diferential_severity_diagnosis
    
    __table_args__ = (
        ForeignKeyConstraint(['cases_bench_id'], ['cases_bench.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['llm_diagnosis_id'], ['llm_diagnosis.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['diagnosis_semantic_relationship_id'], ['diagnosis_semantic_relationship.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['severity_levels_id'], ['severity_levels.id'], ondelete='CASCADE'),
    )