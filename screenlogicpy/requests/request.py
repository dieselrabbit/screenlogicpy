import asyncio
import logging

from ..const import CODE, MESSAGE, ScreenLogicRequestError
from .protocol import ScreenLogicProtocol
from .utility import asyncio_timeout

_LOGGER = logging.getLogger(__name__)


async def async_make_request(
    protocol: ScreenLogicProtocol,
    requestCode: int,
    requestData: bytes = b"",
    max_retries: int = MESSAGE.COM_MAX_RETRIES,
) -> bytes:
    for attempt in range(0, max_retries + 1):
        request = protocol.await_send_message(requestCode, requestData)
        try:
            async with asyncio_timeout(MESSAGE.COM_TIMEOUT):
                await request
        except asyncio.TimeoutError:
            error_message = (
                f"Timeout waiting for response to message code '{requestCode}'"
            )
        except asyncio.CancelledError:
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

        retry_delay = MESSAGE.COM_RETRY_WAIT * (attempt + 1)

        _LOGGER.warning(
            error_message + ". Will retry %i more time(s) in %i seconds",
            max_retries - attempt,
            retry_delay,
        )

        await asyncio.sleep(retry_delay)
