from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dependency_container import Dependency
from fastapi import FastAPI
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine

from src.core.base import import_all_database_models
from src.core.di import include_nats_dependency
from src.core.settings import Settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    import_all_database_models()

    settings = Dependency.get(Settings)
    nats_client = await include_nats_dependency(settings)

    logger.info("Application startup completed")

    try:
        yield

    finally:
        logger.info("Application shutdown started")

        if nats_client is not None:
            await nats_client.drain()

        await Dependency.get(AsyncEngine).dispose()
        logger.info("Application shutdown completed")
