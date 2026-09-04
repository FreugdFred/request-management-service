from typing import Literal
from uuid import UUID

from dependency_container import Dependency
from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from src.domains.requests.enums import RequestStatus
from src.domains.requests.models import DbRequest
from src.domains.requests.query_models import PaginatedQueryModel, RequestQueryModel


class QueryRequestsRepository:
    async def get(self, id: UUID) -> RequestQueryModel | None:
        async with Dependency.get(AsyncSession) as session:
            db_request = await session.get(DbRequest, id)

            if db_request is None:
                return None

            return RequestQueryModel.model_validate(db_request)

    async def get_created_by(
        self,
        created_by_id: str,
        *,
        status: RequestStatus | None = None,
        type: str | None = None,
        reviewed_by_id: str | None = None,
        sort_direction: Literal["asc", "desc"] = "desc",
        limit: int,
        offset: int,
    ) -> PaginatedQueryModel[RequestQueryModel]:
        filters = [DbRequest.created_by_id == created_by_id]
        if status is not None:
            filters.append(DbRequest.status == status)
        if type is not None:
            filters.append(DbRequest.type == type)
        if reviewed_by_id is not None:
            filters.append(DbRequest.reviewed_by_id == reviewed_by_id)

        return await self._get_many(
            filters=filters,
            sort_direction=sort_direction,
            limit=limit,
            offset=offset,
        )

    async def get_reviewed_by(
        self,
        reviewed_by_id: str,
        *,
        status: RequestStatus | None = None,
        type: str | None = None,
        created_by_id: str | None = None,
        sort_direction: Literal["asc", "desc"] = "desc",
        limit: int,
        offset: int,
    ) -> PaginatedQueryModel[RequestQueryModel]:
        filters = [DbRequest.reviewed_by_id == reviewed_by_id]
        if status is not None:
            filters.append(DbRequest.status == status)
        if type is not None:
            filters.append(DbRequest.type == type)
        if created_by_id is not None:
            filters.append(DbRequest.created_by_id == created_by_id)

        return await self._get_many(
            filters=filters,
            sort_direction=sort_direction,
            limit=limit,
            offset=offset,
        )

    async def get_types(
        self,
        *,
        created_by_id: str | None = None,
        reviewed_by_id: str | None = None,
        status: RequestStatus | None = None,
    ) -> list[str]:
        filters = []
        if created_by_id is not None:
            filters.append(DbRequest.created_by_id == created_by_id)
        if reviewed_by_id is not None:
            filters.append(DbRequest.reviewed_by_id == reviewed_by_id)
        if status is not None:
            filters.append(DbRequest.status == status)

        query = (
            select(DbRequest.type)
            .where(*filters)
            .distinct()
            .order_by(DbRequest.type.asc())
        )

        async with Dependency.get(AsyncSession) as session:
            result = await session.scalars(query)
            return list(result.all())

    async def _get_many(
        self,
        *,
        filters: list[ColumnElement[bool]],
        sort_direction: Literal["asc", "desc"],
        limit: int,
        offset: int,
    ) -> PaginatedQueryModel[RequestQueryModel]:
        order = asc if sort_direction == "asc" else desc
        query = (
            select(DbRequest)
            .where(*filters)
            .order_by(order(DbRequest.created_at), order(DbRequest.id))
            .limit(limit)
            .offset(offset)
        )
        count_query = select(func.count(DbRequest.id)).where(*filters)

        async with Dependency.get(AsyncSession) as session:
            total = await session.scalar(count_query)
            result = await session.scalars(query)
            items = [
                RequestQueryModel.model_validate(request)
                for request in result.all()
            ]

        return PaginatedQueryModel[RequestQueryModel](
            items=items,
            total=total or 0,
            limit=limit,
            offset=offset,
        )
