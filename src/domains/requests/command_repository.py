from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.requests.entity import RequestEntity
from src.domains.requests.mapper import RequestMapper
from src.domains.requests.models import DbRequest


class CommandRequestsRepository:
    async def get(self, session: AsyncSession, id: UUID) -> RequestEntity | None:
        db_request = await session.get(DbRequest, id)
        return RequestMapper.to_domain(db_request) if db_request is not None else None

    async def save(self, session: AsyncSession, request: RequestEntity) -> UUID:
        db_request = await session.get(DbRequest, request.id)

        if db_request is None:
            db_request = RequestMapper.from_domain(request)
            session.add(db_request)
        else:
            RequestMapper.update_model_from_domain(db_request, request)

        return db_request.id

    async def remove(self, session: AsyncSession, id: UUID) -> None:
        db_request = await session.get(DbRequest, id)
        if db_request is None:
            return

        await session.delete(db_request)
