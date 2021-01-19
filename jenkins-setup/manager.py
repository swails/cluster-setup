#!/usr/bin/env python3
import argparse
import asyncio
import sys
from pathlib import Path
import logging
import os

logging.basicConfig(level=logging.DEBUG)

from nodemonitor import NodemonitorConfiguration, GlobalState, Jenkins, InfluxWriter, tasks, SchedulerConfig

logging.getLogger("asyncssh").setLevel(logging.WARNING)

def initialize_state() -> GlobalState:
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
        poll_frequency=config.poll_frequency,
    )

    return global_state

async def main(global_state):
    await global_state.initialize()
    while True:
        all_tasks = [
            tasks.poll_running_jobs(global_state),
            tasks.node_manager(global_state),
        ]

        await asyncio.gather(*all_tasks)

        logging.info("Shutdown detected. Resetting tasks")
        global_state.shutdown = False


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    global_state = initialize_state()
    try:
        loop.run_until_complete(main(global_state))
    except Exception:
        logging.exception("Unexpected exception. Trying to restart")

    logging.error("Exiting!")
