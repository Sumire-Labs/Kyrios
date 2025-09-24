from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

from .deepl_extractor import DeepLExtractor, TranslationResult
from .constants import LanguageCodes, TranslationConstants


class TranslationService:
    """翻訳機能の統合サービスクラス"""

    def __init__(self, deepl_extractor: DeepLExtractor, event_bus=None):
        self.deepl_extractor = deepl_extractor
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)

    def is_available(self) -> bool:
        """翻訳サービスが利用可能かチェック"""
        return self.deepl_extractor.is_available()

    async def translate(
        self,
        text: str,
        target_lang: str = TranslationConstants.DEFAULT_TARGET_LANG,
        source_lang: str = TranslationConstants.DEFAULT_SOURCE_LANG,
        user_id: Optional[int] = None,
        guild_id: Optional[int] = None
    ) -> Optional[TranslationResult]:
        """テキスト翻訳のメインメソッド"""

        # 入力検証
        validation_error = self._validate_translation_input(text, source_lang, target_lang)
        if validation_error:
            self.logger.warning(f"Translation validation failed: {validation_error}")
            return None

        try:
            # 翻訳実行
            result = await self.deepl_extractor.translate_text(
                text=text,
                target_lang=target_lang,
                source_lang=source_lang
            )

            if result:
                # イベント発火（統計・ログ用）
                if self.event_bus:
                    await self.event_bus.emit_event("translation_completed", {
                        "user_id": user_id,
                        "guild_id": guild_id,
                        "source_lang": result.source_language,
                        "target_lang": result.target_language,
                        "detected_lang": result.detected_language,
                        "character_count": result.character_count,
                        "timestamp": result.timestamp
                    })

                self.logger.info(f"Translation successful: {result.character_count} characters")

            return result

        except Exception as e:
            # エラーイベント発火
            if self.event_bus:
                await self.event_bus.emit_event("translation_error", {
                    "user_id": user_id,
                    "guild_id": guild_id,
                    "error": str(e),
                    "text_length": len(text),
                    "source_lang": source_lang,
                    "target_lang": target_lang
                })

            self.logger.error(f"Translation service error: {e}")
            return None

    def _validate_translation_input(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> Optional[str]:
        """翻訳入力の検証"""

        # テキスト検証
        if not text or not text.strip():
            return TranslationConstants.ERROR_MESSAGES["TEXT_TOO_SHORT"]

        if len(text) > TranslationConstants.MAX_TEXT_LENGTH:
            return TranslationConstants.ERROR_MESSAGES["TEXT_TOO_LONG"]

        # 言語コード検証
        if source_lang != "auto" and source_lang not in LanguageCodes.SOURCE_LANGUAGES:
            return TranslationConstants.ERROR_MESSAGES["INVALID_LANGUAGE"]

        if target_lang not in LanguageCodes.TARGET_LANGUAGES:
            return TranslationConstants.ERROR_MESSAGES["INVALID_LANGUAGE"]

        return None

    async def detect_language(self, text: str) -> Optional[str]:
        """言語自動検出"""
        if not self.is_available():
            return None

        try:
            detected_lang = await self.deepl_extractor.detect_language(text)

            if detected_lang and self.event_bus:
                await self.event_bus.emit_event("language_detected", {
                    "text_length": len(text),
                    "detected_language": detected_lang
                })

            return detected_lang

        except Exception as e:
            self.logger.error(f"Language detection failed: {e}")
            return None

    async def get_usage_info(self) -> Optional[Dict[str, Any]]:
        """API使用量情報を取得"""
        if not self.is_available():
            return None

        try:
            usage = await self.deepl_extractor.get_usage()
            return usage
        except Exception as e:
            self.logger.error(f"Failed to get usage info: {e}")
            return None

    async def get_supported_languages(self) -> Optional[Dict[str, List[Dict[str, str]]]]:
        """サポートされている言語リストを取得"""
        if not self.is_available():
            return None

        try:
            languages = await self.deepl_extractor.get_supported_languages()
            return languages
        except Exception as e:
            self.logger.error(f"Failed to get supported languages: {e}")
            return None

    def get_popular_languages(self, is_source: bool = True) -> Dict[str, str]:
        """よく使用される言語のリストを取得"""
        if is_source:
            return LanguageCodes.POPULAR_SOURCE_LANGUAGES.copy()
        else:
            return LanguageCodes.POPULAR_TARGET_LANGUAGES.copy()

    def get_language_display_name(self, lang_code: str, is_source: bool = True) -> str:
        """言語コードから表示名を取得"""
        return self.deepl_extractor.get_language_name(lang_code, is_source)

    def format_translation_for_discord(self, result: TranslationResult) -> Dict[str, Any]:
        """Discord用に翻訳結果をフォーマット"""
        return {
            "original_text": result.original_text,
            "translated_text": result.translated_text,
            "source_language": self.get_language_display_name(result.source_language, True),
            "target_language": self.get_language_display_name(result.target_language, False),
            "detected_language": self.get_language_display_name(result.detected_language, True) if result.detected_language else None,
            "character_count": result.character_count,
            "timestamp": result.timestamp
        }

    def get_error_message(self, error_key: str) -> str:
        """エラーメッセージを取得"""
        return TranslationConstants.ERROR_MESSAGES.get(error_key, "不明なエラーが発生しました。")

    async def health_check(self) -> Dict[str, Any]:
        """サービスの健康状態をチェック"""
        health_status = {
            "service_available": self.is_available(),
            "api_key_configured": self.deepl_extractor.api_key is not None,
            "timestamp": datetime.utcnow()
        }

        if self.is_available():
            try:
                usage = await self.get_usage_info()
                if usage:
                    health_status["api_usage"] = usage
                    health_status["api_responsive"] = True
                else:
                    health_status["api_responsive"] = False
            except Exception as e:
                health_status["api_responsive"] = False
                health_status["api_error"] = str(e)

        return health_status