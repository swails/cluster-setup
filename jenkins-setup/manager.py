#!/usr/bin/env python
import asyncio
import sys
from pathlib import Path
import logging
import os

logging.basicConfig(level=logging.DEBUG)

from nodemonitor import Jenkins, SSHConfig, GlobalState, InfluxWriter, tasks, SchedulerConfig

jenkins_username = os.environ["JENKINS_USERNAME"]
jenkins_token = os.environ["JENKINS_TOKEN"]

config = SSHConfig(
    private_key=Path(os.environ["AGENT_SSH_KEY"]),
    passphrase=os.environ["AGENT_SSH_KEY_PASSPHRASE"],
    username='jenkins',
)

admin_config = SSHConfig(username=os.environ["AGENT_ADMIN_USERNAME"],
                         password=os.environ["AGENT_ADMIN_PASSWORD"])

influx_url = f"{os.environ['INFLUX_URL']}:8086"
influx_db = os.environ["INFLUX_DB"]
influx_username = os.environ["INFLUX_USERNAME"]
influx_password = os.environ["INFLUX_PASSWORD"]

poll_frequency = 30 # seconds
node_manager_frequency = 60 # seconds

async def main():

    global_state = GlobalState(
        jenkins_instance=Jenkins("https://jenkins.jasonswails.com", jenkins_username, jenkins_token),
        influx_writer=InfluxWriter(influx_url, influx_db, influx_username, influx_password),
        privileged_ssh_config=admin_config,
        jenkins_ssh_config=config,
        task_config=SchedulerConfig(0, 600),
    )

    await tasks.populate_global_state(global_state)

    all_tasks = [
        tasks.poll_running_jobs(global_state, poll_frequency),
        tasks.shutdown_handler(global_state, poll_frequency),
        tasks.node_manager(global_state, node_manager_frequency),
    ]

    await asyncio.gather(*all_tasks)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

    LOGGER.error("Exiting!")
