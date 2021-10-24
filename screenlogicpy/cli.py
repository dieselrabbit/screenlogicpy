import string
import json
import argparse
from screenlogicpy.discovery import async_discover
from screenlogicpy.gateway import ScreenLogicGateway
from screenlogicpy.const import (
    BODY_TYPE,
    COLOR_MODE,
    DATA,
    EQUIPMENT,
    HEAT_MODE,
    ON_OFF,
    SL_GATEWAY_IP,
    SL_GATEWAY_NAME,
    SL_GATEWAY_PORT,
    ScreenLogicError,
    ScreenLogicWarning,
)


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
                return (
                    f"{slElement['name']}: {slClass.NAME_FOR_NUM[slElement['value']]}"
                )
            else:
                return f"{slElement['name']}: {slElement['value']}"
        else:
            return slElement["value"]

    # Parser functions
    async def async_get_circuit():
        if not int(args.circuit_num) in gateway.get_data()[DATA.KEY_CIRCUITS]:
            print(f"Invalid circuit number: {args.circuit_num}")
            return 4
        print(
            vFormat(
                gateway.get_data()[DATA.KEY_CIRCUITS][int(args.circuit_num)],
                ON_OFF,
            )
        )
        return 0

    async def async_set_circuit():
        state = 0
        if args.state == "1" or args.state.lower() == "on":
            state = 1
        if not int(args.circuit_num) in gateway.get_data()[DATA.KEY_CIRCUITS]:
            print(f"Invalid circuit number: {args.circuit_num}")
            return 4
        if await gateway.async_set_circuit(int(args.circuit_num), state):
            await gateway.async_update()
        else:
            return 4
        print(
            vFormat(
                gateway.get_data()[DATA.KEY_CIRCUITS][int(args.circuit_num)],
                ON_OFF,
            )
        )
        return 0

    async def async_get_heat_mode():
        body = 0
        if args.body == "1" or args.body.lower() == "spa":
            body = 1
        print(
            vFormat(
                gateway.get_data()[DATA.KEY_BODIES][int(body)]["heat_mode"],
                HEAT_MODE,
            )
        )
        return 0

    async def async_set_heat_mode():
        body = 0
        mode = 0
        if args.body == "1" or args.body.lower() == "spa":
            body = 1
        if args.mode in cliFormatDict(HEAT_MODE.NUM_FOR_NAME):
            mode = cliFormatDict(HEAT_MODE.NUM_FOR_NAME)[args.mode]
        else:
            mode = int(args.mode)
        if await gateway.async_set_heat_mode(int(body), mode):
            await gateway.async_update()
        else:
            return 8
        print(
            vFormat(
                gateway.get_data()[DATA.KEY_BODIES][int(body)]["heat_mode"],
                HEAT_MODE,
            )
        )
        return 0

    async def async_get_heat_temp():
        body = 0
        if args.body == "1" or args.body.lower() == "spa":
            body = 1
        print(
            vFormat(
                gateway.get_data()[DATA.KEY_BODIES][int(body)]["heat_set_point"],
            )
        )
        return 0

    async def async_set_heat_temp():
        body = 0
        if args.body == "1" or args.body.lower() == "spa":
            body = 1
        if args.temp != -1:
            if await gateway.async_set_heat_temp(int(body), int(args.temp)):
                await gateway.async_update()
            else:
                return 16
        print(
            vFormat(
                gateway.get_data()[DATA.KEY_BODIES][int(body)]["heat_set_point"],
            )
        )
        return 0

    async def async_get_heat_state():
        body = 0
        if args.body == "1" or args.body.lower() == "spa":
            body = 1
        print(
            vFormat(
                gateway.get_data()[DATA.KEY_BODIES][int(body)]["heat_status"],
                ON_OFF,
            )
        )
        return 0

    async def async_get_current_temp():
        body = 0
        if args.body == "1" or args.body.lower() == "spa":
            body = 1
        print(
            vFormat(
                gateway.get_data()[DATA.KEY_BODIES][int(body)]["last_temperature"],
            )
        )
        return 0

    async def async_set_color_light():
        mode = cliFormatDict(COLOR_MODE.NUM_FOR_NAME).get(args.mode)
        if mode is None:
            mode = int(args.mode)
        if await gateway.async_set_color_lights(mode):
            print(
                f"Set color mode to {COLOR_MODE.NAME_FOR_NUM[mode]}"
                if args.verbose
                else mode
            )
            return 0
        return 32

    async def async_set_scg_config():
        if args.scg_pool == "*" and args.scg_spa == "*":
            print("No new SCG values. Nothing to do.")
            return 65

        scg_data = gateway.get_data()[DATA.KEY_SCG]
        try:
            scg_1 = (
                scg_data["scg_level1"]["value"]
                if args.scg_pool == "*"
                else int(args.scg_pool)
            )
            scg_2 = (
                scg_data["scg_level2"]["value"]
                if args.scg_spa == "*"
                else int(args.scg_spa)
            )
        except ValueError:
            print("Invalid SCG value")
            return 66

        if await gateway.async_set_scg_config(scg_1, scg_2):
            await gateway.async_update()
            print(
                vFormat(gateway.get_data()[DATA.KEY_SCG]["scg_level1"]),
                vFormat(gateway.get_data()[DATA.KEY_SCG]["scg_level2"]),
            )
            return 0
        return 64

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

    body_options = optionsFromDict(BODY_TYPE.NAME_FOR_NUM)
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

    on_off_options = optionsFromDict(ON_OFF.NAME_FOR_NUM)
    set_circuit_parser = set_subparsers.add_parser("circuit", aliases=["c"])
    set_circuit_parser.add_argument(**ARGUMENT_CIRCUIT_NUM)
    set_circuit_parser.add_argument(
        "state",
        metavar="STATE",
        type=str,
        choices=on_off_options,
        help=f"State to set. One of {on_off_options}",
    )

    cl_options = optionsFromDict(COLOR_MODE.NAME_FOR_NUM)
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
    hm_options = optionsFromDict(HEAT_MODE.NAME_FOR_NUM)
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

        gateway = ScreenLogicGateway(**host)

        await gateway.async_connect()

        await gateway.async_update()

        if DATA.KEY_CONFIG not in gateway.get_data():
            return 1

        def print_gateway():
            verb = "Using"
            if discovered:
                verb = "Discovered"
            print(
                "{} '{}' at {}:{}".format(verb, gateway.name, gateway.ip, gateway.port)
            )
            print(
                EQUIPMENT.CONTROLLER_HARDWARE[
                    gateway.get_data()[DATA.KEY_CONFIG]["controller_type"]
                ][gateway.get_data()[DATA.KEY_CONFIG]["hardware_type"]]
            )

        def print_circuits():
            print("{}  {}  {}".format("ID".rjust(3), "STATE", "NAME"))
            print("--------------------------")
            for id in gateway.get_data()[DATA.KEY_CIRCUITS]:
                circuit = gateway.get_data()[DATA.KEY_CIRCUITS][int(id)]
                print(
                    "{}  {}  {}".format(
                        circuit["id"],
                        ON_OFF.NAME_FOR_NUM[circuit["value"]].rjust(5),
                        circuit["name"],
                    )
                )

        def print_heat():
            for id in gateway.get_data()[DATA.KEY_BODIES]:
                body = gateway.get_data()[DATA.KEY_BODIES][int(id)]
                print(
                    "{} temperature is last {}{}".format(
                        BODY_TYPE.NAME_FOR_NUM[body["body_type"]["value"]],
                        body["last_temperature"]["value"],
                        body["last_temperature"]["unit"],
                    )
                )
                print(
                    "{}: {}{}".format(
                        body["heat_set_point"]["name"],
                        body["heat_set_point"]["value"],
                        body["last_temperature"]["unit"],
                    )
                )
                print(
                    "{}: {}".format(
                        body["heat_status"]["name"],
                        HEAT_MODE.NAME_FOR_NUM[body["heat_status"]["value"]],
                    )
                )
                print(
                    "{}: {}".format(
                        body["heat_mode"]["name"],
                        HEAT_MODE.NAME_FOR_NUM[body["heat_mode"]["value"]],
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
