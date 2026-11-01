"""Tests using the installed Home Assistant classes, with mocked bridge I/O."""
import asyncio
import importlib.metadata
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import UpdateFailed
from custom_components.cleanframe_tv.api import BridgeClient, BridgeError
from custom_components.cleanframe_tv.button import TVButton
from custom_components.cleanframe_tv.config_flow import ConfigFlow

@pytest.mark.asyncio
async def test_api_accepts_only_matching_receipt():
    client = BridgeClient(None, '192.0.2.1', 8767)
    async def response(method, path, data):
        return {'accepted': True, 'request_id': data['request_id'], 'display_verified': False}
    client.request = AsyncMock(side_effect=response)
    assert (await client.action('tv_settings'))['accepted']
    client.request = AsyncMock(return_value={'accepted': True, 'request_id': 'wrong'})
    with pytest.raises(BridgeError): await client.action('tv_settings')
    assert client.request.await_count == 1

@pytest.mark.asyncio
async def test_status_validates_protocol():
    client = BridgeClient(None, '192.0.2.1', 8767)
    client.request = AsyncMock(return_value={'api_version': 2, 'apps': {}})
    with pytest.raises(BridgeError): await client.status()

@pytest.mark.asyncio
async def test_button_availability_and_failure():
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.data = {'online': False, 'compatible': True}
    coordinator.client.action = AsyncMock()
    entry = MagicMock(entry_id='example')
    button = TVButton(coordinator, entry, 'tv_settings', 'TV-Einstellungen', None)
    assert not button.available
    coordinator.data['online'] = True
    assert button.available
    await button.async_press()
    coordinator.client.action.assert_awaited_once_with('tv_settings', None)
    coordinator.client.action.side_effect = BridgeError('unreachable')
    with pytest.raises(HomeAssistantError): await button.async_press()
    coordinator.last_update_success = False
    assert not button.available

@pytest.mark.asyncio
async def test_flow_shows_no_token_input():
    flow = ConfigFlow()
    result = await flow.async_step_user()
    assert result['type'] == 'form'
    fields = {str(k) for k in result['data_schema'].schema}
    assert fields == {'host', 'port'}

@pytest.mark.asyncio
async def test_http_timeout_no_retry():
    session = MagicMock()
    session.request.side_effect = TimeoutError
    client = BridgeClient(session, '192.0.2.1', 8767)
    with pytest.raises(BridgeError): await client.action('tv_settings')
    assert session.request.call_count == 1


def test_no_url_injection():
    with pytest.raises(ValueError): BridgeClient(None, 'example.org/path', 8767)
