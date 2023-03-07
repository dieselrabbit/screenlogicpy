"""Client manager for a connection to a ScreenLogic protocol adapter."""
import asyncio
import logging
import random
from typing import Callable

from .const import CODE, COM_KEEPALIVE, MESSAGE, ScreenLogicWarning
from .requests.chemistry import decode_chemistry
from .requests.client import async_request_add_client, async_request_remove_client
from .requests.lights import decode_color_update
from .requests.status import decode_pool_status
from .requests.ping import async_request_ping
from .requests.protocol import ScreenLogicProtocol

_LOGGER = logging.getLogger(__name__)


class ClientManager:
    """Class to manage callback subscriptions to specific ScreenLogic messages."""

    def __init__(self, client_id: int = None) -> None:
        self._client_id = (
            client_id if client_id is not None else random.randint(32767, 65535)
        )
        self._listeners = {}
        self._is_client = False
        self._client_sub_unsub_lock = asyncio.Lock()
        self._protocol = None
        self._data = None
        self._max_retries = MESSAGE.COM_MAX_RETRIES

    @property
    def is_client(self) -> bool:
        """Return if connected to ScreenLogic as a client."""
        return self._is_client and self._protocol and self._protocol.is_connected

    @property
    def client_id(self) -> int:
        return self._client_id

    @property
    def client_needed(self) -> bool:
        """Return if desired to be a client."""
        return self._listeners and not self._is_client

    def _attached(self) -> bool:
        return self._protocol and self._protocol.is_connected

    async def attach(
        self,
        protocol: ScreenLogicProtocol,
        data: dict,
        max_retries: int = MESSAGE.COM_MAX_RETRIES,
    ):
        """
        Update protocol and data reference.

        Updates this ClientManager's reference to a ScreenLogicProtocol instance
        and a current data dict. Will attempt to re-register any existing callbacks
        to the new protocol instance.
        """
        self._protocol = protocol
        self._data = data
        self._max_retries = max_retries
        self._is_client = False
        if self.client_needed:
            self._protocol.remove_all_async_message_callbacks()
            for code in self._listeners:
                self._protocol.register_async_message_callback(
                    code, self._async_common_callback, code, self._data
                )
            await self.async_subscribe_gateway()

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
        if not self._attached():
            return None

        _LOGGER.debug(f"Adding listener {callback}")
        code_listeners: set = self._listeners.setdefault(code, set())

        code_listeners.add(callback)

        if self._attached():
            self._protocol.register_async_message_callback(
                code, self._async_common_callback, code, self._data
            )

        if self.client_needed:
            _LOGGER.debug("Client needed.")
            if not await self.async_subscribe_gateway():
                return None

        def remove_listener():
            """Remove listener callback."""
            if callback in code_listeners:
                _LOGGER.debug(f"Removing listener {callback}")
                code_listeners.remove(callback)
                if not code_listeners:
                    _LOGGER.debug(f"No more listeners for code {code}. Removing.")
                    if code in self._listeners:
                        self._listeners.pop(code)
                        if self._attached():
                            self._protocol.remove_async_message_callback(code)
                            if not self._listeners:
                                _LOGGER.debug(
                                    "No more listeners for any code. Unsubscribing gateway."
                                )
                                asyncio.create_task(self.async_unsubscribe_gateway())

        return remove_listener

    async def _async_ping(self):
        """Check connection before requesting a ping."""
        if not self._attached():
            raise ScreenLogicWarning(
                "Not attached to protocol adapter. request_ping failed."
            )
        _LOGGER.debug("Requesting ping")
        if await async_request_ping(self._protocol, max_retries=self._max_retries):
            _LOGGER.debug("Ping successful.")

    async def _async_add_client(self):
        """Check connection before sending add client request."""
        if not self._attached():
            raise ScreenLogicWarning(
                "Not attached to protocol adapter. add_client failed."
            )
        _LOGGER.debug("Requesting add client")
        return await async_request_add_client(
            self._protocol, self._client_id, max_retries=self._max_retries
        )

    async def _async_remove_client(self):
        """Check connection before sending remove client request."""
        if not self._attached():
            raise ScreenLogicWarning(
                "Not attached to protocol adapter. remove_client failed."
            )
        _LOGGER.debug("Requesting remove client")
        return await async_request_remove_client(
            self._protocol, self._client_id, max_retries=self._max_retries
        )

    async def async_subscribe_gateway(self) -> bool:
        """
        Subscribe as ScreenLogic client.

        Adds this gateway as a client on the ScreenLogic protocol adapter. This
        tells ScreenLogic that we are interested in receiving push update messages.
        """
        if self._attached():
            async with self._client_sub_unsub_lock:
                if not self.is_client:
                    _LOGGER.debug("Subscribing gateway.")
                    if await self._async_add_client():
                        self._is_client = True
                        self._protocol.enable_keepalive(self._async_ping, COM_KEEPALIVE)
                        _LOGGER.debug("Gateway subscribed")
                        return True
                    return False
                return True

    async def async_unsubscribe_gateway(self) -> bool:
        """
        Unsubscribe as ScreenLogic client.

        Removes this gateway as a client on the ScreenLogic protocol adapter.
        ScreenLogic will no longer push update messages.
        """
        if self._attached():
            async with self._client_sub_unsub_lock:
                if self._is_client:
                    self._is_client = False
                    self._protocol.disable_keepalive()
                    self._protocol.remove_all_async_message_callbacks()
                    _LOGGER.debug("Gateway unsubscribing")
                    return await self._async_remove_client()
                return True
