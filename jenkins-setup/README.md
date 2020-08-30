# Jenkins setup

The scripts in this directory handle automating the maintenance of Jenkins
itself.

## Updating nodes

Safely updating nodes should be done in four steps to do it safely and reliably:

1. Take every compute agent offline
1. Wait for every job to finish on any executor of any of those nodes
1. Run `ansible-playbook ubuntu-nodes/update-and-reboot.yml`
1. Bring each node back online

### Take every compute agent offline and wait for every job to finish

This is a privileged operation, and no Jenkinsfile should be allowed to
execute this. To work around this limitation, we create a new freestyle job in
Jenkins that simply executes a system Groovy script and copy the contents of
`take-compute-agents-offline.groovy` into that job.

We then restrict access to running this job so only other jobs inside a
permission-restricted folder can execute it. So that the Jenkinsfiles in this
directory will work, create a new folder `manage-jenkins` and name the freestyle
job that takes agents offline `agents-offline`.

### Reconnect every compute agent

Do the same thing as for the previous step, but use
`put-compute-agents-online.groovy` as the contents for the `agents-online` job
in the `manage-jenkins` folder instead.
