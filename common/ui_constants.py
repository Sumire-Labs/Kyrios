import discord
from enum import Enum
from typing import Dict, Union
from database.models import LogType


class UIColors:
    """UI関連の色定数"""

    # 基本色
    SUCCESS = discord.Color.green()
    ERROR = discord.Color.red()
    WARNING = discord.Color.orange()
    INFO = discord.Color.blue()
    LOADING = discord.Color.yellow()

    # 特殊色
    TICKET = discord.Color.blue()
    AVATAR = discord.Color.blurple()
    PERFORMANCE = discord.Color.gold()

    # ログタイプ別色
    LOG_COLORS = {
        LogType.MESSAGE_DELETE: discord.Color.red(),
        LogType.MESSAGE_EDIT: discord.Color.orange(),
        LogType.MEMBER_JOIN: discord.Color.green(),
        LogType.MEMBER_LEAVE: discord.Color.yellow(),
        LogType.MEMBER_BAN: discord.Color.red(),
        LogType.MEMBER_UNBAN: discord.Color.green(),
        LogType.MEMBER_KICK: discord.Color.red(),
        LogType.MEMBER_TIMEOUT: discord.Color.orange(),
        LogType.ROLE_ADD: discord.Color.blue(),
        LogType.ROLE_REMOVE: discord.Color.purple(),
        LogType.CHANNEL_CREATE: discord.Color.green(),
        LogType.CHANNEL_DELETE: discord.Color.red(),
        LogType.SYSTEM_EVENT: discord.Color.blue()
    }


class UIEmojis:
    """UI関連の絵文字定数"""

    # 基本アクション
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    LOADING = "🔍"

    # ステータス
    ONLINE = "🟢"
    OFFLINE = "⚫"
    IDLE = "🟡"
    DND = "🔴"

    # アクション
    CREATE = "🆕"
    DELETE = "🗑️"
    EDIT = "✏️"
    VIEW = "👀"
    DOWNLOAD = "💾"

    # ユーザー関連
    USER = "👤"
    MEMBER = "👥"
    AVATAR = "🖼️"
    BANNER = "🎨"

    # システム関連
    PING = "🏓"
    CPU = "⚙️"
    MEMORY = "🧠"
    DATABASE = "💾"
    NETWORK = "📡"

    # チケット関連
    TICKET = "🎫"
    TICKET_OPEN = "🟢"
    TICKET_CLOSED = "🔴"
    TICKET_ASSIGNED = "👤"

    # ログタイプ別絵文字
    LOG_EMOJIS = {
        LogType.MESSAGE_DELETE: "🗑️",
        LogType.MESSAGE_EDIT: "✏️",
        LogType.MEMBER_JOIN: "📥",
        LogType.MEMBER_LEAVE: "📤",
        LogType.MEMBER_BAN: "🔨",
        LogType.MEMBER_UNBAN: "🔓",
        LogType.MEMBER_KICK: "👢",
        LogType.MEMBER_TIMEOUT: "⏰",
        LogType.ROLE_ADD: "🏷️",
        LogType.ROLE_REMOVE: "🚫",
        LogType.CHANNEL_CREATE: "📝",
        LogType.CHANNEL_DELETE: "🗂️",
        LogType.SYSTEM_EVENT: "⚙️"
    }


class PerformanceUtils:
    """パフォーマンス関連のユーティリティ"""

    @staticmethod
    def get_latency_color(latency: int) -> discord.Color:
        """レイテンシに基づいて色を取得"""
        if latency < 50:
            return discord.Color.green()
        elif latency < 100:
            return discord.Color.yellow()
        elif latency < 200:
            return discord.Color.orange()
        else:
            return discord.Color.red()

    @staticmethod
    def get_latency_emoji(latency: int) -> str:
        """レイテンシに基づいて絵文字を取得"""
        if latency < 50:
            return "🟢"
        elif latency < 100:
            return "🟡"
        elif latency < 200:
            return "🟠"
        else:
            return "🔴"

    @staticmethod
    def get_performance_rating(avg_latency: float) -> tuple[str, discord.Color]:
        """平均レイテンシに基づいてパフォーマンス評価を取得"""
        if avg_latency < 75:
            return "🚀 優秀", discord.Color.green()
        elif avg_latency < 150:
            return "✅ 良好", discord.Color.yellow()
        elif avg_latency < 250:
            return "⚠️ 普通", discord.Color.orange()
        else:
            return "🐌 低速", discord.Color.red()


class LogUtils:
    """ログ関連のユーティリティ"""

    @staticmethod
    def get_log_color(log_type: LogType) -> discord.Color:
        """ログタイプに基づいて色を取得"""
        return UIColors.LOG_COLORS.get(log_type, discord.Color.default())

    @staticmethod
    def get_log_emoji(log_type: LogType) -> str:
        """ログタイプに基づいて絵文字を取得"""
        return UIEmojis.LOG_EMOJIS.get(log_type, "ℹ️")


class StatusUtils:
    """ステータス関連のユーティリティ"""

    @staticmethod
    def get_member_status_emoji(status: discord.Status) -> str:
        """メンバーのステータスに基づいて絵文字を取得"""
        status_map = {
            discord.Status.online: UIEmojis.ONLINE,
            discord.Status.offline: UIEmojis.OFFLINE,
            discord.Status.idle: UIEmojis.IDLE,
            discord.Status.dnd: UIEmojis.DND
        }
        return status_map.get(status, UIEmojis.OFFLINE)

    @staticmethod
    def format_boolean_status(value: bool, true_text: str = "有効", false_text: str = "無効") -> str:
        """boolean値を絵文字付きで表示"""
        emoji = UIEmojis.SUCCESS if value else UIEmojis.ERROR
        text = true_text if value else false_text
        return f"{emoji} {text}"


class ButtonStyles:
    """ボタンスタイルの定数"""

    # 基本スタイル
    PRIMARY = discord.ButtonStyle.primary
    SECONDARY = discord.ButtonStyle.secondary
    SUCCESS = discord.ButtonStyle.success
    DANGER = discord.ButtonStyle.danger

    # アクション別スタイル
    CREATE = SUCCESS
    DELETE = DANGER
    EDIT = SECONDARY
    VIEW = PRIMARY
    CLOSE = DANGER
    ASSIGN = SECONDARY