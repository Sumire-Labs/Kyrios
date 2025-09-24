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
            # Check if we're using the standard tomllib (Python 3.11+) or toml library
            if tomllib.__name__ == 'tomllib':
                # Python 3.11+ tomllib (binary mode)
                with open(self.config_path, "rb") as f:
                    return tomllib.load(f)  # type: ignore
            else:
                # toml library (text mode)
                with open(self.config_path, "r", encoding="utf-8") as f:
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
        return self.config.get("bot", {}).get("description", "Luna - Advanced Discord Administration Bot")

    @property
    def database_path(self) -> str:
        return self.config.get("database", {}).get("path", "luna.db")

    @property
    def database_backup_interval(self) -> int:
        return self.config.get("database", {}).get("backup_interval", 3600)

    @property
    def logging_level(self) -> str:
        return self.config.get("logging", {}).get("level", "INFO")

    @property
    def logging_file(self) -> str:
        return self.config.get("logging", {}).get("file", "luna.log")

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
    def eventbus_max_history_size(self) -> int:
        return self.config.get("eventbus", {}).get("max_history_size", 1000)

    @property
    def logger_log_joins(self) -> bool:
        return self.config.get("logger", {}).get("log_joins", True)

    @property
    def status_type(self) -> str:
        return self.config.get("status", {}).get("type", "game")

    @property
    def status_message(self) -> str:
        return self.config.get("status", {}).get("message", "Managing your server 🛡️")

    @property
    def status_streaming_url(self) -> str:
        return self.config.get("status", {}).get("streaming_url", "")

    @property
    def spotify_client_id(self) -> Optional[str]:
        return self.config.get("spotify", {}).get("client_id")

    @property
    def spotify_client_secret(self) -> Optional[str]:
        return self.config.get("spotify", {}).get("client_secret")

    @property
    def spotify_enabled(self) -> bool:
        """Spotify機能が有効かチェック"""
        return (self.spotify_client_id is not None and
                self.spotify_client_secret is not None and
                self.spotify_client_id != "your_spotify_client_id")

    @property
    def deepl_api_key(self) -> Optional[str]:
        return self.config.get("deepl", {}).get("api_key")

    @property
    def deepl_is_pro(self) -> bool:
        return self.config.get("deepl", {}).get("api_type", "free").lower() == "pro"

    @property
    def deepl_rate_limit(self) -> int:
        return self.config.get("deepl", {}).get("rate_limit_per_minute", 30)

    @property
    def deepl_default_target_lang(self) -> str:
        return self.config.get("deepl", {}).get("default_target_lang", "ja")

    @property
    def deepl_enabled(self) -> bool:
        """DeepL機能が有効かチェック"""
        return (self.deepl_api_key is not None and
                self.deepl_api_key != "your_deepl_api_key")

    @property
    def features_translation(self) -> bool:
        return self.config.get("features", {}).get("translation", True)

    @property
    def translation_max_text_length(self) -> int:
        return self.config.get("translation", {}).get("max_text_length", 5000)

    @property
    def translation_save_history(self) -> bool:
        return self.config.get("translation", {}).get("save_history", True)

    @property
    def translation_enable_auto_detect(self) -> bool:
        return self.config.get("translation", {}).get("enable_auto_detect", True)

    @property
    def translation_show_confidence(self) -> bool:
        return self.config.get("translation", {}).get("show_confidence", True)