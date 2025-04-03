# example_usage.py

from model_configs import CONFIG_REGISTRY

def get_config(alias: str):
    config_class = CONFIG_REGISTRY[alias]
    return config_class()

my_config = get_config("c3opus")
params = my_config.get_params()
print(params)


import model_configs

print(model_configs.list_registered_configs())
# or directly:
from model_configs import CONFIG_REGISTRY

my_cls = CONFIG_REGISTRY["c3opus"]
my_instance = my_cls()
params = my_instance.get_params()