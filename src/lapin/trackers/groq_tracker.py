"""
Groq API rate limit and price tracking module.
"""

from typing import Dict, List, Optional, Tuple, Any, Type, Callable
from .base_tracker import BaseTracker


TRACKER_REGISTRY = {}


##TODO: Tracker prices should be in a sqlitedb. provider trackers as groq tracker should act as data lake collectors and etls also extends basse tracker if necesary
def register_tracker(cls):
    # Create a temporary instance to get the model name
    tracker = cls()
    name = tracker.model_name
    TRACKER_REGISTRY[name] = cls
    return cls



class GroqTracker(BaseTracker):
	"""
	Groq API provider and model class for tracking rate limits and pricing.
	
	This class extends BaseTracker to provide Groq-specific tracking
	of rate limits, usage, and pricing across multiple models.
	
	It serves both as a provider tracker and as a base class for specific models.
	"""
	
	def __init__(self, model_name: str = None):
		super().__init__()
		self.provider_name = "Groq"
		self.model_name = model_name
		
		# Provider-level rate limits (only used if this instance is a provider, not a model)
		if model_name is None:
			self.rpm = 60  # Provider-wide requests per minute
			self.rpd = 20000  # Provider-wide requests per day
		
		# Model-specific attributes (not used for provider instance)
		self.context_window = 0
		self.is_vision_capable = False
		
		# List to store model instances (only used by provider)
		self.models = []
	
	@staticmethod
	def get_model(model_name: str):
		"""
		Get a tracker instance for the specified model name.
		
		Args:
			model_name: The name of the model to get a tracker for
			
		Returns:
			Instance of the appropriate tracker class or None if not found
		"""
		# Check if model name is an alias

		
		# Check for direct match in registry
		if model_name in TRACKER_REGISTRY:
			tracker_cls = TRACKER_REGISTRY[model_name]
			return tracker_cls()
		# print (f"tracker registry: {TRACKER_REGISTRY}")
		# input("Press Enter to continue...")
		# # Try partial matches #TODO: this should be a list of partial matches
		# for registered_name, tracker_cls in TRACKER_REGISTRY.items():
		# 	# Check if the registered name is contained in the model name
		# 	# or if the model name is contained in the registered name
		# 	if registered_name in model_name or model_name in registered_name:
		# 		return tracker_cls()
		
		return None
	def record_request_by_provider(self, response: Any):
		"""
		Record a request at the provider level.
		
		This allows tracking against provider-wide rate limits.
		
		Args:
			tokens: Number of tokens used (if applicable)
			success: Whether the request was successful
		"""
		tokens = response.usage.total_tokens
		self.prompt_tokens = response.usage.prompt_tokens
		self.completion_tokens = response.usage.completion_tokens    
		super().record_request( prompt_tokens = self.prompt_tokens, completion_tokens= self.completion_tokens)

	def prompt2price_by_provider(self):
		"""
		Calculate the price for the prompt tokens.
		"""
		super().prompt2price(self.prompt_tokens, self.completion_tokens)
































	def list_models(self):
		"""
		List all models registered with this provider.
		
		Returns:
			List of model names
		"""
		return [model.model_name for model in self.models]
	
	def get_model_usage_summary(self):
		"""
		Get a summary of usage across all models.
		
		Returns:
			Dict with model usage information
		"""
		summary = {}
		for model in self.models:
			summary[model.model_name] = {
				"success_count": model.success_count,
				"failed_count": model.failed_count,
				"total_requests": len(model.requests),
				"total_tokens": sum(tokens for _, tokens in model.tokens)
			}
		return summary






	def get_models_by_capability(self, is_vision_capable: bool = False):
		"""
		Get models by capability.
		
		Args:
			is_vision_capable: Filter for vision-capable models
			
		Returns:
			List of model names
		"""
		return [model.model_name for model in self.models if model.is_vision_capable == is_vision_capable]
	
	def get_models_by_context_window(self, min_context_window: int = 0):
		"""
		Get models by minimum context window size.
		
		Args:
			min_context_window: Minimum context window size
			
		Returns:
			List of model names
		"""
		return [model.model_name for model in self.models if model.context_window >= min_context_window]
	
	@classmethod
	def from_config(cls, config):
		"""
		Create a tracker from a model configuration object.
		
		This method bridges between configuration classes and tracker classes.
		
		Args:
			config: A model configuration object with a 'model' attribute
			
		Returns:
			Appropriate tracker instance for the model
		"""
		if not hasattr(config, 'model') or not config.model:
			raise ValueError("Configuration object must have a 'model' attribute")
		
		# Get the model name from the config
		model_name = config.model
		
		# Try to get a tracker for this model
		tracker = cls.get_tracker_for_model(model_name)
		
		# If no specific tracker exists, create a generic one
		if not tracker:
			tracker = cls(model_name)
			
			# Set reasonable defaults based on the model name
			if "70b" in model_name.lower():
				# 70B models typically have higher pricing
				tracker.prompt_price = 0.70
				tracker.completion_price = 2.10
			elif "90b" in model_name.lower():
				# 90B models have the highest pricing
				tracker.prompt_price = 0.90
				tracker.completion_price = 2.70
			else:
				# Default pricing for smaller models
				tracker.prompt_price = 0.20
				tracker.completion_price = 0.60
				
			# Set context window from config if available
			if hasattr(config, 'max_tokens'):
				tracker.context_window = config.max_tokens
				
			# Detect vision capability from model name or system message
			if "vision" in model_name.lower():
				tracker.is_vision_capable = True
			elif hasattr(config, 'system_message') and "vision" in config.system_message.lower():
				tracker.is_vision_capable = True
				
		return tracker


def create_groq_tracker():
	"""
	Create and initialize a GroqTracker instance (as provider).
	
	Returns:
		Initialized GroqTracker
	"""
	return GroqTracker()
