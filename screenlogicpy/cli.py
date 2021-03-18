import sys
import string
import json
import argparse
from screenlogicpy.discovery import discover
from screenlogicpy.gateway import ScreenLogicGateway
from screenlogicpy.const import (
    BODY_TYPE,
    ON_OFF,
    HEAT_MODE,
    EQUIPMENT,
    ScreenLogicError,
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


def vFormat(verbose, slElement, slClass=None):
    if verbose:
        if slClass:
            return (
                f"{slElement['name']}: "
                f"{slClass.GetFriendlyName(slElement['value'])}"
            )
        else:
            return f"{slElement['name']}: {slElement['value']}"
    else:
        return slElement["value"]


# Parser functions
def get_circuit(args, gateway):
    if not int(args.circuit_num) in gateway.get_data()["circuits"]:
        print(f"Invalid circuit number: {args.circuit_num}")
        return 4
    print(
        vFormat(
            args.verbose, gateway.get_data()["circuits"][int(args.circuit_num)], ON_OFF
        )
    )
    return 0


def set_circuit(args, gateway):
    state = 0
    if args.state == "1" or args.state.lower() == "on":
        state = 1
    if not int(args.circuit_num) in gateway.get_data()["circuits"]:
        print(f"Invalid circuit number: {args.circuit_num}")
        return 4
    if gateway.set_circuit(int(args.circuit_num), state):
        gateway.update()
    else:
        return 4
    print(
        vFormat(
            args.verbose, gateway.get_data()["circuits"][int(args.circuit_num)], ON_OFF
        )
    )
    return 0


def get_heat_mode(args, gateway):
    body = 0
    if args.body == "1" or args.body.lower() == "spa":
        body = 1
    print(
        vFormat(
            args.verbose,
            gateway.get_data()["bodies"][int(body)]["heat_mode"],
            HEAT_MODE,
        )
    )
    return 0


def set_heat_mode(args, gateway):
    body = 0
    mode = 0
    if args.body == "1" or args.body.lower() == "spa":
        body = 1
    if args.mode in cliFormatDict(HEAT_MODE.NUM_FOR_NAME):
        mode = cliFormatDict(HEAT_MODE.NUM_FOR_NAME)[args.mode]
    else:
        mode = int(args.mode)
    if gateway.set_heat_mode(int(body), mode):
        gateway.update()
    else:
        return 8
    print(
        vFormat(
            args.verbose,
            gateway.get_data()["bodies"][int(body)]["heat_mode"],
            HEAT_MODE,
        )
    )
    return 0


def get_heat_temp(args, gateway):
    body = 0
    if args.body == "1" or args.body.lower() == "spa":
        body = 1
    print(
        vFormat(args.verbose, gateway.get_data()["bodies"][int(body)]["heat_set_point"])
    )
    return 0


def set_heat_temp(args, gateway):
    body = 0
    if args.body == "1" or args.body.lower() == "spa":
        body = 1
    if args.temp != -1:
        if gateway.set_heat_temp(int(body), int(args.temp)):
            gateway.update()
        else:
            return 16
    print(
        vFormat(args.verbose, gateway.get_data()["bodies"][int(body)]["heat_set_point"])
    )
    return 0


def get_heat_state(args, gateway):
    body = 0
    if args.body == "1" or args.body.lower() == "spa":
        body = 1
    print(
        vFormat(
            args.verbose, gateway.get_data()["bodies"][int(body)]["heat_status"], ON_OFF
        )
    )
    return 0


def get_current_temp(args, gateway):
    body = 0
    if args.body == "1" or args.body.lower() == "spa":
        body = 1
    print(
        vFormat(
            args.verbose, gateway.get_data()["bodies"][int(body)]["current_temperature"]
        )
    )
    return 0


def get_json(args, gateway):
    print(json.dumps(gateway.get_data(), indent=2))
    return 0


# Entry function
def cli():
    """Handle command line args"""

    option_parser = argparse.ArgumentParser(
        description="Interface for Pentair Screenlogic gateway"
    )

    option_parser.add_argument("-v", "--verbose", action="store_true")
    option_parser.add_argument("-i", "--ip")
    option_parser.add_argument("-p", "--port", default=80)

    subparsers = option_parser.add_subparsers(dest="action")

    # Discover command
    # pylint: disable=unused-variable
    discover_parser = subparsers.add_parser("discover")  # noqa F841

    # Get options
    get_parser = subparsers.add_parser("get")
    get_subparsers = get_parser.add_subparsers(dest="get_option")
    get_subparsers.required = True

    get_circuit_parser = get_subparsers.add_parser("circuit", aliases=["c"])
    get_circuit_parser.add_argument("circuit_num", metavar="CIRCUIT_NUM", type=int)
    get_circuit_parser.set_defaults(func=get_circuit)

    body_options = optionsFromDict(BODY_TYPE.NAME_FOR_NUM)
    get_heat_mode_parser = get_subparsers.add_parser("heat-mode", aliases=["hm"])
    get_heat_mode_parser.add_argument(
        "body", metavar="BODY", type=str, choices=body_options
    )
    get_heat_mode_parser.set_defaults(func=get_heat_mode)

    get_heat_temp_parser = get_subparsers.add_parser("heat-temp", aliases=["ht"])
    get_heat_temp_parser.add_argument(
        "body", metavar="BODY", type=str, choices=body_options
    )
    get_heat_temp_parser.set_defaults(func=get_heat_temp)

    get_heat_state_parser = get_subparsers.add_parser("heat-state", aliases=["hs"])
    get_heat_state_parser.add_argument(
        "body", metavar="BODY", type=str, choices=body_options
    )
    get_heat_state_parser.set_defaults(func=get_heat_state)

    get_current_temp_parser = get_subparsers.add_parser("current-temp", aliases=["t"])
    get_current_temp_parser.add_argument(
        "body", metavar="BODY", type=str, choices=body_options
    )
    get_current_temp_parser.set_defaults(func=get_current_temp)

    get_json_parser = get_subparsers.add_parser("json", aliases=["j"])
    get_json_parser.set_defaults(func=get_json)

    # Set options
    set_parser = subparsers.add_parser("set")
    set_subparsers = set_parser.add_subparsers(dest="set_option")
    set_subparsers.required = True

    on_off_options = optionsFromDict(ON_OFF.NAME_FOR_NUM)
    set_circuit_parser = set_subparsers.add_parser("circuit", aliases=["c"])
    set_circuit_parser.add_argument("circuit_num", metavar="CIRCUIT_NUM", type=int)
    set_circuit_parser.add_argument(
        "state", metavar="STATE", type=str, choices=on_off_options
    )
    set_circuit_parser.set_defaults(func=set_circuit)

    set_heat_mode_parser = set_subparsers.add_parser("heat-mode", aliases=["hm"])
    set_heat_mode_parser.add_argument(
        "body", metavar="BODY", type=str, choices=body_options
    )
    hm_options = optionsFromDict(HEAT_MODE.NAME_FOR_NUM)
    set_heat_mode_parser.add_argument(
        "mode", metavar="MODE", type=str, choices=hm_options, default=hm_options[0]
    )
    set_heat_mode_parser.set_defaults(func=set_heat_mode)

    set_heat_temp_parser = set_subparsers.add_parser("heat-temp", aliases=["ht"])
    set_heat_temp_parser.add_argument(
        "body", metavar="BODY", type=str, choices=body_options
    )
    set_heat_temp_parser.add_argument("temp", type=int, metavar="TEMP", default=None)
    set_heat_temp_parser.set_defaults(func=set_heat_temp)

    args = option_parser.parse_args()  # save for debugger: ['-i', 'xx', 'get', 'json']

    try:
        host = {"ip": args.ip, "port": args.port}
        discovered = False
        if not host["ip"]:
            # Try to discover gateway
            hosts = discover()
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
                                    host["name"], host["ip"], host["port"]
                                )
                            )
                        else:
                            print(
                                "{}:{} '{}'".format(
                                    host["ip"], host["port"], host["name"]
                                )
                            )
                    return 0

                # For CLI commands that don't specifiy an ip address, auto use the first gateway discovered
                # Good for most cases where only one exists on the network
                host = hosts[0]

            else:
                print("No ScreenLogic gateways found.")
                return 1

        gateway = ScreenLogicGateway(**host)

        if "config" not in gateway.get_data():
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
                    gateway.get_data()["config"]["controller_type"]
                ][gateway.get_data()["config"]["hardware_type"]]
            )

        def print_circuits():
            print("{}  {}  {}".format("ID".rjust(3), "STATE", "NAME"))
            print("--------------------------")
            for id in gateway.get_data()["circuits"]:
                circuit = gateway.get_data()["circuits"][int(id)]
                print(
                    "{}  {}  {}".format(
                        circuit["id"],
                        ON_OFF.NAME_FOR_NUM[circuit["value"]].rjust(5),
                        circuit["name"],
                    )
                )

        def print_heat():
            for id in gateway.get_data()["bodies"]:
                body = gateway.get_data()["bodies"][int(id)]
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
            return 0

        if args.verbose:
            print_gateway()

        return args.func(args, gateway)

    except ScreenLogicError as err:
        print(err)
        return 32


if __name__ == "__main__":
    sys.exit(cli())
