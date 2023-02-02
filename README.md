# screenlogicpy

![PyPI](https://img.shields.io/pypi/v/screenlogicpy) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/screenlogicpy)

`screenlogicpy` is an interface for Pentair ScreenLogic connected pool controllers over IP via python using asyncio.

# Installation

The `screenlogicpy` package can be installed from PyPI using `pip`.

```shell
$ pip install screenlogicpy
```

# Library usage

_New in v0.5.0: The screenlogicpy library has moved over to using asyncio for all network I/O. Relevant methods now require the `async`/`await` syntax._

The `ScreenLogicGateway` class is the primary interface.

```python
from screenlogicpy import ScreenLogicGateway

    gateway = ScreenLogicGateway("192.168.x.x")
```

_Changed in v0.5.0: Instantiating the gateway no longer automatically connects to the protocol adapter or performs an initial update._

## Connecting to a ScreenLogic Protocol Adapter

Once instantiated, use `async_connect()` to connect and logon to the ScreenLogic protocol adapter.

```python
success = await gateway.async_connect()
```

This method also performs the initial polling of the pool controller configuration.  
_New in v0.5.0._

## Polling the pool state

Once connected, all available state information can be polled with the `async_update()` coroutine.

```python
await gateway.async_update()
```

This update consists of sending requests for:

1. Current pool status
2. Detailed information for _each_ configured pump
3. Detailed pool chemistry information
4. Status and settings for any configured salt chlorine generators

**Warning:** This method is not rate-limited. The calling application is responsible for maintaining reasonable intervals between updates. The ScreenLogic protocol adapter may respond with an error message if too many requests are made too quickly.  
_Changed in v0.5.0: This method is now an async coroutine and no longer disconnects from the protocol adapter after polling the data._

## Subscribing to pool state updates

The preferred method for retrieving updated pool data is to subscribe to updates pushed to the gateway by the ScreenLogic system. This reduces network traffic compared to polling, and improves responsiveness to state changes.

To enable push updates, subscribe to a particular message code using `gateway.clients.async_subscribe(callback, message_code)`, passing a callback method to be called when that message is received, and the [message code](#supported-subscribable-messages) to subscribe to. This function returns a callback that can be called to unsubscribe that particular subscription.

`screenlogicpy` will automatically handle subscribing and unsubscribing as a client to the ScreenLogic protocol adapter upon the first callback subscription and last unsub respectively.

```python
from screenlogicpy.const import CODE

def status_updated():
    # Do something with the updated data    

unsub_method = await gateway.clients.async_subscribe(status_updated, CODE.STATUS_CHANGED)
```

Example in `./examples/async_client.py`

Multiple callbacks can be subscribed to a single message code. Additionally, a single global callback may be subscribed to multiple message codes. 
**Note:** Each combination of callback and code will result in a separate unique unsub callback. The calling application is responsible for managing and unsubing all subscribed callbacks as needed.  

### Pushed data

The ScreenLogic system does not make all state information for all equipment available via push messages. The two main state update messages that can be subscribed to are:

- General status update containing
  - Air and water temperature and heater states
  - Basic status indicators such as Freeze mode and active delays
  - Circuit states
  - Basic chemistry information
- IntelliChem controller status update containing
  - Detailed chemistry information

The status of any pumps or salt chlorine generators is not included in any push updates. To supplement this, the different data sets can now be requested individually.  
**_New in v0.7.0._**

## Polling specific data

To update a specific set of data, you can use any of the following methods:

```python
await gateway.async_get_status()  # Updates the basic status of the pool controller. *Same as pushed data
await gateway.async_get_pumps()  # Updates the state of all configured pumps
await gateway.async_get_chemistry()  # Updates the detailed chemistry information from and IntelliChem controller. *Same as pushed data
await gateway.async_get_scg()  # Updates the state of any configured salt chlorine generators
```

Push subscriptions and polling of all or specific data can be used on their own or at the same time.  
**_New in v0.7.0._**

## Using the data

The `ScreenLogicGateway` class caches all data from the ScreenLogic protocol adapter as a single `dict` object for continued reference by the consuming application. This includes any data processed via push or polling. The consuming application may get this data at anytime with the `get_data()` method.

```python
data = gateway.get_data()
```

## Disconnecting

When done, use `async_disconnect()` to close the connection to the protocol adapter.

```python
await gateway.async_disconnect()  
```

_New in v0.5.0._

---

## Gateway Discovery

The `discovery` module's `async_discover()` function can be used to get a list of all discovered ScreenLogic protocol adapters on the local network. Each protocol adapter is represented as a `dict` object that can then be directly used to instanciate a `ScreenLogicGateway` class.

**Note:** Gateway discovery is limited to discovering ScreenLogic protocol adapters on the same subnet.

```python
hosts = await discovery.async_discover()
```

_Changed in v0.5.0: This method is now an async coroutine._

Example in `./examples/async_discovery.py`

## Basic Implementation Example

```python
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
```

Full example in `./examples/gateway.py`

## Performing actions

The following actions can be performed with methods on the `ScreenLogicGateway` object:

- Set a specific circuit to on or off
- Set a heating mode for a specific body of water (spa/pool)
- Set a target heating temperature for a specific body of water (spa/pool)
- Select various color-enabled lighting options
- Set the chlorinator output levels
- Setting IntelliChem chemistry values

Each method will `return True` if the operation reported no exceptions.
**Note:** The methods do not confirm the requested action is now in effect on the pool controller.

## Turning a circuit ON or OFF

A circuit can be requested to be turned on or off with the `async_set_circuit()` method. `async_set_circuit` takes two required arguments, `circuitID` which is the id number of the circuit as an `int`, and `circuitState` which represents the desired new state of the circuit, as an `int`. See [Circuit State](#circuit-state) below.

```python
success = await gateway.async_set_circuit(circuitID, circuitState)
```

_Changed in v0.5.0: This method is now an async coroutine._

---

## Setting a heating mode

The desired heating mode can be set per body of water (pool or spa) with `async_set_heat_mode()`. `async_set_heat_mode` takes two required arguments, `body` as an `int` representing the [body of water](#body), and `mode` as an `int` of the desired [heating mode](#heat-modes).

```python
success = await gateway.async_set_heat_mode(body, mode)
```

_Changed in v0.5.0: This method is now an async coroutine._

## Setting a target temperature

The target heating temperature can be set per body of water (pool or spa) with `async_set_heat_temp()`. `async_set_heat_temp` takes two required arguments, `body` as an `int` representing the [body of water](#body), and `temp` as an `int` of the desired target temperature.

```python
success = await gateway.async_set_heat_temp(body, temp)
```

_Changed in v0.5.0: This method is now an async coroutine._
  
## Setting light colors or shows

Colors or color-shows can be set for compatible color-enable lighting with `async_set_color_lights()`. `async_set_color_lights` takes one required argument, `light_command` as an `int` representing the desired [command/show/color](#color-modes)

```python
success = await gateway.async_set_color_lights(light_command)
```

_Changed in v0.5.0: This method is now an async coroutine._

## Setting chlorinator output levels

Chlorinator output levels can be set with `async_set_scg_config()`.  `async_set_scg_config` takes two `int` arguments, `pool_output` and `spa_output`.

```python
success = await gateway.async_set_scg_config(pool_output, spa_output)  
```

_New in v0.5.0._

## Setting IntelliChem Chemistry values

Chemistry values used in the IntelliChem system can be set with `async_set_chem_data()`. `async_set_chem_data` takes six arguments, `ph_setpoint`, `orp_setpoint`, `calcium`, `alkalinity`, `cyanuric`, and `salt`.  `ph_setpoint` is a `float` and the rest are `int`.

```python
success = await gateway.async_set_chem_data(ph_setpoint, orp_setpoint, calcium, alkalinity, cyanuric, salt)
```

Currently all values are required, even if you only want to change one of them. For this reason, it is recommended that the calling code gathers all the current values first, then updates whichever value(s) are desired before calling `async_set_chem_data()`.

```python
chem_data = gateway.get_data()[DATA.KEY_CHEMISTRY]
ph = chem_data["ph_setpoint"]["value"]
orp = chem_data["orp_setpoint"]["value"]
ch = chem_data["calcium_harness"]["value"]
ta = chem_data["total_alkalinity"]["value"]
ca = chem_data["cya"]["value"]
sa = chem_data["salt_tds_ppm"]["value"]

ph = ...  # Code to update any of the values

success = await gateway.async_set_chem_data(ph, orp, ch, ta, ca, sa)
```

**Note:** Only `ph_setpoint` and `orp_setpoint` are settable through the command line.  
_New in v0.6.0._

## Handling unsolicited messages

With the move to asyncio, `screenlogicpy` can now handle unsolicited messages from the ScreenLogic protocol adapter (messages that are not a direct response to a request from screenlogicpy).
To do so, you need to tell the `ScreenLogicGateway` what message code to listen for and what to do when it is received. You can register a handler with `register_message_handler()` . This method takes the message code to wait for, the async coroutine to schedule when a message is received, and any parameters you want to pass to your handler. Your handler coroutine needs to accept the bytes message itself, and any additional parameters you specified.

**Notes:**

- Currently the `ScreenLogicGateway` must be connected to the protocol adapter before registering a handler.
- Registering a handler in this way does not subscribe the gateway to state updates from the ScreenLogic system.

**Example:**

```python
WEATHER_UPDATE_CODE = 9806
WEATHER_REQUEST_CODE = 9807

async def weather_request(message: bytes, userData: dict):
    result = await gateway.async_send_message(WEATHER_REQUEST_CODE)
    data = process(result)
    print(data)

gateway.register_async_message_handler(WEATHER_UPDATE_CODE, weather_request, userData)
```

Full example in `./examples/async_client.py`  
**_New in v0.7.0._**

## Debug Information

A debug function is available in the `ScreenLogicGateway` class: `get_debug`. This will return a dict with the raw bytes for the last response for each request the gateway performs during an update. This can be useful for debugging the actual responses from the protocol adapter.  
**Note:** Currently only includes polled data.

```python
last_responses = gateway.get_debug()
```

_New in v0.5.5._

# Command line

Screenlogicpy can also be used via the command line. The primary design is for the command line output to be consumed/parsed by other applications and thus by default is not very human-readable. For more human-friendly output, specify the `-v, --verbose` option.

## Basic usage

```shell
$ screenlogicpy
```

Without any arguments, screenlogicpy will attempt to discover a gateway on the LAN, and display a human readable "dashboard" of the current state of their pool.

```shell
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
```

## Argument usage

```text
screenlogicpy [-h] [-v] [-i IP] [-p PORT] {discover,get,set} ...
```

## Optional arguments

### `-h, --help`

Argparse `help` command. Available at any stage of positional commands.

### `-v, --verbose`

Tells screenlogicpy to be a little more verbose in it's output. Friendlier for humans.

### `-i, --ip`

```shell
screenlogicpy -i xxx.xxx.xxx.xxx
```

Specify the IP address of the ScreenLogic protocol adapter to connect to.  
**Note:** If the IP address is not specified, screenlogicpy will attempt to discover ScreenLogic protocol adapters on the local network, and connect to the first one that responds. This is generally fine if you only have one ScreenLogic protocol adapter. Discovery is limited to finding protocol adapters on the same subnet as the host running `screenlogicpy`.

### `-p, --port`

```shell
screenlogicpy -i xxx.xxx.xxx.xxx -p xx
```

Specify the port of the ScreenLogic protocol adapter to connect to. Needs to be used in conjunction with `-i, --ip` option.

## Positional arguments

### `discover`

```shell
screenlogicpy discover
```

Attempts to discover ScreenLogic protocol adapters on the local network via UDP broadcast. Returns `[ip address]:[port]` of each discovered ScreenLogic protocol adapter, one per line.  
**Note:** Discovery is limited to finding protocol adapters on the same subnet as the host running `screenlogicpy`.

### `get`

```shell
screenlogicpy get {circuit,c,heat-mode,hm,heat-temp,ht,heat-state,hs,current-temp,t,json,j}
```

The get option is use with additional options to return the current state of the additional option specified.

#### get `circuit, c`

```shell
screenlogicpy get circuit [circuit number]
```

Returns 1 for on and 0 for off

#### get `heat-mode, hm`

```shell
screenlogicpy get heat-mode [body]
```

Returns the current heating mode for the specified body of water.  
**Note:** `[body]` can be an `int` or `string` representing the [body of water](#body).

#### get `heat-temp, ht`

```shell
screenlogicpy get heat-temp [body]
```

Returns the current target heating temperature for the specified body of water.  
**Note:** `[body]` can be an `int` or `string` representing the [body of water](#body).

#### get `heat-state, hs`

```shell
screenlogicpy get heat-state [body]
```

Returns the current state of the heater for the specified body of water. The current state will match the heat mode when heating is active, otherwise will be 0 (off).  
**Note:** `[body]` can be an `int` or `string` representing the [body of water](#body).

#### get `current-temp, t`

```shell
screenlogicpy get current-temp [body]
```

Returns the current temperature for the specified body of water. This is actually the last-known temperature from when that body of water was active (Pool or Spa)  
**Note:** `[body]` can be an `int` or `string` representing the [body of water](#body).

#### get `json, j`

```shell
screenlogicpy get json
```

Returns a json dump of all data cached in the data `dict`.

### `set`

```shell
screenlogicpy set {circuit,c,color-lights,cl,heat-mode,hm,heat-temp,ht} ...
```

All `set` commands work like their corresponding `get` commands, but take an additional argument or arguments for the desired setting.

#### set `circuit, c`

```shell
screenlogicpy set circuit [circuit number] [circuit state]
```

Sets the specified circuit to the specified circuit state.  
**Note:** `[circuit state]` can be an `int` or `string` representing the desired [circuit state](#circuit-state).

#### set `heat-mode, hm`

```shell
screenlogicpy set heat-mode [body] [heat mode]
```

Sets the desired heating mode for the specified body of water.  
**Note:** `[body]` can be an `int` or `string` representing the [body of water](#body). `[heat mode]` can be an `int` or `string` representing the desired [heat mode](#heat-modes)

#### set `heat-temp, ht`

```shell
screenlogicpy set heat-temp [body] [heat temp]
```

Sets the desired target heating temperature for the specified body of water.  
**Note:** `[body]` can be an `int` or `string` representing the [body of water](#body). `[heat temp]` is an `int` representing the desired target temperature.

#### set `color-lights, cl`

```shell
screenlogicpy set color-lights [color mode]
```

Sets a color mode for all color-capable lights configured on the pool controller.  
**Note:** `[color mode]` can be either the `int` or `string` representation of a [color mode](#color-modes).  
_New in v0.3.0._

#### set `salt-generator, scg`

```shell
screenlogicpy set salt-generator [pool_pct] [spa_pct]
```

Sets the chlorinator output levels for the pool and spa. Pentair treats spa output level as a percentage of the pool's output level.  
**Note:** `[pool_pct]` can be an `int` between `0`-`100`, or `*` to keep the current value. `[spa_pct]` can be an `int` between `0`-`100`, or `*` to keep the current value.  
_New in v0.5.0._

#### set `chem-data, ch`

```shell
screenlogicpy set chem-data [ph_setpoint] [orp_setpoint]
```

Sets the pH and/or ORP set points for the IntelliChem system.  
**Note:** `[ph_setpoint]` can be a `float` between `7.2`-`7.6`, or `*` to keep the current value. `[orp_setpoint]` can be an `int` between `400`-`800`, or `*` to keep the current value.  
_New in v0.6.0._

# Reference

## Circuit State

| `int` | `string` | Name |
| ----- | -------- | ---- |
| `0`   | `off`    | Off  |
| `1`   | `on`     | On   |

## Body

| `int` | `string` | Name |
| ----- | -------- | ---- |
| `0`   | `pool`   | Pool |
| `1`   | `spa`    | Spa  |

## Heat Modes

| `int` | `string`          | Name            | Description                                                                                                         |
| ----- | ----------------- | --------------- | ------------------------------------------------------------------------------------------------------------------- |
| `0`   | `off`             | Off             | Heating is off                                                                                                      |
| `1`   | `solar`           | Solar           | Heating will use solar heat to achieve the desired temperature set point.                                           |
| `2`   | `solar_preferred` | Solar Preferred | Heating will use solar if available to achieve the desired temperature set point, otherwise it will use the heater. |
| `3`   | `heater`          | Heater          | Heating will use the heater to achieve the desired temperature set point.                                           |
| `4`   | `dont_change`     | Don't Change    | Don't change the heating mode based on circuit or function changes.                                                 |


## Color Modes

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

## Supported Subscribable Messages

`screenlogicpy` includes functionality to automatically decode these messages and update it's data accordingly. Other message codes can be subscribed to, but the consuming application will need to implement any processing of the incoming message.

```python
from screenlogicpy.const import CODE
```

|Message Code|Imported CONST|Description|
|------------|--------------|-----------|
|`12500`|`CODE.STATUS_CHANGED`|Sent when basic status changes. Air/water temp, heater state, circuit state, basic chemistry (if available).|
|`12504`|`CODE.COLOR_UPDATE`|Sent repeatedly during a color lights color mode transition.|
|`12505`|`CODE.CHEMISTRY_CHANGED`|Sent when a change occurs to the state of an attached IntelliChem controller.|

---

## Acknowledgements

Inspired by https://github.com/keithpjolley/soipip

The protocol and codes are documented fairly well here: https://github.com/ceisenach/screenlogic_over_ip
