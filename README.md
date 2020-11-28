# cluster-setup

Setup for my home cluster

## ``qnap/``

This directory contains the setup files for the QNAP NAS device.

## ``ubuntu-nodes/``

This directory contains the Ansible playbooks and setup files needed to configure
a "new" Ubuntu machine to work as a Jenkins build agent.

## ``jenkins-setup/``

Files for automating the maintenance of Jenkins build agents. These files include:

* A Jenkins pipeline for automatically running system updates on Jenkins agents
* A Jenkins system groovy script that takes agents offline and waits for any outstanding jobs to finish
* A Jenkins system groovy script that brings agents back online
