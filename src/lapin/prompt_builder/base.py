"""
PromptBuilder base module.

This module defines a base class for building and managing prompt templates.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Callable
from functools import partial
from string import Formatter
from libs.libs import (separator)

import re
from string import Formatter


class PromptBuilder(ABC):
	"""
	Base class for building prompt templates.
	
	This class provides functionality to load sections from various sources,
	build a template, and create a partial function for efficient reuse.
	"""
	
	def __init__(self, verbose: bool = False):
		"""
		Initialize the PromptTemplateBuilder.
		
		Args:
			verbose: Whether to print status information
		"""
		self.verbose = verbose
		self.sections = {}  # Will store loaded section content
		self.meta_template = ""  # Template string with placeholders
		self.prompt_template = None  # Will store the partial function
	
	def load_section_from_db(self, section_name: str, prompt_alias: Optional[str] = None, prompt_id: Optional[int] = None):
		"""
		Load a section from database.
		
		Args:
			section_name: Name of the section to load
			prompt_alias: Alias of the prompt to load
			prompt_id: ID of the prompt to load
			
		Returns:
			Self for method chaining
		"""
		if self.verbose:
			print(f"Loading section {section_name} from database")
		
		from bench29.libs.prompt_libs import get_prompt
		content = get_prompt(prompt_alias=prompt_alias, prompt_id=prompt_id, verbose=self.verbose)
		self.sections[section_name] = content or ""
		return self
	
	def load_section_from_file(self, section_name: str, file_path: str):
		"""
		Load a section from a local file.
		
		Args:
			section_name: Name of the section to load
			file_path: Path to the file to load
			
		Returns:
			Self for method chaining
		"""
		if self.verbose:
			print(f"Loading section {section_name} from file {file_path}")
		
		from bench29.libs.prompt_libs import load_json_template_file
		content = load_json_template_file(file_path, verbose=self.verbose)
		self.sections[section_name] = content
		return self
	
	def load_section_from_table(self, section_name: str, table_obj, transform_func):
		"""
		Load a section from a database table.
		
		Args:
			section_name: Name of the section to load
			table_obj: SQLAlchemy table object
			transform_func: Function to transform table data to text
			
		Returns:
			Self for method chaining
		"""
		if self.verbose:
			print(f"Loading section {section_name} from table")
		
		content = transform_func(table_obj, verbose=self.verbose)
		self.sections[section_name] = content
		return self
	
	def load_section_from_text(self, section_name: str, default_value: str):
		"""
		Load a section from text, usually from a default value.
		
		Args:
			section_name: Name of the section to load
			default_value: Default value for the section
			
		Returns:
			Self for method chaining
		"""
		if self.verbose:
			print(f"Loading section {section_name} from default value")
			
		self.sections[section_name] = default_value
		return self
	
	def set_section(self, section_name: str, content: str):
		"""
		Set a section directly.
		
		Args:
			section_name: Name of the section to set
			content: Content for the section
			
		Returns:
			Self for method chaining
		"""
		self.sections[section_name] = content
		return self
	
	def set_meta_template(self, template_string: str):
		"""
		Set the template string.
		
		Args:
			template_string: Template string with placeholders
			
		Returns:
			Self for method chaining
		"""
		self.meta_template = template_string
		return self
	

	def get_placeholder_names(self,debug:bool = False):

		
		# Create a formatter that will handle the string formatting
		formatter = Formatter()
		if not self.prompt_template:    
			self.prompt_template = self.meta_template
		
		# Get all field names in the template
		if debug:
			separator()
			print("in get_placeholder_names")
			separator()
			separator(n=2,char="")
			print(self.prompt_template)

			input("Press Enter to continue...")	
			string_formatter = formatter.parse(self.prompt_template)    
			print(string_formatter)
			for first_, field_name, second_, third_ in string_formatter:
				print("first_:",first_)   
				print("field_name:",field_name)
				print("second_:",second_)
				print("third_:",third_)
				separator()
				print("field name")
				if second_:
					print("second_",type(second_))
					input("P¡ ajsb ress Enter to continue...")
				if second_ and "{" in second_ :
					print("\n second contains {")
				separator()
				separator(n=2,char="")
				print(field_name)
				input("Press Enter to continue...")
		field_names = []
		for first_, field_name, second_, third_ in formatter.parse(self.prompt_template):
			if field_name:
				if second_:
					# print("jojo",type(second_))
					# input("jojojoj Press Enter to continue...")
					if "{" in second_:
						separator()
						print("WARNING: your string probably contains a unscaped json")
						separator()
						continue
				field_names.append(field_name)
		
		return list(set(field_names))  # Return unique placeholders

	def build_partial_template(self, debug:bool = False, verbose:bool = False, **kwargs):
		"""
		Build a partially formatted prompt template.
		
		This method replaces only the provided placeholders in the template,
		leaving other placeholders intact for later formatting.
		
		Args:
			**kwargs: Parameters to format in the template
			
		Returns:
			Partially formatted template string with remaining placeholders
		"""
		# Get the original template
		if not self.prompt_template:    
			self.prompt_template = self.meta_template
		
		# Extract placeholders using the new helper method
		if debug: 
			separator()
			print("in build_partial_template") 
			separator()
			separator(n=2,char="")
			print(self.prompt_template) 
		field_names = self.get_placeholder_names()
		
		# For fields that aren't in kwargs, create temporary placeholders
		preserved = {}
		for field in field_names:
			if field not in kwargs:
				# Create a unique temporary placeholder
				preserved[field] = "{" + field + "}"
		
		# Combine kwargs with preserved placeholders
		format_dict = {**kwargs, **preserved}
		
		# Do the formatting
		self.prompt_template = self.prompt_template.format(**format_dict)
		
		# debug = True
		if debug:
			separator()
			print("in build_partial_template") 
			separator()
			separator(n=2,char="")
			print(f"Created partially formatted template with: {list(kwargs.keys())}")
			print(f"Remaining placeholders: {[k for k in preserved.keys()]}")
			input("Press Enter to continue...")
			print(self.prompt_template)
			input("Press Enter to continue...")
		# verbose = True
		if verbose:
			print(f"Created partially formatted template with: {list(kwargs.keys())}")
			print(f"Remaining placeholders: {[k for k in preserved.keys()]}")
		
		return self.prompt_template

	def build_template(self):
		"""
		Build the prompt template as a partial function.
		
		This creates a reusable partial function that can be called
		multiple times with different parameters.
		
		Returns:
			Self for method chaining
		"""
		if self.verbose:
			print("Building prompt template")
		
		# Start with the template string
		if self.verbose:
			print("Template built successfully") 
		# Populate the template with sections
 
		self.prompt_template = self.build_partial_template(**self.sections)

		return self.prompt_template



	def to_prompt(self, text: str = None, kwargs: dict = None): 
		"""
		Format the prompt with the given parameters.
		
		Args:
			**kwargs: Parameters to use in formatting
			
		Returns:
			Formatted prompt string
		"""
		if not self.prompt_template:
			if self.verbose:
				print("Template not built yet, building now")
			self.build_template()
		if not kwargs:
			placeholders = self.get_placeholder_names()
			if len(placeholders) != 1:
				raise ValueError(f"""WARNING: you have more than one placeholder in your template,
				placeholder list: {placeholders} """)
			placeholder = placeholders[0]
			kwargs = {placeholder:text}
			verbose = True
			if verbose:
				print(f"kwargs: {kwargs}")
		# Format with the given parameters
		return self.prompt_template.format(**kwargs)
	
	def reset(self):
		"""
		Reset the builder state.
		
		Returns:
			Self for method chaining
		"""
		self.sections = {}
		self.meta_template = ""
		self.prompt_template = None
		return self
	
	@abstractmethod
	def initialize(self):
		"""
		Initialize the builder with its default configuration.
		
		This method should be implemented by subclasses to set up
		their specific template and default sections.
		
		Returns:
			Self for method chaining
		"""
		pass
