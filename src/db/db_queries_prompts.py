from sqlalchemy import exists

def get_prompt_id(session, prompt_name):
    """
    Get prompt ID from database by alias.
    
    Args:
        session: SQLAlchemy session
        prompt_name: Prompt alias to look for
        
    Returns:
        Integer ID of the prompt or None if not found
    """
    from db.prompts.prompts_models import Prompt
    prompt = session.query(Prompt).filter(Prompt.alias == prompt_name).first()
    if prompt:
        return prompt.id
    return None

def add_prompt(session, prompt_name):
    """
    Add prompt to database if it doesn't exist.
    
    Args:
        session: SQLAlchemy session
        prompt_name: Prompt name/alias to add
        
    Returns:
        Integer ID of the prompt (new or existing)
    """
    from db.prompts.prompts_models import Prompt
    
    # Check if prompt exists
    if not session.query(exists().where(Prompt.alias == prompt_name)).scalar():
        # Create descriptions based on prompt type
        descriptions = {
            "standard": "Standard diagnosis prompt without special techniques",
            "few_shot": "Few-shot learning approach with examples",
            "dynamic_few_shot": "Dynamic few-shot learning with adaptive examples",
            "auto-cot": "Auto Chain-of-Thought prompting for reasoning",
            "medprompt": "Medical-specific prompt optimized for diagnosis"
        }
        
        description = descriptions.get(prompt_name, f"Custom prompt: {prompt_name}")
        
        # Create new prompt
        new_prompt = Prompt(
            alias=prompt_name,
            content=description
        )
        session.add(new_prompt)
        session.commit()
    
    # Get prompt id
    return session.query(Prompt).filter(Prompt.alias == prompt_name).first().id