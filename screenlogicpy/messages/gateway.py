from .base import *

__all__ = (
    "GatewayVersionRequest",
    "GatewayVersionResponse",
)


class GatewayVersionRequest(BaseRequest):
    _code = MessageCode.GET_VERSION


class GatewayVersionResponse(BaseResponse):
    _code = MessageCode.GET_VERSION + 1

    def decode(self) -> str:
        return self.payload.next_string()
