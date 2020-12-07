""" A set of classes for monitoring Jenkins job queues and states """
import datetime
import logging
import re
from typing import List, Dict, Any, Union

import aiohttp

from .nodes import JenkinsAgent, AgentStatus, Node

LOGGER = logging.getLogger(__name__)

class QueuedJob:

    all_nodes_offline = re.compile(r'^All nodes of label .(\w+). are offline')
    waiting_for_node = re.compile(r'^Waiting for next available executor on .(\w+).')
    some_nodes_offline = re.compile(r'.([\w \-]+). is offline')

    def __init__(self, id: int, stuck: bool, reason: str, queued_since: datetime.datetime):
        self.id = id
        self.stuck = stuck
        self.waiting_for = self._extract_wait_from_reason(reason)
        self.queued_since = queued_since

    def __repr__(self):
        stuck = 'stuck ' if self.stuck else ''
        return f'<{self.__class__.__name__} {self.id}; {stuck}waiting for {self.waiting_for} since {self.queued_since.isoformat()}>'

    def _extract_wait_from_reason(self, reason: str) -> Dict[str, Union[List[str], str]]:
        if self.stuck:
            rematch = self.all_nodes_offline.match(reason)
        else:
            rematch = self.waiting_for_node.match(reason)

        if rematch is None:
            if not self.stuck:
                nodes = self.some_nodes_offline.findall(reason)
                if nodes:
                    return dict(nodes=nodes)
            LOGGER.error(f'Could not find needed node via regex match for [{reason}]')
            return None

        return dict(label=rematch.groups()[0])

class Jenkins:

    def __init__(self,
                 url: str,
                 username: str,
                 token: str):
        self.url = url.rstrip('/')
        self.username = username
        self._token = token
        self.nodes = dict()
        self._session = aiohttp.ClientSession(auth=aiohttp.BasicAuth(username, token))

    def __repr__(self):
        return f"<{self.__class__.__name__}; {len(self.nodes)} agents>"

    async def fetch_computers(self):
        """ Fetches list of nodes from Jenkins using the REST interface """
        comp_attr = "displayName,offline,numExecutors"
        req_attr = "busyExecutors,name" if not self.nodes else "busyExecutors"
        params = dict(depth="1", tree=f"computer[{comp_attr},assignedLabels[{req_attr}]]")
        response = await self._request_json("get", "computer/api/json", params=params)
        for computer in response['computer']:
            self._process_computer(computer)

    async def get_queue(self) -> List[QueuedJob]:
        """ Fetches all of the builds that are currently running """
        response = await self._request_json("get", f"queue/api/json")
        # Gets the list of all builds and the reasons they are not running
        return [
            QueuedJob(item['id'], item['stuck'], item['why'],
                      datetime.datetime.fromtimestamp(item['inQueueSince'] / 1000))
            for item in response['items']
        ]

    async def build_job(self, job_path: str):
        # The href in a job with path my/path/here is /job/my/job/path/job/here
        href = f'/job/{"/job/".join(job_path.split("/"))}/build'
        await self._request_json('post', href)

    def _process_computer(self, computer: Dict[str, Any]) -> JenkinsAgent:
        name = computer['displayName']
        status = AgentStatus.Offline if computer['offline'] else AgentStatus.Online
        # To save on data transfer, we only ask for labels the first time
        labels = [label.get('name', []) for label in computer['assignedLabels']]
        num_executors = computer['numExecutors']
        try:
            busy_executors = computer['assignedLabels'][0]['busyExecutors']
        except IndexError:
            LOGGER.warning(f"Could not find any assigned labels for {computer}")
            busy_executors = 0
        if name in self.nodes:
            self.nodes[name].status = status
            self.nodes[name].num_executors = num_executors
            self.nodes[name].busy_executors = busy_executors
        else:
            self.nodes[name] = JenkinsAgent(name, labels, status, num_executors, busy_executors)

    async def _request_json(self,
                            verb: str,
                            href: str,
                            params: Dict[str, str] = None,
                            payload: Dict[str, str] = None,
                            data: bytes = None) -> Dict[str, Any]:
        async with self._session.request(verb, f"{self.url}/{href}", params=params, data=data, json=payload) as resp:
            async with resp:
                if resp.status >= 400:
                    text = await resp.text()
                    LOGGER.warning(f"Failed requesting {href} - {resp.status} [{text}]")
                try:
                    return await resp.json()
                except aiohttp.ContentTypeError:
                    return await resp.text()

    async def close(self):
        await self._session.close()
