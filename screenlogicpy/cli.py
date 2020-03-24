import sys
import json
import argparse
from screenlogicpy.discovery import discover
from screenlogicpy.gateway import ScreenLogicGateway
from screenlogicpy.const import BODY_TYPE, ON_OFF, HEAT_MODE, ScreenLogicError

def cli():
    
    _ip = None
    _port = None
    _type = None
    _subtype = None
    _name = None

    parser = argparse.ArgumentParser(
        description="Interface for Pentair Screenlogic gateway")
    parser.add_argument('-v','--verbose', action='store_true')
    parser.add_argument('-i','--ip')
    parser.add_argument('-p','--port')
    parser.add_argument('-g','--getcircuit', metavar="CIRCUIT", type=int)
    parser.add_argument('-s','--setcircuit', nargs=2, metavar=("CIRCUIT", "STATE"))
    parser.add_argument('-m','--heatmode', nargs=2, metavar=("BODY", "HEATMODE"))
    parser.add_argument('-t','--heattemp', nargs=2, metavar=("BODY", "HEATTEMP"))
    parser.add_argument('-j','--json', action='store_true')
    args = parser.parse_args()

    try:
        _ip = args.ip
        _port = args.port
        _verbose = args.verbose
        # Try to discover gateway
        if (not _ip or not _port):
            #pylint: disable=unused-variable
            _ip, _port, _type, _subtype, _name = discover()
            if (_ip and _port and _verbose == True):
                print("Found ScreenLogic Gateway at {}:{}".format(_ip, _port))

        gateway = ScreenLogicGateway(_ip, _port, _type, _subtype, _name)

        if ('config' not in gateway.get_data()):
            return 1

        if (args.getcircuit):
            print(ON_OFF.GetFriendlyName(
                    int(gateway.get_data()['circuits']
                        [int(args.getcircuit)]['value'])))
            return 0
        elif (args.setcircuit):
            state = 0
            if (args.setcircuit[1] == '1' or args.setcircuit[1].lower() == 'on'):
                state = 1
            if (gateway.set_circuit(int(args.setcircuit[0]), state)):
                gateway.update()
                print(ON_OFF.GetFriendlyName(
                        int(gateway.get_data()['circuits']
                            [int(args.setcircuit[0])]['value'])))
                return 0
            else:
                return 1
        elif (args.heatmode):
            if (gateway.set_heat_mode(
                int(args.heatmode[0]), int(args.heatmode[1]))):
                gateway.update()
                print(BODY_TYPE.GetFriendlyName(
                    gateway.get_data()['bodies']
                    [int(args.heatmode[0])]['body_type']['value']),
                    HEAT_MODE.GetFriendlyName(
                    gateway.get_data()['bodies']
                    [int(args.heatmode[0])]['heat_mode']['value']))
                return 0
            else:
                return 1
        elif (args.heattemp):
            if (gateway.set_heat_temp(int(args.heattemp[0]), int(args.heattemp[1]))):
                gateway.update()
                print(BODY_TYPE.GetFriendlyName(
                    gateway.get_data()['bodies']
                    [int(args.heattemp[0])]['body_type']['value']),
                    gateway.get_data()['bodies']
                    [int(args.heattemp[0])]['heat_set_point']['value'])
                return 0
            else:
                return 1
        else:
            print(json.dumps(gateway.get_data(), indent=2))
            return 0

    except ScreenLogicError as err:
        print(err)
        return 1

if __name__ == "__main__":
    sys.exit(cli())
