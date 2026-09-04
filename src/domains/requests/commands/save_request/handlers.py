
from src.core.handler_base import HandlerBase
from src.domains.requests.command_repository import CommandRequestsRepository
from src.domains.requests.commands.save_request.command import SaveRequestCommand
from src.domains.requests.entity import RequestEntity
from src.exceptions import ValidationException


class SaveRequestCommandHandler(HandlerBase):
    def __init__(self, requests_repository: CommandRequestsRepository) -> None:
        self._requests_repository = requests_repository

    async def handle(self, command: SaveRequestCommand) -> None:
        existing_request = await self._requests_repository.get(command.id)

        if existing_request is None:
            request = self._create_entity(command)
        else:
            request = self._update_entity(existing_request, command)

        await self._requests_repository.save(request)
        await self.publish_events(request.pull_events())

    @staticmethod
    def _create_entity(command: SaveRequestCommand) -> RequestEntity:
        required_fields = {
            "type": command.type,
            "status": command.status,
            "created_by_id": command.created_by_id,
        }
        missing_fields = [
            name for name, value in required_fields.items() if value is None
        ]
        if missing_fields:
            raise ValidationException(
                f"Cannot create request {command.id}: missing required fields: "
                f"{', '.join(missing_fields)}."
            )

        assert command.type is not None
        assert command.status is not None
        assert command.created_by_id is not None

        return RequestEntity.create(
            id=command.id,
            note=command.note,
            type=command.type,
            status=command.status,
            data=command.data if command.data is not None else {},
            created_by_id=command.created_by_id,
            reviewed_by_id=command.reviewed_by_id,
        )

    @staticmethod
    def _update_entity(
        request: RequestEntity,
        command: SaveRequestCommand,
    ) -> RequestEntity:
        if "note" in command.model_fields_set:
            request.set_note(command.note)

        if command.type is not None:
            request.set_type(command.type)

        if command.status is not None:
            request.set_status(command.status)

        if command.data is not None:
            request.set_data(command.data)

        if command.created_by_id is not None:
            request.set_created_by_id(command.created_by_id)

        if "reviewed_by_id" in command.model_fields_set:
            request.set_reviewed_by_id(command.reviewed_by_id)

        return request


