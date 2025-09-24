import deepl
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass

from .constants import LanguageCodes, TranslationConstants


@dataclass
class TranslationResult:
    """翻訳結果を表すデータクラス"""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    detected_language: Optional[str] = None
    character_count: int = 0
    confidence: Optional[float] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.character_count == 0:
            self.character_count = len(self.original_text)


class DeepLExtractor:
    """DeepL APIとの統合を管理するクラス"""

    def __init__(self, api_key: Optional[str], is_pro: bool = False):
        self.api_key = api_key
        self.is_pro = is_pro
        self.logger = logging.getLogger(__name__)
        self._translator: Optional[deepl.Translator] = None
        self._rate_limit_reset = datetime.utcnow()
        self._request_count = 0
        self._max_requests_per_minute = TranslationConstants.DEFAULT_RATE_LIMIT

        if api_key and api_key != "your_deepl_api_key":
            self._initialize_translator()
        else:
            self.logger.warning("DeepL API key not configured")

    def _initialize_translator(self) -> None:
        """DeepL Translatorを初期化"""
        try:
            self._translator = deepl.Translator(self.api_key)
            self.logger.info("DeepL Translator initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize DeepL Translator: {e}")
            self._translator = None

    def is_available(self) -> bool:
        """DeepL APIが利用可能かチェック"""
        return self._translator is not None

    async def get_usage(self) -> Optional[Dict[str, Any]]:
        """API使用量を取得"""
        if not self.is_available():
            return None

        try:
            # DeepL APIの使用量取得は同期処理なので、非同期で実行
            usage = await asyncio.to_thread(self._translator.get_usage)
            return {
                "character_count": usage.character.count,
                "character_limit": usage.character.limit,
                "character_remaining": usage.character.limit - usage.character.count if usage.character.limit else None,
                "usage_percentage": (usage.character.count / usage.character.limit * 100) if usage.character.limit else 0
            }
        except Exception as e:
            self.logger.error(f"Failed to get usage information: {e}")
            return None

    async def get_supported_languages(self) -> Optional[Dict[str, List[Dict[str, str]]]]:
        """サポートされている言語リストを取得"""
        if not self.is_available():
            return None

        try:
            source_langs = await asyncio.to_thread(self._translator.get_source_languages)
            target_langs = await asyncio.to_thread(self._translator.get_target_languages)

            return {
                "source": [{"code": lang.code, "name": lang.name} for lang in source_langs],
                "target": [{"code": lang.code, "name": lang.name} for lang in target_langs]
            }
        except Exception as e:
            self.logger.error(f"Failed to get supported languages: {e}")
            return None

    def _check_rate_limit(self) -> bool:
        """レート制限をチェック"""
        now = datetime.utcnow()

        # 1分経過していたらカウントリセット
        if now >= self._rate_limit_reset + timedelta(minutes=1):
            self._request_count = 0
            self._rate_limit_reset = now

        # レート制限チェック
        if self._request_count >= self._max_requests_per_minute:
            self.logger.warning("Rate limit exceeded")
            return False

        return True

    def _validate_text(self, text: str) -> bool:
        """テキストの妥当性をチェック"""
        if not text or len(text.strip()) == 0:
            return False

        if len(text) > TranslationConstants.MAX_TEXT_LENGTH:
            return False

        return True

    def _validate_language_codes(self, source_lang: str, target_lang: str) -> bool:
        """言語コードの妥当性をチェック"""
        if source_lang != "auto" and source_lang not in LanguageCodes.SOURCE_LANGUAGES:
            return False

        if target_lang not in LanguageCodes.TARGET_LANGUAGES:
            return False

        return True

    async def translate_text(
        self,
        text: str,
        target_lang: str = "ja",
        source_lang: str = "auto"
    ) -> Optional[TranslationResult]:
        """テキストを翻訳"""
        if not self.is_available():
            self.logger.error("DeepL Translator not available")
            return None

        # バリデーション
        if not self._validate_text(text):
            self.logger.error("Invalid text for translation")
            return None

        if not self._validate_language_codes(source_lang, target_lang):
            self.logger.error(f"Invalid language codes: {source_lang} -> {target_lang}")
            return None

        # レート制限チェック
        if not self._check_rate_limit():
            self.logger.error("Rate limit exceeded")
            return None

        try:
            # DeepL APIで翻訳実行
            self._request_count += 1

            # 翻訳パラメータ設定
            translate_params = {
                "text": text,
                "target_lang": target_lang
            }

            # source_langが"auto"でない場合のみ指定
            if source_lang != "auto":
                translate_params["source_lang"] = source_lang

            # 翻訳実行（非同期）
            result = await asyncio.to_thread(self._translator.translate_text, **translate_params)

            # 結果を返す
            translation_result = TranslationResult(
                original_text=text,
                translated_text=result.text,
                source_language=source_lang,
                target_language=target_lang,
                detected_language=result.detected_source_lang,
                character_count=len(text)
            )

            self.logger.info(f"Translation completed: {source_lang} -> {target_lang} ({len(text)} chars)")
            return translation_result

        except deepl.exceptions.QuotaExceededException:
            self.logger.error("DeepL API quota exceeded")
            return None
        except deepl.exceptions.AuthorizationException:
            self.logger.error("DeepL API authorization failed")
            return None
        except Exception as e:
            self.logger.error(f"Translation failed: {e}")
            return None

    async def detect_language(self, text: str) -> Optional[str]:
        """テキストの言語を検出"""
        if not self.is_available():
            return None

        if not self._validate_text(text):
            return None

        try:
            # 翻訳を実行して検出された言語を取得
            # DeepLには専用の言語検出APIがないため、この方法を使用
            result = await asyncio.to_thread(
                self._translator.translate_text,
                text=text[:100],  # 最初の100文字のみで検出
                target_lang="en"  # 一時的に英語に翻訳
            )
            return result.detected_source_lang
        except Exception as e:
            self.logger.error(f"Language detection failed: {e}")
            return None

    def get_language_name(self, lang_code: str, is_source: bool = True) -> str:
        """言語コードから言語名を取得"""
        if is_source:
            return LanguageCodes.SOURCE_LANGUAGES.get(lang_code, lang_code)
        else:
            return LanguageCodes.TARGET_LANGUAGES.get(lang_code, lang_code)