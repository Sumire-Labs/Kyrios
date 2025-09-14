from typing import Optional, Dict, Any
try:
    import tomllib
except ImportError:
    import toml as tomllib
from pathlib import Path


class Settings:
    def __init__(self, config_path: str = "config.toml"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            # Check if we're using the toml library (has loads method) or tomllib
            if hasattr(tomllib, 'loads'):
                # toml library (text mode)
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return tomllib.load(f)  # type: ignore
            else:
                # Python 3.11+ tomllib (binary mode)
                with open(self.config_path, "rb") as f:
                    return tomllib.load(f)  # type: ignore
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        except Exception as e:
            raise ValueError(f"Invalid TOML in config file: {e}")

    def reload_config(self) -> None:
        self.config: Dict[str, Any] = self._load_config()

    @property
    def bot_token(self) -> str:
        token = self.config.get("bot", {}).get("token")
        if not token or token == "YOUR_BOT_TOKEN_HERE":
            raise ValueError("Bot token not configured in config.toml")
        return token

    @property
    def bot_prefix(self) -> str:
        return self.config.get("bot", {}).get("prefix", "!")

    @property
    def bot_description(self) -> str:
        return self.config.get("bot", {}).get("description", "Kyrios - Advanced Discord Administration Bot")

    @property
    def database_path(self) -> str:
        return self.config.get("database", {}).get("path", "data/databases/kyrios.db")

    @property
    def database_backup_interval(self) -> int:
        return self.config.get("database", {}).get("backup_interval", 3600)

    @property
    def logging_level(self) -> str:
        return self.config.get("logging", {}).get("level", "INFO")

    @property
    def logging_file(self) -> str:
        return self.config.get("logging", {}).get("file", "data/logs/kyrios.log")

    @property
    def logging_max_size(self) -> int:
        return self.config.get("logging", {}).get("max_size", 10485760)

    @property
    def features_tickets(self) -> bool:
        return self.config.get("features", {}).get("tickets", True)

    @property
    def features_logger(self) -> bool:
        return self.config.get("features", {}).get("logger", True)

    @property
    def features_auto_mod(self) -> bool:
        return self.config.get("features", {}).get("auto_mod", False)

    @property
    def tickets_category_id(self) -> Optional[int]:
        category_id = self.config.get("tickets", {}).get("category_id")
        return int(category_id) if category_id else None

    @property
    def tickets_archive_category_id(self) -> Optional[int]:
        archive_id = self.config.get("tickets", {}).get("archive_category_id")
        return int(archive_id) if archive_id else None

    @property
    def tickets_max_per_user(self) -> int:
        return self.config.get("tickets", {}).get("max_per_user", 3)

    @property
    def logger_ignore_bots(self) -> bool:
        return self.config.get("logger", {}).get("ignore_bots", True)

    @property
    def logger_log_edits(self) -> bool:
        return self.config.get("logger", {}).get("log_edits", True)

    @property
    def logger_log_deletes(self) -> bool:
        return self.config.get("logger", {}).get("log_deletes", True)

    @property
    def logger_log_joins(self) -> bool:
        return self.config.get("logger", {}).get("log_joins", True)