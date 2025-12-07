import os

import yaml


class Config:
    """Secure loader for API keys and provider settings.
    Loads ats/config/keys.yaml but never commits it.
    """

    def __init__(self, path: str = "ats/config/keys.yaml"):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing config file: {path}")

        with open(path, "r") as f:
            self.data = yaml.safe_load(f)

    def polygon_key(self):
        return self.data["polygon"]["api_key"]

    def benzinga_key(self):
        return self.data["benzinga"]["api_key"]

    def ibkr_host(self):
        return self.data["ibkr"]["host"]

    def ibkr_port(self):
        return self.data["ibkr"]["port"]

    def ibkr_client_id(self):
        return self.data["ibkr"]["client_id"]

    def twitter_token(self):
        return self.data["twitter"]["bearer_token"]
