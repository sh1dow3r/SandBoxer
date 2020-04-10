#!/bin/bash

#Run vagrant up
sudo su; cd /home/cuckoo/vagrant_files; vagrant up 2>/dev/null


#Make snapshot of the vm  
$VM_NAME = "cuckoo1"

VBoxManage snapshot "cuckoo1" take "Stable_State" --description "Stable State For Cuckoo1"


