#!/usr/bin/env python
import argparse
import asyncio
import sys
from pathlib import Path
import logging
import os

logging.basicConfig(level=logging.DEBUG)

from nodemonitor import NodemonitorConfiguration, GlobalState, Jenkins, InfluxWriter, tasks, SchedulerConfig

logging.getLogger("asyncssh").setLevel(logging.WARNING)

async def main():

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config-file", default="config.ini", dest="config_file",
                        help="Configuration file with all manager options")

    args = parser.parse_args()

    config = NodemonitorConfiguration.parse_configfile(args.config_file)

    global_state = GlobalState(
        jenkins_instance=Jenkins(config.jenkins.url, config.jenkins.username, config.jenkins.token),
        influx_writer=InfluxWriter(config.influx.hostname, config.influx.database, config.influx.username, config.influx.password),
        privileged_ssh_config=config.agent_ssh_config,
        task_config=SchedulerConfig(config.idle_time_before_launch, config.idle_time_before_shutdown, config.node_priority),
    )

    await tasks.populate_global_state(global_state)

    all_tasks = [
        tasks.poll_running_jobs(global_state, config.poll_frequency),
        tasks.shutdown_handler(global_state, config.poll_frequency),
        tasks.node_manager(global_state, config.poll_frequency * 2),
    ]

    await asyncio.gather(*all_tasks)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

    logging.error("Exiting!")
