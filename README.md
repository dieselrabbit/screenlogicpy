# screenlogicpy

`screenlogicpy` is an interface for Pentair ScreenLogic connected pool controllers over IP via python.

# Installation

The `screenlogicpy` package can be installed from PyPI using `pip`.

    pip install screenlogicpy

# Library usage

The `ScreenLogicGateway` class is the primary interface.

    from screenlogicpy import ScreenLogicGateway
    gateway = ScreenLogicGateway("192.168.x.x")

## Gateway Discovery

The `discovery` module's `discover()` function can be used to get a list of all discovered ScreenLogic gateways on the local network. Each gateway is represented as a `dict` object that can then be directly used to instanciate a `ScreenLogicGateway` class.

    from screenlogicpy import ScreenLogicGateway, discovery

    hosts = discovery.discover()
    if len(hosts) > 0:
        gateway = ScreenLogicGateway(**hosts[0])
        data = gateway.get_data()
    else:
        print("No gateways found")

## Querying data

The `ScreenLogicGateway` class updates all data at once from the ScreenLogic gateway. That data is cached as a `dict` object for continued reference by the consuming application. The consuming application may get this data at anytime with the `get_data()` method.

    data = gateway.get_data()

## Updating the data

When instanciated, the `ScreenLogicGateway` class object will perform an initial update of all available data to populate it's internal cache. A consuming application may request further updates of the internal data with the `update()` method.

    gateway.update()

After `update()`, The consuming application may then query the new data with `get_data()`.

**Note:** This update consists of:

1. Connecting and logging-on to the specified ScreenLogic gateway.
2. Sending requests for
    1. Pool controller configuration
    2. Current pool status
    3. Detailed information for *each* configured pump
    4. Detailed pool chemistry information
3. Closing the connection to the gateway.

**Warning:** This method is not rate-limited. The calling application is responsible for maintaining reasonable intervals between updates.

## Performing actions

The following actions can be performed with methods on the `ScreenLogicGateway` object:

- Set a specific circuit to on or off
- Set a heating mode for a specific body of water (spa/pool)
- Set a target heating temperature for a specific body of water (spa/pool)
- Select various color-enabled lighting options

Each method will `return True` if the operation reported no exceptions.
**Note:** The methods do not confirm the requested action is now in effect on the pool controller.

## Turning a circuit ON or OFF

A circuit can be requested to be turned on or off with the `set_circuit()` method. `set_circuit` takes two required arguments, `circuitID` which is the id number of the circuit as an `int`, and `circuitState` which represents the desired new state of the circuit, as an `int`: 0 = off, 1 = on.

    success = gateway.set_circuit(circuitID, circuitState)

## Setting a heating mode

The desired heating mode can be set per body of water (pool or spa) with `set_heat_mode()`. `set_heat_mode` takes two required arguments, `body` as an `int`: 0 = Pool, 1 = Spa, and `mode` as an `int` of the desired heating mode: 0 = Off, 1 = Solar, 2 = Solar Prefered, 3 = Heater, 4 = Don't Change.

    success = gateway.set_heat_mode(body, mode)

## Setting a target temperature

The target heating temperature can be set per body of water (pool or spa) with `set_heat_temp()`. `set_heat_temp` takes two required arguments, `body` as an `int`: 0 = Pool, 1 = Spa, and `temp` as an `int` of the desired target temperature.

    success = gateway.set_heat_temp(body, temp)

## Setting light colors or shows

Colors or color-shows can be set for compatible color-enable lighting with `set_color_lights()`. `set_color_lights` takes one required argument, `light_command` as an `int` representing the desired command/show/color:
`0` = All Off, `1`= All On, `2` = Color Set, `3` = Color Sync, `4` = Color Swim, `5` = Party, `6` = Romance, `7` = Caribbean, `8` = American, `9` = Sunset, `10` = Royal, `11` = Save, `12` = Recall, `13` = Blue, `14` =Green, `15` = Red, `16` = White, `17` = Magenta, `18` = Thumper, `19` = Next, `20` = Reset, `21` = Hold.

    success = gateway.set_color_lights(light_command)

# Command line

Screenlogicpy can also be used via the command line. The primary design is for the command line output to be consume/parsed by other applications and thus by default is not very human-readable. For more human-friendly output, specify the `-v` option.

## Basic usage

    screenlogicpy

Without any arguments, screenlogicpy will attempt to discover a gateway on the LAN, and display a human readable "dashboard" of the current state of their pool.

    $ screenlogicpy
    Discovered 'Pentair: XX-XX-XX' at 192.168.XX.XX:80
    EasyTouch2 8
    **************************
    Pool temperature is last 58°F
    Pool Heat Set Point: 86°F
    Pool Heat: Off
    Pool Heat Mode: Off
    --------------------------
    Spa temperature is last 97°F
    Spa Heat Set Point: 97°F
    Spa Heat: Off
    Spa Heat Mode: Heater
    --------------------------
    **************************
     ID  STATE  NAME
    --------------------------
    500    Off  Spa
    501    Off  Waterfall
    502    Off  Pool Light
    503    Off  Spa Light
    504    Off  Cleaner
    505     On  Pool Low
    506    Off  Yard Light
    507    Off  Aux 6
    508    Off  Pool High
    510    Off  Feature 1
    511    Off  Feature 2
    512    Off  Feature 3
    513    Off  Feature 4
    514    Off  Feature 5
    515    Off  Feature 6
    516    Off  Feature 7
    517    Off  Feature 8
    519    Off  AuxEx
    **************************

## Argument usage

    screenlogicpy [-h] [-v] [-i IP] [-p PORT] {discover,get,set} ...

## Optional arguments

### `-h, --help`

Argparse `help` command. Available at any stage of positional commands.

### `-v, --verbose`

Tells screenlogicpy to be a little more verbose in it's output. Friendlier for humans.

### `-i, --ip`

    screenlogicpy -i xxx.xxx.xxx.xxx

Specify the IP address of the ScreenLogic gateway to connect to. **Note:** If the IP address is not specified, screenlogicpy will attempt to discover ScreenLogic gateways on the local network, and connect to the first one that responds. This is generally fine if you only have one ScreenLogic gateway.

### `-p, --port`

    screenlogicpy -i xxx.xxx.xxx.xxx -p xx

Specify the port of the ScreenLogic gateway to connect to. Needs to be used in conjunction with `-i, --ip` option.

## Positional arguments

### `discover`

    screenlogicpy discover

Attempts to discover ScreenLogic gateways on the local network via UDP broadcast. Returns `[ip address]:[port]` of each discovered ScreenLogic gateway, one per line.

### `get`

    screenlogicpy get {circuit,c,heat-mode,hm,heat-temp,ht,heat-state,hs,current-temp,t,json,j}

The get option is use with additional options to return the current state of the additional option specified.

#### get `circuit, c`

    screenlogicpy get circuit [circuit number]

Returns 1 for on and 0 for off

#### get `heat-mode, hm`

    screenlogicpy get heat-mode [body]

Returns the current heating mode for the specified body of water.
**Note:** `[body]` can be body number (`0` or `1`) or `pool` or `spa`.

#### get `heat-temp, ht`

    screenlogicpy get heat-temp [body]

Returns the current target heating temperature for the specified body of water.
**Note:** `[body]` can be body number (`0` or `1`) or `pool` or `spa`.

#### get `heat-state, hs`

    screenlogicpy get heat-state [body]

Returns the current state of the heater for the specified boty of water. The current state will match the heat mode when heating is active, otherwise will be 0 (off).
**Note:** `[body]` can be body number (`0` or `1`) or `pool` or `spa`.

#### get `current-temp, t`

    screenlogicpy get current-temp [body]

Returns the current temperature for the specified body of water. This is actually the last-known temperature from when that body of water was active (Pool or Spa)
**Note:** `[body]` can be body number (`0` or `1`) or `pool` or `spa`.

#### get `json, j`

    screenlogicpy get json

Returns a json dump of all data cached in the data `dict`.

### `set`

    screenlogicpy set {circuit,c,color-lights,cl,heat-mode,hm,heat-temp,ht} ...

All `set` commands work like their corresponding `get` commands, but take an additional argument or arguments for the desired setting.

#### set `circuit, c`

    screenlogicpy set circuit [circuit number] [circuit state]

Sets the specified circuit to the specified circuit state. **Note:** `[circuit state]` can be number state (`0` or `1`) or `on`, or `off`.

#### set `heat-mode, hm`

    screenlogicpy set heat-mode [body] [heat mode]

Sets the desired heating mode for the specified body of water.
**Note:** `[body]` can be body number (`0` or `1`) or `pool` or `spa`. `[heat mode]` can be any one of: [`0` or `off`, `1` or `solar`, `2` or `solar_preferred`, `3` or `heater`, `4` or `dont_change`]

#### set `heat-temp, ht`

    screenlogicpy set heat-temp [body] [heat temp]

Sets the desired target heating temperature for the specified body of water.
**Note:** `[body]` can be body number or `pool` or `spa`. `[heat temp]` is an `int` representing the desired target temperature.

**v0.3.0+:**

#### set `color-lights, cl`

    screenlogicpy set color-lights [color mode]

Sets a color mode for *all* color-capable lights configured on the pool controller. **Note:** `[color mode]` can be one of: [
`0` or  `all_off`, `1` or `all_on`, `2` or `color_set`, `3` or `color_sync`, `4` or `color_swim`, `5` or `party`, `6` or `romance`, `7` or `caribbean`, `8` or `american`, `9` or `sunset`, `10` or `royal`, `11` or `save`, `12` or `recall`, `13` or `blue`, `14` or `green`, `15` or `red`, `16` or `white`, `17` or `magenta`, `18` or `thumper`, `19` or `next_mode`, `20` or `reset`, `21` or `hold`]

## Acknowledgements

Based on https://github.com/keithpjolley/soipip

The protocol and codes are documented fairly well here: https://github.com/ceisenach/screenlogic_over_ip
