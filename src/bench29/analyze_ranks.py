import os
import csv
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy_models_working import Base, LlmAnalysis, Models, Prompts, LlmDiagnosis
from math_libs import rescaled_penalized_weighted_stats

def get_session():
    """Create and return a database session"""
    DATABASE_URL = "postgresql://dummy_user:dummy_password_42@localhost/bench29"
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

def analyze_model_prompt_performance(weights=None):
    """
    Analyze performance of each model-prompt combination based on predicted ranks
    and create a CSV file with the results
    
    Args:
        weights: Optional dictionary mapping ranks to weights for the calculation
    """
    # Default weights if none provided
    if weights is None:
        weights = {1: 0.01, 2: 0.02, 3: 0.07, 4: 0.20, 5: 0.30, 6: 0.50}
        
    session = get_session()
    
    print("Querying all analysis records...")
    
    # Get all models
    models = {model.id: (model.name, model.alias) for model in session.query(Models).all()}
    
    # Get all prompts
    prompts = {prompt.id: prompt.alias for prompt in session.query(Prompts).all()}
    
    # Get all analysis records with predicted ranks
    analyses = session.query(
        LlmAnalysis.predicted_rank,
        LlmAnalysis.llm_diagnosis_id
    ).all()
    
    # Now get all diagnosis records to map to models and prompts
    diagnosis_map = {}
    from sqlalchemy_models_working import LlmDiagnosis
    diagnoses = session.query(
        LlmDiagnosis.id,
        LlmDiagnosis.model_id,
        LlmDiagnosis.prompt_id
    ).all()
    for diag_id, model_id, prompt_id in diagnoses:
        diagnosis_map[diag_id] = (model_id, prompt_id)
    
    # Group by model and prompt
    results = {}
    for rank, diag_id in analyses:
        if diag_id in diagnosis_map:
            model_id, prompt_id = diagnosis_map[diag_id]
            if model_id in models and prompt_id in prompts:
                model_name, model_alias = models[model_id]
                prompt_name = prompts[prompt_id]
                
                key = (model_name, model_alias, prompt_name)
                if key not in results:
                    results[key] = []
                
                results[key].append(rank)
    
    # Calculate statistics
    final_results = []
    for (model_name, model_alias, prompt_name), ranks in results.items():
        # Calculate all statistics using our math library
        mean, weighted_mean, penalized_mean, penalized_weighted_mean = rescaled_penalized_weighted_stats(ranks, weights)
        
        final_results.append({
            'model_name': model_name,
            'model_alias': model_alias,
            'prompt_name': prompt_name,
            'sample_count': len(ranks),
            'mean': mean,
            'weighted_mean': weighted_mean,
            'penalized_mean': penalized_mean,
            'penalized_weighted_mean': penalized_weighted_mean
        })
    
    # Sort results by penalized weighted mean (higher is better)
    final_results.sort(key=lambda x: x['penalized_weighted_mean'], reverse=True)
    
    # Write to CSV
    csv_file = 'model_prompt_performance.csv'
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'model_name', 'model_alias', 'prompt_name', 'sample_count',
            'mean', 'weighted_mean', 'penalized_mean', 'penalized_weighted_mean'
        ])
        writer.writeheader()
        writer.writerows(final_results)
    
    print(f"Analysis complete! Results written to {csv_file}")
    
    # Display top 5 best performing model-prompt combinations
    print("\nTop 5 best performing model-prompt combinations:")
    for i, result in enumerate(final_results[:5]):
        print(f"{i+1}. {result['model_name']} ({result['model_alias']}) with {result['prompt_name']} prompt:")
        print(f"   Penalized weighted mean: {result['penalized_weighted_mean']:.4f}")
        print(f"   Weighted mean: {result['weighted_mean']:.4f}")
        print(f"   Mean: {result['mean']:.4f}")
        print(f"   Sample count: {result['sample_count']}")
    
    session.close()
    return final_results

if __name__ == "__main__":
    # Default weights
    weights = {1: 0.01, 2: 0.02, 3: 0.07, 4: 0.20, 5: 0.30, 6: 0.50}
    analyze_model_prompt_performance(weights)
