"""Configure the local bridge, without a token field."""
import ipaddress
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .api import BridgeClient, BridgeError
from .const import DOMAIN, DEFAULT_PORT

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                host = str(ipaddress.IPv4Address(user_input["host"]))
                port = user_input["port"]
                client = BridgeClient(async_get_clientsession(self.hass), host, port)
                await client.status()  # TV may be off; reachable bridge is sufficient.
            except (ValueError, BridgeError):
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="CleanFrame TV", data={"host": host, "port": port})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({
            vol.Required("host"): str,
            vol.Required("port", default=DEFAULT_PORT): vol.All(vol.Coerce(int), vol.Range(min=1024, max=65535)),
        }), errors=errors)

    async def async_step_reconfigure(self, user_input=None):
        entry = self._get_reconfigure_entry()
        errors = {}
        if user_input is not None:
            try:
                host = str(ipaddress.IPv4Address(user_input["host"]))
                port = user_input["port"]
                client = BridgeClient(async_get_clientsession(self.hass), host, port)
                await client.status()
            except (ValueError, BridgeError):
                errors["base"] = "cannot_connect"
            else:
                unique_id = f"{host}:{port}"
                if any(other.entry_id != entry.entry_id and other.unique_id == unique_id
                       for other in self._async_current_entries()):
                    return self.async_abort(reason="already_configured")
                return self.async_update_reload_and_abort(
                    entry, unique_id=unique_id, data={"host": host, "port": port},
                )
        return self.async_show_form(step_id="reconfigure", data_schema=vol.Schema({
            vol.Required("host", default=entry.data["host"]): str,
            vol.Required("port", default=entry.data["port"]): vol.All(vol.Coerce(int), vol.Range(min=1024, max=65535)),
        }), errors=errors)
