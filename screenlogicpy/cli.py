import asyncio
import string
import json
import argparse
from screenlogicpy.discovery import async_discover
from screenlogicpy.gateway import ScreenLogicGateway
from screenlogicpy.const.common import (
    ON_OFF,
    RANGE,
    SL_GATEWAY_IP,
    SL_GATEWAY_NAME,
    SL_GATEWAY_PORT,
    SLIntEnum,
    ScreenLogicError,
    ScreenLogicWarning,
)
from screenlogicpy.device_const.chemistry import RANGE_ORP_SETPOINT, RANGE_PH_SETPOINT
from screenlogicpy.device_const.heat import HEAT_MODE
from screenlogicpy.device_const.system import BODY_TYPE, COLOR_MODE
from screenlogicpy.const.data import ATTR, DEVICE, GROUP, VALUE


def cliFormat(name: str):
    table = str.maketrans(" ", "_", string.punctuation)
    return name.translate(table).lower()


def cliFormatDict(mapping: dict):
    return {
        cliFormat(key)
        if isinstance(key, str)
        else key: cliFormat(value)
        if isinstance(value, str)
        else value
        for key, value in mapping.items()
    }


def optionsFromDict(mapping: dict):
    options = []
    for key, value in cliFormatDict(mapping).items():
        options.extend((str(key), str(value)))
    return options


# Entry function
async def cli(cli_args):
    """Handle command line args"""

    def vFormat(slElement: dict, slClass=None):
        if args.verbose:
            if slClass:
                if issubclass(slClass, SLIntEnum):
                    return f"{slElement[ATTR.NAME]}: {slClass(slElement[ATTR.VALUE]).title}"
                else:
                    return f"{slElement[ATTR.NAME]}: {slClass.NAME_FOR_NUM[slElement[ATTR.VALUE]]}"
            else:
                return f"{slElement[ATTR.NAME]}: {slElement[ATTR.VALUE]}"
        else:
            if slClass and issubclass(slClass, SLIntEnum):
                return slClass(slElement[ATTR.VALUE]).value
            else:
                return slElement[ATTR.VALUE]

    # Parser functions
    async def async_get_circuit():
        circuit_id = int(args.circuit_num)
        if circuit_id not in gateway.get_data(DEVICE.CIRCUIT):
            print(f"Invalid circuit number: {args.circuit_num}")
            return 4
        print(
            vFormat(
                gateway.get_data(DEVICE.CIRCUIT, circuit_id),
                ON_OFF,
            )
        )
        return 0

    async def async_set_circuit():
        state = ON_OFF.parse(args.state).value
        circuit_id = int(args.circuit_num)
        if circuit_id not in gateway.get_data(DEVICE.CIRCUIT):
            print(f"Invalid circuit number: {args.circuit_num}")
            return 4
        if await gateway.async_set_circuit(circuit_id, state):
            await gateway.async_update()
        else:
            return 4
        print(
            vFormat(
                gateway.get_data(DEVICE.CIRCUIT, circuit_id),
                ON_OFF,
            )
        )
        return 0

    async def async_get_heat_mode():
        body = BODY_TYPE.parse(args.body).value
        print(
            vFormat(
                gateway.get_data(DEVICE.BODY, int(body), VALUE.HEAT_MODE),
                HEAT_MODE,
            )
        )
        return 0

    async def async_set_heat_mode():
        body = BODY_TYPE.parse(args.body).value
        mode = HEAT_MODE.parse(args.mode).value
        if await gateway.async_set_heat_mode(body, mode):
            await gateway.async_update()
        else:
            return 8
        print(
            vFormat(
                gateway.get_data(DEVICE.BODY, body, VALUE.HEAT_MODE),
                HEAT_MODE,
            )
        )
        return 0

    async def async_get_heat_temp():
        body = BODY_TYPE.parse(args.body).value
        print(
            vFormat(
                gateway.get_data(DEVICE.BODY, body, VALUE.HEAT_SETPOINT),
            )
        )
        return 0

    async def async_set_heat_temp():
        body = BODY_TYPE.parse(args.body).value
        if args.temp != -1:
            if await gateway.async_set_heat_temp(body, int(args.temp)):
                await gateway.async_update()
            else:
                return 16
        print(
            vFormat(
                gateway.get_data(DEVICE.BODY, body, VALUE.HEAT_SETPOINT),
            )
        )
        return 0

    async def async_get_heat_state():
        body = BODY_TYPE.parse(args.body).value
        print(
            vFormat(
                gateway.get_data(DEVICE.BODY, body, VALUE.HEAT_STATE),
                ON_OFF,
            )
        )
        return 0

    async def async_get_current_temp():
        body = BODY_TYPE.parse(args.body)
        print(
            vFormat(
                gateway.get_data(DEVICE.BODY, body, VALUE.LAST_TEMPERATURE),
            )
        )
        return 0

    async def async_set_color_light():
        mode = COLOR_MODE.parse(args.mode).value
        if mode is None:
            mode = int(args.mode)
        if await gateway.async_set_color_lights(mode):
            print(
                f"Set color mode to {COLOR_MODE(mode).title}" if args.verbose else mode
            )
            return 0
        return 32

    async def async_set_scg_config():
        if args.scg_pool == "*" and args.scg_spa == "*":
            print("No new Chlorinator values. Nothing to do.")
            return 65

        scg_config_data = gateway.get_data(DEVICE.SCG, GROUP.CONFIGURATION)
        try:
            scg_1 = (
                scg_config_data[VALUE.POOL_SETPOINT][ATTR.VALUE]
                if args.scg_pool == "*"
                else int(args.scg_pool)
            )
            scg_2 = (
                scg_config_data[VALUE.SPA_SETPOINT][ATTR.VALUE]
                if args.scg_spa == "*"
                else int(args.scg_spa)
            )
        except ValueError:
            print("Invalid Chlorinator value")
            return 66

        if await gateway.async_set_scg_config(scg_1, scg_2):
            await gateway.async_update()
            new_scg_config_data = gateway.get_data(DEVICE.SCG, GROUP.CONFIGURATION)
            print(
                vFormat(new_scg_config_data[VALUE.POOL_SETPOINT]),
                vFormat(new_scg_config_data[VALUE.SPA_SETPOINT]),
            )
            return 0
        return 64

    async def async_set_chem_data():
        if args.ph_setpoint == "*" and args.orp_setpoint == "*":
            print("No new setpoint values. Nothing to do.")
            return 129

        chem_config_data = gateway.get_data(DEVICE.INTELLICHEM, GROUP.CONFIGURATION)
        try:
            ph = (
                chem_config_data[VALUE.PH_SETPOINT][ATTR.VALUE]
                if args.ph_setpoint == "*"
                else float(args.ph_setpoint)
            )
            orp = (
                chem_config_data[VALUE.ORP_SETPOINT][ATTR.VALUE]
                if args.orp_setpoint == "*"
                else int(args.orp_setpoint)
            )
        except ValueError:
            print("Invalid Chemistry Setpoint value")
            return 130

        ch = chem_config_data[VALUE.CALCIUM_HARNESS][ATTR.VALUE]
        ta = chem_config_data[VALUE.TOTAL_ALKALINITY][ATTR.VALUE]
        ca = chem_config_data[VALUE.CYA][ATTR.VALUE]
        sa = chem_config_data[VALUE.SALT_TDS_PPM][ATTR.VALUE]

        if await gateway.async_set_chem_data(ph, orp, ch, ta, ca, sa):
            await asyncio.sleep(3)
            await gateway.async_update()
            new_chem_config_data = gateway.get_data(
                DEVICE.INTELLICHEM, GROUP.CONFIGURATION
            )
            print(
                vFormat(new_chem_config_data[VALUE.PH_SETPOINT]),
                vFormat(new_chem_config_data[VALUE.ORP_SETPOINT]),
            )
            return 0
        return 128

    # Begin Parser Setup
    async def async_get_json():
        print(json.dumps(gateway.get_data(), indent=2))
        return 0

    option_parser = argparse.ArgumentParser(
        description="Interface for Pentair Screenlogic gateway"
    )

    option_parser.add_argument("-v", "--verbose", action="store_true")
    option_parser.add_argument("-i", "--ip")
    option_parser.add_argument("-p", "--port", default=80)

    subparsers = option_parser.add_subparsers(dest="action")

    # Discover command
    # pylint: disable=unused-variable
    discover_parser = subparsers.add_parser(  # noqa F841
        "discover", help="Attempt to discover all available ScreenLogic gateways"
    )

    # Get options
    get_parser = subparsers.add_parser("get", help="Gets the option specified")
    get_subparsers = get_parser.add_subparsers(dest="get_option")
    get_subparsers.required = True

    ARGUMENT_CIRCUIT_NUM = {
        "dest": "circuit_num",
        "metavar": "CIRCUIT_NUM",
        "type": int,
        "help": "Circuit number",
    }
    get_circuit_parser = get_subparsers.add_parser("circuit", aliases=["c"])
    get_circuit_parser.add_argument(**ARGUMENT_CIRCUIT_NUM)
    get_circuit_parser.set_defaults(async_func=async_get_circuit)

    body_options = BODY_TYPE.parsable()
    ARGUMENT_BODY = {
        "dest": "body",
        "metavar": "BODY",
        "type": str,
        "choices": body_options,
        "help": f"Body of water. One of: {body_options}",
    }
    get_heat_mode_parser = get_subparsers.add_parser("heat-mode", aliases=["hm"])
    get_heat_mode_parser.add_argument(**ARGUMENT_BODY)
    get_heat_mode_parser.set_defaults(async_func=async_get_heat_mode)

    get_heat_temp_parser = get_subparsers.add_parser("heat-temp", aliases=["ht"])
    get_heat_temp_parser.add_argument(**ARGUMENT_BODY)
    get_heat_temp_parser.set_defaults(async_func=async_get_heat_temp)

    get_heat_state_parser = get_subparsers.add_parser("heat-state", aliases=["hs"])
    get_heat_state_parser.add_argument(**ARGUMENT_BODY)
    get_heat_state_parser.set_defaults(async_func=async_get_heat_state)

    get_current_temp_parser = get_subparsers.add_parser("current-temp", aliases=["t"])
    get_current_temp_parser.add_argument(**ARGUMENT_BODY)
    get_current_temp_parser.set_defaults(async_func=async_get_current_temp)

    get_json_parser = get_subparsers.add_parser("json", aliases=["j"])
    get_json_parser.set_defaults(async_func=async_get_json)

    # Set options
    set_parser = subparsers.add_parser("set")
    set_subparsers = set_parser.add_subparsers(dest="set_option")
    set_subparsers.required = True

    on_off_options = ON_OFF.parsable()
    set_circuit_parser = set_subparsers.add_parser("circuit", aliases=["c"])
    set_circuit_parser.add_argument(**ARGUMENT_CIRCUIT_NUM)
    set_circuit_parser.add_argument(
        "state",
        metavar="STATE",
        type=str,
        choices=on_off_options,
        help=f"State to set. One of {on_off_options}",
    )

    cl_options = COLOR_MODE.parsable()
    set_circuit_parser.set_defaults(async_func=async_set_circuit)
    set_color_light_parser = set_subparsers.add_parser("color-lights", aliases=["cl"])
    set_color_light_parser.add_argument(
        "mode",
        metavar="MODE",
        type=str,
        choices=cl_options,
        help=f"Color lights command, color or show. One of :{cl_options}",
    )
    set_color_light_parser.set_defaults(async_func=async_set_color_light)

    set_heat_mode_parser = set_subparsers.add_parser("heat-mode", aliases=["hm"])
    set_heat_mode_parser.add_argument(**ARGUMENT_BODY)
    hm_options = HEAT_MODE.parsable()
    set_heat_mode_parser.add_argument(
        "mode",
        metavar="MODE",
        type=str,
        choices=hm_options,
        default=hm_options[0],
        help=f"Heat mode to set. One of: {hm_options}",
    )
    set_heat_mode_parser.set_defaults(async_func=async_set_heat_mode)

    set_heat_temp_parser = set_subparsers.add_parser("heat-temp", aliases=["ht"])
    set_heat_temp_parser.add_argument(**ARGUMENT_BODY)
    set_heat_temp_parser.add_argument(
        "temp",
        type=int,
        metavar="TEMP",
        default=None,
        help="Temperature to set in same unit of measurement as controller settings",
    )
    set_heat_temp_parser.set_defaults(async_func=async_set_heat_temp)

    set_scg_config_parser = set_subparsers.add_parser("salt-generator", aliases=["scg"])
    set_scg_config_parser.add_argument(
        "scg_pool",
        type=str,
        metavar="POOL_PCT",
        default=None,
        help="Chlorinator output for when system is in POOL mode. 0-100, or * to keep current value.",
    )
    set_scg_config_parser.add_argument(
        "scg_spa",
        type=str,
        metavar="SPA_PCT",
        default=None,
        help="Chlorinator output for when system is in SPA mode. 0-20, or * to keep current value.",
    )
    set_scg_config_parser.set_defaults(async_func=async_set_scg_config)

    set_chem_data_parser = set_subparsers.add_parser("chem-data", aliases=["ch"])
    set_chem_data_parser.add_argument(
        "ph_setpoint",
        type=str,
        metavar="PH_SETPOINT",
        default=None,
        help=f"PH set point for IntelliChem. {RANGE_PH_SETPOINT[RANGE.MIN]}-{RANGE_PH_SETPOINT[RANGE.MAX]}, or * to keep current value.",
    )
    set_chem_data_parser.add_argument(
        "orp_setpoint",
        type=str,
        metavar="ORP_SETPOINT",
        default=None,
        help=f"ORP set point for IntelliChem. {RANGE_ORP_SETPOINT[RANGE.MIN]}-{RANGE_ORP_SETPOINT[RANGE.MAX]}, or * to keep current value.",
    )
    set_chem_data_parser.set_defaults(async_func=async_set_chem_data)

    args = option_parser.parse_args(cli_args)

    try:
        host = {SL_GATEWAY_IP: args.ip, SL_GATEWAY_PORT: args.port}
        discovered = False
        if not host[SL_GATEWAY_IP]:
            # Try to discover gateway
            hosts = await async_discover()
            # Host(s) found
            if len(hosts) > 0:
                discovered = True
                if args.action == "discover":
                    if args.verbose:
                        print("Discovered:")
                    for host in hosts:
                        if args.verbose:
                            print(
                                "'{}' at {}:{}".format(
                                    host[SL_GATEWAY_NAME],
                                    host[SL_GATEWAY_IP],
                                    host[SL_GATEWAY_PORT],
                                )
                            )
                        else:
                            print(
                                "{}:{} '{}'".format(
                                    host[SL_GATEWAY_IP],
                                    host[SL_GATEWAY_PORT],
                                    host[SL_GATEWAY_NAME],
                                )
                            )
                    return 0

                # For CLI commands that don't specify an ip address, auto use the first gateway discovered
                # Good for most cases where only one exists on the network
                host = hosts[0]

            else:
                print("No ScreenLogic gateways found.")
                return 1

        gateway = ScreenLogicGateway()

        await gateway.async_connect(**host)

        await gateway.async_update()

        if DEVICE.CONTROLLER not in gateway.get_data():
            return 1

        def print_gateway():
            verb = "Discovered" if discovered else "Using"
            print(
                "{} '{}' at {}:{}".format(verb, gateway.name, gateway.ip, gateway.port)
            )
            print(gateway.get_value(DEVICE.CONTROLLER, VALUE.MODEL))
            if args.verbose:
                print(f"Version: {gateway.version}")

        def print_circuits():
            print("{}  {}  {}".format("ID".rjust(3), "STATE", "NAME"))
            print("--------------------------")
            for id, circuit in gateway.get_data(DEVICE.CIRCUIT).items():
                print(
                    "{}  {}  {}".format(
                        id,
                        ON_OFF(circuit[ATTR.VALUE]).title.rjust(5),
                        circuit[ATTR.NAME],
                    )
                )

        def print_heat():
            for body in gateway.get_data(DEVICE.BODY).values():
                print(
                    "{} temperature is last {}{}".format(
                        BODY_TYPE(body[ATTR.BODY_TYPE]).title,
                        body[VALUE.LAST_TEMPERATURE][ATTR.VALUE],
                        body[VALUE.LAST_TEMPERATURE][ATTR.UNIT],
                    )
                )
                print(
                    "{}: {}{}".format(
                        body[VALUE.HEAT_SETPOINT][ATTR.NAME],
                        body[VALUE.HEAT_SETPOINT][ATTR.VALUE],
                        body[VALUE.LAST_TEMPERATURE][ATTR.UNIT],
                    )
                )
                print(
                    "{}: {}".format(
                        body[VALUE.HEAT_STATE][ATTR.NAME],
                        HEAT_MODE(body[VALUE.HEAT_STATE][ATTR.VALUE]).title,
                    )
                )
                print(
                    "{}: {}".format(
                        body[VALUE.HEAT_MODE][ATTR.NAME],
                        HEAT_MODE(body[VALUE.HEAT_MODE][ATTR.VALUE]).title,
                    )
                )
                print("--------------------------")

        def print_dashboard():
            print_gateway()
            print("**************************")
            print_heat()
            print("**************************")
            print_circuits()
            print("**************************")

        if args.action is None:
            print_dashboard()
            await gateway.async_disconnect()
            return 0

        if args.verbose:
            print_gateway()
        result = await args.async_func()
        await gateway.async_disconnect()
        return result

    except (ScreenLogicError, ScreenLogicWarning) as err:
        print(err)
        return 128
