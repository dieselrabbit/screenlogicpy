import time
from tests.fake_gateway import fake_ScreenLogicGateway
from screenlogicpy.requests.login import connect_to_gateway


def test_gateway_login():
    _ = fake_ScreenLogicGateway(discovery=False)

    time.sleep(1)

    soc, mac = connect_to_gateway("127.0.0.1", "80")

    assert soc

    print(mac)

    soc.close()


if __name__ == "__main__":
    test_gateway_login()
