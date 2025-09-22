"""
音楽システム用定数定義

マジックナンバーを排除し、保守性と可読性を向上
"""

from enum import Enum


class MusicConstants:
    """音楽システム関連の定数"""

    # 再生制御
    MAX_RETRY_COUNT = 5
    PLAYBACK_SEARCH_LIMIT = 5
    MUSIC_SCORE_THRESHOLD = 5

    # タイムアウト設定
    PLAYBACK_TIMEOUT_SECONDS = 300  # 5分
    VIEW_TIMEOUT_SECONDS = 300      # UIタイムアウト

    # 楽曲制限
    MIN_DURATION_SECONDS = 30       # 最小再生時間
    MAX_DURATION_SECONDS = 1800     # 最大再生時間(30分)

    # UI制限
    QUERY_DISPLAY_MAX_LENGTH = 50   # 検索クエリ表示の最大文字数
    DESCRIPTION_MAX_LENGTH = 500    # 説明文最大長

    # FFmpeg設定
    FFMPEG_RECONNECT_DELAY_MAX = 5
    FFMPEG_RECONNECT_ATTEMPTS = 1

    # 画像処理最適化
    IMAGE_RESIZE_MAX_SIZE = 32      # 主要色抽出用リサイズ最大サイズ
    IMAGE_COLOR_MAX_COLORS = 128    # 色解析の最大色数

    # EventBus設定
    EVENT_HISTORY_MAX_SIZE = 1000   # イベント履歴最大サイズ

    # アバター解析
    AVATAR_SIZE_OPTIONS = [128, 256, 512, 1024]  # サポートする解像度


class LoopMode(Enum):
    """ループモード"""
    NONE = "none"
    TRACK = "track"
    QUEUE = "queue"


class MusicSource(Enum):
    """音楽ソース"""
    YOUTUBE = "youtube"
    SPOTIFY = "spotify"
    SEARCH = "search"


class PlaybackState(Enum):
    """再生状態"""
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"
    LOADING = "loading"


class RetryStrategy:
    """再試行戦略の定数"""

    # 異なる種類の操作に対する再試行制限
    TRACK_PLAYBACK_MAX_RETRIES = 3
    QUEUE_PROCESSING_MAX_RETRIES = 5
    API_REQUEST_MAX_RETRIES = 3
    CONNECTION_MAX_RETRIES = 2

    # 再試行間隔（秒）
    RETRY_DELAY_SECONDS = 1.0
    BACKOFF_MULTIPLIER = 2.0


# 後方互換性のためのエイリアス
MAX_RETRY_COUNT = MusicConstants.MAX_RETRY_COUNT
MIN_DURATION_SECONDS = MusicConstants.MIN_DURATION_SECONDS
MAX_DURATION_SECONDS = MusicConstants.MAX_DURATION_SECONDS