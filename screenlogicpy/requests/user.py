from ..const.common import ScreenLogicException
from ..const.data import ATTR, DEVICE


async def async_set_user_data(data: dict, data_path: str, name: str, value: str | int)-> None:
    set_data = {
        ATTR.NAME: name,
        ATTR.VALUE: value,
    }
    await async_set_user_data(data, data_path, set_data)

async def async_set_user_data(data: dict, data_path: str, set_data: dict)-> None:
    user_data = data.setdefault(DEVICE.USER, {})
    user_data[data_path] = set_data
