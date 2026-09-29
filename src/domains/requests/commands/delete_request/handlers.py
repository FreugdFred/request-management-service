from loguru import logger

from src.core.handler_base import HandlerBase
from src.core.unit_of_work import UnitOfWork
from src.domains.requests.command_repository import CommandRequestsRepository
from src.domains.requests.commands.delete_request.command import DeleteRequestCommand


class DeleteRequestCommandHandler(HandlerBase):
    def __init__(self, requests_repository: CommandRequestsRepository) -> None:
        self._requests_repository = requests_repository

    async def handle(self, command: DeleteRequestCommand) -> None:
        async with UnitOfWork() as session:
            request = await self._requests_repository.get(session, command.id)
            if request is None:
                logger.debug(
                    "Delete request command skipped; request not found request_id={}",
                    command.id,
                )
                return

            request.delete()
            await self._requests_repository.remove(session, request.id)
            await self.save_events(session, request.pull_events())

        logger.info("Delete request command completed request_id={}", command.id)
