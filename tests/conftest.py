import asyncio
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from zoneinfo import ZoneInfo

import pytest
from dependency_container import Dependency
from pydantic import NatsDsn
from sqlalchemy.ext.asyncio import AsyncEngine
from time_provider import AbstractTimeProvider, FakeTimeProvider

from src.core.base import Base
from src.core.di import include_core_dependencies
from src.core.settings import Settings
from src.domains.requests.command_repository import CommandRequestsRepository
from src.domains.requests.di import include_request_dependencies
from src.messaging.di import include_messaging_dependencies

DEFAULT_NOW = datetime(2026, 9, 2, 12, tzinfo=UTC)


async def create_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


@pytest.fixture(autouse=True)
def configure_dependencies(tmp_path: Path) -> Iterator[None]:
    database_path = (tmp_path / "test.db").resolve()
    sqlite_path = database_path.as_posix()
    settings = Settings.model_validate(
        {"DATABASE_URL": f"sqlite+aiosqlite:///{sqlite_path}", "NATS_URL": None}
    )

    Dependency.clear()
    include_core_dependencies(settings)
    include_messaging_dependencies()
    include_request_dependencies()
    Dependency.overwrite(
        AbstractTimeProvider,
        FakeTimeProvider(
            local_timezone=ZoneInfo("Europe/Amsterdam"),
            time=DEFAULT_NOW,
            freeze=True,
        ),
    )
    engine = Dependency.get(AsyncEngine)
    asyncio.run(create_schema(engine))

    yield

    Dependency.clear()
    asyncio.run(engine.dispose())


@pytest.fixture
def command_requests_repository() -> CommandRequestsRepository:
    return Dependency.get(CommandRequestsRepository)


@pytest.fixture
def enable_messaging() -> None:
    Dependency.get(Settings).NATS_URL = NatsDsn("nats://localhost:4222")


@pytest.fixture
def time_provider() -> FakeTimeProvider:
    return cast(FakeTimeProvider, Dependency.get(AbstractTimeProvider))
