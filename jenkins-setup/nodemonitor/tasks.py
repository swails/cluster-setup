""" Various tasks that should be performed """
import asyncio
import logging
import time

from .globalstate import GlobalState, NodeStatus
from .nodes import JenkinsAgent

LOGGER = logging.getLogger(__name__)


async def populate_global_state(state: GlobalState):
    state.jenkins_instance.fetch_computers()
    queued_jobs = state.jenkins_instance.get_queue()
    for agent_name, agent in state.jenkins_instance.nodes.items():
        state.time_at_last_status_change[agent_name] = time.time()
        state.last_status[agent_name] = NodeStatus.Busy if agent.busy_executors else NodeStatus.Idle
    state.job_queue.extend(queued_jobs)


async def poll_running_jobs(state: GlobalState, frequency: float):
    """ Runs until state indicates a shutdown, polling with the given frequency """
    while not state.shutdown:
        queued_jobs = await state.jenkins_instance.get_queue()
        LOGGER.info("Fetching build queue and executor status")
        state.job_queue.clear()
        state.job_queue.extend(queued_jobs)
        await state.jenkins_instance.fetch_computers()
        await _update_state_from_fetch(state)
        await asyncio.sleep(frequency)


async def shutdown_handler(state: GlobalState, frequency: float):
    """ Handles the shutdown by closing the jenkins instance when requested """
    while not state.shutdown:
        await asyncio.sleep(frequency)
    LOGGER.info("Shutdown detected - closing the jenkins instance")
    await state.jenkins_instance.close()
    await state.influx_writer.close()


async def node_manager(state: GlobalState, frequency: float):
    """ Handles shutting down and waking Jenkins instances """
    while not state.shutdown:
        await asyncio.sleep(frequency)
        # Maybe we can improve this at some point, but for now simply power on everyone.
        if state.job_queue:
            await _boot_all_agents(state)
        else:
            await _shutdown_idle_agents(state)


async def _update_state_from_fetch(state: GlobalState):
    # Update the job queue
    if not state.job_queue:
        state.last_time_queue_empty = time.time()

    # Update the computers
    for agent_name, agent in state.jenkins_instance.nodes.items():
        current_status = NodeStatus.Busy if agent.busy_executors else NodeStatus.Idle
        old_status = state.last_status[agent_name]
        if old_status is not current_status:
            LOGGER.info(f"Agent {agent_name} went from {old_status} to {current_status}")
            state.time_at_last_status_change[agent_name] = time.time()
        state.last_status[agent_name] = current_status


async def _boot_all_agents(state: GlobalState) -> bool:
    nodes_to_boot = []
    for name, agent in state.jenkins_instance.nodes.items():
        if agent.node is None:
            continue
        if await agent.node.is_available():
            LOGGER.info(f"{name} is already available. Relaunching if needed")
            continue
        if agent.node in nodes_to_boot:
            LOGGER.info(f"{name} underlying node already scheduled for boot")
        else:
            nodes_to_boot.append(agent.node)
    if not nodes_to_boot:
        return False
    tasks = [node.wakeup() for node in nodes_to_boot]
    await asyncio.gather(tasks)
    return True


async def _shutdown_idle_agents(state: GlobalState):
    await state.jenkins_instance.fetch_computers()
    await _update_state_from_fetch(state)
    do_not_shutdown = []
    shutdown_list = []
    for name, agent in state.jenkins_instance.nodes.items():
        if agent.node is None:
            continue
        if not agent.node.is_available():
            LOGGER.info(f"Shutdown - ignoring {name} as it is not available")
            continue
        if agent.busy_executors:
            LOGGER.info(f"Shutdown - {name} is currently in use. Not shutting down node.")
            do_not_shutdown.append(agent.node)
            continue
        if time.time() - agent.time_last_job_finished > state.task_config.idle_time_before_shutdown:
            LOGGER.info(f"Shutdown - {name} finished last job more than {state.task_config.idle_time_before_shutdown} "
                        f"seconds. Candidate for shutdown.")
            time_since_last_boot = time.time() - agent.time_booted
            if time_since_last_boot < state.task_config.idle_time_before_shutdown:
                LOGGER.info(f"Shutdown - {name} only booted {time_since_last_boot} seconds ago. Not shutting down yet")
            else:
                LOGGER.info(f"Shutdown - {name} has been idle for {time_since_last_boot} seconds. Marking shutdown")
                shutdown_list.append(agent.node)

    for node in shutdown_list:
        if node in do_not_shutdown:
            LOGGER.info(f"Not shutting down node {node.name} since it is still in use in another agent")
        else:
            LOGGER.info(f"Shutting down {node.name} since it is idle")
            await node.shutdown(state.privileged_ssh_config, force=False)
