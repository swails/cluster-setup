/**
 * This script will disable all of the Jenkins agent nodes that run jobs
 */

List computeAgents = []

Boolean computerHasBusyExecutors(def computer) {
    return computer.getExecutors().any {
        it.isBusy()
    }
}

// First take every computer temporarily offline
Jenkins.instance.computers.each { computer ->
    if (computer.getAssignedLabels().any { it.getExpression() == 'ansible' || it.getExpression() == 'master' }) {
        println('INFO: Not taking offline either master or ansible nodes')
    } else {
        computeAgents.add(computer)
        println("INFO: Setting ${computer.nodeName} offline")
        computer.setTemporarilyOffline(true)
        computer.doChangeOfflineCause('Updating and possibly rebooting this node')
    }
}

// Now, wait for every executor of every node to finish. 
computeAgents.each { agent ->
    while(computerHasBusyExecutors(agent)) {
        // 30,000 milliseconds in 30 seconds.
        println("WARN: ${agent.nodeName} has busy executors, waiting to finish")
        sleep(30000)
    }
    println("INFO: ${agent.nodeName} has no busy executors!")
}
