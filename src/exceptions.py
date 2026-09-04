class NotFoundException(Exception):
    """Exception raised when a requested model instance is not found."""

    def __init__(
        self,
        model: type,
        identifier: str | None = None,
        *,
        detail: str | None = None,
    ):
        """
        Args:
            model: The model class that was not found.
            identifier: Optional identifier for the specific instance (e.g., ID).
            detail: Optional context-specific error message.
        """
        if detail is not None:
            super().__init__(detail)
            return

        model_name = model.__name__ if hasattr(model, "__name__") else str(model)
        if identifier:
            message = f"{model_name} with identifier '{identifier}' not found."
        else:
            message = f"{model_name} not found."
        super().__init__(message)


class ValidationException(Exception):
    """Raised when a domain command does not contain valid input."""
