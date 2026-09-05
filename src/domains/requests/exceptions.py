class InvalidStateChangeException(Exception):
    """Raised when an entity cannot transition from its current state."""

    def __init__(self) -> None:
        super().__init__("The requested state change is not allowed.")
