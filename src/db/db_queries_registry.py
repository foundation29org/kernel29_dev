"""
Database query utilities for the registry schema.
Contains functions for retrieving and manipulating registry data.
"""

def get_semantic_relationship_id(session, relationship_name, default_id=1):
    """
    Get the ID for a semantic relationship by name.
    
    Args:
        session: SQLAlchemy session
        relationship_name: Name of the semantic relationship to find
        default_id: Default ID to return if relationship is not found
        
    Returns:
        Integer ID of the relationship, or default_id if not found
    """
    from db.registry.registry_models import DiagnosisSemanticRelationship
    
    relationship = session.query(DiagnosisSemanticRelationship).filter_by(
        semantic_relationship=relationship_name
    ).first()
    
    if relationship:
        return relationship.id
    
    # If not found, return default ID
    print(f"Warning: Semantic relationship '{relationship_name}' not found, using default ID {default_id}")
    return default_id

def get_severity_id(session, severity_name, default_id=5):
    """
    Get the ID for a severity level by name.
    
    Args:
        session: SQLAlchemy session
        severity_name: Name of the severity level to find
        default_id: Default ID to return if severity is not found
        
    Returns:
        Integer ID of the severity, or default_id if not found
    """
    from db.registry.registry_models import SeverityLevels
    
    severity = session.query(SeverityLevels).filter_by(name=severity_name).first()
    
    if severity:
        return severity.id
    
    # If not found, return default ID
    print(f"Warning: Severity level '{severity_name}' not found, using default ID {default_id}")
    return default_id
