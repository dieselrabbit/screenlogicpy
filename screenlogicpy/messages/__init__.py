import struct

from .base import *
from .chemistry import *
from .client import *
from .config import *
from .datetime import *
from .equipment import *
from .gateway import *
from .login import *
from .pump import *
from .scg import *
from .status import *
from .user import *


__all__ = (
    base.__all__
    + chemistry.__all__
    + client.__all__
    + config.__all__
    + datetime.__all__
    + equipment.__all__
    + gateway.__all__
    + login.__all__
    + pump.__all__
    + scg.__all__
    + status.__all__
    + user.__all__
    + ("from_bytes",)
)

_MESSAGE_CODE_MAP = {
    MessageCode.CHALLENGE: ChallengeRequest,
    MessageCode.CHALLENGE + 1: ChallengeResponse,
    MessageCode.LOCAL_LOGIN: LocalLoginRequest,
    MessageCode.LOCAL_LOGIN + 1: LocalLoginResponse,
    MessageCode.GET_USER_CONFIG: UserConfigRequest,
    MessageCode.GET_USER_CONFIG + 1: UserConfigResponse,
    MessageCode.GET_DATETIME: GetControllerDateTimeRequest,
    MessageCode.GET_DATETIME + 1: GetControllerDateTimeResponse,
    MessageCode.SET_DATETIME: SetControllerDateTimeRequest,
    MessageCode.SET_DATETIME + 1: SetControllerDateTimeResponse,
    MessageCode.GET_VERSION: GatewayVersionRequest,
    MessageCode.GET_VERSION + 1: GatewayVersionResponse,
    MessageCode.GET_WEATHER_FORECAST: BaseRequest,
    MessageCode.GET_WEATHER_FORECAST + 1: BaseResponse,
    MessageCode.ADD_CLIENT: AddClientRequest,
    MessageCode.ADD_CLIENT + 1: AddClientResponse,
    MessageCode.REMOVE_CLIENT: RemoveClientRequest,
    MessageCode.REMOVE_CLIENT + 1: RemoveClientResponse,
    MessageCode.GET_POOL_STATUS: PoolStatusRequest,
    MessageCode.GET_POOL_STATUS + 1: PoolStatusResponse,
    MessageCode.SET_HEAT_TEMPERATURE: BaseRequest,
    MessageCode.SET_HEAT_TEMPERATURE + 1: BaseResponse,
    MessageCode.SET_CIRCUIT: BaseRequest,
    MessageCode.SET_CIRCUIT + 1: BaseResponse,
    MessageCode.GET_POOL_CONFIG: GetPoolConfigRequest,
    MessageCode.GET_POOL_CONFIG + 1: GetPoolConfigResponse,
    MessageCode.SET_HEAT_MODE: BaseRequest,
    MessageCode.SET_HEAT_MODE + 1: BaseResponse,
    MessageCode.SET_LIGHTS: BaseRequest,
    MessageCode.SET_LIGHTS + 1: BaseResponse,
    MessageCode.SET_CHEMISTRY_CONFIG: SetChemistryConfigRequest,
    MessageCode.SET_CHEMISTRY_CONFIG + 1: SetChemistryConfigResponse,
    MessageCode.GET_EQUIPMENT: GetEquipmentConfigRequest,
    MessageCode.GET_EQUIPMENT + 1: GetEquipmentConfigResponse,
    MessageCode.GET_SCG_CONFIG: GetSaltCellConfigRequest,
    MessageCode.GET_SCG_CONFIG + 1: GetSaltCellConfigResponse,
    MessageCode.SET_SCG: SetSaltCellConfigRequest,
    MessageCode.SET_SCG + 1: SetSaltCellConfigResponse,
    MessageCode.GET_PUMP_STATUS: PumpStatusRequest,
    MessageCode.GET_PUMP_STATUS + 1: PumpStatusResponse,
    MessageCode.SET_COOL_TEMPERATURE: BaseRequest,
    MessageCode.SET_COOL_TEMPERATURE + 1: BaseResponse,
    MessageCode.GET_CHEMISTRY: GetChemistryStatusRequest,
    MessageCode.GET_CHEMISTRY + 1: GetChemistryStatusResponse,
    MessageCode.GET_GATEWAY_CONFIG: BaseRequest,
    MessageCode.GET_GATEWAY_CONFIG + 1: BaseResponse,
    MessageCode.PING_REQ: PingRequest,
    MessageCode.PING_REQ + 1: PingResponse,
    MessageCode.WEATHER_FORECAST_CHANGED: BaseResponse,
    MessageCode.STATUS_CHANGED: PoolStatusChanged,
    MessageCode.COLOR_UPDATE: BaseResponse,
    MessageCode.CHEMISTRY_CHANGED: ChemistryStatusChanged,
    MessageCode.LOGIN_REJECTED: LocalLoginResponse,
    MessageCode.INVALID_REQUEST: InvalidRequestResponse,
    MessageCode.BAD_PARAMETER: BadParameterResponse,
}


def _msg_factory(code: int) -> AbstractMessage:
    if code in _MESSAGE_CODE_MAP:
        return _MESSAGE_CODE_MAP[code]
    else:
        return AbstractMessage


def from_bytes(data: bytes):
    id, code, size = struct.unpack_from(HEADER_FORMAT, data)
    payload = Payload(data[HEADER_LENGTH : HEADER_LENGTH + size])
    message_class = _msg_factory(code)
    if issubclass(message_class, Exception):
        raise message_class
    if issubclass(message_class, BaseResponse):
        return message_class(payload, id)
    return message_class()
