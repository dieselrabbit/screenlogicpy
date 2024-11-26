__all__ = (
    "ScreenLogicException",
    "ScreenLogicWarning",
    "ScreenLogicError",
    "ScreenLogicCommunicationError",
    "ScreenLogicRequestError",
    "ScreenLogicConnectionError",
    "ScreenLogicResponseError",
    "ScreenLogicLoginError",
)


class ScreenLogicException(Exception):
    """Common class for all ScreenLogic exceptions."""

    def __init__(self, *args: object) -> None:
        self.msg = None
        if len(args) > 0:
            self.msg = args[0]
        super().__init__(*args)


class ScreenLogicWarning(ScreenLogicException):
    pass


class ScreenLogicError(ScreenLogicException):
    """General error."""

    pass


class ScreenLogicCommunicationError(ScreenLogicException):
    """Base class for all communication errors."""

    pass


class ScreenLogicRequestError(ScreenLogicCommunicationError):
    """Protocol adapter indicated an unknown or malformed request."""

    pass


class ScreenLogicConnectionError(ScreenLogicCommunicationError):
    """Connection to the protocol adapter was lost."""

    pass


class ScreenLogicResponseError(ScreenLogicCommunicationError):
    """Protocol adapter returned an unexpected response."""

    pass


class ScreenLogicLoginError(ScreenLogicCommunicationError):
    """The login was explicitly rejected."""

    pass
