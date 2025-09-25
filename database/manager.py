from typing import Optional, List, Any
from pathlib import Path
import logging
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import desc
from datetime import datetime, timedelta

from .models import (Ticket, Log, GuildSettings, TicketMessage, TicketStatus, LogType,
                      AvatarHistory, UserAvatarStats, AvatarHistoryType,
                      Track, Queue, MusicSession, MusicSource, LoopMode)


class DatabaseManager:
    def __init__(self, database_path: str):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        # aiosqliteを使用したasync engine
        self.engine = create_async_engine(f"sqlite+aiosqlite:///{self.database_path}")
        self.async_session = async_sessionmaker(self.engine, expire_on_commit=False)
        self.logger = logging.getLogger(__name__)

    async def _create_tables(self) -> None:
        """非同期でテーブル作成"""
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        self.logger.info("Database tables created successfully")

    async def initialize(self) -> None:
        """データベース初期化（非同期）"""
        await self._create_tables()

    def get_session(self) -> AsyncSession:
        """下位互換性のため残す（非推奨）"""
        self.logger.warning("get_session() is deprecated, use async context managers")
        return self.async_session()

    @asynccontextmanager
    async def transaction(self):
        """非同期トランザクション管理用のコンテキストマネージャー"""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
                self.logger.debug("Transaction committed successfully")
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Transaction rolled back due to error: {e}")
                raise

    async def execute_in_transaction(self, operations):
        """複数の操作を一つのトランザクションで実行"""
        async with self.transaction() as session:
            results = []
            for operation in operations:
                if callable(operation):
                    # 非同期操作をサポート
                    result = await operation(session) if hasattr(operation, '__call__') else operation(session)
                    results.append(result)
                else:
                    raise ValueError("Operation must be callable")
            return results

    # Ticket methods
    async def create_ticket(self, guild_id: int, channel_id: int, user_id: int,
                           title: str, description: Optional[str] = None) -> Ticket:
        async with self.async_session() as session:
            ticket = Ticket(
                guild_id=guild_id,
                channel_id=channel_id,
                user_id=user_id,
                title=title,
                description=description
            )
            session.add(ticket)
            await session.commit()
            await session.refresh(ticket)
            self.logger.info(f"Created ticket {ticket.id} for user {user_id} in guild {guild_id}")
            return ticket

    async def get_ticket(self, ticket_id: int) -> Optional[Ticket]:
        async with self.async_session() as session:
            return await session.get(Ticket, ticket_id)

    async def get_tickets_by_user(self, guild_id: int, user_id: int) -> List[Ticket]:
        async with self.async_session() as session:
            statement = select(Ticket).where(
                Ticket.guild_id == guild_id,
                Ticket.user_id == user_id,
                Ticket.status != TicketStatus.CLOSED
            )
            result = await session.execute(statement)
            return list(result.scalars().all())

    async def get_open_tickets(self, guild_id: int) -> List[Ticket]:
        async with self.async_session() as session:
            statement = select(Ticket).where(
                Ticket.guild_id == guild_id,
                Ticket.status == TicketStatus.OPEN
            )
            result = await session.execute(statement)
            return list(result.scalars().all())

    async def get_all_open_tickets(self) -> List[Ticket]:
        """すべてのギルドのオープンチケットを取得（永続View復元用）"""
        async with self.async_session() as session:
            statement = select(Ticket).where(Ticket.status == TicketStatus.OPEN)
            result = await session.execute(statement)
            return list(result.scalars().all())

    async def update_ticket(self, ticket_id: int, **kwargs) -> Optional[Ticket]:
        async with self.async_session() as session:
            ticket = await session.get(Ticket, ticket_id)
            if not ticket:
                return None

            for key, value in kwargs.items():
                if hasattr(ticket, key):
                    setattr(ticket, key, value)

            session.add(ticket)
            await session.commit()
            await session.refresh(ticket)
            self.logger.info(f"Updated ticket {ticket_id}")
            return ticket

    async def close_ticket(self, ticket_id: int) -> Optional[Ticket]:
        return await self.update_ticket(
            ticket_id,
            status=TicketStatus.CLOSED,
            closed_at=datetime.now()
        )

    # Log methods
    async def create_log(self, guild_id: int, log_type: LogType, action: str,
                        user_id: Optional[int] = None, moderator_id: Optional[int] = None,
                        channel_id: Optional[int] = None, details: Optional[str] = None) -> Log:
        async with self.async_session() as session:
            log = Log(
                guild_id=guild_id,
                log_type=log_type,
                user_id=user_id,
                moderator_id=moderator_id,
                channel_id=channel_id,
                action=action,
                details=details
            )
            session.add(log)
            await session.commit()
            await session.refresh(log)
            self.logger.debug(f"Created log entry: {action} in guild {guild_id}")
            return log

    async def get_logs(self, guild_id: int, log_type: Optional[LogType] = None,
                      limit: int = 100) -> List[Log]:
        async with self.async_session() as session:
            statement = select(Log).where(Log.guild_id == guild_id)

            if log_type:
                statement = statement.where(Log.log_type == log_type)

            statement = statement.order_by(Log.timestamp.desc()).limit(limit)
            result = await session.execute(statement)
            return list(result.scalars().all())

    # Guild Settings methods
    async def get_guild_settings(self, guild_id: int) -> Optional[GuildSettings]:
        async with self.async_session() as session:
            statement = select(GuildSettings).where(GuildSettings.guild_id == guild_id)
            result = await session.execute(statement)
            return result.scalars().first()

    async def create_or_update_guild_settings(self, guild_id: int, **kwargs) -> GuildSettings:
        async with self.async_session() as session:
            statement = select(GuildSettings).where(GuildSettings.guild_id == guild_id)
            result = await session.execute(statement)
            settings = result.scalars().first()

            if settings:
                for key, value in kwargs.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)
                settings.updated_at = datetime.now()
            else:
                settings = GuildSettings(guild_id=guild_id, **kwargs)

            session.add(settings)
            await session.commit()
            await session.refresh(settings)
            self.logger.info(f"Updated settings for guild {guild_id}")
            return settings

    # Ticket Message methods
    async def add_ticket_message(self, ticket_id: int, user_id: int, message_id: int,
                               content: str, is_system_message: bool = False) -> TicketMessage:
        async with self.async_session() as session:
            message = TicketMessage(
                ticket_id=ticket_id,
                user_id=user_id,
                message_id=message_id,
                content=content,
                is_system_message=is_system_message
            )
            session.add(message)
            await session.commit()
            await session.refresh(message)
            return message

    async def get_ticket_messages(self, ticket_id: int) -> List[TicketMessage]:
        async with self.async_session() as session:
            statement = select(TicketMessage).where(
                TicketMessage.ticket_id == ticket_id
            ).order_by(TicketMessage.timestamp.desc())
            result = await session.execute(statement)
            return list(result.scalars().all())

    # Avatar History methods
    async def record_avatar_change(self, user_id: int, history_type: AvatarHistoryType,
                                 old_avatar_url: Optional[str] = None,
                                 new_avatar_url: Optional[str] = None,
                                 guild_id: Optional[int] = None,
                                 dominant_color: Optional[str] = None,
                                 image_format: Optional[str] = None,
                                 image_size: Optional[int] = None) -> AvatarHistory:
        async with self.transaction() as session:
            # 1. アバター履歴を作成
            history = AvatarHistory(
                user_id=user_id,
                guild_id=guild_id,
                history_type=history_type,
                old_avatar_url=old_avatar_url,
                new_avatar_url=new_avatar_url,
                dominant_color=dominant_color,
                image_format=image_format,
                image_size=image_size
            )
            session.add(history)
            await session.flush()  # IDを取得するため（コミットはしない）
            await session.refresh(history)

            # 2. ユーザー統計を同じトランザクション内で更新
            await self._update_user_avatar_stats_sync(user_id, history_type, session)

            # トランザクション終了時に自動コミット（context manager）
            self.logger.info(f"Recorded avatar change for user {user_id}")
            return history

    async def get_avatar_history(self, user_id: int, limit: int = 10) -> List[AvatarHistory]:
        async with self.async_session() as session:
            statement = select(AvatarHistory).where(
                AvatarHistory.user_id == user_id
            ).order_by(AvatarHistory.timestamp.desc()).limit(limit)
            result = await session.execute(statement)
            return list(result.scalars().all())

    async def get_user_avatar_stats(self, user_id: int) -> Optional[UserAvatarStats]:
        async with self.async_session() as session:
            statement = select(UserAvatarStats).where(UserAvatarStats.user_id == user_id)
            result = await session.execute(statement)
            return result.scalars().first()

    async def _update_user_avatar_stats_sync(self, user_id: int, history_type: AvatarHistoryType, session: AsyncSession) -> None:
        """非同期版のユーザー統計更新（トランザクション内で使用）"""
        statement = select(UserAvatarStats).where(UserAvatarStats.user_id == user_id)
        result = await session.execute(statement)
        stats = result.scalars().first()

        if not stats:
            stats = UserAvatarStats(user_id=user_id)
            session.add(stats)

        if history_type in [AvatarHistoryType.AVATAR_CHANGE, AvatarHistoryType.SERVER_AVATAR_CHANGE]:
            stats.total_avatar_changes += 1
            stats.last_avatar_change = datetime.now()
        elif history_type == AvatarHistoryType.BANNER_CHANGE:
            stats.total_banner_changes += 1
            stats.last_banner_change = datetime.now()

        # session.commit() は呼ばない（トランザクション管理はコンテキストマネージャーに委譲）

    async def _update_user_avatar_stats(self, user_id: int, history_type: AvatarHistoryType, session: AsyncSession) -> None:
        """後方互換性のための非推奨メソッド"""
        self.logger.warning("_update_user_avatar_stats is deprecated, use _update_user_avatar_stats_sync within transaction")
        await self._update_user_avatar_stats_sync(user_id, history_type, session)

    # Utility methods
    async def cleanup_old_logs(self, days: int = 30) -> int:
        cutoff_date = datetime.now() - timedelta(days=days)
        async with self.async_session() as session:
            statement = select(Log).where(Log.timestamp < cutoff_date)
            result = await session.execute(statement)
            old_logs = list(result.scalars().all())

            for log in old_logs:
                await session.delete(log)

            await session.commit()
            self.logger.info(f"Cleaned up {len(old_logs)} old log entries")
            return len(old_logs)

    # 音楽システム関連メソッド
    async def create_track(
        self,
        guild_id: int,
        title: str,
        artist: str,
        url: str,
        duration: int,
        thumbnail_url: Optional[str],
        requested_by: int,
        source: MusicSource = MusicSource.YOUTUBE
    ) -> Track:
        """楽曲をデータベースに保存"""
        async with self.transaction() as session:
            track = Track(
                guild_id=guild_id,
                title=title,
                artist=artist,
                url=url,
                source=source,
                duration=duration,
                thumbnail_url=thumbnail_url,
                requested_by=requested_by
            )
            session.add(track)
            await session.flush()  # IDを取得するためにflush
            self.logger.info(f"Created track {track.id}: {title} for guild {guild_id}")
            return track

    async def add_to_queue(self, guild_id: int, track_id: int, added_by: int) -> Queue:
        """楽曲をキューに追加"""
        async with self.transaction() as session:
            # 現在のキュー位置を取得
            statement = select(Queue).where(Queue.guild_id == guild_id).order_by(desc(Queue.position))
            result = await session.execute(statement)
            last_queue_item = result.scalars().first()

            next_position = (last_queue_item.position + 1) if last_queue_item else 1

            queue_item = Queue(
                guild_id=guild_id,
                track_id=track_id,
                position=next_position,
                added_by=added_by
            )
            session.add(queue_item)
            await session.flush()
            self.logger.info(f"Added track {track_id} to queue position {next_position} for guild {guild_id}")
            return queue_item

    async def get_next_in_queue(self, guild_id: int) -> Optional[Queue]:
        """キューの次の楽曲を取得"""
        async with self.async_session() as session:
            statement = select(Queue).where(Queue.guild_id == guild_id).order_by(Queue.position).limit(1)
            result = await session.execute(statement)
            return result.scalars().first()

    async def remove_from_queue(self, guild_id: int, queue_id: int) -> bool:
        """キューから楽曲を削除"""
        async with self.transaction() as session:
            statement = select(Queue).where(Queue.guild_id == guild_id, Queue.id == queue_id)
            result = await session.execute(statement)
            queue_item = result.scalars().first()

            if queue_item:
                await session.delete(queue_item)
                self.logger.info(f"Removed queue item {queue_id} from guild {guild_id}")
                return True
            return False

    async def get_guild_queue(self, guild_id: int) -> List[dict]:
        """
        ギルドのキューを取得 (楽曲情報付き)

        パフォーマンス最適化:
        - JOINで一度にQueue+Trackデータを取得してN+1クエリを回避
        - SQLAlchemyの適切なJOIN使用で1回のクエリで完了
        """
        async with self.async_session() as session:
            # N+1クエリ回避: JOINで一度にデータ取得
            statement = select(Queue, Track).join(Track, Queue.track_id == Track.id).where(
                Queue.guild_id == guild_id
            ).order_by(Queue.position)
            result = await session.execute(statement)

            queue_items = []
            # result.all()は既に取得済みデータの反復処理（追加クエリなし）
            for queue_item, track in result.all():
                queue_items.append({
                    'queue_id': queue_item.id,
                    'position': queue_item.position,
                    'title': track.title,
                    'artist': track.artist,
                    'duration': track.duration,
                    'url': track.url,
                    'thumbnail_url': track.thumbnail_url
                })

            return queue_items

    async def clear_queue(self, guild_id: int) -> int:
        """キューをクリア"""
        async with self.transaction() as session:
            statement = select(Queue).where(Queue.guild_id == guild_id)
            result = await session.execute(statement)
            queue_items = list(result.scalars().all())

            for item in queue_items:
                await session.delete(item)

            self.logger.info(f"Cleared {len(queue_items)} items from queue for guild {guild_id}")
            return len(queue_items)

    async def clear_guild_tracks(self, guild_id: int) -> int:
        """ギルドの楽曲履歴をクリア"""
        async with self.transaction() as session:
            statement = select(Track).where(Track.guild_id == guild_id)
            result = await session.execute(statement)
            tracks = list(result.scalars().all())

            for track in tracks:
                await session.delete(track)

            self.logger.info(f"Cleared {len(tracks)} tracks from history for guild {guild_id}")
            return len(tracks)

    async def get_track_by_id(self, track_id: int) -> Optional[Track]:
        """トラックIDで楽曲を取得"""
        async with self.async_session() as session:
            statement = select(Track).where(Track.id == track_id)
            result = await session.execute(statement)
            return result.scalars().first()

    async def create_session(
        self,
        guild_id: int,
        voice_channel_id: int,
        text_channel_id: int
    ) -> MusicSession:
        """音楽セッションを作成または更新（UPSERT）"""
        async with self.transaction() as session:
            # 既存セッションを検索
            statement = select(MusicSession).where(MusicSession.guild_id == guild_id)
            result = await session.execute(statement)
            existing = result.scalars().first()

            if existing:
                # 既存セッションを更新
                existing.voice_channel_id = voice_channel_id
                existing.text_channel_id = text_channel_id
                existing.updated_at = datetime.now()
                session.add(existing)
                self.logger.info(f"Updated existing music session for guild {guild_id}")
                return existing
            else:
                # 新規セッション作成
                music_session = MusicSession(
                    guild_id=guild_id,
                    voice_channel_id=voice_channel_id,
                    text_channel_id=text_channel_id
                )
                session.add(music_session)
                await session.flush()
                self.logger.info(f"Created new music session for guild {guild_id}")
                return music_session

    async def update_session_current_track(self, guild_id: int, track_id: int) -> bool:
        """セッションの現在楽曲を更新"""
        async with self.transaction() as session:
            statement = select(MusicSession).where(MusicSession.guild_id == guild_id)
            result = await session.execute(statement)
            music_session = result.scalars().first()

            if music_session:
                music_session.current_track_id = track_id
                music_session.updated_at = datetime.now()
                return True
            return False

    async def delete_session(self, guild_id: int) -> bool:
        """音楽セッションを削除"""
        async with self.transaction() as session:
            statement = select(MusicSession).where(MusicSession.guild_id == guild_id)
            result = await session.execute(statement)
            music_session = result.scalars().first()

            if music_session:
                await session.delete(music_session)
                self.logger.info(f"Deleted music session for guild {guild_id}")
                return True
            return False

    async def get_session(self, guild_id: int) -> Optional[MusicSession]:
        """音楽セッションを取得"""
        async with self.async_session() as session:
            statement = select(MusicSession).where(MusicSession.guild_id == guild_id)
            result = await session.execute(statement)
            return result.scalars().first()