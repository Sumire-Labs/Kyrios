from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging


class Command(ABC):
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.executed_at: Optional[datetime] = None
        self.executed_by: Optional[int] = None
        self.result: Optional[Any] = None

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        pass

    async def undo(self) -> bool:
        return False

    def can_undo(self) -> bool:
        return False


class CommandInvoker:
    def __init__(self):
        self.history: List[Command] = []
        self.logger = logging.getLogger(__name__)

    async def execute_command(self, command: Command, *args, **kwargs) -> Any:
        try:
            command.executed_at = datetime.now()
            result = await command.execute(*args, **kwargs)
            command.result = result
            self.history.append(command)
            self.logger.info(f"Command {command.name} executed successfully")
            return result
        except Exception as e:
            self.logger.error(f"Command {command.name} failed: {e}")
            raise

    async def undo_last_command(self) -> bool:
        if not self.history:
            return False

        last_command = self.history[-1]
        if not last_command.can_undo():
            return False

        try:
            success = await last_command.undo()
            if success:
                self.history.pop()
                self.logger.info(f"Command {last_command.name} undone successfully")
            return success
        except Exception as e:
            self.logger.error(f"Failed to undo command {last_command.name}: {e}")
            return False

    def get_command_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        recent_commands = self.history[-limit:]
        return [
            {
                "name": cmd.name,
                "description": cmd.description,
                "executed_at": cmd.executed_at,
                "executed_by": cmd.executed_by,
                "result": str(cmd.result) if cmd.result else None
            }
            for cmd in recent_commands
        ]