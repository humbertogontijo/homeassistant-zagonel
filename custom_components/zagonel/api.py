"""Sample API Client."""
from __future__ import annotations

import json
import logging
from asyncio import Future
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Literal, Optional

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


class ZagonelControlMode(int, Enum):
    """ZagonelControlMode."""

    MANUAL = 0
    AUTOMATIC = 1


class ZagonelParentalMode(int, Enum):
    """ZagonelParentalMode."""

    OFF = 0
    SOUND = 1
    SHUTDOWN = 2
    SOUND_AND_SHUTDOWN = 3


class ZagonelRGBMode(int, Enum):
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

    Type: Literal["Chars"]
    User_Id: str
    Device_Id: str
    Hw_Id: str
    Hw_Version: str
    Fw_Version: str
    Fw_Timestamp: str
    Control_Mode: ZagonelControlMode
    Rgb_Mode: ZagonelRGBMode
    Rgb_Color: str
    Buzzer_Volume: int
    Parental_Mode: ZagonelParentalMode
    Parental_Limit: int
    Preset_1: int
    Preset_2: int
    Preset_3: int
    Preset_4: int
    Wifi_SSID: str


@dataclass
class ZagonelStatus(ZagonelBase):
    """ZagonelStatus."""

    Type: Literal["Status"]
    Fl: int
    Vi: int
    Ti: int
    To: int
    Ts: int
    Ps: int
    De: int
    Pw: int
    Hp: int
    Up: int
    Pp: int
    Wi: int


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
        self.status_fut: Optional[Future] = None
        self.chars_fut: Optional[Future] = None

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
            loop = self.chars_fut.get_loop()
            loop.call_soon_threadsafe(self.chars_fut.set_result, True)
        elif payload.get("Type") == "Status":
            if not self.data:
                status = ZagonelStatus.from_dict(payload)
                self.data = ZagonelData(status=status)
            elif not self.data.status:
                self.data.status = ZagonelStatus.from_dict(payload)
            else:
                self.data.status.update(payload)
            loop = self.status_fut.get_loop()
            loop.call_soon_threadsafe(self.status_fut.set_result, True)

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
        command = payload["command"]
        fut = Future()
        if command == "getStatus":
            self.status_fut = fut
        else:
            self.chars_fut = fut
        info = self._client.publish(f"{self._device_id}_AS", json.dumps(payload))
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            raise ZagonelApiClientError(f"Failed to publish ({mqtt.error_string(info.rc)})")
        _LOGGER.debug(f"Sent message {payload}")
        if fut:
            await fut

    async def async_load_data(self):
        """Get data from the API."""
        if not self.is_connected():
            await self.connect()
        if not self.data:
            await self.send_command({"command": "getChars"})
            await self.send_command({"command": "getStatus"})
