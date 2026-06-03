#!/usr/bin/env python3
from pathlib import Path
import yaml

PROMPTS_PATH = Path(__file__).parent.parent / "prompts" / "v1.yaml"

class PromptLoader:
    def __init__(self, file_path: Path = PROMPTS_PATH):
        self.file_path = file_path
        self.prompts = self._load_yaml()

    def _load_yaml(self) -> dict:
        if not self.file_path.exists():
            raise FileNotFoundError(f"Prompts configuration file not found at {self.file_path}")
            
        with open(self.file_path, "r", encoding="utf-8") as f:
            try:
                return yaml.safe_load(f)
            except Exception as e:
                raise ValueError(f"Failed to parse prompts YAML file: {e}")

    def get_prompt(self, version: str = "v2") -> str:
        """
        Retrieves the system prompt for the specified version.
        Raises an error if the version does not exist.
        """
        if not self.prompts or version not in self.prompts:
            available = list(self.prompts.keys()) if self.prompts else []
            raise ValueError(f"Prompt version '{version}' does not exist. Available versions: {available}")
            
        version_data = self.prompts[version]
        system_prompt = version_data.get("system_prompt")
        
        if not system_prompt:
            raise ValueError(f"Version '{version}' is missing the 'system_prompt' key.")
            
        return system_prompt

if __name__ == "__main__":
    print("=== Prompt Loader Tester ===")
    loader = PromptLoader()
    try:
        v1_prompt = loader.get_prompt("v1")
        print("v1 loaded successfully, length:", len(v1_prompt))
        v2_prompt = loader.get_prompt("v2")
        print("v2 loaded successfully, length:", len(v2_prompt))
    except Exception as e:
        print("Error:", e)
