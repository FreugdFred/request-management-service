from collections.abc import Iterable

from dependency_container import Dependency
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.events import DomainEvent
from src.core.settings import Settings
from src.messaging.commands.repository import CommandMessagingRepository


class HandlerBase:
    @staticmethod
    async def save_events(
        session: AsyncSession,
        events: Iterable[DomainEvent],
    ) -> None:
        if Dependency.get(Settings).NATS_URL is None:
            return

        repository = Dependency.get(CommandMessagingRepository)
        await repository.save_many(session, events)
