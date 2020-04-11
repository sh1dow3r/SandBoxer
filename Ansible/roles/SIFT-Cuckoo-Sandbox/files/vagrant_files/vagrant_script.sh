#!/bin/bash

#Run vagrant up
vagrant up 


#Make snapshot of the vm  
$VM_NAME = "cuckoo1"

VBoxManage snapshot "cuckoo1" take "Stable_State" --description "Stable State For Cuckoo1"


