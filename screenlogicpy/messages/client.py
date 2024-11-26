import struct

from .base import *

__all__ = (
    "AddClientRequest",
    "AddClientResponse",
    "RemoveClientRequest",
    "RemoveClientResponse",
    "PingRequest",
    "PingResponse",
)


class AddClientRequest(BaseRequest):
    _code = MessageCode.ADD_CLIENT

    def __init__(self, client_id: int) -> None:
        self._payload = Payload(struct.pack("<II", 0, client_id))


class AddClientResponse(BaseResponse):
    _code = MessageCode.ADD_CLIENT + 1


class RemoveClientRequest(BaseRequest):
    _code = MessageCode.REMOVE_CLIENT

    def __init__(self, client_id: int) -> None:
        self._payload = Payload(struct.pack("<II", 0, client_id))


class RemoveClientResponse(BaseResponse):
    _code = MessageCode.REMOVE_CLIENT + 1


class PingRequest(BaseRequest):
    _code = MessageCode.PING_REQ


class PingResponse(BaseResponse):
    _code = MessageCode.PING_REQ + 1
