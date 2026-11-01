"""Configure the local bridge, without a token field."""
import ipaddress
import re
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import entity_registry as er, selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .api import BridgeClient, BridgeError
from .const import DOMAIN, DEFAULT_PORT

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def _controls(self, user_input):
        data = {}
        source = user_input.get("samsung_entity")
        if source:
            entity = er.async_get(self.hass).async_get(source)
            if not entity or entity.platform != "samsungtv" or not source.startswith("media_player."):
                raise ValueError("Select an existing Samsung TV media player")
            data["samsung_entity"] = source
        mac = user_input.get("wake_mac", "").strip().replace("-", ":").lower()
        if mac:
            if not source or not re.fullmatch(r"(?:[0-9a-f]{2}:){5}[0-9a-f]{2}", mac):
                raise ValueError("Invalid Wake-on-LAN address")
            data["wake_mac"] = mac
        if user_input.get("wake_broadcast"):
            data["wake_broadcast"] = str(ipaddress.IPv4Address(user_input["wake_broadcast"]))
        return data

    def _control_schema(self, data=None):
        data = data or {}
        return {
            vol.Optional("samsung_entity", description={"suggested_value": data.get("samsung_entity")}): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="media_player", integration="samsungtv")),
            vol.Optional("wake_mac", description={"suggested_value": data.get("wake_mac", "")}): str,
            vol.Optional("wake_broadcast", default=data.get("wake_broadcast", "255.255.255.255")): str,
        }

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                host = str(ipaddress.IPv4Address(user_input["host"]))
                port = user_input["port"]
                controls = self._controls(user_input)
                client = BridgeClient(async_get_clientsession(self.hass), host, port)
                await client.status()  # TV may be off; reachable bridge is sufficient.
            except (ValueError, BridgeError):
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="CleanFrame TV", data={"host": host, "port": port, **controls})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({
            vol.Required("host"): str,
            vol.Required("port", default=DEFAULT_PORT): vol.All(vol.Coerce(int), vol.Range(min=1024, max=65535)),
            **self._control_schema(),
        }), errors=errors)

    async def async_step_reconfigure(self, user_input=None):
        entry = self._get_reconfigure_entry()
        errors = {}
        if user_input is not None:
            try:
                host = str(ipaddress.IPv4Address(user_input["host"]))
                port = user_input["port"]
                controls = self._controls({**entry.data, **user_input})
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
                    entry, unique_id=unique_id, data={"host": host, "port": port, **controls},
                )
        return self.async_show_form(step_id="reconfigure", data_schema=vol.Schema({
            vol.Required("host", default=entry.data["host"]): str,
            vol.Required("port", default=entry.data["port"]): vol.All(vol.Coerce(int), vol.Range(min=1024, max=65535)),
            **self._control_schema(entry.data),
        }), errors=errors)
