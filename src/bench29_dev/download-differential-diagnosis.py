"""
Script to download differential diagnoses from database or files.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional

# Add the parent directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))

from db.utils.db_utils import get_session
from db.bench29.bench29_models import CasesBench, LlmDifferentialDiagnosis
from db.db_queries import get_model_id, get_prompt_id
from bench29.libs.parser_libs import parse_differential_diagnosis

def download_differential_diagnoses_from_db(
	output_dir: str,
	case_ids=None,
	model_id=None,
	prompt_id=None,
	limit=None,
	verbose=False
) -> List[Dict[str, Any]]:
	"""
	Download differential diagnoses from database.
	
	Args:
		output_dir: Directory to save downloaded diagnoses
		case_ids: Optional list of case IDs to filter by
		model_id: Optional model ID to filter by
		prompt_id: Optional prompt ID to filter by
		limit: Optional limit on number of diagnoses to retrieve
		verbose: Whether to print status information
		
	Returns:
		List of downloaded diagnosis dictionaries
	"""
	if verbose:
		print("Downloading differential diagnoses from database")
		
	# Create output directory if it doesn't exist
	os.makedirs(output_dir, exist_ok=True)
	
	# Create database session
	session = get_session()
	

	# Build query
	query = session.query(LlmDifferentialDiagnosis)
	
	# Apply filters
	if case_ids:
		query = query.filter(LlmDifferentialDiagnosis.cases_bench_id.in_(case_ids))
	if model_id is not None:
		query = query.filter(LlmDifferentialDiagnosis.model_id == model_id)
	if prompt_id is not None:
		query = query.filter(LlmDifferentialDiagnosis.prompt_id == prompt_id)
	if limit is not None:
		query = query.limit(limit)
		
	# Execute query
	diagnoses = query.all()
	diagnoses_dict = [diag.to_dict() for diag in diagnoses]
	if verbose:
		print(f"Found {len(diagnoses)} differential diagnoses")
		
	# Download each diagnosis
	downloaded = []
	
	for i, diagnosis in enumerate(diagnoses):
		if verbose and (i == 0 or (i+1) % 10 == 0 or i+1 == len(diagnoses)):
			print(f"Downloading diagnosis {i+1}/{len(diagnoses)}")
			
			

		
		# Save to file
		filename = f"differential_{diagnosis.cases_bench_id}_{diagnosis.model_id}_{diagnosis.prompt_id}_{diagnosis.id}.json"
		filepath = os.path.join(output_dir, filename)
		

		with open(filepath, 'w', encoding='utf-8') as f:
			json.dump(diagnosis_data, f, indent=2)
			
	
	return 
		


def import_differential_diagnoses_from_files(
	input_dir: str,
	save_to_db: bool = True,
	verbose: bool = False
) -> List[Dict[str, Any]]:
	"""
	Import differential diagnoses from files.
	
	Args:
		input_dir: Directory containing diagnosis files
		save_to_db: Whether to save parsed diagnoses to database
		verbose: Whether to print status information
		
	Returns:
		List of imported diagnosis dictionaries
	"""
	if verbose:
		print(f"Importing differential diagnoses from {input_dir}")
		
	# Check if directory exists
	if not os.path.exists(input_dir) or not os.path.isdir(input_dir):
		if verbose:
			print(f"Input directory {input_dir} does not exist")
		return []
		
	# Get all JSON files
	json_files = [f for f in os.listdir(input_dir) if f.endswith('.json') or f.endswith('.jsonl')]
	
	if verbose:
		print(f"Found {len(json_files)} JSON files")
		
	# Import each file
	imported = []
	
	for i, filename in enumerate(json_files):
	import json
	from sqlalchemy import create_engine
	from sqlalchemy.orm import sessionmaker
	from models import LlmDifferentialDiagnosis  # your model definition

	# Create an engine and session
	engine = create_engine("your_connection_string")
	Session = sessionmaker(bind=engine)
	session = Session()

	# Read the JSON file
	with open("diagnoses.json", "r") as f:
		diagnoses_data = json.load(f)

	# Create ORM instances and add to session
	for diag_data in diagnoses_data:
		diagnosis = LlmDifferentialDiagnosis(**diag_data)
		session.add(diagnosis)

	# Commit the transaction to persist changes
	session.commit()