#
# Copyright I.T. Dev Ltd 2014
# http://www.itdev.co.uk
#
import argparse
import sys
from mcvirt import McVirt, McVirtException, McVirtCommandException
from virtual_machine.virtual_machine import VirtualMachine
from virtual_machine.hard_drive import HardDrive
from virtual_machine.disk_drive import DiskDrive
from virtual_machine.network_adapter import NetworkAdapter

class ArgumentParserError(Exception):
  pass

class ThrowingArgumentParser(argparse.ArgumentParser):
  def error(self, message):
    print message
    raise ArgumentParserError(message)

class Parser:

  def __init__(self):
    self.parent_parser = ThrowingArgumentParser(add_help=False)

    # Create an argument parser object
    self.parser = ThrowingArgumentParser(description='Manage the McVirt host')
    self.subparsers = self.parser.add_subparsers(dest='action', metavar='Action', help='Action to perform on VM')

    # Add arguments for starting a VM
    self.start_parser = self.subparsers.add_parser('start', help='Start VM help', parents=[self.parent_parser])
    self.start_parser.add_argument('--iso', metavar='ISO Path', type=str, help='Path of ISO to attach to VM')
    self.start_parser.add_argument('vm_name', metavar='VM Name', type=str, help='Name of VM')

    # Add arguments for stopping a VM
    self.stop_parser = self.subparsers.add_parser('stop', help='Stop VM help', parents=[self.parent_parser])
    self.stop_parser.add_argument('vm_name', metavar='VM Name', type=str, help='Name of VM')

    # Add arguments for creating a VM
    self.create_parser = self.subparsers.add_parser('create', help='Create VM help', parents=[self.parent_parser])
    self.create_parser.add_argument('--memory', dest='memory', metavar='Memory', type=int,
      help='Amount of memory to allocate to the VM (MiB)', required=True)
    self.create_parser.add_argument('--disk-size', dest='disk_size', metavar='Disk Size', type=int,
      help='Size of disk to be created for the VM (MB)', required=True)
    self.create_parser.add_argument('--cpu-count', dest='cpu_count', metavar='CPU Count', type=int,
      help='Number of virtual CPU cores to be allocated to the VM', required=True)
    self.create_parser.add_argument('--network', dest='networks', metavar='Network Connection', type=str,
      action='append', help='Name of networks to connect VM to (each network has a separate NIC)')
    self.create_parser.add_argument('vm_name', metavar='VM Name', type=str, help='Name of VM')

    # Get arguments for deleting a VM
    self.delete_parser = self.subparsers.add_parser('delete', help='Delete VM help', parents=[self.parent_parser])
    self.delete_parser.add_argument('--remove-data', dest='remove_data', help='Removes the VM data from the host',
      action='store_true')
    self.delete_parser.add_argument('vm_name', metavar='VM Name', type=str, help='Name of VM')

    # Get arguments for updating a VM
    self.update_parser = self.subparsers.add_parser('update', help='Update VM help', parents=[self.parent_parser])
    self.update_parser.add_argument('--memory', dest='memory', metavar='Memory', type=int,
      help='Amount of memory to allocate to the VM (MiB)')
    self.update_parser.add_argument('--cpu-count', dest='cpu_count', metavar='CPU Count', type=int,
      help='Number of virtual CPU cores to be allocated to the VM')
    self.update_parser.add_argument('--add-network', dest='add_network', metavar='Add Network', type=str,
      help='Adds a NIC to the VM, connected to the given network')
    self.update_parser.add_argument('--remove-network', dest='remove_network', metavar='Remove Network', type=str,
      help='Removes a NIC from VM with the given MAC-address (e.g. \'00:00:00:00:00:00)\'')
    self.update_parser.add_argument('--add-disk', dest='add_disk', metavar='Add Disk', type=int,
      help='Add disk to the VM (size in MB)')
    self.update_parser.add_argument('--increase-disk', dest='increase_disk', metavar='Increase Disk', type=int,
      help='Increases VM disk by provided amount (MB)')
    self.update_parser.add_argument('--disk-id', dest='disk_id', metavar='Disk Id', type=int,
      help='The ID of the disk to be increased by')
    self.update_parser.add_argument('vm_name', metavar='VM Name', type=str, help='Name of VM')

    # Get arguments for making permission changes to a VM
    self.permission_parser = self.subparsers.add_parser('permission', help='Update VM permissions help', parents=[self.parent_parser])
    self.permission_parser.add_argument('--add-user', dest='add_user', metavar='Add User', type=str,
      help='Adds a given user to a VM, allowing them to perform basic functions.')
    self.permission_parser.add_argument('--delete-user', dest='delete_user', metavar='Delete User', type=str,
      help='Removes a given user from a VM. This prevents them to perform basic functions.')
    self.permission_parser.add_argument('--add-owner', dest='add_owner', metavar='Add Owner', type=str,
      help='Adds a given user as an owner to a VM, allowing them to perform basic functions and manager users.')
    self.permission_parser.add_argument('--delete-owner', dest='delete_owner', metavar='Delete User', type=str,
      help='Removes a given owner from a VM. This prevents them to perform basic functions and manager users.')
    self.permission_parser.add_argument('vm_name', metavar='VM Name', type=str, help='Name of VM')

    # Get arguments for getting VM information
    self.info_parser = self.subparsers.add_parser('info', help='View VM info help', parents=[self.parent_parser])
    self.info_parser.add_argument('--vnc-port', dest='vnc_port', help='Displays the port that VNC is being hosted from',
      action='store_true')
    self.info_parser.add_argument('vm_name', metavar='VM Name', type=str, help='Name of VM')

    # Get arguments for listing VMs
    self.list_parser = self.subparsers.add_parser('list', help='List VMs present on host', parents=[self.parent_parser])

    # Get arguments for cloning a VM
    self.clone_parser = self.subparsers.add_parser('clone', help='Clone a VM permissions help', parents=[self.parent_parser])
    self.clone_parser.add_argument('--template', dest='template', metavar='Parent VM', type=str, required=True,
      help='The name of the VM to clone from')
    self.clone_parser.add_argument('vm_name', metavar='VM Name', type=str, help='Name of VM')

  def parse_arguments(self, script_args = None):
    # If arguments have been specified, split, so that
    # an array is sent to the argument parser
    if (script_args != None):
      script_args = script_args.split()

    args = self.parser.parse_args(script_args)
    action = args.action

    # Get an instance of McVirt
    mcvirt_instance = McVirt()

    try:
      # Perform functions on the VM based on the action passed to the script
      if (action == 'start'):
        vm_object = VirtualMachine(mcvirt_instance, args.vm_name)
        disk_drive_object = DiskDrive(vm_object)

        if (args.iso):
          # If an ISO has been specified, attach it to the VM before booting
          # and adjust boot order to boot from ISO first
          disk_drive_object.attachISO(args.iso)
          vm_object.setBootOrder(['cdrom', 'hd'])
        else:
          # If not ISO was specified, remove any attached ISOs and change boot order
          # to boot from HDD
          disk_drive_object.removeISO()
          vm_object.setBootOrder(['hd'])
        vm_object.start()

      elif (action == 'stop'):
        vm_object = VirtualMachine(mcvirt_instance, args.vm_name)
        vm_object.stop()

      elif (action == 'create'):
        # Convert memory allocation from MiB to KiB
        memory_allocation = int(args.memory) * 1024
        VirtualMachine.createAuthCheck(mcvirt_instance, args.vm_name, args.cpu_count,
          memory_allocation, [args.disk_size], args.networks)

      elif (action == 'delete'):
        vm_object = VirtualMachine(mcvirt_instance, args.vm_name)
        vm_object.delete(args.remove_data)

      elif (action == 'update'):
        vm_object = VirtualMachine(mcvirt_instance, args.vm_name)
        if (args.memory):
          old_ram_allocation = int(vm_object.getRAM()) / 1024
          print 'RAM allocation will be changed from %sMiB to %sMiB.' % (old_ram_allocation, args.memory)
          new_ram_allocation = int(args.memory) * 1024
          vm_object.updateRAM(new_ram_allocation)
        if (args.cpu_count):
          old_cpu_count = vm_object.getCPU()
          print 'Number of virtual cores will be changed from %s to %s.' % (old_cpu_count, args.cpu_count)
          vm_object.updateCPU(args.cpu_count)
        if (args.remove_network):
          NetworkAdapter.delete(vm_object, args.remove_network)
        if (args.add_network):
          NetworkAdapter.create(vm_object, args.add_network)
        if (args.add_disk):
          HardDrive.create(vm_object, args.add_disk)
        if (args.increase_disk and args.disk_id):
          harddrive_object = HardDrive(vm_object, args.disk_id)
          harddrive_object.increaseSize(args.increase_disk)

      elif (action == 'permission'):
        vm_object = VirtualMachine(mcvirt_instance, args.vm_name)
        auth_object = mcvirt_instance.getAuthObject()
        if (args.add_user):
          auth_object.addUserPermissionGroup(vm_object, 'user', args.add_user)
        if (args.delete_user):
          auth_object.deleteUserPermissionGroup(vm_object, 'user', args.delete_user)
        if (args.add_owner):
          auth_object.addUserPermissionGroup(vm_object, 'owner', args.add_owner)
        if (args.delete_owner):
          auth_object.deleteUserPermissionGroup(vm_object, 'owner', args.delete_owner)

      elif (action == 'info'):
        vm_object = VirtualMachine(mcvirt_instance, args.vm_name)
        auth_object = mcvirt_instance.getAuthObject()
        if (args.vnc_port):
          print vm_object.getVncPort()
        else:
          vm_object.printInfo()

      elif (action == 'clone'):
        vm_object = VirtualMachine(mcvirt_instance, args.template)
        vm_object.clone(mcvirt_instance, args.vm_name)

      elif (action == 'list'):
        mcvirt_instance.listVms()
    except Exception, e:
      # Unset mcvirt instance - forcing the object to be destroyed
      mcvirt_instance = None
      raise e