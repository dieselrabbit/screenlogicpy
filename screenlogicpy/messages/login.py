import struct

from .base import *

CONNECT_PING = b"CONNECTSERVERHOST\r\n\r\n"  # as bytes, not string

__all__ = (
    "ChallengeRequest",
    "ChallengeResponse",
    "LocalLoginRequest",
    "LocalLoginResponse",
)


class ChallengeRequest(BaseRequest):
    _code = MessageCode.CHALLENGE


class ChallengeResponse(BaseResponse):
    _code = MessageCode.CHALLENGE + 1

    def decode(self) -> str:
        return self._payload.next_string()


class LocalLoginRequest(BaseRequest):
    _code = MessageCode.LOCAL_LOGIN

    def __init__(self, id: int = 0) -> None:
        super().__init__(id)
        schema = 348
        connectionType = 0
        clientVersion = encode_string("Android")
        pid = 2
        password = encode_string(
            "0000000000000000"
        )  # passwd must be <= 16 chars. empty is not OK.
        fmt = f"<II{len(clientVersion)}s{len(password)}sxI"
        self._payload = Payload(
            struct.pack(fmt, schema, connectionType, clientVersion, password, pid)
        )


class LocalLoginResponse(BaseResponse):
    _code = MessageCode.LOCAL_LOGIN + 1
