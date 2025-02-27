import asyncio
from dataclasses import asdict
from datetime import timedelta, timezone
import logging
from random import randint
from typing import Any, Callable

from .connection import (
    COM_MAX_RETRIES,
    COM_RETRY_WAIT,
    COM_TIMEOUT,
    Connection,
    GatewayInfo,
    Transaction,
)
from .system import *
from .devices import *
from .messages import *

_LOGGER = logging.getLogger(__name__)

REDACTED = ["user_zip", "user_latitude", "user_longitude", "mac"]


def redact_dict_factory(fields: list[tuple[str, Any]]) -> dict:
    return {
        name: value
        for name, value in fields
        if name not in REDACTED and "Pentair:" not in str(value)
    }


class ScreenLogicClient:
    """Defines a client of a ScreenLogic Gateway."""

    _id: int
    _loop: asyncio.AbstractEventLoop
    _connection: Connection | None = None
    _system: System | None = None
    _is_client: bool = False
    _msg_callbacks: dict[MessageCode, set[Callable[[BaseResponse], None]]]
    _conn_lost_fut: asyncio.Future = None
    _debug_data: dict[int, bytes] = None

    timeout: int = COM_TIMEOUT
    retry_delay: int = COM_RETRY_WAIT
    max_attempts: int = COM_MAX_RETRIES

    def __init__(self, *, client_id: int = -1, system: System = None) -> None:

        self._id = client_id if (32767 < client_id < 65535) else randint(32767, 65535)
        self._system = system
        self._loop = asyncio.get_event_loop()
        self._debug_data = {}
        self._msg_callbacks = {}

    @property
    def id(self) -> int:
        return self._id

    @property
    def connection(self) -> Connection:
        return self._connection

    @property
    def system(self) -> System:
        return self._system

    def get_debug(self) -> dict:
        return self._debug_data

    async def connect(
        self,
        gw_info: GatewayInfo,
        *,
        timeout: int = None,
        retry_delay: int = None,
        max_attempts: int = None
    ) -> asyncio.Future:
        """Create and open a Connection to the ScreenLogic gateway.

        Required:
         `gateway` - A GatewayInfo object with the details of the ScreenLogic gateway to connect to.
        Keyword Arguments:
         `timeout` - Number in seconds to wait for each transaction to complete.
         `retry_delay` - Number in seconds to pause between attempts to complete a transaction.
         `max_attempts` - Number of attempts to make to complete a transaction.
        """
        self.timeout = timeout or self.timeout
        self.retry_delay = retry_delay or self.retry_delay
        self.max_attempts = max_attempts or self.max_attempts
        self._connection = Connection(
            timeout=self.timeout,
            retry_delay=self.retry_delay,
            max_attempts=self.max_attempts,
            async_message_cb=self._handle_async_message,
            connection_lost_cb=self._handle_connection_lost,
        )
        gateway = await self._connection.open(gw_info)
        self._system = (
            self._system if gateway == self._system.gateway else System(gateway)
        )
        await self.update_config()
        await self.update_status()
        await self._add_client()
        self._conn_lost_fut = self._loop.create_future()
        return self._conn_lost_fut

    async def disconnect(self) -> None:
        await self._remove_client()
        await self._connection.close()
        self._connection = None

    def add_message_callback(
        self, code: MessageCode, callback: Callable[[BaseResponse], None]
    ) -> Callable:
        cb_set: set[Callable[[BaseResponse], None]] = self._msg_callbacks.setdefault(
            code, set()
        )
        cb_set.add(callback)

        def remove():
            cb_set.remove(callback)
            if len(cb_set) == 0:
                self._msg_callbacks.pop(code)

        return remove

    async def update_config(self) -> None:
        """Request all configuration information and update the Controller data."""
        await self.get_pool_config()
        await self.get_equipment_config()
        await self.get_user_config()

    async def update_status(self) -> None:
        """Request updates for all applicable pool equipment and update the Controller data."""
        await self.get_pool_status()
        await self.get_pool_timedate()
        await self.update_pumps()
        if EQUIPMENT_FLAG.INTELLICHEM in self._system.controller.equipment_flags:
            await self.get_chemistry_status()
        if EQUIPMENT_FLAG.CHLORINATOR in self._system.controller.equipment_flags:
            await self.get_scg_status()

    async def get_pool_config(self) -> None:
        """Request the base pool configuration and update the Controller data."""
        response: GetPoolConfigResponse = await self.create_transaction(
            GetPoolConfigRequest()
        ).execute_via(self._connection.connected_send)
        response.decode(self._system)
        if EQUIPMENT_FLAG.INTELLICHEM in self.system.controller.equipment_flags:
            self.system.chemistry = IntelliChem()

        if EQUIPMENT_FLAG.CHLORINATOR in self.system.controller.equipment_flags:
            self.system.chlorinator = SaltChlorineGenerator()

        self._debug_data[response.code] = response.to_bytes()

    async def get_equipment_config(self) -> None:
        """Requests detailed pool equipment configuration and updates the Controller data."""
        response: GetEquipmentConfigResponse = await self.create_transaction(
            GetEquipmentConfigRequest()
        ).execute_via(self._connection.connected_send)
        response.decode(self._system)
        self._debug_data[response.code] = response.to_bytes()

    async def get_user_config(self) -> None:
        """Request user configuration and update the Controller data."""
        response: UserConfigResponse = await self.create_transaction(
            UserConfigRequest()
        ).execute_via(self._connection.connected_send)
        response.decode(self._system)
        self._debug_data[response.code] = response.to_bytes()

    async def get_pool_timedate(self) -> None:
        """Requests the pool controller's current time and date."""
        response: GetControllerDateTimeResponse = await self.create_transaction(
            GetControllerDateTimeRequest()
        ).execute_via(self._connection.connected_send)
        response.decode(
            self._system,
            timezone(
                timedelta(hours=self._system.controller.config.time_config.tz_offset)
            ),
        )
        self._debug_data[response.code] = response.to_bytes()

    async def get_pool_status(self) -> None:
        """Request the current pool status and update the Controller data."""
        response: PoolStatusResponse = await self.create_transaction(
            PoolStatusRequest()
        ).execute_via(self._connection.connected_send)
        response.decode(self._system)
        self._debug_data[response.code] = response.to_bytes()

    async def update_pumps(self) -> None:
        """Requestes status for all installed pumps and update Controller data."""
        for i, pump in self._system.pumps.items():
            if pump:
                pump_index = int(i)
                await self.get_pump_status(pump_index)

    async def get_pump_status(self, pump_index: int) -> None:
        """Request pump status and update the Controller data."""
        response: PumpStatusResponse = await self.create_transaction(
            PumpStatusRequest(pump_index)
        ).execute_via(self._connection.connected_send)
        response.decode(self._system, pump_index)
        debug_pump_stat = self._debug_data.setdefault(response.code, {})
        debug_pump_stat[pump_index] = response.to_bytes()

    async def get_chemistry_status(self) -> None:
        """Request chemistry controller status and update the pool Controller data."""
        response: GetChemistryStatusResponse = await self.create_transaction(
            GetChemistryStatusRequest()
        ).execute_via(self._connection.connected_send)
        response.decode(self._system)
        self._debug_data[response.code] = response.to_bytes()

    async def get_scg_status(self) -> None:
        """Request salt cell status and update the Controller data."""
        response: GetSaltCellConfigResponse = await Transaction(
            GetSaltCellConfigRequest()
        ).execute_via(self._connection.connected_send)
        response.decode(self._system)
        self._debug_data[response.code] = response.to_bytes()

    def _handle_async_message(self, response: BaseResponse) -> None:
        if response.code in (
            MessageCode.STATUS_CHANGED,
            MessageCode.CHEMISTRY_CHANGED,
        ):
            response.decode(self._system)
        if response.code in self._msg_callbacks:
            for callback in self._msg_callbacks[response.code]:
                self._loop.call_soon(callback, response)

    def _handle_connection_lost(self, user_init: bool) -> None:
        self._is_client = False
        try:
            if user_init:
                self._conn_lost_fut.set_result("_handle_connection_lost")
            else:
                self._conn_lost_fut.cancel()
        except asyncio.exceptions.InvalidStateError as ise:
            print(self._conn_lost_fut.result())

    def create_transaction(self, request: BaseRequest) -> Transaction:
        return Transaction(
            request,
            timout=self.timeout,
            retry_delay=self.retry_delay,
            max_attempts=self.max_attempts,
        )

    async def _add_client(self) -> None:
        try:
            if not self._is_client:
                await self.create_transaction(AddClientRequest(self._id)).execute_via(
                    self._connection.connected_send
                )
                self._connection.enable_keepalive()
                self._is_client = True
        except:
            raise

    async def _remove_client(self) -> None:
        try:
            if self._is_client:
                await self.create_transaction(
                    RemoveClientRequest(self._id)
                ).execute_via(self._connection.connected_send)
                self._connection.disable_keepalive()
                self._is_client = False
        except:
            raise
