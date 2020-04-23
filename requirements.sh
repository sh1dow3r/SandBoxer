!/bin/bash

# Setup for Ansible + vmware_deploy_ovf dependencies
apt-add-repository --yes --update ppa:ansible/ansible
apt install ansible
apt install python3 python3-pip
pip3 install pyvmomi
