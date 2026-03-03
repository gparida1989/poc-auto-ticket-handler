import os
import yaml

class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.data = self._load_config()

    def _load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}

    def get(self, key, default=None):
        return self.data.get(key, default)
