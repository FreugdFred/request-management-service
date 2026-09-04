from loguru import logger

from src.core.handler_base import HandlerBase
from src.domains.requests.command_repository import CommandRequestsRepository
from src.domains.requests.commands.delete_request.command import DeleteRequestCommand


class DeleteRequestCommandHandler(HandlerBase):
    def __init__(self, requests_repository: CommandRequestsRepository) -> None:
        self._requests_repository = requests_repository

    async def handle(self, command: DeleteRequestCommand) -> None:
        request = await self._requests_repository.get(command.id)
        if request is None:
            logger.debug(
                "Delete request command skipped; request not found request_id={}",
                command.id,
            )
            return

        request.delete()
        await self._requests_repository.remove(request.id)
        logger.info("Delete request command completed request_id={}", command.id)
        await self.publish_events(request.pull_events())
