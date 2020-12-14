""" Classes for managing Jenkins agents """
import asyncio
import concurrent.futures
import enum
import logging
import pathlib
import time
from dataclasses import dataclass
from typing import List, Optional

import asyncssh
from wakeonlan import send_magic_packet

LOGGER = logging.getLogger(__name__)

@dataclass
class SSHConfig:
    username: str
    private_key: Optional[pathlib.Path] = None
    passphrase: Optional[str] = None
    password: Optional[str] = None

    def options(self) -> dict:
        ssh_options = dict(username=self.username)
        if self.private_key:
            ssh_options['client_keys'] = str(self.private_key)
            if self.passphrase:
                ssh_options['passphrase'] = self.passphrase
        else:
            ssh_options['password'] = self.password
        return ssh_options

class NodeStatus(enum.Enum):
    On = "On"
    Off = "Off"

class Node:

    def __init__(self, name: str, local_ip_address: str, mac_address: str):
        self.name = name
        self.local_ip_address = local_ip_address
        self.mac_address = mac_address

        self._time_shutdown = None
        self._time_woken = None

    async def is_available(self) -> bool:
        open_fut = asyncio.open_connection(self.local_ip_address, 22)
        try:
            _, writer = await asyncio.wait_for(open_fut, 3)
        except (concurrent.futures.TimeoutError, OSError):
            return False
        else:
            writer.close()
            return True

    async def run_ssh_command(self, config: SSHConfig, command: str):
        async with asyncssh.connect(self.local_ip_address, **config.options()) as conn:
            return await conn.run(command)

    async def is_in_use(self, config: SSHConfig):
        async with asyncssh.connect(self.local_ip_address, **config.options()) as conn:
            result = await conn.run("users")

        LOGGER.debug(f"Saw '{result.stdout.strip()}' when looking for logged-in users")
        all_users = set(result.stdout.strip().split())
        return not all_users.issubset({'jenkins', ''})

    async def wakeup(self):
        if await self.is_available():
            LOGGER.info(f"{self.name} is already awake")
            return True
        LOGGER.info(f'WoL {self.name} - Initiating wake-on-lan')
        self._time_woken = time.time()
        send_magic_packet(self.mac_address.lower())
        for _ in range(20):
            # Wait up to 2 minutes to wake up (is_available will wait 3 seconds if it's off, too)
            await asyncio.sleep(3)
            LOGGER.info(f"WoL {self.name} - Checking node availability")
            available = await self.is_available()
            if available:
                LOGGER.info(f"WoL {self.name} - now available!")
                return True
        LOGGER.warning(f"WoL {self.name} - Did not respond >2 minutes after WoL sent!")
        # One last try
        return await self.is_available()

    @property
    def time_shutdown(self) -> float:
        return 0.0 if self._time_shutdown is None else self._time_shutdown

    @property
    def time_woken(self) -> float:
        return 0.0 if self._time_woken is None else self._time_woken

    async def shutdown(self, admin_config: SSHConfig, force: bool = False):
        if await self.is_in_use(admin_config) and not force:
            LOGGER.info(f'{self.name} is in use. Not shutting down')
            return
        if await self.is_available():
            self._time_shutdown = time.time()
            await self.run_ssh_command(admin_config, 'sudo shutdown +1')
        else:
            LOGGER.info(f'{self.name} cannot shut down, not even awake')

NODES = {
    'Batman': Node('Batman', '192.168.1.3', 'C8:60:00:78:00:0C'),
    'Green Lantern': Node('Green Lantern', '192.168.1.140', '04:D9:F5:B9:F7:0B'),
    'Green Arrow': Node('Green Arrow', '192.168.1.141', '1C:69:7A:31:52:21'),
    'Wonder Woman': Node('Wonder Woman', '192.168.1.142', '00:D8:61:FF:31:47'),
    'Supergirl': Node('Supergirl', '192.168.1.143', '2C:F0:5D:27:5E:AA'),
}
# Now add the CUDA nodes
NODES['Green Lantern-cuda'] = NODES['Green Lantern']
NODES['Green Arrow-cuda'] = NODES['Green Arrow']
NODES['Wonder Woman-cuda'] = NODES['Wonder Woman']
NODES['Supergirl-cuda'] = NODES['Supergirl']


class AgentStatus(enum.Enum):
    Online = 'Online'
    Offline = 'Offline'

class JenkinsAgent:

    def __init__(self, name: str, labels: List[str], status: AgentStatus,
                 num_executors: int, busy_executors: int):
        self.name = name
        self.labels = labels
        self.status = status
        self.node = NODES.get(self.name, None)
        self.num_executors = num_executors
        self.busy_executors = busy_executors

        self._time_last_job_finished = None
        self._time_booted = None

    def __repr__(self):
        return (f"<{self.__class__.__name__} {self.name}; labels={self.labels}; "
                f"{self.num_executors} executors ({self.busy_executors} busy); "
                f"{'no ' if self.node is None else ''}node; {self.status.value}>")

    def is_offline(self):
        return self.status is AgentStatus.Offline

    def is_online(self):
        return self.status is AgentStatus.Online

    async def is_available(self):
        return self.node is not None and await self.node.is_available()

    async def wakeup(self) -> bool:
        if self.node is None:
            LOGGER.info(f'Cannot wake up {self.name} - I have no known node')
            return False
        return await self.node.wakeup()

    async def shutdown(self, admin_config: SSHConfig, force: bool = False):
        if self.node is None:
            LOGGER.info(f'Cannot shut down {self.name} - I have no known node')
            return
        await self.node.shutdown(admin_config, force)

    @property
    def time_shutdown(self):
        if self.node is None:
            return None
        return self.node.time_shutdown

    @property
    def time_woken(self):
        if self.node is None:
            return None
        return self.node.time_woken
