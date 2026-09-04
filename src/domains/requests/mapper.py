from src.core.mapper_base import MapperBase
from src.domains.requests.entity import RequestEntity
from src.domains.requests.models import DbRequest


class RequestMapper(MapperBase[RequestEntity, DbRequest]):
    domain_model = RequestEntity
    db_model = DbRequest
