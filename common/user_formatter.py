import discord
from datetime import datetime
from typing import Optional, Union, List


class UserFormatter:
    """ユーザー情報フォーマット用のユーティリティクラス"""

    @staticmethod
    def format_user_mention_and_tag(user: Union[discord.User, discord.Member]) -> str:
        """ユーザーのメンションとタグを統一フォーマットで表示"""
        return f"{user.mention}\n`{user}`"

    @staticmethod
    def format_user_id(user: Union[discord.User, discord.Member]) -> str:
        """ユーザーIDを統一フォーマットで表示"""
        return f"`{user.id}`"

    @staticmethod
    def format_user_basic_info(user: Union[discord.User, discord.Member]) -> str:
        """基本的なユーザー情報をフォーマット"""
        info = f"**名前:** {user.display_name}\n"
        info += f"**ID:** `{user.id}`\n"
        info += f"**アカウント作成:** <t:{int(user.created_at.timestamp())}:R>"
        return info

    @staticmethod
    def format_member_join_info(member: discord.Member) -> str:
        """メンバーの参加情報をフォーマット"""
        info = UserFormatter.format_user_basic_info(member)
        if member.joined_at:
            info += f"\n**サーバー参加:** <t:{int(member.joined_at.timestamp())}:R>"
        return info

    @staticmethod
    def format_user_with_avatar(user: Union[discord.User, discord.Member]) -> str:
        """アバター付きでユーザー情報をフォーマット"""
        info = f"**{user.display_name}**\n"
        info += f"ID: `{user.id}`\n"
        info += f"作成日: <t:{int(user.created_at.timestamp())}:F>"
        return info

    @staticmethod
    def format_channel_info(channel: discord.abc.GuildChannel) -> str:
        """チャンネル情報をフォーマット"""
        if hasattr(channel, 'mention'):
            return channel.mention
        elif hasattr(channel, 'name'):
            return f"#{channel.name}"
        else:
            return f"チャンネルID: {channel.id}"

    @staticmethod
    def format_timestamp(dt: datetime, style: str = "F") -> str:
        """日時をDiscordタイムスタンプ形式でフォーマット

        Args:
            dt: フォーマットする日時
            style: タイムスタンプスタイル
                - "t": 短時間 (16:20)
                - "T": 長時間 (16:20:30)
                - "d": 短日付 (20/04/2021)
                - "D": 長日付 (20 April 2021)
                - "f": 短日時 (20 April 2021 16:20)
                - "F": 長日時 (Tuesday, 20 April 2021 16:20)
                - "R": 相対時間 (2 months ago)
        """
        return f"<t:{int(dt.timestamp())}:{style}>"

    @staticmethod
    def format_role_list(roles: List[discord.Role], max_roles: int = 10) -> str:
        """ロール一覧をフォーマット"""
        if not roles:
            return "なし"

        # @everyone ロールを除外
        filtered_roles = [role for role in roles if role.name != "@everyone"]

        if len(filtered_roles) > max_roles:
            displayed_roles = filtered_roles[:max_roles]
            remaining_count = len(filtered_roles) - max_roles
            role_mentions = [role.mention for role in displayed_roles]
            return " ".join(role_mentions) + f" (+{remaining_count}個)"
        else:
            role_mentions = [role.mention for role in filtered_roles]
            return " ".join(role_mentions) if role_mentions else "なし"

    @staticmethod
    def format_account_age_warning(user: Union[discord.User, discord.Member], threshold_days: int = 7) -> Optional[str]:
        """アカウント年数に基づく警告メッセージを生成"""
        account_age = datetime.now() - user.created_at
        if account_age.days < threshold_days:
            return f"⚠️ 新しいアカウントです ({account_age.days}日前に作成)"
        return None

    @staticmethod
    def format_user_id_or_mention(user_input: str) -> Optional[int]:
        """ユーザーIDまたはメンションからユーザーIDを抽出"""
        user_input = user_input.strip()

        # メンション形式の場合
        if user_input.startswith('<@') and user_input.endswith('>'):
            # <@!123456789> または <@123456789> の形式
            user_id_str = user_input[2:-1].replace('!', '')
            try:
                return int(user_id_str)
            except ValueError:
                return None

        # 直接IDの場合
        try:
            return int(user_input)
        except ValueError:
            return None

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """ファイルサイズを人間が読みやすい形式でフォーマット"""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024.0 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1

        return f"{size_bytes:.1f} {size_names[i]}"

    @staticmethod
    def format_duration(seconds: int) -> str:
        """秒数を時間形式でフォーマット"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            if remaining_seconds > 0:
                return f"{minutes}分{remaining_seconds}秒"
            return f"{minutes}分"
        else:
            hours = seconds // 3600
            remaining_minutes = (seconds % 3600) // 60
            if remaining_minutes > 0:
                return f"{hours}時間{remaining_minutes}分"
            return f"{hours}時間"

    @staticmethod
    def format_percentage(value: float, decimal_places: int = 1) -> str:
        """パーセンテージをフォーマット"""
        return f"{value:.{decimal_places}f}%"

    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """テキストを指定長に切り詰め"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix

    @staticmethod
    def format_code_block(content: str, language: str = "") -> str:
        """コードブロック形式でフォーマット"""
        return f"```{language}\n{content}\n```"

    @staticmethod
    def format_inline_code(content: str) -> str:
        """インラインコード形式でフォーマット"""
        return f"`{content}`"