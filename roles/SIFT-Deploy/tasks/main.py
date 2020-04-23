- name: Deploy SIFT workstation 
  vmware_deploy_ovf:
    validate_certs: '{{ validate_certs }}'
    hostname: '{{ vcenter_address }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    allow_duplicates: false
    name: 'SIFT Workstation'
    ovf: '{{Path_To_SIFT_Workstation}}'
    networks: "{{ VM_network }}'}"
    datastore: '{{ datastore }}'
    datacenter: '{{ datacenter }}'
    wait_for_ip_address: false
    power_on: yes
  delegate_to: localhost
