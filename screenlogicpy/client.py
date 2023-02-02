"""Client manager for a connection to a ScreenLogic protocol adapter."""
import asyncio
import logging
from typing import Callable

from .const import CODE, COM_KEEPALIVE, ScreenLogicWarning
from .requests.chemistry import decode_chemistry
from .requests.client import async_request_add_client, async_request_remove_client
from .requests.color import decode_color_update
from .requests.status import decode_pool_status
from .requests.ping import async_request_ping
from .requests.protocol import ScreenLogicProtocol

_LOGGER = logging.getLogger(__name__)


class ClientManager:
    """Class to manage callback subscriptions to specific ScreenLogic messages."""

    def __init__(self) -> None:
        self._listeners = {}
        self._is_client = False
        self._client_desired = False
        self._attached = False

    @property
    def is_client(self):
        """Return if connected to ScreenLogic as a client."""
        return self._is_client

    @property
    def client_desired(self):
        """Return if desired to be a client."""
        return self._client_desired

    async def attach(self, protocol: ScreenLogicProtocol, data: dict):
        """
        Update protocol and data reference.

        Updates this ClientManager's reference to a ScreenLogicProtocol instance
        and a current data dict. Will attempt to re-register any existing callbacks
        to the new protocol instance.
        """
        self._protocol = protocol
        self._data = data
        self._attached = True
        if self._listeners:
            self._protocol.remove_all_async_message_callbacks()
            for code in self._listeners:
                self._protocol.register_async_message_callback(
                    code, self._async_common_callback, code, self._data
                )

    def _notify_listeners(self, code: int) -> None:
        """Notify all listeners."""
        for callback in self._listeners.get(code):
            callback()

    def _callback_factory(self, code) -> Callable:
        """Return decoding method for known message codes."""
        if code == CODE.STATUS_CHANGED:
            return decode_pool_status
        elif code == CODE.CHEMISTRY_CHANGED:
            return decode_chemistry
        elif code == CODE.COLOR_UPDATE:
            return decode_color_update
        else:
            return None

    async def _async_common_callback(self, message, code, data):
        """Decode known incoming messages."""
        if decoder := self._callback_factory(code):
            decoder(message, data)

        self._notify_listeners(code)

    async def async_subscribe(
        self, callback: Callable[..., any], code: int
    ) -> Callable:
        """
        Register listener callback.

        Registers a callback method to call when a message with the specified
        message code is received. Messages with known codes will be processed
        and applied to gateway data before callback method is called.
        """
        if not self._attached:
            return None

        if len(self._listeners) == 0:
            _LOGGER.debug("No previous listeners. Subscribing gateway.")
            if not await self.async_subscribe_gateway():
                return None

        _LOGGER.debug(f"Adding listener {callback}")
        code_listeners: set = self._listeners.setdefault(code, set())

        code_listeners.add(callback)

        self._protocol.register_async_message_callback(
            code, self._async_common_callback, code, self._data
        )

        def remove_listener():
            """Remove listener callback."""
            if callback in code_listeners:
                _LOGGER.debug(f"Removing listener {callback}")
                code_listeners.remove(callback)
                if not code_listeners:
                    _LOGGER.debug(f"No more listeners for code {code}. Removing.")
                    if code in self._listeners:
                        self._listeners.pop(code)
                        self._protocol.remove_async_message_callback(code)
                        if not self._listeners:
                            _LOGGER.debug(
                                "No more listeners for any code. Unsubscribing gateway."
                            )
                            asyncio.create_task(self.async_unsubscribe_gateway())

        return remove_listener

    async def _async_ping(self):
        """Check connection before requesting a ping."""
        if not self._protocol.is_connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. request_ping failed."
            )
        _LOGGER.debug("Requesting ping")
        if await async_request_ping(self._protocol):
            _LOGGER.debug("Ping successful.")

    async def _async_add_client(self):
        """Check connection before sending add client request."""
        if not self._protocol.is_connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. add_client failed."
            )
        _LOGGER.debug("Requesting add client")
        return await async_request_add_client(self._protocol)

    async def _async_remove_client(self):
        """Check connection before sending remove client request."""
        if not self._protocol.is_connected:
            raise ScreenLogicWarning(
                "Not connected to protocol adapter. remove_client failed."
            )
        _LOGGER.debug("Requesting remove client")
        return await async_request_remove_client(self._protocol)

    async def async_subscribe_gateway(self) -> bool:
        """
        Subscribe as ScreenLogic client.

        Adds this gateway as a client on the ScreenLogic protocol adapter. This
        tells ScreenLogic that we are interested in receiving push update messages.
        """
        self._client_desired = True
        if await self._async_add_client():
            self._is_client = True
            self._protocol.enable_keepalive(self._async_ping, COM_KEEPALIVE)
            _LOGGER.debug("Gateway subscribed")
            return True  # await self._async_setup_push()
        return False

    async def async_unsubscribe_gateway(self) -> bool:
        """
        Unsubscribe as ScreenLogic client.

        Removes this gateway as a client on the ScreenLogic protocol adapter.
        ScreenLogic will no longer push update messages.
        """
        if self._is_client:
            self._client_desired = False
            self._is_client = False
            self._protocol.disable_keepalive()
            self._protocol.remove_all_async_message_callbacks()
            _LOGGER.debug("Gateway unsubscribing")
            return await self._async_remove_client()
        return True
