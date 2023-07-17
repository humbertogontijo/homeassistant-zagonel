"""Sample API Client."""
from __future__ import annotations

import json
import logging
from asyncio import Future
from dataclasses import asdict, dataclass
from enum import Enum, IntEnum
from typing import Any, Literal, Optional

import async_timeout
import paho.mqtt.client as mqtt
from dacite import Config, from_dict

_LOGGER = logging.getLogger(__name__)


class ZagonelApiClientError(Exception):
    """Exception to indicate a general API error."""


class ZagonelApiClientCommunicationError(
    ZagonelApiClientError
):
    """Exception to indicate a communication error."""


class ZagonelApiClientAuthenticationError(
    ZagonelApiClientError
):
    """Exception to indicate an authentication error."""


class ZagonelEnum(IntEnum):
    """ZagonelEnum."""

    @property
    def name(self) -> str:
        """ZagonelEnum.name."""
        return super().name.lower()


class ZagonelControlMode(ZagonelEnum):
    """ZagonelControlMode."""

    MANUAL = 0
    AUTOMATIC = 1


class ZagonelParentalMode(ZagonelEnum):
    """ZagonelParentalMode."""

    OFF = 0
    SOUND = 1
    SHUTDOWN = 2
    SOUND_AND_SHUTDOWN = 3


class ZagonelRGBMode(ZagonelEnum):
    """ZagonelRGBMode."""

    POWER = 0
    TEMPERATURE = 1
    FIXED = 2


@dataclass
class ZagonelBase:
    """ZagonelBase."""

    def update(self, data: dict):
        """Update."""
        for key, value in data.items():
            if hasattr(self, key):
                if key == "Control_Mode":
                    setattr(self, key, ZagonelControlMode(value))
                elif key == "Rgb_Mode":
                    setattr(self, key, ZagonelRGBMode(value))
                elif key == "Parental_Mode":
                    setattr(self, key, ZagonelParentalMode(value))
                else:
                    setattr(self, key, value)

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        """from_dict."""
        if isinstance(data, dict):
            return from_dict(cls, data, config=Config(cast=[Enum]))

    def as_dict(self) -> dict:
        """as_dict."""
        return asdict(
            self,
            dict_factory=lambda _fields: {
                key: value.value if isinstance(value, Enum) else value
                for (key, value) in _fields
                if value is not None
            },
        )


@dataclass
class ZagonelChars(ZagonelBase):
    """ZagonelChars."""

    Type: Optional[Literal["Chars"]] = None
    User_Id: Optional[str] = None
    Device_Id: Optional[str] = None
    Hw_Id: Optional[str] = None
    Hw_Version: Optional[str] = None
    Fw_Version: Optional[str] = None
    Fw_Timestamp: Optional[str] = None
    Control_Mode: Optional[ZagonelControlMode] = None
    Rgb_Mode: Optional[ZagonelRGBMode] = None
    Rgb_Color: Optional[str] = None
    Buzzer_Volume: Optional[int] = None
    Parental_Mode: Optional[ZagonelParentalMode] = None
    Parental_Limit: Optional[int] = None
    Preset_1: Optional[int] = None
    Preset_2: Optional[int] = None
    Preset_3: Optional[int] = None
    Preset_4: Optional[int] = None
    Wifi_SSID: Optional[str] = None


@dataclass
class ZagonelStatus(ZagonelBase):
    """ZagonelStatus."""

    Type: Optional[Literal["Status"]] = None
    St: Optional[str] = None
    Fl: Optional[int] = None
    Vi: Optional[int] = None
    Ti: Optional[int] = None
    To: Optional[int] = None
    Ts: Optional[int] = None
    Ps: Optional[int] = None
    De: Optional[int] = None
    Pw: Optional[int] = None
    Hp: Optional[int] = None
    Up: Optional[int] = None
    Pp: Optional[int] = None
    Wi: Optional[int] = None


@dataclass
class ZagonelData(ZagonelBase):
    """ZagonelData."""

    chars: Optional[ZagonelChars] = None
    status: Optional[ZagonelStatus] = None


class ZagonelApiClient:
    """Sample API Client."""

    def __init__(
            self,
            device_id: str
    ) -> None:
        """Sample API Client."""
        self._device_id = device_id
        self._client = mqtt.Client(transport="websockets")
        self.data: Optional[ZagonelData] = None
        self.waiting_queue: list[Future] = []

    def on_connect(self, _userdata=None, _flags_dict=None, _reason=None, _properties=None):
        """on_connect."""
        self._client.subscribe(f"{self._device_id}_SA")

    def on_message(self, _client=None, _userdata=None, message: mqtt.MQTTMessage = None):
        """on_message."""
        payload: dict = json.loads(message.payload)
        _LOGGER.debug(f"Got message {payload}")
        if payload.get("Type") == "Chars":
            if not self.data:
                chars = ZagonelChars.from_dict(payload)
                self.data = ZagonelData(chars=chars)
            elif not self.data.chars:
                self.data.chars = ZagonelChars.from_dict(payload)
            else:
                self.data.chars.update(payload)
        elif payload.get("Type") == "Status":
            if not self.data:
                status = ZagonelStatus.from_dict(payload)
                self.data = ZagonelData(status=status)
            elif not self.data.status:
                self.data.status = ZagonelStatus.from_dict(payload)
            else:
                self.data.status.update(payload)
        if len(self.waiting_queue) > 0:
            fut = self.waiting_queue.pop()
            loop = fut.get_loop()
            loop.call_soon_threadsafe(fut.set_result, True)

    def is_connected(self):
        """is_connected."""
        return self._client.is_connected()

    async def connect(self):
        """connect."""
        if not self.is_connected():
            self._client.on_connect = self.on_connect
            self._client.on_message = self.on_message
            self._client.connect(host="smartbanho.zagonel.com.br", port=58083)
            self._client.loop_start()

    async def send_command(self, payload: dict):
        """send_command."""
        if self.is_running():
            raise ZagonelApiClientError("Can't send commands while device is running")
        info = self._client.publish(f"{self._device_id}_AS", json.dumps(payload))
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            raise ZagonelApiClientError(f"Failed to publish ({mqtt.error_string(info.rc)})")
        _LOGGER.debug(f"Sent message {payload}")
        try:
            async with async_timeout.timeout(5):
                fut = Future()
                self.waiting_queue.append(fut)
                await fut
        except TimeoutError as exception:
            raise ZagonelApiClientError(exception) from exception

    def is_running(self):
        """Check if device is running."""
        return self.data.status.St == "RUN" if self.data and self.data.status else False

    async def async_load_data(self):
        """Get data from the API."""
        if not self.is_connected():
            await self.connect()
        await self.send_command({"command": "getChars"})
        await self.send_command({"command": "getStatus"})
