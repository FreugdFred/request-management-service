from uuid import UUID

from dependency_container import Dependency
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.requests.entity import RequestEntity
from src.domains.requests.mapper import RequestMapper
from src.domains.requests.models import DbRequest


class CommandRequestsRepository:
    async def get(self, id: UUID) -> RequestEntity | None:
        async with Dependency.get(AsyncSession) as session:
            db_request = await session.get(DbRequest, id)
            return RequestMapper.to_domain(db_request) if db_request else None

    async def save(self, request: RequestEntity) -> UUID:
        async with Dependency.get(AsyncSession) as session:
            db_request = await session.get(DbRequest, request.id)

            if db_request is None:
                db_request = RequestMapper.from_domain(request)
                session.add(db_request)
            else:
                RequestMapper.update_model_from_domain(db_request, request)

            await session.commit()
            return db_request.id

    async def remove(self, id: UUID) -> None:
        async with Dependency.get(AsyncSession) as session:
            db_request = await session.get(DbRequest, id)
            if db_request is None:
                return

            await session.delete(db_request)
            await session.commit()
