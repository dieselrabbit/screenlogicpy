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


def cli():
    
    _ip = None
    _port = 80
    _type = 0
    _subtype = 0
    _name = "Unnamed Gateway"

    parser = argparse.ArgumentParser(
        description="Interface for Pentair Screenlogic gateway")
    parser.add_argument('-d','--discover-only', action='store_true')
    parser.add_argument('-v','--verbose', action='store_true')
    parser.add_argument('-i','--ip')
    parser.add_argument('-p','--port', default=80)
    parser.add_argument('-c','--circuit', metavar="CIRCUIT", type=int)
    parser.add_argument('-s','--state', metavar="STATE")
    parser.add_argument('-b','--body', metavar="BODY", type=int)
    parser.add_argument('-hm','--heat-mode', nargs='?', metavar="HEATMODE", type=int, const=-1)
    parser.add_argument('-ht','--heat-temp', nargs='?', metavar="HEATTEMP", type=int, const=-1)
    parser.add_argument('-hs','--heat-state', action='store_true')
    parser.add_argument('-ct','--current-temp', action='store_true')
    parser.add_argument('-j','--json', action='store_true')
    args = parser.parse_args()#"-v -b 0".split())

    try:
        _ip = args.ip
        _port = args.port
        verbose = args.verbose
        if (args.discover_only or not _ip):
            # Try to discover gateway
            _ip, _port, _type, _subtype, _name = discover()
            if (args.discover_only):
                if (verbose):
                    print("Found {} at {}:{}".format(_name, _ip, _port))
                else:
                    print("{}:{}".format(_ip, _port))

        gateway = ScreenLogicGateway(_ip, _port, _type, _subtype, _name)

        if ('config' not in gateway.get_data()):
            return 1

        if (args.json):
            print(json.dumps(gateway.get_data(), indent=2))
            return 0

        if (args.circuit):
            if (not args.state is None):
                state = 0
                if (args.state == '1' or args.state.lower() == 'on'):
                    state = 1
                if (gateway.set_circuit(int(args.circuit), state)):
                    gateway.update()
                else:
                    return 4
            print(vFormat(verbose, 
                gateway.get_data()['circuits'][int(args.circuit)],
                ON_OFF))

        if (not args.body is None):
            if (not args.heat_mode is None):
                if (args.heat_mode != -1):
                    if (gateway.set_heat_mode(int(args.body), int(args.heat_mode))):
                        gateway.update()
                    else:
                        return 8
                print(vFormat(verbose, 
                    gateway.get_data()['bodies'][int(args.body)]['heat_mode'],
                    HEAT_MODE))
            if (args.heat_temp):
                if (args.heat_temp != -1):
                    if (gateway.set_heat_temp(int(args.body), int(args.heat_temp))):
                        gateway.update()
                    else:
                        return 16
                print(vFormat(verbose, 
                    gateway.get_data()['bodies'][int(args.body)]['heat_set_point']))
            if (args.current_temp):
                print(vFormat(verbose, 
                    gateway.get_data()['bodies'][int(args.body)]['current_temperature']))
            if (args.heat_state):
                print(vFormat(verbose, 
                    gateway.get_data()['bodies'][int(args.body)]['heat_status'],
                    ON_OFF))

            if (args.heat_mode is None and args.heat_temp is None and args.current_temp == False and args.heat_state == False):
                #print(vFormat(verbose, 
                #    gateway.get_data()['bodies'][int(args.body)]['body_type'],
                #    BODY_TYPE))
                print(vFormat(verbose, 
                    gateway.get_data()['bodies'][int(args.body)]['current_temperature']))
                print(vFormat(verbose, 
                    gateway.get_data()['bodies'][int(args.body)]['heat_set_point']))
                print(vFormat(verbose, 
                    gateway.get_data()['bodies'][int(args.body)]['heat_mode'],
                    HEAT_MODE))
                print(vFormat(verbose, 
                    gateway.get_data()['bodies'][int(args.body)]['heat_status'],
                    ON_OFF))

    except ScreenLogicError as err:
        print(err)
        return 32

if __name__ == "__main__":
    sys.exit(cli())
