from src.core.di import include_core_dependencies
from src.domains.requests.di import include_request_dependencies
from src.messaging.di import include_messaging_dependencies

include_core_dependencies()
include_messaging_dependencies()
include_request_dependencies()
