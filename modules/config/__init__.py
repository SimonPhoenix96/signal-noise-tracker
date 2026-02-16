"""
Config Management Module

Handles loading, validation, and management of configuration files.
"""

import yaml
from typing import Dict, Any
from pathlib import Path

from ..logger import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """Manages configuration files"""

    def __init__(self, config_dir: str = "./config"):
        self.config_dir = Path(config_dir)
        self.configs: Dict[str, Any] = {}
        logger.info(f"ConfigManager initialized (config_dir={self.config_dir})")

    def load_config(self, filename: str, required: bool = True) -> Dict[str, Any]:
        """
        Load a configuration file

        Args:
            filename: Configuration filename (without .yaml extension)
            required: Whether the config is required

        Returns:
            Configuration dictionary
        """
        config_path = self.config_dir / f"{filename}.yaml"

        if not config_path.exists():
            if required:
                logger.error(f"Required config file not found: {config_path}")
                raise FileNotFoundError(f"Config file not found: {config_path}")
            else:
                logger.warning(f"Config file not found, using defaults: {config_path}")
                return {}

        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            self.configs[filename] = config
            logger.info(f"Loaded config: {filename}")
            return config

        except yaml.YAMLError as e:
            logger.error(f"Failed to parse config {filename}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load config {filename}: {e}")
            raise

    def get_config(self, filename: str) -> Dict[str, Any]:
        """Get a loaded configuration"""
        return self.configs.get(filename, {})

    def reload_all(self):
        """Reload all configuration files"""
        config_files = ["feeds", "agents", "settings"]

        for filename in config_files:
            try:
                self.load_config(filename, required=False)
            except Exception as e:
                logger.error(f"Failed to reload {filename}: {e}")

        logger.info("All configurations reloaded")

    def validate_config(self, config: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        Validate configuration against schema

        Args:
            config: Configuration dictionary
            schema: Schema dictionary

        Returns:
            True if valid
        """
        # Simple validation - check required keys exist
        required = schema.get("required", [])
        optional = schema.get("optional", [])

        for key in required:
            if key not in config:
                logger.error(f"Missing required config key: {key}")
                return False

        logger.debug("Configuration validated")
        return True
