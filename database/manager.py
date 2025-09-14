from typing import Optional, List, Any
from pathlib import Path
import logging
from sqlmodel import SQLModel, create_engine, Session, select
from sqlalchemy import desc
from datetime import datetime, timedelta

from .models import (Ticket, Log, GuildSettings, TicketMessage, TicketStatus, LogType,
                      AvatarHistory, UserAvatarStats, AvatarHistoryType)


class DatabaseManager:
    def __init__(self, database_path: str):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(f"sqlite:///{self.database_path}")
        self.logger = logging.getLogger(__name__)
        self._create_tables()

    def _create_tables(self) -> None:
        SQLModel.metadata.create_all(self.engine)
        self.logger.info("Database tables created successfully")

    def get_session(self) -> Session:
        return Session(self.engine)

    # Ticket methods
    async def create_ticket(self, guild_id: int, channel_id: int, user_id: int,
                           title: str, description: Optional[str] = None) -> Ticket:
        with self.get_session() as session:
            ticket = Ticket(
                guild_id=guild_id,
                channel_id=channel_id,
                user_id=user_id,
                title=title,
                description=description
            )
            session.add(ticket)
            session.commit()
            session.refresh(ticket)
            self.logger.info(f"Created ticket {ticket.id} for user {user_id} in guild {guild_id}")
            return ticket

    async def get_ticket(self, ticket_id: int) -> Optional[Ticket]:
        with self.get_session() as session:
            return session.get(Ticket, ticket_id)

    async def get_tickets_by_user(self, guild_id: int, user_id: int) -> List[Ticket]:
        with self.get_session() as session:
            statement = select(Ticket).where(
                Ticket.guild_id == guild_id,
                Ticket.user_id == user_id,
                Ticket.status != TicketStatus.CLOSED
            )
            return list(session.exec(statement))

    async def get_open_tickets(self, guild_id: int) -> List[Ticket]:
        with self.get_session() as session:
            statement = select(Ticket).where(
                Ticket.guild_id == guild_id,
                Ticket.status == TicketStatus.OPEN
            )
            return list(session.exec(statement))

    async def update_ticket(self, ticket_id: int, **kwargs) -> Optional[Ticket]:
        with self.get_session() as session:
            ticket = session.get(Ticket, ticket_id)
            if not ticket:
                return None

            for key, value in kwargs.items():
                if hasattr(ticket, key):
                    setattr(ticket, key, value)

            session.add(ticket)
            session.commit()
            session.refresh(ticket)
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
        with self.get_session() as session:
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
            session.commit()
            session.refresh(log)
            self.logger.debug(f"Created log entry: {action} in guild {guild_id}")
            return log

    async def get_logs(self, guild_id: int, log_type: Optional[LogType] = None,
                      limit: int = 100) -> List[Log]:
        with self.get_session() as session:
            statement = select(Log).where(Log.guild_id == guild_id)

            if log_type:
                statement = statement.where(Log.log_type == log_type)

            statement = statement.order_by(desc(Log.timestamp)).limit(limit)
            return list(session.exec(statement))

    # Guild Settings methods
    async def get_guild_settings(self, guild_id: int) -> Optional[GuildSettings]:
        with self.get_session() as session:
            statement = select(GuildSettings).where(GuildSettings.guild_id == guild_id)
            return session.exec(statement).first()

    async def create_or_update_guild_settings(self, guild_id: int, **kwargs) -> GuildSettings:
        with self.get_session() as session:
            statement = select(GuildSettings).where(GuildSettings.guild_id == guild_id)
            settings = session.exec(statement).first()

            if settings:
                for key, value in kwargs.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)
                settings.updated_at = datetime.now()
            else:
                settings = GuildSettings(guild_id=guild_id, **kwargs)

            session.add(settings)
            session.commit()
            session.refresh(settings)
            self.logger.info(f"Updated settings for guild {guild_id}")
            return settings

    # Ticket Message methods
    async def add_ticket_message(self, ticket_id: int, user_id: int, message_id: int,
                               content: str, is_system_message: bool = False) -> TicketMessage:
        with self.get_session() as session:
            message = TicketMessage(
                ticket_id=ticket_id,
                user_id=user_id,
                message_id=message_id,
                content=content,
                is_system_message=is_system_message
            )
            session.add(message)
            session.commit()
            session.refresh(message)
            return message

    async def get_ticket_messages(self, ticket_id: int) -> List[TicketMessage]:
        with self.get_session() as session:
            statement = select(TicketMessage).where(
                TicketMessage.ticket_id == ticket_id
            ).order_by(TicketMessage.timestamp)
            return list(session.exec(statement))

    # Avatar History methods
    async def record_avatar_change(self, user_id: int, history_type: AvatarHistoryType,
                                 old_avatar_url: Optional[str] = None,
                                 new_avatar_url: Optional[str] = None,
                                 guild_id: Optional[int] = None,
                                 dominant_color: Optional[str] = None,
                                 image_format: Optional[str] = None,
                                 image_size: Optional[int] = None) -> AvatarHistory:
        with self.get_session() as session:
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
            session.commit()
            session.refresh(history)

            # Update user stats
            await self._update_user_avatar_stats(user_id, history_type, session)
            self.logger.info(f"Recorded avatar change for user {user_id}")
            return history

    async def get_avatar_history(self, user_id: int, limit: int = 10) -> List[AvatarHistory]:
        with self.get_session() as session:
            statement = select(AvatarHistory).where(
                AvatarHistory.user_id == user_id
            ).order_by(desc(AvatarHistory.timestamp)).limit(limit)
            return list(session.exec(statement))

    async def get_user_avatar_stats(self, user_id: int) -> Optional[UserAvatarStats]:
        with self.get_session() as session:
            statement = select(UserAvatarStats).where(UserAvatarStats.user_id == user_id)
            return session.exec(statement).first()

    async def _update_user_avatar_stats(self, user_id: int, history_type: AvatarHistoryType, session: Session) -> None:
        statement = select(UserAvatarStats).where(UserAvatarStats.user_id == user_id)
        stats = session.exec(statement).first()

        if not stats:
            stats = UserAvatarStats(user_id=user_id)
            session.add(stats)

        if history_type in [AvatarHistoryType.AVATAR_CHANGE, AvatarHistoryType.SERVER_AVATAR_CHANGE]:
            stats.total_avatar_changes += 1
            stats.last_avatar_change = datetime.now()
        elif history_type == AvatarHistoryType.BANNER_CHANGE:
            stats.total_banner_changes += 1
            stats.last_banner_change = datetime.now()

        session.commit()

    # Utility methods
    async def cleanup_old_logs(self, days: int = 30) -> int:
        cutoff_date = datetime.now() - timedelta(days=days)
        with self.get_session() as session:
            statement = select(Log).where(Log.timestamp < cutoff_date)
            old_logs = list(session.exec(statement))

            for log in old_logs:
                session.delete(log)

            session.commit()
            self.logger.info(f"Cleaned up {len(old_logs)} old log entries")
            return len(old_logs)