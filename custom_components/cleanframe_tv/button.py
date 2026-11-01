"""One button per allowed app, plus the TV/settings sequence."""
from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .api import BridgeError
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    entities = [TVButton(coordinator, entry, "tv_settings", "TV-Einstellungen", None)]
    entities.extend(TVButton(coordinator, entry, "launch_app", name, app_id)
                    for app_id, name in coordinator.data["apps"].items())
    async_add_entities(entities)

class TVButton(CoordinatorEntity, ButtonEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:television"

    def __init__(self, coordinator, entry, action, name, app_id):
        super().__init__(coordinator)
        self.action = action
        self.app_id = app_id
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{app_id or action}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)}, name="CleanFrame TV",
            manufacturer="Samsung", model="GQ65Q95TDTXZG",
        )

    @property
    def available(self):
        return (super().available and self.coordinator.data.get("online", False)
                and self.coordinator.data.get("compatible", False))

    async def async_press(self):
        try:
            await self.coordinator.client.action(self.action, self.app_id)
        except BridgeError as err:
            raise HomeAssistantError(str(err)) from err
