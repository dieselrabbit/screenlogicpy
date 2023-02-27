import asyncio
import logging
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
from screenlogicpy.validation import DATA_BOUNDS as DB


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

    async def async_set_scg_setpoint():
        if args.pool is None and args.spa is None:
            set_scg_setpoint_parser.error("At least one argument required.")

        try:
            if args.pool is not None:
                DB.SCG_SETPOINT_POOL.validate(args.pool)
            scg_pool = args.pool
            if args.spa is not None:
                DB.SCG_SETPOINT_SPA.validate(args.spa)
            scg_spa = args.spa
        except ValueError:
            set_scg_setpoint_parser.error("Invalid SCG setpoint value.")

        if await gateway.async_set_scg_config(
            pool_output=scg_pool,
            spa_output=scg_spa,
        ):
            for x in range(5):
                await asyncio.sleep(2)
                await gateway.async_get_scg()
                new_data = gateway.get_data()
                new_pool_sp_data = new_data[DATA.KEY_SCG]["scg_level1"]
                new_spa_sp_data = new_data[DATA.KEY_SCG]["scg_level2"]
                if (
                    new_pool_sp_data["value"] == scg_pool
                    or new_spa_sp_data["value"] == scg_spa
                ):
                    break
                elif x == 4:
                    print("Failed to confirm updated scg values.")
                    return 64

            if scg_pool is not None:
                print(vFormat(new_pool_sp_data))
            if scg_spa is not None:
                print(vFormat(new_spa_sp_data))
            return 0
        return 64

    async def async_set_scg_super():
        if args.state is None and args.time is None:
            set_scg_super_parser.error("At least one argument required.")

        try:
            if args.state is not None:
                DB.ON_OFF.validate(args.state)
            sup = args.state
            if args.time is not None:
                DB.SC_RUNTIME.validate(args.time)
            timer = args.time
        except ValueError:
            set_scg_super_parser.error("Invalid super chlorinate value")

        if await gateway.async_set_scg_config(
            super_chlor=sup,
            super_time=timer,
        ):
            for x in range(5):
                await asyncio.sleep(2)
                await gateway.async_get_scg()
                new_data = gateway.get_data()
                new_scg_data = new_data[DATA.KEY_SCG]["scg_flags"]
                new_timer_data = new_data[DATA.KEY_SCG]["scg_super_chlor_timer"]
                if new_scg_data["value"] == sup or new_timer_data["value"] == timer:
                    break
                elif x == 4:
                    print("Failed to confirm updated scg values.")
                    return 64

            if sup is not None:
                print(vFormat(new_scg_data))
            if timer is not None:
                print(vFormat(new_timer_data))
            return 0
        return 64

    async def async_set_chem_setpoint():
        if args.ph is None and args.orp is None:
            set_chem_setpoint_parser.error("At least one argument required.")

        try:
            if args.ph is not None:
                DB.CHEM_SETPOINT_PH.validate(args.ph)
            ph = args.ph
            if args.orp is not None:
                DB.CHEM_SETPOINT_ORP.validate(args.orp)
            orp = args.orp
        except ValueError:
            set_chem_setpoint_parser.error("Invalid chemistry setpoint value.")

        if await gateway.async_set_chem_data(
            ph_setpoint=ph,
            orp_setpoint=orp,
        ):
            for x in range(5):
                await asyncio.sleep(2)
                await gateway.async_get_chemistry()
                new_data = gateway.get_data()
                new_ph_data = new_data[DATA.KEY_CHEMISTRY]["ph_setpoint"]
                new_orp_data = new_data[DATA.KEY_CHEMISTRY]["orp_setpoint"]
                if new_ph_data["value"] == ph or new_orp_data["value"] == orp:
                    break
                elif x == 4:
                    print("Failed to confirm updated chemistry values.")
                    return 128

            if ph is not None:
                print(vFormat(new_ph_data))
            if orp is not None:
                print(vFormat(new_orp_data))

            return 0
        return 128

    async def async_set_chem_data():
        if (
            args.ch is None
            and args.ta is None
            and args.cya is None
            and args.salt is None
        ):
            set_chem_data_parser.error("At least one argument required.")

        try:
            if args.ch is not None:
                DB.CHEM_CALCIUM_HARDNESS.validate(args.ch)
            ch = args.ch
            if args.ta is not None:
                DB.CHEM_TOTAL_ALKALINITY.validate(args.ta)
            ta = args.ta
            if args.cya is not None:
                DB.CHEM_CYANURIC_ACID.validate(args.cya)
            cya = args.cya
            if args.salt is not None:
                DB.CHEM_SALT_TDS.validate(args.salt)
            salt = args.salt
        except ValueError:
            set_chem_data_parser.error("Invalid chemistry value.")

        if await gateway.async_set_chem_data(
            calcium_harness=ch,
            total_alkalinity=ta,
            cya=cya,
            salt_tds_ppm=salt,
        ):
            for x in range(5):
                await asyncio.sleep(2)
                await gateway.async_get_chemistry()
                new_data = gateway.get_data()
                new_ch_data = new_data[DATA.KEY_CHEMISTRY]["calcium_harness"]
                new_ta_data = new_data[DATA.KEY_CHEMISTRY]["total_alkalinity"]
                new_cya_data = new_data[DATA.KEY_CHEMISTRY]["cya"]
                new_salt_data = new_data[DATA.KEY_CHEMISTRY]["salt_tds_ppm"]
                if (
                    new_ch_data["value"] == ch
                    or new_ta_data["value"] == ta
                    or new_cya_data["value"] == cya
                    or new_salt_data["value"] == salt
                ):
                    break
                elif x == 3:
                    print("Failed to confirm updated chemistry values.")
                    return 128

            await asyncio.sleep(3)
            await gateway.async_get_chemistry()
            new_data = gateway.get_data()
            if ch is not None:
                print(vFormat(new_data[DATA.KEY_CHEMISTRY]["calcium_harness"]))
            if ta is not None:
                print(vFormat(new_data[DATA.KEY_CHEMISTRY]["total_alkalinity"]))
            if cya is not None:
                print(vFormat(new_data[DATA.KEY_CHEMISTRY]["cya"]))
            if salt is not None:
                print(vFormat(new_data[DATA.KEY_CHEMISTRY]["salt_tds_ppm"]))

            return 0
        return 128

    async def async_get_json():
        print(json.dumps(gateway.get_data(), indent=2))
        return 0

    option_parser = argparse.ArgumentParser(
        prog="screenlogicpy", description="Interface for Pentair Screenlogic gateway"
    )

    option_parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Enables verbose output. Additional 'v's increase logging up to '-vvv' for DEBUG logging",
    )
    option_parser.add_argument(
        "-i",
        "--ip",
        help="Bypasses discovery and specifies the ip address of the protocol adapter",
    )
    option_parser.add_argument(
        "-p", "--port", default=80, help="Specifies the port of the protocol adapter"
    )

    subparsers = option_parser.add_subparsers(dest="action")

    # Discover command
    # pylint: disable=unused-variable
    discover_parser = subparsers.add_parser(  # noqa F841
        "discover", help="Attempt to discover all available ScreenLogic gateways"
    )

    # Get options
    get_parser = subparsers.add_parser("get", help="Gets the specified value or state")
    get_subparsers = get_parser.add_subparsers(dest="get_option")
    get_subparsers.required = True

    ARGUMENT_CIRCUIT_NUM = {
        "dest": "circuit_num",
        "metavar": "CIRCUIT_NUM",
        "type": int,
        "help": "Circuit number",
    }
    get_circuit_parser = get_subparsers.add_parser(
        "circuit", aliases=["c"], help="Get the state of the specified circuit"
    )
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
    get_heat_mode_parser = get_subparsers.add_parser(
        "heat-mode", aliases=["hm"], help="Get the heat mode for the specified body"
    )
    get_heat_mode_parser.add_argument(**ARGUMENT_BODY)
    get_heat_mode_parser.set_defaults(async_func=async_get_heat_mode)

    get_heat_temp_parser = get_subparsers.add_parser(
        "heat-temp",
        aliases=["ht"],
        help="Get the target temperature for the specified body",
    )
    get_heat_temp_parser.add_argument(**ARGUMENT_BODY)
    get_heat_temp_parser.set_defaults(async_func=async_get_heat_temp)

    get_heat_state_parser = get_subparsers.add_parser(
        "heat-state",
        aliases=["hs"],
        help="Get the current heating state for the specified body",
    )
    get_heat_state_parser.add_argument(**ARGUMENT_BODY)
    get_heat_state_parser.set_defaults(async_func=async_get_heat_state)

    get_current_temp_parser = get_subparsers.add_parser(
        "current-temp",
        aliases=["t"],
        help="Get the current temperature for the specified body",
    )
    get_current_temp_parser.add_argument(**ARGUMENT_BODY)
    get_current_temp_parser.set_defaults(async_func=async_get_current_temp)

    get_json_parser = get_subparsers.add_parser(
        "json", aliases=["j"], help="Return the full data dict as JSON"
    )
    get_json_parser.set_defaults(async_func=async_get_json)

    # Set options
    set_parser = subparsers.add_parser(
        "set", help="Sets the specified option, state, or value"
    )
    set_subparsers = set_parser.add_subparsers(dest="set_option")
    set_subparsers.required = True

    on_off_options = optionsFromDict(ON_OFF.NAME_FOR_NUM)
    set_circuit_parser = set_subparsers.add_parser(
        "circuit",
        aliases=["c"],
        help="Set the specified circuit to the specified state",
    )
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
    set_color_light_parser = set_subparsers.add_parser(
        "color-lights",
        aliases=["cl"],
        help="Send the specified color lights or IntelliBrite command",
    )
    set_color_light_parser.add_argument(
        "mode",
        metavar="MODE",
        type=str,
        choices=cl_options,
        help=f"Color lights command, color or show. One of :{cl_options}",
    )
    set_color_light_parser.set_defaults(async_func=async_set_color_light)

    set_heat_mode_parser = set_subparsers.add_parser(
        "heat-mode",
        aliases=["hm"],
        help="Set the specified heat mode for the specified body",
    )
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

    set_heat_temp_parser = set_subparsers.add_parser(
        "heat-temp",
        aliases=["ht"],
        help="Set the specified target temperature for the specified body",
    )
    set_heat_temp_parser.add_argument(**ARGUMENT_BODY)
    set_heat_temp_parser.add_argument(
        "temp",
        type=int,
        metavar="TEMP",
        help="Temperature to set in same unit of measurement as controller settings",
    )
    set_heat_temp_parser.set_defaults(async_func=async_set_heat_temp)

    set_scg_setpoint_parser = set_subparsers.add_parser(
        "salt-generator",
        aliases=["scg"],
        help="Set the SCG output level(s) for the pool and/or spa",
    )
    set_scg_setpoint_parser.add_argument(
        "-p",
        "--pool",
        type=int,
        metavar="OUTPUT",
        default=None,
        help="Chlorinator output for when system is in POOL mode. 0-100",
    )
    set_scg_setpoint_parser.add_argument(
        "-s",
        "--spa",
        type=int,
        metavar="OUTPUT",
        default=None,
        help="Chlorinator output for when system is in SPA mode. 0-100",
    )
    set_scg_setpoint_parser.set_defaults(async_func=async_set_scg_setpoint)

    set_scg_super_parser = set_subparsers.add_parser(
        "super-chlorinate", aliases=["sup"], help="Configure super chlorination"
    )
    set_scg_super_parser.add_argument(
        "-s",
        "--state",
        type=str,
        choices=on_off_options,
        default=None,
        help=f"State of super chlorination. One of {on_off_options}",
    )
    set_scg_super_parser.add_argument(
        "-t",
        "--time",
        type=int,
        metavar="HOURS",
        default=None,
        help=f"Time in hours to run super chlorination. {DB.SC_RUNTIME.min}-{DB.SC_RUNTIME.max}",
    )
    set_scg_super_parser.set_defaults(async_func=async_set_scg_super)

    set_chem_setpoint_parser = set_subparsers.add_parser(
        "chem-setpoint",
        aliases=["csp"],
        help="Set the specified pH and/or ORP setpoint(s) for the IntelliChem system",
    )
    set_chem_setpoint_parser.add_argument(
        "-p",
        "--ph",
        type=float,
        default=None,
        help=(
            "PH set point for IntelliChem. "
            f"{DB.CHEM_SETPOINT_PH.min}-{DB.CHEM_SETPOINT_PH.max}"
        ),
    )
    set_chem_setpoint_parser.add_argument(
        "-o",
        "--orp",
        type=int,
        default=None,
        help=(
            "ORP set point for IntelliChem. "
            f"{DB.CHEM_SETPOINT_ORP.min}-{DB.CHEM_SETPOINT_ORP.max}"
        ),
    )
    set_chem_setpoint_parser.set_defaults(async_func=async_set_chem_setpoint)

    set_chem_data_parser = set_subparsers.add_parser(
        "chem-data",
        aliases=["cd"],
        help="Set various chemistry values for LSI calculation in the IntelliChem system",
    )
    set_chem_data_parser.add_argument(
        "-c",
        "--ch",
        type=int,
        default=None,
        help="Calcium hardness for LSI calculations in the IntelliChem system.",
    )
    set_chem_data_parser.add_argument(
        "-t",
        "--ta",
        type=int,
        default=None,
        help="Total alkalinity for LSI calculations in the IntelliChem system.",
    )
    set_chem_data_parser.add_argument(
        "-y",
        "--cya",
        type=int,
        default=None,
        help="Cyanuric acid for LSI calculations in the IntelliChem system.",
    )
    set_chem_data_parser.add_argument(
        "-s",
        "--salt",
        type=int,
        default=None,
        help="Salt or total dissolved solids (if not using a SCG) for LSI calculations in the IntelliChem system.",
    )
    set_chem_data_parser.set_defaults(async_func=async_set_chem_data)

    args = option_parser.parse_args(cli_args)

    if args.verbose == 2:
        logging.basicConfig(
            level=logging.INFO,
        )
    elif args.verbose == 3:
        logging.basicConfig(
            format="%(asctime)s %(levelname)-8s %(message)s",
            level=logging.DEBUG,
            datefmt="%Y-%m-%d %H:%M:%S",
        )

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
            if args.verbose:
                print(f"Version: {gateway.version}")

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
