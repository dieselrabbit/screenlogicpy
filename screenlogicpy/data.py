from dataclasses import asdict, dataclass
import json
from typing import Any

from .const.common import DATA_REQUEST
from .requests.chemistry import decode_chemistry
from .requests.config import decode_pool_config
from .requests.datetime import decode_date_time
from .requests.gateway import decode_version
from .requests.lights import decode_color_update
from .requests.pump import decode_pump_status
from .requests.scg import decode_scg_config
from .requests.status import decode_pool_status

REQUEST_DECODE_FUNCS = {
    DATA_REQUEST.VERSION: decode_version,
    DATA_REQUEST.CONFIG: decode_pool_config,
    DATA_REQUEST.STATUS: decode_pool_status,
    DATA_REQUEST.PUMPS: decode_pump_status,
    DATA_REQUEST.CHEMISTRY: decode_chemistry,
    DATA_REQUEST.SCG: decode_scg_config,
    DATA_REQUEST.KEY_COLOR: decode_color_update,
    DATA_REQUEST.DATE_TIME: decode_date_time,
}


@dataclass(frozen=True)
class ScreenLogicResponseSet:
    raw: bytes
    decoded: dict


@dataclass(frozen=True)
class ScreenLogicResponseCollection:
    decoded_complete: dict
    version: ScreenLogicResponseSet | None = None
    config: ScreenLogicResponseSet | None = None
    status: ScreenLogicResponseSet | None = None
    pumps: list[ScreenLogicResponseSet] = None
    chemistry: ScreenLogicResponseSet | None = None
    scg: ScreenLogicResponseSet | None = None
    color: list[ScreenLogicResponseSet] = None
    date_time: ScreenLogicResponseSet | None = None


def build_response_collection(raw: dict, data: dict) -> ScreenLogicResponseCollection:
    SLResponseColArgs = {}

    for req, dec_func in REQUEST_DECODE_FUNCS.items():
        if raw_resp := raw.get(req):
            if isinstance(raw_resp, dict):
                resp_sets = []
                for idx, raw_resp_i in raw_resp.items():
                    dec_resp_i = {}
                    dec_func(raw_resp_i, dec_resp_i, idx)
                    resp_sets.append(ScreenLogicResponseSet(raw_resp_i, dec_resp_i))
                SLResponseColArgs[req] = resp_sets
            else:
                dec_resp = {}
                dec_func(raw_resp, dec_resp)
                SLResponseColArgs[req] = ScreenLogicResponseSet(raw_resp, dec_resp)

    return ScreenLogicResponseCollection(data, **SLResponseColArgs)


def deconstruct_response_collection(
    collection: ScreenLogicResponseCollection,
) -> tuple[dict, dict]:
    data = collection.decoded_complete
    raw = {}
    for dr, data_request in asdict(collection).items():
        if dr == "decoded_complete":
            continue
        if isinstance(data_request, list):
            data_dict = raw.setdefault(dr, {})
            for idx, val in enumerate(data_request):
                data_dict[idx] = val["raw"]

        else:
            raw[dr] = data_request["raw"] if data_request is not None else None

    return raw, data


T_KEY = "__type"


def int_key_json_decoder(o: dict) -> Any:
    if isinstance(o, dict):
        strkeys = []
        for key in o.keys():
            if isinstance(key, str):
                if key.isdigit():
                    strkeys.append(key)
        for strkey in strkeys:
            o[int(strkey)] = o.pop(strkey)
    return o


# Patch for color RGB tuples
def value_list_json_decoder(o: dict) -> Any:
    if "value" in o:
        value = o["value"]
        if isinstance(value, list) and len(value) == 3:
            o["value"] = tuple(value)
    return int_key_json_decoder(o)


def response_set_json_decoder(o: dict) -> Any:
    if "decoded" in o and "raw" in o:
        return ScreenLogicResponseSet(**o)
    return value_list_json_decoder(o)


def bytes_json_decoder(o: dict) -> Any:
    if T_KEY in o:
        return eval(o["repr"])
    return response_set_json_decoder(o)


def read_sl_data_json(filename: str) -> dict:
    with open(filename, "r", encoding="utf-8") as fp:
        return json.load(fp, object_hook=bytes_json_decoder)


def bytes_json_encoder(o: Any) -> Any:
    if isinstance(o, bytes):
        return {T_KEY: repr(type(o)), "repr": repr(o)}
    return o


def write_sl_data_json(filename: str, data: dict) -> None:
    with open(filename, "w", encoding="utf-8") as fp:
        json.dump(
            data,
            fp,
            default=bytes_json_encoder,
            ensure_ascii=False,
            indent=2,
        )


def import_response_collection(filename: str) -> ScreenLogicResponseCollection:
    return ScreenLogicResponseCollection(**read_sl_data_json(filename))


def export_response_collection(
    response_collection: ScreenLogicResponseCollection, filename: str
) -> None:
    write_sl_data_json(filename, asdict(response_collection))
