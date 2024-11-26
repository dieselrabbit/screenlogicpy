from datetime import datetime, timedelta, timezone
import struct

from ..system import *
from .base import *

__all__ = (
    "GetControllerDateTimeRequest",
    "GetControllerDateTimeResponse",
    "SetControllerDateTimeRequest",
    "SetControllerDateTimeResponse",
)


def format_timedelta(td: timedelta) -> str:
    """Formats a timedelta object into a human-readable string."""

    seconds = int(abs(td.total_seconds()))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    parts = []
    if days > 0:
        parts.append(f"{days} days")
    if hours > 0:
        parts.append(f"{hours} hours")
    if minutes > 0:
        parts.append(f"{minutes} minutes")
    if seconds > 0:
        parts.append(f"{seconds} seconds")

    if not parts:
        return "0 seconds"
    return ", ".join(parts)


class GetControllerDateTimeRequest(BaseRequest):
    _code = MessageCode.GET_DATETIME


class GetControllerDateTimeResponse(BaseResponse):
    _code = MessageCode.GET_DATETIME + 1

    def decode(self, system: System, tz: timezone = timezone.utc) -> None:

        controller = system.controller
        slpy_host_datetime = datetime.now(tz)
        controller_datetime = self.payload.next_datetime(tz)
        controller.time = controller_datetime.timestamp()
        controller.config.time_config.client = slpy_host_datetime.timestamp()

        time_delta = slpy_host_datetime - controller_datetime
        controller.config.time_config.delta = time_delta.total_seconds()

        # controller.properties["clock_delta"] = State(
        #    "Clock Delta",
        #    format_timedelta(time_delta),
        # )

        controller.config.time_config.auto_dst = bool(self.payload.next_uint32())


class SetControllerDateTimeRequest(BaseRequest):
    _code = MessageCode.SET_DATETIME

    def __init__(self, dt: datetime, auto_dst: int | bool = True) -> None:
        auto_dst_int = int(auto_dst)
        self._payload = Payload(encode_datetime(dt) + struct.pack("<I", auto_dst_int))


class SetControllerDateTimeResponse(BaseResponse):
    _code = MessageCode.SET_DATETIME + 1
