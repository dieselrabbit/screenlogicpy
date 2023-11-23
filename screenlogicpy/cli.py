import argparse
import asyncio
from datetime import datetime
import json
import logging
import string

from screenlogicpy import __version__
from screenlogicpy.discovery import async_discover
from screenlogicpy.gateway import ScreenLogicGateway
from screenlogicpy.const.common import (
    ON_OFF,
    SL_GATEWAY_IP,
    SL_GATEWAY_NAME,
    SL_GATEWAY_PORT,
    SLIntEnum,
    ScreenLogicException,
)
from screenlogicpy.data import build_response_collection, export_response_collection
from screenlogicpy.device_const.chemistry import CHEM_RANGE
from screenlogicpy.device_const.circuit import INTERFACE
from screenlogicpy.device_const.heat import HEAT_MODE
from screenlogicpy.device_const.system import BODY_TYPE, COLOR_MODE
from screenlogicpy.device_const.scg import SCG_RANGE
from screenlogicpy.const.data import ATTR, DEVICE, GROUP, VALUE


def file_format(name: str):
    table = str.maketrans(" ", "-", string.punctuation)
    return name.translate(table).lower()


# Entry function
async def cli(cli_args):
    """Handle command line args"""

    gateway = ScreenLogicGateway()

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
        state = (ON_OFF.parse(args.state)).value
        circuit_id = int(args.circuit_num)
        if circuit_id not in gateway.get_data(DEVICE.CIRCUIT):
            print(f"Invalid circuit number: {args.circuit_num}")
            return 4
        await gateway.async_set_circuit(circuit_id, state)
        await gateway.async_update()
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
        await gateway.async_set_heat_mode(body, mode)
        await gateway.async_update()
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
            await gateway.async_set_heat_temp(body, int(args.temp))
            await gateway.async_update()
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
        await gateway.async_set_color_lights(mode)
        print(f"Set color mode to {COLOR_MODE(mode).title}" if args.verbose else mode)
        return 0

    async def async_set_scg_setpoint():
        return await async_set_scg_config(pool=args.pool, spa=args.spa)

    async def async_set_scg_super():
        return await async_set_scg_config(state=args.state, time=args.time)

    async def async_set_scg_config(
        *,
        pool: int | None = None,
        spa: int | None = None,
        state: int | None = None,
        time: int | None = None,
    ):
        if all(
            (
                pool is None,
                spa is None,
                state is None,
                time is None,
            )
        ):
            print("No new chlorinator values. Nothing to do.")
            return 65

        kwargs = {
            VALUE.POOL_SETPOINT: pool,
            VALUE.SPA_SETPOINT: spa,
            VALUE.SUPER_CHLORINATE: state,
            VALUE.SUPER_CHLOR_TIMER: time,
        }

        await gateway.async_set_scg_config(**kwargs)
        # await asyncio.sleep(3)
        await gateway.async_get_scg()
        new_scg_config_data = gateway.get_data(DEVICE.SCG, GROUP.CONFIGURATION)
        print(
            *[
                vFormat(new_scg_config_data[key])
                for key, value in kwargs.items()
                if key in new_scg_config_data and value is not None
            ]
        )
        return 0

    async def async_set_chem_setpoint():
        return await async_set_chem_data(ph=args.ph, orp=args.orp)

    async def async_set_chem_value():
        return await async_set_chem_data(
            calcium_hardness=args.calcium_hardness,
            total_alkalinity=args.total_alkalinity,
            cyanuric_acid=args.cyanuric_acid,
            total_dissolved_solids=args.total_dissolved_solids,
        )

    async def async_set_chem_data(
        *,
        ph: float | None = None,
        orp: int | None = None,
        calcium_hardness: int | None = None,
        total_alkalinity: int | None = None,
        cyanuric_acid: int | None = None,
        total_dissolved_solids: int | None = None,
    ):
        if all(
            (
                ph is None,
                orp is None,
                calcium_hardness is None,
                total_alkalinity is None,
                cyanuric_acid is None,
                total_dissolved_solids is None,
            )
        ):
            print("No new chemistry values. Nothing to do.")
            return 129

        kwargs = {
            VALUE.PH_SETPOINT: ph,
            VALUE.ORP_SETPOINT: orp,
            VALUE.CALCIUM_HARDNESS: calcium_hardness,
            VALUE.TOTAL_ALKALINITY: total_alkalinity,
            VALUE.CYA: cyanuric_acid,
            VALUE.SALT_TDS_PPM: total_dissolved_solids,
        }
        await gateway.async_set_chem_data(**kwargs)
        # await asyncio.sleep(3)
        await gateway.async_get_chemistry()
        new_chem_config_data = gateway.get_data(DEVICE.INTELLICHEM, GROUP.CONFIGURATION)
        print(
            *[
                vFormat(new_chem_config_data[key])
                for key, value in kwargs.items()
                if key in new_chem_config_data and value is not None
            ]
        )
        return 0

    async def async_get_date_time():
        format = args.format
        await gateway.async_get_datetime()
        timestamp = gateway.get_data(
            DEVICE.CONTROLLER, GROUP.DATE_TIME, VALUE.TIMESTAMP, strict=True
        )
        if format is None:
            print(datetime.fromtimestamp(timestamp))
        else:
            print(datetime.fromtimestamp(timestamp).strftime(format))
        return 0

    async def async_get_auto_dst():
        await gateway.async_get_datetime()
        print(
            vFormat(
                gateway.get_data(DEVICE.CONTROLLER, GROUP.DATE_TIME, VALUE.AUTO_DST)
            )
        )
        return 0

    async def async_set_date_time():
        date_time = (
            datetime.fromisoformat(args.date_time)
            if args.date_time is not None
            else None
        )
        auto_dst = args.auto_dst

        if all(
            (
                date_time is None,
                auto_dst is None,
            )
        ):
            date_time = datetime.now()

        await gateway.async_get_datetime()
        await gateway.async_set_date_time(date_time=date_time, auto_dst=auto_dst)
        await asyncio.sleep(0.5)
        await gateway.async_get_datetime()
        timestamp = gateway.get_data(
            DEVICE.CONTROLLER, GROUP.DATE_TIME, VALUE.TIMESTAMP, strict=True
        )
        print(f"Controller time now: {datetime.fromtimestamp(timestamp)}")
        return 0

    async def async_export_data_collection():
        sl_ver = file_format(__version__)
        pa_ver = file_format(gateway.version)
        model = file_format(gateway.controller_model)
        equip = gateway.equipment_flags.value
        filename = f"slpy{sl_ver}_{pa_ver}_{model}_{equip}.json"
        response_collection = build_response_collection(
            gateway.get_debug(), gateway.get_data()
        )
        export_response_collection(response_collection, filename)
        return 0

    async def async_get_json():
        print(json.dumps(gateway.get_data(), indent=2))
        return 0

    # Begin Parser Setup
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

    # pylint: disable=unused-variable
    export_parser = subparsers.add_parser(
        "export",
        help="Exports complete response collection to slpy[libversion]\_[adapter-firmware]\_[controller-model]\_[equipment-flags].json",
    )  # noqa F841

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

    body_options = BODY_TYPE.parsable_values()
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

    get_date_time_parser = get_subparsers.add_parser("date-time", aliases=["dt"])
    get_date_time_parser.add_argument(
        "-f",
        "--format",
        default=None,
        type=str,
        help="Optional format string to format the datetime value",
    )
    get_date_time_parser.set_defaults(async_func=async_get_date_time)

    get_auto_dst_parser = get_subparsers.add_parser("auto-dst", aliases=["dst"])
    get_auto_dst_parser.set_defaults(async_func=async_get_auto_dst)

    get_json_parser = get_subparsers.add_parser("json", aliases=["j"])
    get_json_parser.set_defaults(async_func=async_get_json)

    # Set options
    set_parser = subparsers.add_parser(
        "set", help="Sets the specified option, state, or value"
    )
    set_subparsers = set_parser.add_subparsers(dest="set_option")
    set_subparsers.required = True

    on_off_options = ON_OFF.parsable_values()
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

    cl_options = COLOR_MODE.parsable_values()
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
    hm_options = HEAT_MODE.parsable_values()
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
        help=f"Chlorinator output for when system is in POOL mode. {SCG_RANGE.POOL_SETPOINT.minimum}-{SCG_RANGE.POOL_SETPOINT.maximum}",
    )
    set_scg_setpoint_parser.add_argument(
        "-s",
        "--spa",
        type=int,
        metavar="OUTPUT",
        default=None,
        help=f"Chlorinator output for when system is in SPA mode. {SCG_RANGE.SPA_SETPOINT.minimum}-{SCG_RANGE.SPA_SETPOINT.maximum}",
    )
    set_scg_setpoint_parser.set_defaults(async_func=async_set_scg_setpoint)

    set_scg_super_parser = set_subparsers.add_parser(
        "super-chlorinate", aliases=["sc"], help="Configure super chlorination"
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
        help=f"Time in hours to run super chlorination. {SCG_RANGE.SUPER_CHLOR_RT.minimum}-{SCG_RANGE.SUPER_CHLOR_RT.maximum}",
    )
    set_scg_super_parser.set_defaults(async_func=async_set_scg_super)

    set_chem_setpoint_parser = set_subparsers.add_parser(
        "chemistry-setpoint",
        aliases=["cs"],
        help="Set the specified pH and/or ORP setpoint(s) for the IntelliChem system",
    )

    set_chem_setpoint_parser.add_argument(
        "-p",
        "--ph",
        type=float,
        default=None,
        help=(
            "PH set point for IntelliChem. "
            f"{CHEM_RANGE.PH_SETPOINT.minimum}-{CHEM_RANGE.PH_SETPOINT.maximum}"
        ),
    )

    set_chem_setpoint_parser.add_argument(
        "-o",
        "--orp",
        type=int,
        default=None,
        help=(
            "ORP set point for IntelliChem. "
            f"{CHEM_RANGE.ORP_SETPOINT.minimum}-{CHEM_RANGE.ORP_SETPOINT.maximum}"
        ),
    )
    set_chem_setpoint_parser.set_defaults(async_func=async_set_chem_setpoint)

    set_chem_data_parser = set_subparsers.add_parser(
        "chemistry-value",
        aliases=["cv"],
        help="Set various user-supplied chemistry values for LSI calculation in the IntelliChem system",
    )
    set_chem_data_parser.add_argument(
        "-ch",
        "--calcium-hardness",
        type=int,
        default=None,
        help="Calcium hardness for LSI calculations in the IntelliChem system.",
    )
    set_chem_data_parser.add_argument(
        "-ta",
        "--total-alkalinity",
        type=int,
        default=None,
        help="Total alkalinity for LSI calculations in the IntelliChem system.",
    )
    set_chem_data_parser.add_argument(
        "-cya",
        "--cyanuric-acid",
        type=int,
        default=None,
        help="Cyanuric acid for LSI calculations in the IntelliChem system.",
    )
    set_chem_data_parser.add_argument(
        "-tds",
        "--total-dissolved-solids",
        type=int,
        default=None,
        help="Salt or total dissolved solids (if not using a SCG) for LSI calculations in the IntelliChem system.",
    )
    set_chem_data_parser.set_defaults(async_func=async_set_chem_value)

    set_date_time_parser = set_subparsers.add_parser(
        "date-time",
        aliases=["dt"],
        help="Sets pool controller date/time to host's date and time.",
    )
    set_date_time_parser.add_argument(
        "-dt",
        "--date-time",
        default=None,
        metavar="ISO_8601",
        type=str,
        help="Specify a datetime with an ISO 8601 formatted string",
    )
    set_date_time_parser.add_argument(
        "-dst",
        "--auto-dst",
        default=None,
        choices=on_off_options,
        type=str,
        help="Automatic adjustment of system time for Daylight Saving Time",
    )
    set_date_time_parser.set_defaults(async_func=async_set_date_time)

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

        await gateway.async_connect(**host)

        await gateway.async_update()

        if DEVICE.CONTROLLER not in gateway.get_data():
            return 1

        if args.action == "export":
            result = await async_export_data_collection()
            return result

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
                if circuit[ATTR.INTERFACE] != INTERFACE.DONT_SHOW:
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

    except ScreenLogicException as err:
        print(err)
        return -1
