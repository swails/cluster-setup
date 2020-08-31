/**
 * This script will reconnect every compute agent
 */
import jenkins.model.Jenkins

// Mark them *not* temporarily offline
Jenkins.instance.computers.each { computer ->
    computer.setTemporarilyOffline(false)
}

/* While they are no longer marked offline temporarily, they may be disconnected
 * and require launching the ssh agent. Check that here.
 */
Jenkins.instance.computers.each { computer ->
    if (computer.isOffline()) {
        println("INFO: ${computer.nodeName} is offline. Attempting to launch agent")
        if (computer.isLaunchSupported()) {
            println('INFO: Attempting launch...')
            computer.connect(false)
        } else {
            println('WARN: Launching agent is not supported!')
        }
    } else {
        println("INFO: ${computer.nodeName} is back online!")
    }
}
