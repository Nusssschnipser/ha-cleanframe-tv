"""TV power and volume using Wake-on-LAN and an existing Samsung entity."""
import socket

from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature
from homeassistant.const import STATE_OFF, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN

FORWARDED_FEATURES = (
    MediaPlayerEntityFeature.TURN_OFF | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_STEP | MediaPlayerEntityFeature.VOLUME_MUTE
)


def send_wake_packet(mac, broadcast):
    """Send a single standard magic packet; no power toggle or retry."""
    address = bytes.fromhex(mac.replace(":", ""))
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(b"\xff" * 6 + address * 16, (broadcast, 9))


async def async_setup_entry(hass, entry, async_add_entities):
    if entry.data.get("samsung_entity"):
        async_add_entities([CleanFramePlayer(entry)])


class CleanFramePlayer(MediaPlayerEntity):
    _attr_has_entity_name = True
    _attr_name = "TV-Steuerung"
    _attr_device_class = "tv"
    _attr_should_poll = False

    def __init__(self, entry):
        self.source = entry.data["samsung_entity"]
        self.mac = entry.data.get("wake_mac")
        self.broadcast = entry.data.get("wake_broadcast", "255.255.255.255")
        self._attr_unique_id = f"{entry.entry_id}_media_player"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)}, name="CleanFrame TV",
            manufacturer="Samsung", model="GQ65Q95TDTXZG",
        )

    async def async_added_to_hass(self):
        self.async_on_remove(async_track_state_change_event(
            self.hass, [self.source], self._source_changed,
        ))

    @callback
    def _source_changed(self, event):
        self.async_write_ha_state()

    @property
    def source_state(self):
        return self.hass.states.get(self.source)

    @property
    def available(self):
        state = self.source_state
        return bool(self.mac or (state and state.state != STATE_UNAVAILABLE))

    @property
    def state(self):
        state = self.source_state
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return STATE_UNKNOWN
        return state.state

    @property
    def supported_features(self):
        state = self.source_state
        features = MediaPlayerEntityFeature.TURN_ON if self.mac else MediaPlayerEntityFeature(0)
        if state and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            features |= MediaPlayerEntityFeature(state.attributes.get("supported_features", 0)) & FORWARDED_FEATURES
        return features

    @property
    def volume_level(self):
        state = self.source_state
        return state.attributes.get("volume_level") if state else None

    @property
    def is_volume_muted(self):
        state = self.source_state
        return state.attributes.get("is_volume_muted") if state else None

    async def async_turn_on(self):
        if not self.mac:
            raise HomeAssistantError("No Wake-on-LAN address configured")
        await self.hass.async_add_executor_job(send_wake_packet, self.mac, self.broadcast)

    async def _forward(self, service, feature, **data):
        state = self.source_state
        if not state or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, STATE_OFF):
            raise HomeAssistantError("Samsung TV is not online")
        if not (self.supported_features & feature):
            raise HomeAssistantError("Samsung TV does not support this action")
        await self.hass.services.async_call(
            "media_player", service, {"entity_id": self.source, **data}, blocking=True,
        )

    async def async_turn_off(self):
        if self.state == STATE_OFF:
            return
        await self._forward("turn_off", MediaPlayerEntityFeature.TURN_OFF)

    async def async_set_volume_level(self, volume):
        await self._forward("volume_set", MediaPlayerEntityFeature.VOLUME_SET, volume_level=volume)

    async def async_volume_up(self):
        await self._forward("volume_up", MediaPlayerEntityFeature.VOLUME_STEP)

    async def async_volume_down(self):
        await self._forward("volume_down", MediaPlayerEntityFeature.VOLUME_STEP)

    async def async_mute_volume(self, mute):
        await self._forward("volume_mute", MediaPlayerEntityFeature.VOLUME_MUTE, is_volume_muted=mute)
