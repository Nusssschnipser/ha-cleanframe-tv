"""Async client; never retries actions after an ambiguous response."""
import asyncio
import ipaddress
import uuid

import aiohttp

class BridgeError(Exception):
    """Bridge rejected a request or could not be reached."""

class BridgeClient:
    def __init__(self, session, host, port):
        self.session = session
        # Literal IP only; no URL fragments, credentials or user-controlled paths.
        self.host = str(ipaddress.IPv4Address(host))
        self.port = int(port)
        if not 1024 <= self.port <= 65535:
            raise ValueError("Invalid port")
        self.url = f"http://{self.host}:{self.port}"

    async def request(self, method, path, data=None):
        try:
            async with asyncio.timeout(120):
                async with self.session.request(method, self.url + path, json=data, allow_redirects=False) as response:
                    if response.status != 200:
                        raise BridgeError(f"Bridge returned HTTP {response.status}; check developer access and IP allowlist")
                    result = await response.json()
                    if not isinstance(result, dict):
                        raise BridgeError("Invalid bridge response")
                    return result
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise BridgeError("Bridge unreachable or invalid response; command state may be unknown. No automatic retry.") from err

    async def status(self):
        result = await self.request("GET", "/v1/status")
        if (result.get("api_version") != 1 or not isinstance(result.get("apps"), dict)
                or not isinstance(result.get("online"), bool) or not isinstance(result.get("compatible"), bool)):
            raise BridgeError("Unsupported bridge response")
        return result

    async def action(self, action, app_id=None):
        request = {"action": action, "request_id": uuid.uuid4().hex}
        if app_id is not None:
            request["app_id"] = app_id
        result = await self.request("POST", "/v1/action", request)
        if result.get("accepted") is not True or result.get("request_id") != request["request_id"]:
            raise BridgeError("TV did not acknowledge this request")
        return result
