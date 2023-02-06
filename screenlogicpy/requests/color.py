from ..const import DATA
from .utility import getSome, getString


def decode_color_update(buff: bytes, data: dict):
    config = data.setdefault(DATA.KEY_CONFIG, {})

    color_state = config.setdefault("color_state", {})

    mode, offset = getSome("I", buff, 0)  # 0
    color_state["mode"] = mode

    progress, offset = getSome("I", buff, offset)  # 4
    color_state["progress"] = progress

    limit, offset = getSome("I", buff, offset)  # 8
    color_state["limit"] = limit

    text, offset = getString(buff, offset)  # 12
    color_state["text"] = text
