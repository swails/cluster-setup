# Setting up the worker nodes with Ansible

## Before getting started

Ansible connects via ssh, so it's important to have ssh key access from the
control node, so make sure the public key of the ssh key pair is copied to
`~/.ssh/authorized_keys` on each of the remotes.

Ansible also needs to be installed on the control node.
[Follow the official instructions.](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#installation-guide):

For Ubuntu:
```bash
sudo apt update
sudo apt install software-properties-common
sudo apt-add-repository --yes --update ppa:ansible/ansible
sudo apt install ansible
```

## Defining the remote hosts

The control node needs a defined `/etc/ansible/hosts` file that can either be a
simple list of FQDNs or IP addresses, INI format, or YAML format. Use the
following example:

```yaml
all:
  hosts:
    batwoman:
      ansible_host: 192.168.1.26
      ansible_python_interpreter: /usr/bin/python3
      ansible_become_password: <sudo password>
    green-lantern:
      ansible_host: 192.168.1.140
      ansible_python_interpreter: /usr/bin/python3
      ansible_become_password: <sudo password>
    green-arrow:
      ansible_host: 192.168.1.141
      ansible_python_interpreter: /usr/bin/python3
      ansible_become_password: <sudo password>
    wonder-woman:
      ansible_host: 192.168.1.142
      ansible_python_interpreter: /usr/bin/python3
      ansible_become_password: <sudo password>
    supergirl:
      ansible_host: 192.168.1.143
      ansible_python_interpreter: /usr/bin/python3
      ansible_become_password: <sudo password>
  children:
    cuda:
      hosts:
        batwoman:
        green-lantern:
        wonder-woman:
        supergirl:
    nogpu:
      hosts:
        green-arrow:
    amber:
      hosts:
        green-lantern:
        green-arrow:
        wonder-woman:
        supergirl:
```

## Updating the remote hosts

There is an Ansible playbook that simply updates, upgrades, and reboots:
`update-and-reboot.yml`.

## Setting up as Jenkins agents

The playbook `setup-worker-nodes.yml` will install the necessary packages,
3rd-party repositories, keys, user accounts, and ssh access keys required
for nodes to be configured as a Jenkins worker agent.
