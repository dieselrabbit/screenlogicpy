import time
from screenlogicpy.discovery import discover
from tests.fake_gateway import fake_ScreenLogicGateway


def test_gateway_discovery():
    _ = fake_ScreenLogicGateway(request=False)

    time.sleep(2)

    hosts = discover()

    assert len(hosts) > 0

    print(hosts)


if __name__ == "__main__":
    test_gateway_discovery()
