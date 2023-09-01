import asyncio
import logging

from ..const import ScreenLogicRequestError
from ..const.msg import CODE, COM_MAX_RETRIES, COM_RETRY_WAIT, COM_TIMEOUT
from .protocol import ScreenLogicProtocol
from .utility import asyncio_timeout

_LOGGER = logging.getLogger(__name__)


async def async_make_request(
    protocol: ScreenLogicProtocol,
    requestCode: int,
    requestData: bytes = b"",
    max_retries: int = COM_MAX_RETRIES,
) -> bytes:
    for attempt in range(0, max_retries + 1):
        if not protocol.is_connected:
            raise ScreenLogicRequestError(
                "Unable to make request. No active connection"
            )

        request = protocol.await_send_message(requestCode, requestData)
        try:
            async with asyncio_timeout(COM_TIMEOUT):
                await request
        except asyncio.TimeoutError:
            error_message = (
                f"Timeout waiting for response to message code '{requestCode}'"
            )
        except asyncio.CancelledError:
            _LOGGER.debug(f"Future for request '{requestCode}' was canceled!")
            return

        if not request.cancelled():
            _, responseCode, responseData = request.result()

            if responseCode == requestCode + 1:
                return responseData
            elif responseCode == CODE.ERROR_LOGIN_REJECTED:
                error_message = f"Login Rejected for request code: {requestCode}, request: {requestData}"
            elif responseCode == CODE.ERROR_INVALID_REQUEST:
                error_message = f"Invalid Request for request code: {requestCode}, request: {requestData}"
            elif responseCode == CODE.ERROR_BAD_PARAMETER:
                error_message = f"Bad Parameter for request code: {requestCode}, request: {requestData}"
            else:
                error_message = f"Unexpected response code '{responseCode}' for request code: {requestCode}, request: {requestData}"

        if attempt == max_retries:
            raise ScreenLogicRequestError(
                f"{error_message} after {max_retries + 1} attempts"
            )

        retry_delay = COM_RETRY_WAIT * (attempt + 1)

        _LOGGER.debug(
            error_message + ". Will retry %i more time(s) in %i seconds",
            max_retries - attempt,
            retry_delay,
        )

        await asyncio.sleep(retry_delay)
