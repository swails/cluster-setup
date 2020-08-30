/**
 * This script will reconnect every compute agent
 */

Jenkins.instance.computers.each { computer ->
    computer.setTemporarilyOffline(false)
}
