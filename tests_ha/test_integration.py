"""Tests using the installed Home Assistant classes, with mocked bridge I/O."""
import asyncio
import importlib.metadata
from unittest.mock import AsyncMock, MagicMock

import pytest

TEST_MAC = ":".join(["00", "11", "22", "33", "44", "55"])
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
    assert fields == {'host', 'port', 'samsung_entity', 'wake_mac', 'wake_broadcast'}

@pytest.mark.asyncio
async def test_http_timeout_no_retry():
    session = MagicMock()
    session.request.side_effect = TimeoutError
    client = BridgeClient(session, '192.0.2.1', 8767)
    with pytest.raises(BridgeError): await client.action('tv_settings')
    assert session.request.call_count == 1


def test_no_url_injection():
    with pytest.raises(ValueError): BridgeClient(None, 'example.org/path', 8767)

@pytest.mark.asyncio
async def test_reconfigure_preserves_entry_and_changes_bridge():
    from unittest.mock import patch
    flow = ConfigFlow()
    flow.hass = MagicMock()
    entry = MagicMock(entry_id='preserved', data={'host': '192.0.2.1', 'port': 8767})
    flow._get_reconfigure_entry = MagicMock(return_value=entry)
    flow._async_current_entries = MagicMock(return_value=[entry])
    flow.async_update_reload_and_abort = MagicMock(return_value={'type': 'abort'})
    with patch('custom_components.cleanframe_tv.config_flow.async_get_clientsession'), patch('custom_components.cleanframe_tv.config_flow.BridgeClient') as cls:
        cls.return_value.status = AsyncMock(return_value={})
        result = await flow.async_step_reconfigure({'host': '192.0.2.2', 'port': 8767})
    flow.async_update_reload_and_abort.assert_called_once_with(entry, unique_id='192.0.2.2:8767', data={'host': '192.0.2.2', 'port': 8767})

@pytest.mark.asyncio
async def test_reconfigure_failure_keeps_current_entry():
    from unittest.mock import patch
    flow = ConfigFlow()
    flow.hass = MagicMock()
    entry = MagicMock(entry_id='preserved', data={'host': '192.0.2.1', 'port': 8767})
    flow._get_reconfigure_entry = MagicMock(return_value=entry)
    flow.async_update_reload_and_abort = MagicMock()
    with patch('custom_components.cleanframe_tv.config_flow.async_get_clientsession'), patch('custom_components.cleanframe_tv.config_flow.BridgeClient') as cls:
        cls.return_value.status = AsyncMock(side_effect=BridgeError('offline'))
        result = await flow.async_step_reconfigure({'host': '192.0.2.2', 'port': 8767})
    assert result['errors'] == {'base': 'cannot_connect'}
    flow.async_update_reload_and_abort.assert_not_called()

@pytest.mark.asyncio
async def test_player_wakes_without_source_and_never_toggles():
    from homeassistant.core import State
    from homeassistant.components.media_player import MediaPlayerEntityFeature as F
    from custom_components.cleanframe_tv.media_player import CleanFramePlayer, send_wake_packet
    entry = MagicMock(entry_id='test', data={'samsung_entity':'media_player.samsung','wake_mac':TEST_MAC})
    player = CleanFramePlayer(entry)
    player.hass = MagicMock()
    player.hass.async_add_executor_job = AsyncMock()
    player.hass.services.async_call = AsyncMock()
    player.hass.states.get.return_value = State('media_player.samsung','off',{'supported_features':int(F.TURN_OFF)})
    assert player.available
    assert player.state == 'off'
    assert player.supported_features & F.TURN_ON
    await player.async_turn_on()
    player.hass.async_add_executor_job.assert_awaited_once_with(send_wake_packet,TEST_MAC,'255.255.255.255')
    await player.async_turn_off()
    player.hass.services.async_call.assert_not_awaited()
    player.hass.states.get.return_value = None
    assert player.state == 'unknown'
    with pytest.raises(HomeAssistantError): await player.async_volume_up()

@pytest.mark.asyncio
async def test_player_forwards_only_to_selected_samsung_entity():
    from homeassistant.core import State
    from homeassistant.components.media_player import MediaPlayerEntityFeature as F
    from custom_components.cleanframe_tv.media_player import CleanFramePlayer
    entry = MagicMock(entry_id='test', data={'samsung_entity':'media_player.samsung'})
    player = CleanFramePlayer(entry)
    player.hass = MagicMock()
    player.hass.services.async_call = AsyncMock()
    player.hass.states.get.return_value = State('media_player.samsung','on',{'supported_features':int(F.VOLUME_SET|F.VOLUME_MUTE|F.TURN_OFF),'volume_level':.12})
    assert player.volume_level == .12
    await player.async_set_volume_level(.13)
    player.hass.services.async_call.assert_awaited_once_with('media_player','volume_set',{'entity_id':'media_player.samsung','volume_level':.13},blocking=True)
    with pytest.raises(HomeAssistantError): await player.async_volume_up()


def test_wake_packet_format():
    from unittest.mock import patch
    from custom_components.cleanframe_tv.media_player import send_wake_packet
    with patch('custom_components.cleanframe_tv.media_player.socket.socket') as cls:
        send_wake_packet(TEST_MAC,'192.0.2.255')
    cls.return_value.__enter__.return_value.sendto.assert_called_once_with(
        b'\xff'*6+bytes.fromhex('001122334455')*16,('192.0.2.255',9))

@pytest.mark.asyncio
async def test_flow_rejects_recursive_media_player_and_invalid_mac():
    from unittest.mock import patch
    flow = ConfigFlow()
    flow.hass = MagicMock()
    with patch('custom_components.cleanframe_tv.config_flow.er.async_get') as registry:
        registry.return_value.async_get.return_value = MagicMock(platform='cleanframe_tv')
        with pytest.raises(ValueError): flow._controls({'samsung_entity':'media_player.cleanframe'})
        registry.return_value.async_get.return_value = MagicMock(platform='samsungtv')
        with pytest.raises(ValueError): flow._controls({'samsung_entity':'media_player.samsung','wake_mac':'bad'})
        assert flow._controls({'samsung_entity':'media_player.samsung','wake_mac':'00-11-22-33-44-55'})['wake_mac']==TEST_MAC
