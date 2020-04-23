- name: Deploy SIFT workstation 
  vmware_deploy_ovf:
    validate_certs: '{{ validate_certs }}'
    hostname: '{{ vcenter_address }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    allow_duplicates: false
    name: '{{ SIFT_name }}'
    networks: '{{ VM_network }}'
    datastore: '{{ SIFT_datastore }}'
    datacenter: '{{ SIFT_datacenter }}'
    resource_pool: '{{ SIFT_resource_pool}}'
    folder: '{{ SIFT_Folder }}'
    ovf: '{{SIFT_OVA_file}}'
    wait_for_ip_address: false
    power_on: yes
  delegate_to: localhost
