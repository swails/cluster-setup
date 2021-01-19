""" Wrapper around influx to write events """
import logging
import aiohttp

LOGGER = logging.getLogger(__name__)


class InfluxWriter:

    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url
        self.db = db
        self.username = username
        self._password = password

    async def write_point(self, node_name: str, power_mode: int):
        node_name = node_name.replace(" ", "\\ ")
        data = f"node_power,node_name={node_name} value={power_mode}"
        async with aiohttp.ClientSession(auth=aiohttp.BasicAuth(self.username, self._password)) as session:
            async with session.post(
                f"{self.url}/write", params=dict(db=self.db), data=data
            ) as resp:
                try:
                    resp.raise_for_status()
                except aiohttp.ClientResponseError:
                    text = await resp.text()
                    LOGGER.exception(f"Failed to log influxdb event: {text}")
