import sys
import json
import argparse
from screenlogicpy.discovery import discover
from screenlogicpy.gateway import ScreenLogicGateway
from screenlogicpy.const import BODY_TYPE, ON_OFF, HEAT_MODE, ScreenLogicError

def vFormat(verbose, slElement, slClass=None):
    if (verbose):
        if (slClass):
            return "{}: {}".format(slElement['name'], slClass.GetFriendlyName(slElement['value']))
        else:
            return "{}: {}".format(slElement['name'], slElement['value'])
    else:
        return slElement['value']


#parser functions
def discover_action(args, gateway):
    print("{}:{}".format(gateway.ip, gateway.port))
    return 0

def get_circuit(args, gateway):
    if (not int(args.circuit_num) in gateway.get_data()['circuits']):
        print(f'Invalid circuit number: {args.circuit_num}')
        return 4
    print(vFormat(args.verbose, 
        gateway.get_data()['circuits'][int(args.circuit_num)],
        ON_OFF))
    return 0

def set_circuit(args, gateway):
    state = 0
    if (args.state == '1' or args.state.lower() == 'on'):
        state = 1
    if (not int(args.circuit_num) in gateway.get_data()['circuits']):
        print(f'Invalid circuit number: {args.circuit_num}')
        return 4
    if (gateway.set_circuit(int(args.circuit_num), state)):
        gateway.update()
    else:
        return 4
    print(vFormat(args.verbose, 
        gateway.get_data()['circuits'][int(args.circuit_num)],
        ON_OFF))
    return 0

def get_heat_mode(args, gateway):
    body = 0
    if (args.body == '1' or args.body.lower() == 'spa'):
        body = 1
    print(vFormat(args.verbose, 
        gateway.get_data()['bodies'][int(body)]['heat_mode'],
        HEAT_MODE))
    return 0

def set_heat_mode(args, gateway):
    body = 0
    if (args.body == '1' or args.body.lower() == 'spa'):
        body = 1
    if (gateway.set_heat_mode(int(body), int(args.mode))):
        gateway.update()
    else:
        return 8
    print(vFormat(args.verbose, 
        gateway.get_data()['bodies'][int(body)]['heat_mode'],
        HEAT_MODE))
    return 0

def get_heat_temp(args, gateway):
    body = 0
    if (args.body == '1' or args.body.lower() == 'spa'):
        body = 1
    print(vFormat(args.verbose, 
        gateway.get_data()['bodies'][int(body)]['heat_set_point']))
    return 0

def set_heat_temp(args, gateway):
    body = 0
    if (args.body == '1' or args.body.lower() == 'spa'):
        body = 1
    if (args.temp != -1):
        if (gateway.set_heat_temp(int(body), int(args.temp))):
            gateway.update()
        else:
            return 16
    print(vFormat(args.verbose, 
        gateway.get_data()['bodies'][int(body)]['heat_set_point']))
    return 0

def get_heat_state(args, gateway):
    body = 0
    if (args.body == '1' or args.body.lower() == 'spa'):
        body = 1
    print(vFormat(args.verbose, 
        gateway.get_data()['bodies'][int(body)]['heat_status'],
        ON_OFF))
    return 0

def get_current_temp(args, gateway):
    body = 0
    if (args.body == '1' or args.body.lower() == 'spa'):
        body = 1
    print(vFormat(args.verbose, 
        gateway.get_data()['bodies'][int(body)]['current_temperature']))
    return 0

def get_json(args, gateway):
    print(json.dumps(gateway.get_data(), indent=2))
    return 0


#entry function
def cli():
    
    _ip = None
    _port = 80
    _type = 0
    _subtype = 0
    _name = "Unnamed Gateway"

    option_parser = argparse.ArgumentParser(
        description="Interface for Pentair Screenlogic gateway")

    option_parser.add_argument('-v','--verbose', action='store_true')
    option_parser.add_argument('-i','--ip')
    option_parser.add_argument('-p','--port', default=80)

    subparsers = option_parser.add_subparsers(dest='action')

    # Discover command
    discover_parser = subparsers.add_parser('discover')
    discover_parser.set_defaults(func=discover_action)
 
    # Get options
    get_parser = subparsers.add_parser('get')
    get_subparsers = get_parser.add_subparsers(dest='get_option')
    get_subparsers.required = True

    get_circuit_parser = get_subparsers.add_parser('circuit', aliases=['c'])
    get_circuit_parser.add_argument('circuit_num', metavar='CIRCUIT_NUM', type=int)
    get_circuit_parser.set_defaults(func=get_circuit)

    get_heat_mode_parser = get_subparsers.add_parser('heat-mode', aliases=['hm'])
    get_heat_mode_parser.add_argument('body', metavar='BODY', type=str, choices=['0', '1', 'pool', 'spa'])
    get_heat_mode_parser.set_defaults(func=get_heat_mode)

    get_heat_temp_parser = get_subparsers.add_parser('heat-temp', aliases=['ht'])
    get_heat_temp_parser.add_argument('body', metavar='BODY', type=str, choices=['0', '1', 'pool', 'spa'])
    get_heat_temp_parser.set_defaults(func=get_heat_temp)

    get_heat_state_parser = get_subparsers.add_parser('heat-state', aliases=['hs'])
    get_heat_state_parser.add_argument('body', metavar='BODY', type=str, choices=['0', '1', 'pool', 'spa'])
    get_heat_state_parser.set_defaults(func=get_heat_state)

    get_current_temp_parser = get_subparsers.add_parser('current-temp', aliases=['t'])
    get_current_temp_parser.add_argument('body', metavar='BODY', type=str, choices=['0', '1', 'pool', 'spa'])
    get_current_temp_parser.set_defaults(func=get_current_temp)

    get_json_parser = get_subparsers.add_parser('json', aliases=['j'])
    get_json_parser.set_defaults(func=get_json)

    # Set options
    set_parser = subparsers.add_parser('set')
    set_subparsers = set_parser.add_subparsers(dest='set_option')
    set_subparsers.required = True

    set_circuit_parser = set_subparsers.add_parser('circuit', aliases=['c'])
    set_circuit_parser.add_argument('circuit_num', metavar='CIRCUIT_NUM', type=int)
    set_circuit_parser.add_argument('state', metavar='STATE', type=str, choices=['0', '1', 'off', 'on'])
    set_circuit_parser.set_defaults(func=set_circuit)

    set_heat_mode_parser = set_subparsers.add_parser('heat-mode', aliases=['hm'])
    set_heat_mode_parser.add_argument('body', metavar='BODY', type=str, choices=['0', '1', 'pool', 'spa'])
    options = list(range(len(HEAT_MODE._names)))
    for mode in HEAT_MODE._names:
        options.append(mode.replace(' ', '_').replace('\'', '').lower())
    set_heat_mode_parser.add_argument('mode', metavar='MODE', type=str, choices=options, default=options[0])
    set_heat_mode_parser.set_defaults(func=set_heat_mode)

    set_heat_temp_parser = set_subparsers.add_parser('heat-temp', aliases=['ht'])
    set_heat_temp_parser.add_argument('body', metavar='BODY', type=str, choices=['0', '1', 'pool', 'spa'])
    set_heat_temp_parser.add_argument('temp', type=int, metavar='TEMP', default=None)
    set_heat_temp_parser.set_defaults(func=set_heat_temp)

    args = option_parser.parse_args()
    try:
        _ip = args.ip
        _port = args.port
        discovered = False
        if (not _ip):
            # Try to discover gateway
            host = discover()
            #_ip, _port, _type, _subtype, _name = discover()
            if (host['ip']):
                discovered = True
                _ip = host['ip']
                _port = host['port']
                _type = host['type']
                _subtype = host['subtype']
                _name = host['name']
                if (args.verbose):
                    print("Found '{}' at {}:{}".format(_name, _ip, _port))
            # discover() will error if gateway not found
                

        gateway = ScreenLogicGateway(_ip, _port, _type, _subtype, _name)

        if ('config' not in gateway.get_data()):
            return 1

        def print_gateway():
            verb = 'Using'
            if (discovered):
                verb = "Discovered"
            print("{} '{}' at {}:{}".format(verb, gateway.name, gateway.ip, gateway.port))

        def print_circuits():
            print("{}  {}  {}".format("ID".rjust(3), "STATE", "NAME"))
            print("--------------------------")
            for id in gateway.get_data()['circuits']:
                circuit = gateway.get_data()['circuits'][int(id)]
                print("{}  {}  {}".format(
                    circuit['id'], ON_OFF.GetFriendlyName(circuit['value']).rjust(5), circuit['name']))

        def print_heat():
            for id in gateway.get_data()['bodies']:
                body = gateway.get_data()['bodies'][int(id)]
                print("{} temperature is last {}{}".format(
                    BODY_TYPE.GetFriendlyName(body['body_type']['value']),
                    body['current_temperature']['value'],
                    body['current_temperature']['unit'] ))
                print("{}: {}".format(
                    body['heat_set_point']['name'], body['heat_set_point']['value']))
                print("{}: {}".format(
                    body['heat_status']['name'], HEAT_MODE.GetFriendlyName(body['heat_status']['value'])))
                print("{}: {}".format(
                    body['heat_mode']['name'], HEAT_MODE.GetFriendlyName(body['heat_mode']['value'])))
                print("--------------------------")


        def print_dashboard():
            print_gateway()
            print("**************************")
            print_heat()
            print("**************************")
            print_circuits()
            print("**************************")


        if (args.action is None):
            print_dashboard()
            return 0

            
        return args.func(args, gateway)

    except ScreenLogicError as err:
        print(err)
        return 32

if __name__ == "__main__":
    sys.exit(cli())
