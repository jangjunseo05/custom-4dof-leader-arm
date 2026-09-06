import yaml
from pathlib import Path


class ConfigLoader:
    """
    config.yaml 파일을 읽는 클래스
    """

    def __init__(self, config_path="config/config.yaml"):
        self.config_path = Path(config_path)
        self.config = self.load()

    def load(self):
        with open(self.config_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)

    def get(self):
        return self.config