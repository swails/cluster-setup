""" Reads a configuration file. Example is shown below

[JENKINS]
url = https://jenkins.jasonswails.com
username = myuser
token = encrypted-secret-token

[AGENTS]
username = username
password = encrypted-password-or-ssh-key-passcode
private_key = encrypted-contents-of-ssh-key-file

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
import os
from dataclasses import dataclass
from typing import List, Optional, Callable

from asyncssh import SSHKey, import_private_key

from .encryption import decrypt
from .nodes import SSHConfig


PASSWORD = os.environ.get("NODEMONITOR_ENCRYPTION_PASSWORD", None)


@dataclass
class JenkinsConfig:
    url: str
    username: str
    token: str

    def __repr__(self):
        return f"<JenkinsConfig; url={self.url}; username={self.username}; token={self.token}>"

    @classmethod
    def create(cls, url: str, username: str, token: str) -> JenkinsConfig:
        if PASSWORD is None:
            raise ValueError("Must set a decryption password environment variable NODEMONITOR_ENCRYPTION_PASSWORD")
        return JenkinsConfig(url=url, username=username, token=decrypt(token, PASSWORD))


@dataclass
class InfluxConfig:
    hostname: str
    username: str
    password: str
    database: str

    def __repr__(self):
        return (f"<InfluxConfig; hostname={self.hostname}; username={self.username}; "
                f"password={self.password}; database={self.database}>")

    @classmethod
    def create(cls, hostname: str, username: str, password: str, database: str) -> InfluxConfig:
        if PASSWORD is None:
            raise ValueError("Must set a decryption password environment variable NODEMONITOR_ENCRYPTION_PASSWORD")
        return InfluxConfig(hostname=hostname, username=username, password=decrypt(password, PASSWORD), database=database)


@dataclass
class NodemonitorConfiguration:
    idle_time_before_launch: int
    idle_time_before_shutdown: int
    poll_frequency: int
    node_priority: List[str]

    jenkins: JenkinsConfig
    agent_ssh_config: SSHConfig
    influx: Optional[InfluxConfig] = None

    @classmethod
    def parse_configfile(cls, filename: pathlib.Path) -> NodemonitorConfiguration:
        parser = configparser.ConfigParser()
        parser.read(filename)
        jenkins_config = JenkinsConfig.create(**parser["JENKINS"])
        influx_config = InfluxConfig.create(**parser["INFLUX"]) if "INFLUX" in parser else None
        ssh_config_kwargs = parser["AGENTS"]
        if "private_key" in ssh_config_kwargs:
            ssh_config_kwargs["private_key"] = decrypt(ssh_config_kwargs["private_key"], PASSWORD)
        if "password" in ssh_config_kwargs:
            ssh_config_kwargs["password"] = decrypt(ssh_config_kwargs["password"], PASSWORD)
        else:
            ssh_config_kwargs["password"] = None
        ssh_config = SSHConfig.create(**ssh_config_kwargs)
        kwargs = dict(
            idle_time_before_launch=int(parser["SCHEDULER"].get("idle_time_before_launch", 300)),
            idle_time_before_shutdown=int(parser["SCHEDULER"].get("idle_time_before_shutdown", 300)),
            poll_frequency=int(parser["SCHEDULER"].get("poll_frequency", 30)),
            node_priority=[x.strip() for x in parser["SCHEDULER"].get("node_priority", "").split(",")],
            agent_ssh_config=ssh_config,
            influx=influx_config,
            jenkins=jenkins_config,
        )
        return cls(**kwargs)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config-file", dest="config_file", default="config.ini",
                        help="The name of the config file to parse and print out")

    args = parser.parse_args()

    config = NodemonitorConfiguration.parse_configfile(pathlib.Path(args.config_file))

    for attr in ("idle_time_before_launch", "idle_time_before_shutdown", "poll_frequency"):
        print(f"config.{attr} = {getattr(config, attr)}")

    print()
    for attr in dir(config.agent_ssh_config):
        if attr.startswith("_") or callable(getattr(config.agent_ssh_config, attr)):
            continue
        print(f"config.agent_ssh_config.{attr} = {getattr(config.agent_ssh_config, attr)}")

    print()
    print(repr(config.jenkins))
    print()
    print(repr(config.influx))
