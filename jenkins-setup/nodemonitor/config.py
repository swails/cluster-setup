""" Reads a configuration file. Example is shown below

[JENKINS]
url = https://jenkins.jasonswails.com
username = myuser
token = encrypted-secret-token

[AGENTS]
ssh_username = username
ssh_password = encrypted-password-or-ssh-key-passcode
ssh_key = encrypted-contents-of-ssh-key-file

[INFLUX]
username = username
password = encrypted-password
hostname = 192.168.1.55
database = name-of-db

[SCHEDULER]
idle_time_before_launch = 300   # seconds
idle_time_before_shutdown = 300 # seconds
node_priority = Supergirl,
                Wonder Woman,
                Green Lantern,
                Green Arrow,
                Supergirl-cuda,
                Wonder Woman-cuda,
                Green Lantern-cuda,
                Green Arrow-cuda
"""
from __future__ import annotations

import configparser
import pathlib
from dataclasses import dataclass
from typing import List, Optional

from asyncssh import SSHKey, import_private_key

@dataclass
class JenkinsConfig:
    url: str
    username: str
    token: str


@dataclass
class InfluxConfig:
    hostname: str
    username: str
    password: str
    database: str


@dataclass
class AgentConfig:
    username: str
    password: Optional[str] = None
    ssh_key: Optional[SSHKey] = None

    @classmethod
    def create(cls, username: str, password: str, ssh_key: Optional[str] = None) -> AgentConfig:
        if ssh_key is not None:
            loaded_ssh_key = import_private_key(ssh_key, password)
        else:
            loaded_ssh_key = None
        return cls(username=username, password=password, ssh_key=loaded_ssh_key)


@dataclass
class NodemonitorConfiguration:
    idle_time_before_launch: int
    idle_time_before_shutdown: int
    node_priority: List[str]

    jenkins: JenkinsConfig
    influx: InfluxConfig
    agent_ssh_config: AgentConfig

    @classmethod
    def parse_configfile(cls, filename: pathlib.Path) -> NodemonitorConfiguration:
        parser = configparser.ConfigParser()
        parser.read(filename)
        return cls()