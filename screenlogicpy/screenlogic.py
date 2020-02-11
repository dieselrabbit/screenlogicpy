import sys
import json
import argparse
from . slgateway.gateway import gateway as slgateway
from . slgateway.const import mapping

def cli():
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

    gateway = slgateway(args.verbose, args.ip, args.port)

    if ('config' not in gateway.get_data()):
        sys.exit(1)

    if (args.getcircuit):
        print(mapping.ON_OFF[
                int(gateway.get_data()['circuits']
                    [int(args.getcircuit)]['value'])])
        sys.exit()
    elif (args.setcircuit):
        state = 0
        if (args.setcircuit[1] == '1' or args.setcircuit[1].lower() == 'on'):
            state = 1
        if (gateway.set_circuit(int(args.setcircuit[0]), state)):
            gateway.update()
            print(mapping.ON_OFF[
                    int(gateway.get_data()['circuits']
                        [int(args.setcircuit[0])]['value'])])
            sys.exit()
        else:
            sys.exit(1)
    elif (args.heatmode):
        if (gateway.set_heat_mode(
            int(args.heatmode[0]), int(args.heatmode[1]))):
            gateway.update()
            print(mapping.BODY_TYPE
                  [gateway.get_data()['bodies']
                   [int(args.heatmode[0])]['body_type']['value']],
                  mapping.HEAT_MODE
                  [gateway.get_data()['bodies']
                   [int(args.heatmode[0])]['heat_mode']['value']])
            sys.exit()
        else:
            sys.exit(1)
    elif (args.heattemp):
        if (gateway.set_heat_temp(int(args.heattemp[0]), int(args.heattemp[1]))):
            gateway.update()
            print(mapping.BODY_TYPE
                  [gateway.get_data()['bodies']
                   [int(args.heattemp[0])]['body_type']['value']],
                  gateway.get_data()['bodies']
                   [int(args.heattemp[0])]['heat_set_point']['value'])
            sys.exit()
        else:
            sys.exit(1)
    else:
        print(json.dumps(gateway.get_data(), indent=2))
        sys.exit()

if __name__ == "__main__":
    sys.exit(cli())
