from sqlalchemy import exists

def get_model_id(session, model_name):
    """
    Get model ID from database by alias.
    
    Args:
        session: SQLAlchemy session
        model_name: Model alias to look for
        
    Returns:
        Integer ID of the model or None if not found
    """
    from db.llm.llm_models import Models
    model = session.query(Models).filter(Models.alias == model_name).first()
    if model:
        return model.id
    return None

def add_model(session, model_name):
    """
    Add model to database if it doesn't exist.
    
    Args:
        session: SQLAlchemy session
        model_name: Model name/alias to add
        
    Returns:
        Integer ID of the model (new or existing)
    """
    from db.llm.llm_models import Models
    
    # Check if model exists
    if not session.query(exists().where(Models.alias == model_name)).scalar():
        # Determine provider based on model name
        if "glm" in model_name.lower():
            provider = "Zhipu"
        elif "llama" in model_name.lower():
            provider = "Meta"
        elif "mistral" in model_name.lower():
            provider = "Mistral AI"
        elif "gemini" in model_name.lower():
            provider = "Google"
        elif "chatglm" in model_name.lower():
            provider = "Zhipu"
        else:
            provider = "Unknown"
        
        # Create new model
        new_model = Models(
            alias=model_name,
            name=model_name,
            provider=provider
        )
        session.add(new_model)
        session.commit()
    
    # Get model id
    return session.query(Models).filter(Models.alias == model_name).first().id