/**
 * This script will reconnect every compute agent
 */
import jenkins.model.Jenkins

Jenkins.instance.computers.each { computer ->
    computer.setTemporarilyOffline(false)
}
