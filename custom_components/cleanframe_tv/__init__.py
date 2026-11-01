"""Home Assistant entities backed by the launch-only native bridge."""
from datetime import timedelta
from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import logging
from .api import BridgeClient, BridgeError
from .const import DOMAIN

PLATFORMS = [Platform.BUTTON]
_LOGGER = logging.getLogger(__name__)

class TVCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=30))
        self.client = BridgeClient(async_get_clientsession(hass), entry.data["host"], entry.data["port"])

    async def _async_update_data(self):
        try:
            return await self.client.status()
        except BridgeError as err:
            raise UpdateFailed(str(err)) from err

async def async_setup_entry(hass, entry):
    coordinator = TVCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
