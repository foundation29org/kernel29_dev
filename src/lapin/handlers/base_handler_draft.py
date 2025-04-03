# model_handler.py

from .conf.base_conf import CONFIG_REGISTRY #relative import, this will work?

class ModelHandler:
    """
    Manages the orchestration between configuration classes and caller classes.
    """
    def __init__(self):
        # Optionally, you can store state here or load more context if needed
        pass

    def get_response(self, alias: str, prompt: str) -> str:
        """
        High-level method that:
          1) Looks up the config class by alias in CONFIG_REGISTRY.
          2) Instantiates the config object.
          3) Retrieves the caller class from config.caller_class().
          4) Builds the caller with config.get_params().
          5) Calls the LLM and returns the text.
        """
        config_cls = CONFIG_REGISTRY.get(alias)
        if not config_cls:
            raise ValueError(f"No configuration found for alias '{alias}'.")

        config_obj = config_cls()  # Instantiate the configuration
        caller_cls = config_obj.caller_class()
        params = config_obj.get_params()

        caller = caller_cls(params)
        return caller.call_llm(prompt)

    # Additional methods could be added here. For example:
    # - a method to list available aliases
    # - a method to refresh environment variables
    # - concurrency or request tracking


    def list_available_models(self) -> List[str]:
        """
        Return a list of all available model aliases.
        """
        return sorted(CONFIG_REGISTRY.keys())

    def reload_config(self):
        """
        Example method to reload or refresh the model configurations.
        You could do importlib.reload(model_config) and then rebuild CONFIG_REGISTRY,
        or re-read environment variables, etc.
        """
        # For demonstration, we just print a statement.
        print("reload_config() called, but not implemented yet.")

    def handle_error(self, exc: Exception, alias: str, prompt: str):
        """
        A custom error handling strategy – logs the error to console here,
        but could log to a file, database, monitoring system, etc.
        """
        print(f"[ERROR] Model '{alias}' had an error for prompt: {prompt}\n{exc}")

    def enable_caching(self, enabled: bool = True):
        """
        Enable or disable the caching mechanism.
        If disabled, we'll clear the cache.
        """
        if not enabled:
            self.cache.clear()
            print("[INFO] Cache disabled and cleared.")
        else:
            print("[INFO] Caching enabled. Current cache size:", len(self.cache))
        # In a more robust system, you'd store a state to skip caching in get_response() if disabled.

    def set_concurrency_limit(self, alias: str, concurrency_limit: int):
        """
        Set or update a concurrency limit for a given model alias.
        If concurrency_limit = 0, remove any concurrency limit (infinite).
        """
        if concurrency_limit <= 0:
            # Means "no limit"
            if alias in self.concurrency_limits:
                del self.concurrency_limits[alias]
            print(f"[INFO] Removed concurrency limit for '{alias}'.")
        else:
            self.concurrency_limits[alias] = threading.Semaphore(concurrency_limit)
            print(f"[INFO] Set concurrency limit of {concurrency_limit} for '{alias}'.")

    def summarize_usage(self) -> str:
        """
        Return a string summarizing usage (i.e., how many times each alias was called).
        """
        lines = []
        for alias in sorted(CONFIG_REGISTRY.keys()):
            count = self.usage_counts.get(alias, 0)
            lines.append(f"{alias}: {count} calls")
        return "\n".join(lines)

    # ---------- Private Helpers ----------

    def _increment_usage(self, alias: str):
        """Increment usage count for the given model alias."""
        self.usage_counts[alias] = self.usage_counts.get(alias, 0) + 1
