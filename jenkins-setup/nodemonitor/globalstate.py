""" A global state of the running process """
import enum
from dataclasses import dataclass, field
from typing import List, Dict

from .influx import InfluxWriter
from .jenkins import Jenkins, QueuedJob
from .nodes import Node, JenkinsAgent, SSHConfig

class NodeStatus(str, enum.Enum):
    Busy = 'Busy'
    Idle = 'Idle'


@dataclass
class SchedulerConfig:
    idle_time_before_launch: float
    idle_time_before_shutdown: float
    node_priority: List[Node]


@dataclass
class GlobalState:
    # Must be provided
    jenkins_instance: Jenkins
    influx_writer: InfluxWriter
    privileged_ssh_config: SSHConfig
    jenkins_ssh_config: SSHConfig
    task_config: SchedulerConfig

    # Populated from Jenkins
    job_queue: List[QueuedJob] = field(default_factory=list)
    nodes: List[JenkinsAgent] = field(default_factory=list)
    shutdown: bool = False
    time_at_last_status_change: Dict[str, float] = field(default_factory=dict)
    last_status: Dict[str, NodeStatus] = field(default_factory=dict)
    initialized: bool = False
    last_time_queue_empty: float = 0
