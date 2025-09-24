import discord
from typing import Dict, List, Tuple


class LanguageCodes:
    """DeepL APIでサポートされている言語コード"""

    # 翻訳元言語（自動検出含む）
    SOURCE_LANGUAGES = {
        "auto": "自動検出",
        "bg": "ブルガリア語",
        "cs": "チェコ語",
        "da": "デンマーク語",
        "de": "ドイツ語",
        "el": "ギリシャ語",
        "en": "英語",
        "es": "スペイン語",
        "et": "エストニア語",
        "fi": "フィンランド語",
        "fr": "フランス語",
        "hu": "ハンガリー語",
        "id": "インドネシア語",
        "it": "イタリア語",
        "ja": "日本語",
        "ko": "韓国語",
        "lt": "リトアニア語",
        "lv": "ラトビア語",
        "nb": "ノルウェー語",
        "nl": "オランダ語",
        "pl": "ポーランド語",
        "pt": "ポルトガル語",
        "ro": "ルーマニア語",
        "ru": "ロシア語",
        "sk": "スロバキア語",
        "sl": "スロベニア語",
        "sv": "スウェーデン語",
        "tr": "トルコ語",
        "uk": "ウクライナ語",
        "zh": "中国語（簡体字）"
    }

    # 翻訳先言語
    TARGET_LANGUAGES = {
        "bg": "ブルガリア語",
        "cs": "チェコ語",
        "da": "デンマーク語",
        "de": "ドイツ語",
        "el": "ギリシャ語",
        "en-gb": "英語（イギリス）",
        "en-us": "英語（アメリカ）",
        "es": "スペイン語",
        "et": "エストニア語",
        "fi": "フィンランド語",
        "fr": "フランス語",
        "hu": "ハンガリー語",
        "id": "インドネシア語",
        "it": "イタリア語",
        "ja": "日本語",
        "ko": "韓国語",
        "lt": "リトアニア語",
        "lv": "ラトビア語",
        "nb": "ノルウェー語",
        "nl": "オランダ語",
        "pl": "ポーランド語",
        "pt-br": "ポルトガル語（ブラジル）",
        "pt-pt": "ポルトガル語（ポルトガル）",
        "ro": "ルーマニア語",
        "ru": "ロシア語",
        "sk": "スロバキア語",
        "sl": "スロベニア語",
        "sv": "スウェーデン語",
        "tr": "トルコ語",
        "uk": "ウクライナ語",
        "zh": "中国語（簡体字）"
    }

    # よく使用される言語のショートリスト
    POPULAR_SOURCE_LANGUAGES = {
        "auto": "自動検出",
        "en": "英語",
        "ja": "日本語",
        "ko": "韓国語",
        "zh": "中国語",
        "fr": "フランス語",
        "de": "ドイツ語",
        "es": "スペイン語"
    }

    POPULAR_TARGET_LANGUAGES = {
        "ja": "日本語",
        "en-us": "英語（アメリカ）",
        "en-gb": "英語（イギリス）",
        "ko": "韓国語",
        "zh": "中国語",
        "fr": "フランス語",
        "de": "ドイツ語",
        "es": "スペイン語"
    }


class TranslationUI:
    """翻訳機能のUI定数"""

    # 色定数
    COLORS = {
        "TRANSLATION": discord.Color.teal(),
        "SUCCESS": discord.Color.green(),
        "ERROR": discord.Color.red(),
        "INFO": discord.Color.blue()
    }

    # 絵文字定数
    EMOJIS = {
        "TRANSLATE": "🌐",
        "SOURCE_LANG": "📝",
        "TARGET_LANG": "🎯",
        "AUTO_DETECT": "🔍",
        "SUCCESS": "✅",
        "ERROR": "❌",
        "INFO": "ℹ️",
        "HISTORY": "📜",
        "STATS": "📊",
        "REVERSE": "🔄"
    }

    # ボタンスタイル
    BUTTON_STYLES = {
        "TRANSLATE": discord.ButtonStyle.primary,
        "HISTORY": discord.ButtonStyle.secondary,
        "STATS": discord.ButtonStyle.secondary,
        "REVERSE": discord.ButtonStyle.success,
        "DELETE": discord.ButtonStyle.danger
    }


class TranslationConstants:
    """翻訳機能の制限・定数"""

    # テキスト制限
    MAX_TEXT_LENGTH = 5000
    MIN_TEXT_LENGTH = 1

    # API制限
    DEFAULT_RATE_LIMIT = 30  # per minute
    FREE_TIER_LIMIT = 500000  # characters per month

    # UI制限
    EMBED_FIELD_MAX_LENGTH = 1024
    EMBED_DESCRIPTION_MAX_LENGTH = 4096

    # デフォルト設定
    DEFAULT_SOURCE_LANG = "auto"
    DEFAULT_TARGET_LANG = "ja"

    # エラーメッセージ
    ERROR_MESSAGES = {
        "API_KEY_MISSING": "DeepL APIキーが設定されていません。管理者にお問い合わせください。",
        "TEXT_TOO_LONG": f"テキストが長すぎます。{MAX_TEXT_LENGTH}文字以内で入力してください。",
        "TEXT_TOO_SHORT": "翻訳するテキストを入力してください。",
        "INVALID_LANGUAGE": "指定された言語コードは無効です。",
        "RATE_LIMIT_EXCEEDED": "API使用量制限に達しました。しばらく時間をおいて再度お試しください。",
        "NETWORK_ERROR": "ネットワークエラーが発生しました。時間をおいて再度お試しください。",
        "API_ERROR": "翻訳APIでエラーが発生しました。"
    }