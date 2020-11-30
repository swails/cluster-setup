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
        batwoman:
```

## Invoking playbooks with specific hosts

By default, each playbook will operate on a set of hosts that usually make the
most sense. Sometimes, we want to perform actions on a greater or smaller
subset of the available hosts. In this case, you can use `--extra-vars` to pass
the `hosts` option to the Ansible playbook to limit or broaden the scope of the
playbook. For example:

```bash
ansible-playbook setup-worker-nodes.yml --extra-vars="varhosts=batwoman"
```

## Updating the remote hosts

There is an Ansible playbook that simply updates, upgrades, and reboots:
`update-and-reboot.yml`.

## Setting up as Jenkins agents

The playbook `setup-worker-nodes.yml` will install the necessary packages,
3rd-party repositories, keys, user accounts, and ssh access keys required
for nodes to be configured as a Jenkins worker agent.

To run this playbook, run `ansible-playbook setup-worker-nodes.yml`

# Power Saving with Wake on LAN

Capable desktops draw a lot of power, even when idling. There are 5 nodes in the Ubuntu cluster:

| Machine Name  | Processor            | GPU         | Idle power (est) | MAC Address       |
|---------------|----------------------|-------------|------------------|-------------------|
| batwoman      | 6-core Xeon 3600     | GTX 780     |  75 W            | 00:24:E8:45:13:E6 |
| green-arrow   | 6-core Core i5-9400  | GTX 780     |  40 W            | 1C:69:7A:31:52:21 |
| green-lantern | 6-core Core i5-9400F | GTX 1660    |  35 W            | 04:D9:F5:B9:F7:0B |
| wonder-woman  | 6-core Core i5-9400F | GTX 980Ti   |  40 W            | 00:D8:61:FF:31:47 |
| supergirl     | 8-core Ryzen 7 3700x | GTX TITAN X |  50 W            | 2C:F0:5D:27:5E:AA |

While these idling power draws (~240 W combined) may seem low for 5 machines, left on 24/7/365 would
draw ~2.1 MWh, or roughly 240USD over the course of 1 year at 0.12USD/kWh.

## Wake On LAN

Wake on LAN (WoL) requires setup on the client machine. It must be enabled in the BIOS (typically
under power management) as well as in the operating system. On a Linux machine, you can use the
`ethtool` utility to inspect whether WoL is supported or enabled. Note that ErP must be disabled for
WoL to work, because ErP saves additional energy by turning off services such as the LAN in
deep shutdown mode. This obviously precludes the use of WoL.

By default, WoL is disabled and, when supported, must be re-enabled *every time the machine boots*.

The instructions below come from [here](https://help.ubuntu.com/community/WakeOnLan#:~:text=To%20enable%20WoL%20in%20the,Save%20your%20settings%20and%20reboot.)
and [here](https://askubuntu.com/questions/1244785/trouble-with-wakeonlan-with-ubuntu-20-04).

### Checking whether WoL is supported

To check whether WoL is supported, use `ethtool` with the Ethernet NIC.  As an example:

```
$ sudo ethtool eth0
Settings for eth0:
	Supported ports: [ TP ]
	Supported link modes:   10baseT/Half 10baseT/Full 
	                        100baseT/Half 100baseT/Full 
	                        1000baseT/Full 
	Supported pause frame use: No
	Supports auto-negotiation: Yes
	Supported FEC modes: Not reported
	Advertised link modes:  10baseT/Half 10baseT/Full 
	                        100baseT/Half 100baseT/Full 
	                        1000baseT/Full 
	Advertised pause frame use: No
	Advertised auto-negotiation: Yes
	Advertised FEC modes: Not reported
	Speed: 1000Mb/s
	Duplex: Full
	Port: Twisted Pair
	PHYAD: 1
	Transceiver: internal
	Auto-negotiation: on
	MDI-X: on (auto)
	Supports Wake-on: pumbg                <----------- presence of "g" means WoL supported
	Wake-on: d                             <----------- "d" means disabled. "g" means magic-number WoL
	Current message level: 0x00000007 (7)
			       drv probe link
	Link detected: yes
```

### Enabling WoL

Assuming WoL is disabled, you can enable it with the following command:

```
$ sudo ethtool -s eth0 wol g
```

In this case, `eth0` should be the name of the NIC (you can get that from the output of `ip addr` -
it will be the one that starts with `e`).

However, this will only enable WoL for the very next boot. After that, WoL will be disabled.
The solution is to run the above command on boot every time the network comes up. To do this,
create a file in `/etc/network/if-up.d/` with the above command in it. In Ubuntu, `ethtool` is
found in `/usr/sbin/ethtool`, but you can use `/usr/bin/env ethtool` to make it OS-independent.

```
$ sudo cat > /etc/network/if-up.d/wol << EOF
#!/bin/sh
/usr/bin/env ethtool -s eth0 wol g
EOF
$ sudo chmod +x /etc/network/if-up.d/wol
```

## Waking up

The [`wakeonlan` Python package](https://pypi.org/project/wakeonlan/) provides a library useful
both as a reference implementation and as a library for executing WoL operations on machines that
have been shut down.

The design I am going to shoot for is to have a simple service running inside a docker container
that periodically polls the Jenkins server to look for queued jobs (say every minute). If jobs
are queued, it will turn on any nodes that match the requested labels.

Once all of the jobs have been completed, the nodes will be shut down.
