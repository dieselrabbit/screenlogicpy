from screenlogicpy import ScreenLogicGateway, discovery, const
from tests.fake_gateway import fake_ScreenLogicGateway


def test_gateway():
    _ = fake_ScreenLogicGateway()

    hosts = discovery.discover()
    if len(hosts) > 0:
        gateway = ScreenLogicGateway(**hosts[0])
        print(f"{gateway.ip}:{gateway.port} {gateway.name}")
        data = gateway.get_data()
        print(
            const.EQUIPMENT.CONTROLLER_HARDWARE[data["config"]["controller_type"]][
                data["config"]["hardware_type"]
            ]
        )
        return 0
    else:
        print("No gateways found")
        return 1


if __name__ == "__main__":
    test_gateway()
