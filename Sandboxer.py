from pyVmomi import vim
from pyVim.connect import SmartConnect, SmartConnectNoSSL, Disconnect
import atexit
import argparse
import ssl
from pyVmomi import vmodl
import re
import requests

"Static Inputs to connect to cptc-server"

INPUTS = {'vcenter_ip': 'cptc-vcenter.csec.rit.edu',
          'vcenter_user': 'cptc.local\\administrator',
          'vcenter_password': 'CPTC4Capstone!',
          'datacenter' : 'Datacenter',
          'datastore' : 'datastore1', 
          'cluster' : 'CPTCCluster',
          'RP' :    'DevRP', 
          'dea_name': 'Pf-Template',
          'new_clone_name': 'Pfsesne-wow',
          'new_clone_domain': 'cptc.local',
          'new_clone_ip': '10.0.1.44',
          'new_clone_netmask': '255.255.255.0',
          'new_clone_gateway': '10.0.1.1',
          'new_clone_dns': '10.0.0.1',
          'folder_path' : 'dad/son/',
          'vSwitch' :    'Test_vSwitch',
          'PG' : 'Test_PG',
          'VlanID':     '1',
          "Template_Name" : "pf", 
          'VM_Name':   "TheWorking_VM"
          }


class Sandboxer():
    
    def __init__(self, vcenter_ip, vcenter_user, vcenter_password):
        self.vcenter_ip = vcenter_ip
        self.vcenter_user = vcenter_user
        self.vcenter_password = vcenter_password

    
    def login(self):
        """
        login function take vcenter ip, user, password and sign in to retrive a service instance.
        :param vcenter_ip: vcenter ip address
        :param vcenter_user:  vcenter username 
        :param vcenter_password: vcenter password
        :return: service instance content object
        """
        #Connectin to vCenter
        context = ssl._create_unverified_context()
        serviceInstance = SmartConnect(host=self.vcenter_ip,
                            user=self.vcenter_user,
                            pwd=self.vcenter_password,
                            port=int(443), sslContext=context)
        if not serviceInstance:
            print("Could not connect to the specified host using specified "
                    "username and password")
            return -1
        atexit.register(Disconnect, serviceInstance)
        return serviceInstance

    def logout(self, si):
        """
        logout function to logout 
        :param si: service instance
        :return: N/A
        """
        si.content.sessionManager.Logout()

    def retrive_content(self, si):
        """
        retrive content from a service instance
        :param si: service instance
        :return: service instance content 
        """
        content = si.RetrieveContent()
        return content

    def get_obj(self,content, vimtype, name):
        """
        take the content and type of vim and name and return the object
        :param content: service instance content
        :param vimtype: the type of vim
        :param the name of the object
        :return: The object in question 
        """
        obj = None
        container = content.viewManager.CreateContainerView(
            content.rootFolder, vimtype, True)
        for c in container.view:
            if c.name == name:
                obj = c
                break
        return obj
    def wait_for_task(self,task):
        """
        wait for a vCenter task to finish 
        :param task: task to be waited for
        :return N/A
        """
        task_done = False
        while not task_done:
            if task.info.state == 'success':
                return task.info.result

            if task.info.state == 'error':
                print("there was an error")
                task_done = True

    def mkdir_task(self, base_obj, dir_name):
        """
        helper function takes the base object and dir name and creat the folder with dir name
        :param base_obj: base object
        :param dir_name: folder name
        :returns: the base object
        """
        try:
            return base_obj.CreateFolder(dir_name)
        except (vim.fault.InvalidName) as e:
            print(e)
            import sys

    def create_folder(self, content, base_obj, folder_path):
        """
        takes the content, base object and nested folder pathe and creats that folder dirctory
        :param content: service instance content
        :param base_obj: base object
        :param folder_path: nested path e.g. /folder1/folder2/folder3
        :return : N/A
        """
        folder_path_parts = folder_path.strip('/').split('/')
        for path_part in folder_path_parts:
            if base_obj.childEntity:
                for y, child_obj in enumerate(base_obj.childEntity):
                    if child_obj.name == path_part:
                        base_obj = child_obj
                        break
                    elif y >= len(base_obj.childEntity)-1:
                        base_obj = self.mkdir_task(base_obj, path_part)
                        break
            else:
                base_obj = self.mkdir_task(base_obj, path_part)


    def test_folder_creation(self,content, folder_path):
        """
        test the functionality of create_folder and check whether the folder exist or not
        :param content: service instance content
        :param folder_path: nested path e.g. /folder1/folder2/folder3
        """
        dc = self.get_obj(content, [vim.Datacenter], INPUTS['datacenter'])
        if (self.get_obj(content, [vim.Folder], INPUTS['folder_path'])):
            print("Folder '%s' already exists" % INPUTS['folder_path'])
            return 0
        else:
            self.create_folder(content, dc.hostFolder, INPUTS['folder_path'])
            print("Successfully created the host folder '%s'" % INPUTS['folder_path'])
            self.create_folder(content, dc.vmFolder, INPUTS['folder_path'])
            print("Successfully created the VM folder '%s'" % INPUTS['folder_path'])
            return 0



    def GetVMHosts(self,content):
        """
        get VM hosts view
        :param content: service instance content
        :return object of VM hosts
        """
        host_view = content.viewManager.CreateContainerView(content.rootFolder,[vim.HostSystem],True)
        obj = [host for host in host_view.view]
        host_view.Destroy()
        return obj


    def Create_vSwitch(self, hosts, vswitch_Name):
        """
        create a virtual switch to the vcenter
        :param hosts: hosts to create virtual switch to
        :param vswitch_Name: the vswitch name 
        :return : N/A
        """
        for host in hosts:
            try:
                vswitch_spec = vim.host.VirtualSwitch.Specification()
                vswitch_spec.numPorts = 1024
                vswitch_spec.mtu = 1450
                host.configManager.networkSystem.AddVirtualSwitch(vswitch_Name,vswitch_spec)
            except vim.fault.AlreadyExists:
                print("vSwitch {} alredy exist".format(vswitch_Name))


    def Create_PortGroup(self,hosts, vswitch_Name, PG_Name, vlanId):
        """
        create a port group to the vcenter and add it to a virtual switch with a spesfic vlan ID 
        :param hosts: hosts to create virtual switch to
        :param vswitch_Name: the vswitch name 
        :param PG_Name: port group name
        :param vlanId: vlan id number
        :return : N/A
        """
        for host in hosts:
            try:
                portgroup_spec = vim.host.PortGroup.Specification()
                portgroup_spec.vswitchName = vswitch_Name
                portgroup_spec.name = PG_Name
                portgroup_spec.vlanId = int(vlanId)
                network_policy = vim.host.NetworkPolicy()
                network_policy.security = vim.host.NetworkPolicy.SecurityPolicy()
                network_policy.security.allowPromiscuous = True
                network_policy.security.macChanges = False
                network_policy.security.forgedTransmits = False
                portgroup_spec.policy = network_policy
                host.configManager.networkSystem.AddPortGroup(portgroup_spec)
            except vim.fault.AlreadyExists:
                    print("Port group {} alredy exist in vSwitch {} ".format(PG_Name, vswitch_Name))        


    def add_nic(self,content, VM, PG_Name):
        """
        create a network interface card for a specfic vm and attach it to a port group
        :param content: service instance content
        :param VM: the vm to add the nic to  
        :param PG_Name: port group name
        :return : N/A
        """
        spec = vim.VM.ConfigSpec()
        nic_changes = []

        nic_spec = vim.VM.device.VirtualDeviceSpec()
        nic_spec.operation = vim.VM.device.VirtualDeviceSpec.Operation.add

        nic_spec.device = vim.VM.device.VirtualE1000()

        nic_spec.device.deviceInfo = vim.Description()
        nic_spec.device.deviceInfo.summary = 'vCenter API test'

        network = self.get_obj(content, [vim.Network], PG_Name)
        if isinstance(network, vim.OpaqueNetwork):
            nic_spec.device.backing = vim.VM.device.VirtualEthernetCard.OpaqueNetworkBackingInfo()
            nic_spec.device.backing.opaqueNetworkType = network.summary.opaqueNetworkType
            nic_spec.device.backing.opaqueNetworkId = network.summary.opaqueNetworkId
        else:
            nic_spec.device.backing = vim.VM.device.VirtualEthernetCard.NetworkBackingInfo()
            nic_spec.device.backing.useAutoDetect = False
            nic_spec.device.backing.deviceName = network.name

        nic_spec.device.connectable = vim.VM.device.VirtualDevice.ConnectInfo()
        nic_spec.device.connectable.startConnected = True
        nic_spec.device.connectable.allowGuestControl = True
        nic_spec.device.connectable.connected = False
        nic_spec.device.connectable.status = 'untried'
        nic_spec.device.wakeOnLanEnabled = True
        nic_spec.device.addressType = 'assigned'

        nic_changes.append(nic_spec)
        spec.deviceChange = nic_changes
        #e = VM.ReconfigVM_Task(spec=spec)
        print("NIC CARD ADDED")


    def wait_for_task(self,task):
        """
        wait for a vCenter task to finish 
        :param task: task to be waited for
        :return N/A
        """
        task_done = False
        while not task_done:
            if task.info.state == 'success':
                return task.info.result

            if task.info.state == 'error':
                print("there was an error")
                task_done = True

    def get_datestore(self, content, Thedatastore):
        datastores = []
        # Get the list of all datacenters we have available to us
        datacenters_object_view = content.viewManager.CreateContainerView(
            content.rootFolder,
            [vim.Datacenter],
            True)

        # Find the datastore and datacenter we are using
        datacenter = None
        datastore = None
        for dc in datacenters_object_view.view:
            datastores_object_view = content.viewManager.CreateContainerView(dc,[vim.Datastore],True)
            for ds in datastores_object_view.view:
                datastores.append(ds.info.name)
                if ds.info.name == Thedatastore:
                    datacenter = dc
                    Thedatastore = ds
        if not datacenter or not Thedatastore:
            print("Could not find the datastore specified")
            raise SystemExit(-1)
        # Clean up the views now that we have what we need
        datastores_object_view.Destroy()
        datacenters_object_view.Destroy()
        return datastores


    def upload_file(self, si,localfile, remotefile):
        try:
            # Build the url to put the file - https://hostname:port/resource?params
            if not remotefile.startswith("/"):
                remote_file = "/" + remote_file
            else:
                remote_file = remotefile
            resource = "/folder" + remotefile
            params = {"dsName": INPUTS["datastore"],
                    "dcPath": INPUTS["datacenter"]}
            http_url = "https://" + self.vcenter_ip + ":443" + resource

            # Get the cookie built from the current session
            client_cookie = si._stub.cookie

            # Break apart the cookie into it's component parts - This is more than
            # is needed, but a good example of how to break apart the cookie
            # anyways. The verbosity makes it clear what is happening.
            cookie_name = client_cookie.split("=", 1)[0]
            cookie_value = client_cookie.split("=", 1)[1].split(";", 1)[0]
            cookie_path = client_cookie.split("=", 1)[1].split(";", 1)[1].split(
                ";", 1)[0].lstrip()
            cookie_text = " " + cookie_value + "; $" + cookie_path
            # Make a cookie
            cookie = dict()
            cookie[cookie_name] = cookie_text

            # Get the request headers set up
            headers = {'Content-Type': 'application/octet-stream'}

            # Get the file to upload ready, extra protection by using with against
            # leaving open threads
            with open(localfile, "rb") as f:
                # Connect and upload the file
                request = requests.put(http_url,
                                    params=params,
                                    data=f,
                                    headers=headers,
                                    cookies=cookie,
                                    verify=False)

        except vmodl.MethodFault as e:
            print("Caught vmodl fault : " + e.msg)
            raise SystemExit(-1)

        raise SystemExit(0)



def main():
    print("Starting main!")
    #Connectin to vCenter
    Sandboxer1 = Sandboxer(INPUTS['vcenter_ip'],INPUTS['vcenter_user'],INPUTS['vcenter_password'])
    si = Sandboxer1.login()
    content = Sandboxer1.retrive_content(si)

    #Test Folder creating
    #test_folder_creating(content)
    #Test vSwitch_Creat
    #Hosts  =  Sandboxer1.GetVMHosts(content)
    #vSwitch_Creat(Hosts,INPUTS['vSwitch'])

    #Test PGroup Creation 
    #Sandboxer1.Create_PortGroup(Hosts, INPUTS['vSwitch'], INPUTS['PG'], INPUTS['VlanID'])

    #Test adding NIC to a vim
    #vm = get_obj(content, [vim.VirtualMachine], "pf")
    #add_nic(content, vm, INPUTS['PG'])


    #Test clonning "GOD Speed"
    #Sandboxer1.clone_vm(content, INPUTS['VM_Name'], INPUTS['Template_Name'], INPUTS['new_clone_ip'], INPUTS['new_clone_gateway'],INPUTS['new_clone_netmask'], INPUTS['new_clone_dns'])
    lol = Sandboxer1.get_datestore(content,INPUTS['datastore'])
    print(lol)
    local_file = "/Users/t3/Documents/githubRepo/Projects/snadboxer/docs/SIFT-Workstation.ovf"
    remote_file = "/ISO/Linux/SIFT-Workstation.ovf"
    plzgod = Sandboxer1.upload_file(si,local_file,remote_file)












# start this thing
if __name__ == "__main__":
    main()

