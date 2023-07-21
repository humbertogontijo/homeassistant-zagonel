"""Sample API Client."""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from enum import Enum, IntEnum
from typing import Any, Literal

import paho.mqtt.client as mqtt
from dacite import Config, from_dict

from custom_components.zagonel.zagonel_future import ZagonelFuture

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

    Type: Literal["Chars"] | None = None
    User_Id: str | None = None
    Device_Id: str | None = None
    Hw_Id: str | None = None
    Hw_Version: str | None = None
    Fw_Version: str | None = None
    Fw_Timestamp: str | None = None
    Control_Mode: ZagonelControlMode | None = None
    Rgb_Mode: ZagonelRGBMode | None = None
    Rgb_Color: str | None = None
    Buzzer_Volume: int | None = None
    Parental_Mode: ZagonelParentalMode | None = None
    Parental_Limit: int | None = None
    Preset_1: int | None = None
    Preset_2: int | None = None
    Preset_3: int | None = None
    Preset_4: int | None = None
    Wifi_SSID: str | None = None


@dataclass
class ZagonelStatus(ZagonelBase):
    """ZagonelStatus."""

    Type: Literal["Status"] | None = None
    St: str | None = None
    Fl: int | None = None
    Vi: int | None = None
    Ti: int | None = None
    To: int | None = None
    Ts: int | None = None
    Ps: int | None = None
    De: int | None = None
    Pw: int | None = None
    Hp: int | None = None
    Up: int | None = None
    Pp: int | None = None
    Wi: int | None = None


@dataclass
class ZagonelData(ZagonelBase):
    """ZagonelData."""

    chars: ZagonelChars | None = None
    status: ZagonelStatus | None = None


class ZagonelApiClient:
    """Sample API Client."""

    def __init__(
            self,
            device_id: str
    ) -> None:
        """Sample API Client."""
        self._device_id = device_id
        self._client = mqtt.Client(transport="websockets")
        self.data: ZagonelData | None = None
        self.waiting_queue: list[ZagonelFuture] = []

    def on_connect(self, _userdata=None, _flags_dict=None, _reason=None, _properties=None):
        """on_connect."""
        _LOGGER.debug("Connected to mqtt")
        (info, _) = self._client.subscribe(f"{self._device_id}_SA")
        if info != mqtt.MQTT_ERR_SUCCESS:
            raise ZagonelApiClientError(f"Failed to subscribe ({mqtt.error_string(info)})")
        _LOGGER.debug(f"Subscribed to {self._device_id}_SA")

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
            fut.resolve(True)

    def is_connected(self):
        """is_connected."""
        return self._client.is_connected()

    async def connect(self):
        """connect."""
        if not self.is_connected():
            self._client.on_connect = self.on_connect
            self._client.on_message = self.on_message
            _LOGGER.debug("Connecting to mqtt")
            self._client.connect(host="smartbanho.zagonel.com.br", port=58083)
            self._client.loop_start()

    async def send_command(self, payload: dict):
        """send_command."""
        command = payload["command"]
        if self.is_running() and command == "getChars":
            raise ZagonelApiClientError("Can't send commands while device is running")
        info = self._client.publish(f"{self._device_id}_AS", json.dumps(payload))
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            raise ZagonelApiClientError(f"Failed to publish ({mqtt.error_string(info.rc)})")
        _LOGGER.debug(f"Sent message {payload}")
        try:
            fut = ZagonelFuture()
            self.waiting_queue.append(fut)
            await fut.async_get(5)
        except TimeoutError as exception:
            raise ZagonelApiClientError(exception) from exception

    def is_running(self):
        """Check if device is running."""
        return self.data.status.St == "RUN" if self.data and self.data.status else False

    async def async_load_data(self):
        """Get data from the API."""
        if not self.is_connected():
            await self.connect()
        await self.send_command({"command": "getStatus"})
        if not self.is_running():
            await self.send_command({"command": "getChars"})
