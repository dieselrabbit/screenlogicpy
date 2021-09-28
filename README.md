# screenlogicpy

`screenlogicpy` is an interface for Pentair ScreenLogic connected pool controllers over IP via python using asyncio.

# Installation

The `screenlogicpy` package can be installed from PyPI using `pip`.

    pip install screenlogicpy

# Library usage

***New for v0.5.0:** The screenlogicpy library has moved over to using asyncio for all network I/O. Relevent methods now require the **async/await** syntax.*

The `ScreenLogicGateway` class is the primary interface.

    from screenlogicpy import ScreenLogicGateway

    gateway = ScreenLogicGateway("192.168.x.x")
*Changed in v0.5.0: Instanciating the gateway no longer automatically connects to the protocol adapter or performs an initial update.*

## Connecting to a ScreenLogic Protocol Adapter

Once instanciated, use `async_connect()` to connect and logon to the ScreenLogic protocol adapter.

    success = await gateway.async_connect()

This method also performs the initial polling of the pool controller configuration.  
*New in v0.5.0*

## Polling the data

Once connected, all available data can be polled with the `async_update()` coroutine.

    await gateway.async_update()

This update consists of sending requests for:

1. Current pool status
2. Detailed information for *each* configured pump
3. Detailed pool chemistry information
4. Status ans settings for any configured salt chlorine generators

**Warning:** This method is not rate-limited. The calling application is responsible for maintaining reasonable intervals between updates.  
*Changed in v0.5.0: This method is now an async coroutine and no longer disconnects from the protocol adapter after polling the data.*

## Using the data

The `ScreenLogicGateway` class updates all data at once from the ScreenLogic protocol adapter. That data is cached as a `dict` object for continued reference by the consuming application. The consuming application may get this data at anytime with the `get_data()` method.

    data = gateway.get_data()

## Disconnecting

When done, use `async_disconnect()` to close the connection to the protocol adapter.

    await gateway.async_disconnect()  
*New in v0.5.0*

## Gateway Discovery

The `discovery` module's `async_discover()` function can be used to get a list of all discovered ScreenLogic protocol adapters on the local network. Each protocol adapter is represented as a `dict` object that can then be directly used to instanciate a `ScreenLogicGateway` class.

    hosts = await discovery.async_discover()
*Changed in v0.5.0: This method is now an async coroutine.*

## Example

    from screenlogicpy import ScreenLogicGateway, discovery

    hosts = await discovery.async_discover()
    if len(hosts) > 0:
        gateway = ScreenLogicGateway(**hosts[0])
        if await gateway.async_connect():
            await gateway.async_update()
            await gateway.async_disconnect()
            data = gateway.get_data()
    else:
        print("No gateways found")

## Performing actions

The following actions can be performed with methods on the `ScreenLogicGateway` object:

- Set a specific circuit to on or off
- Set a heating mode for a specific body of water (spa/pool)
- Set a target heating temperature for a specific body of water (spa/pool)
- Select various color-enabled lighting options

Each method will `return True` if the operation reported no exceptions.
**Note:** The methods do not confirm the requested action is now in effect on the pool controller.

## Turning a circuit ON or OFF

A circuit can be requested to be turned on or off with the `async_set_circuit()` method. `async_set_circuit` takes two required arguments, `circuitID` which is the id number of the circuit as an `int`, and `circuitState` which represents the desired new state of the circuit, as an `int`. See [Circuit State](#circuit-state) below.

    success = await gateway.async_set_circuit(circuitID, circuitState)
*Changed in v0.5.0: This method is now an async coroutine.*

## Setting a heating mode

The desired heating mode can be set per body of water (pool or spa) with `async_set_heat_mode()`. `async_set_heat_mode` takes two required arguments, `body` as an `int` representing the [body of water](#body), and `mode` as an `int` of the desired [heating mode](#heat-modes).

    success = await gateway.async_set_heat_mode(body, mode)
*Changed in v0.5.0: This method is now an async coroutine.*

## Setting a target temperature

The target heating temperature can be set per body of water (pool or spa) with `async_set_heat_temp()`. `async_set_heat_temp` takes two required arguments, `body` as an `int` representing the [body of water](#body), and `temp` as an `int` of the desired target temperature.

    success = await gateway.async_set_heat_temp(body, temp)
*Changed in v0.5.0: This method is now an async coroutine.*

## Setting light colors or shows

Colors or color-shows can be set for compatible color-enable lighting with `async_set_color_lights()`. `async_set_color_lights` takes one required argument, `light_command` as an `int` representing the desired [command/show/color](#color-modes)

    success = await gateway.async_set_color_lights(light_command)
*Changed in v0.5.0: This method is now an async coroutine.*

## Setting chlorinator output levels
Chlorinator output levels can be set with `async_set_scg_config()`.  `async_set_scg_config` takes two `int` arguments, `pool_output` and `spa_output`.
    
    success = await gateway.async_set_scg_config(pool_output, spa_output)  
*New in v0.5.0*

# Command line

Screenlogicpy can also be used via the command line. The primary design is for the command line output to be consumed/parsed by other applications and thus by default is not very human-readable. For more human-friendly output, specify the `-v, --verbose` option.

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

Specify the IP address of the ScreenLogic protocol adapter to connect to.  
**Note:** If the IP address is not specified, screenlogicpy will attempt to discover ScreenLogic protocol adapters on the local network, and connect to the first one that responds. This is generally fine if you only have one ScreenLogic protocol adapter.

### `-p, --port`

    screenlogicpy -i xxx.xxx.xxx.xxx -p xx

Specify the port of the ScreenLogic protocol adapter to connect to. Needs to be used in conjunction with `-i, --ip` option.

## Positional arguments

### `discover`

    screenlogicpy discover

Attempts to discover ScreenLogic protocol adapters on the local network via UDP broadcast. Returns `[ip address]:[port]` of each discovered ScreenLogic protocol adapter, one per line.

### `get`

    screenlogicpy get {circuit,c,heat-mode,hm,heat-temp,ht,heat-state,hs,current-temp,t,json,j}

The get option is use with additional options to return the current state of the additional option specified.

#### get `circuit, c`

    screenlogicpy get circuit [circuit number]

Returns 1 for on and 0 for off

#### get `heat-mode, hm`

    screenlogicpy get heat-mode [body]

Returns the current heating mode for the specified body of water.  
**Note:** `[body]` can be an `int` or `string` representing the [body of water](#body).

#### get `heat-temp, ht`

    screenlogicpy get heat-temp [body]

Returns the current target heating temperature for the specified body of water.  
**Note:** `[body]` can be an `int` or `string` representing the [body of water](#body).

#### get `heat-state, hs`

    screenlogicpy get heat-state [body]

Returns the current state of the heater for the specified boty of water. The current state will match the heat mode when heating is active, otherwise will be 0 (off).  
**Note:** `[body]` can be an `int` or `string` representing the [body of water](#body).

#### get `current-temp, t`

    screenlogicpy get current-temp [body]

Returns the current temperature for the specified body of water. This is actually the last-known temperature from when that body of water was active (Pool or Spa)  
**Note:** `[body]` can be an `int` or `string` representing the [body of water](#body).

#### get `json, j`

    screenlogicpy get json

Returns a json dump of all data cached in the data `dict`.

### `set`

    screenlogicpy set {circuit,c,color-lights,cl,heat-mode,hm,heat-temp,ht} ...

All `set` commands work like their corresponding `get` commands, but take an additional argument or arguments for the desired setting.

#### set `circuit, c`

    screenlogicpy set circuit [circuit number] [circuit state]

Sets the specified circuit to the specified circuit state.  
**Note:** `[circuit state]` can be an `int` or `string` representing the desired [circuit state](#circuit-state).

#### set `heat-mode, hm`

    screenlogicpy set heat-mode [body] [heat mode]

Sets the desired heating mode for the specified body of water.  
**Note:** `[body]` can be an `int` or `string` representing the [body of water](#body). `[heat mode]` can be an `int` or `string` representing the desired [heat mode](#heat-modes)

#### set `heat-temp, ht`

    screenlogicpy set heat-temp [body] [heat temp]

Sets the desired target heating temperature for the specified body of water.  
**Note:** `[body]` can be an `int` or `string` representing the [body of water](#body). `[heat temp]` is an `int` representing the desired target temperature.

#### set `color-lights, cl`

    screenlogicpy set color-lights [color mode]

Sets a color mode for *all* color-capable lights configured on the pool controller.  
**Note:** `[color mode]` can be either the `int` or `string` representation of a [color mode](#color-modes).  
*New in v0.3.0*

#### set `salt-generator, scg`

    screenlogicpy set salt-generator [pool_pct] [spa_pct]

Sets the chlorinator output levels for the pool and spa. Pentair treats spa output level as a percentage of the pool's output level.  
**Note:** `[pool_pct]` can be an `int` between `1`-`100`, or `*` to keep the current value. `[spa_pct]` can be an `int` between `1`-`20`, or `*` to keep the current value.  
*New in v0.5.0*

# Reference

### Circuit State

| `int` | `string` | Name |
| ----- | -------- | ---- |
| `0`   | `off`    | Off  |
| `1`   | `on`     | On   |

### Body

| `int` | `string` | Name |
| ----- | -------- | ---- |
| `0`   | `pool`   | Pool |
| `1`   | `spa`    | Spa  |

### Heat Modes

| `int` | `string`          | Name            | Description                                                                                                         |
| ----- | ----------------- | --------------- | ------------------------------------------------------------------------------------------------------------------- |
| `0`   | `off`             | Off             | Heating is off                                                                                                      |
| `1`   | `solar`           | Solar           | Heating will use solar heat to achieve the desired temperature set point.                                           |
| `2`   | `solar_preferred` | Solar Preferred | Heating will use solar if available to achieve the desired temperature set point, otherwise it will use the heater. |
| `3`   | `heater`          | Heater          | Heating will use the heater to achieve the desired temperature set point.                                           |
| `4`   | `dont_change`     | Don't Change    | Don't change the heating mode based on circuit or function changes.                                                 |


### Color Modes

| `int` | `string`     | Name         | Description                                                                                               |
| ----- | ------------ | ------------ | --------------------------------------------------------------------------------------------------------- |
| `0`   | `all_off`    | All Off      | Turns all light circuits off.                                                                             |
| `1`   | `all_on`     | All On       | Turns all light circuits on to their last mode.                                                           |
| `2`   | `color_set`  | Color Set    | Sets light circuits to their pre-set colors as set in the pool controller.                                |
| `3`   | `color_sync` | Color Sync   | Synchronize all IntelliBrite, SAm, SAL, or FIBERworks color changing lights and synchronize their colors. |
| `4`   | `color_swim` | Color Swim   | Cycles through white, magenta, blue and green colors. (Emulates Pentair SAm color changing light.)        |
| `5`   | `party`      | Party        | Rapid color changing building the energy and excitement.                                                  |
| `6`   | `romance`    | Romance      | Slow color transitions creating a mesmerizing and calming effect.                                         |
| `7`   | `caribbean`  | Caribbean    | Transitions between a variety of blues and greens.                                                        |
| `8`   | `american`   | American     | Patriotic red, white and blue transitions.                                                                |
| `9`   | `sunset`     | Sunset       | Dramatic transitions of orange, red and magenta tones.                                                    |
| `10`  | `royal`      | Royal        | Richer, deeper, color tones.                                                                              |
| `11`  | `save`       | Save Color   | Save the exact colors that are being displayed.                                                           |
| `12`  | `recall`     | Recall Color | Recall the saved colors.                                                                                  |
| `13`  | `blue`       | Blue         | Fixed color: Blue                                                                                         |
| `14`  | `green`      | Green        | Fixed color: Green                                                                                        |
| `15`  | `red`        | Red          | Fixed color: Red                                                                                          |
| `16`  | `white`      | White        | Fixed color: White                                                                                        |
| `17`  | `magenta`    | Magenta      | Fixed color: Magenta                                                                                      |
| `18`  | `thumper`    | Thumper      | Toggles the solenoid thumper on MagicStream laminars.                                                     |
| `19`  | `next_mode`  | Next Mode    | Cycle to the next color mode.                                                                             |
| `20`  | `reset`      | Reset        | Reset light modes.                                                                                        |
| `21`  | `hold`       | Hold         | Hold light transitions.                                                                                   |

## Acknowledgements

Inspired by https://github.com/keithpjolley/soipip

The protocol and codes are documented fairly well here: https://github.com/ceisenach/screenlogic_over_ip
