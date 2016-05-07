# Copyright (c) 2014 - I.T. Dev Ltd
#
# This file is part of MCVirt.
#
# MCVirt is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# MCVirt is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with MCVirt.  If not, see <http://www.gnu.org/licenses/>

import Pyro4

from mcvirt.mcvirt import MCVirtException
from mcvirt.virtual_machine.hard_drive.local import Local
from mcvirt.virtual_machine.hard_drive.drbd import DRBD
from mcvirt.virtual_machine.hard_drive.config.local import Local as ConfigLocal
from mcvirt.virtual_machine.hard_drive.config.drbd import DRBD as ConfigDRBD
from mcvirt.auth.auth import Auth
from mcvirt.rpc.lock import lockingMethod


class UnknownStorageTypeException(MCVirtException):
    """An hard drive object with an unknown disk type has been initialised"""
    pass


class Factory(object):
    """Provides a factory for creating hard drive/hard drive config objects"""

    STORAGE_TYPES = [Local, DRBD]
    DEFAULT_STORAGE_TYPE = 'Local'
    OBJECT_TYPE = 'network'

    def __init__(self, mcvirt_instance):
        """Create object, storing MCVirt instance"""
        self.mcvirt_instance = mcvirt_instance

    @staticmethod
    def getObject(vm_object, disk_id):
        """Returns the storage object for a given disk"""
        vm_config = vm_object.getConfigObject().getConfig()
        storage_type = vm_config['storage_type']

        return Factory.getClass(storage_type)(vm_object, disk_id)

    @staticmethod
    def getConfigObject(vm_object, storage_type, disk_id=None, config=None):
        """Returns the config object for a given disk"""
        for config_class in [ConfigLocal, ConfigDRBD]:
            if (storage_type == config_class.__name__):
                return config_class(vm_object, disk_id, config=config)
        raise UnknownStorageTypeException(
            'Attempted to initialise an unknown storage config type: %s' %
            storage_type
        )

    @staticmethod
    def getRemoteConfigObject(mcvirt_instance, arguments):
        """Returns a hard drive config object, using arguments sent to a remote machine"""
        from mcvirt.virtual_machine.virtual_machine import VirtualMachine
        vm_object = VirtualMachine(mcvirt_instance, arguments['vm_name'])
        return Factory.getConfigObject(vm_object=vm_object, storage_type=arguments['storage_type'],
                                       config=arguments['config'])

    @Pyro4.expose()
    @lockingMethod()
    def create(self, *args, **kwargs):
        """Performs the creation of a hard drive"""
        return self._create(*args, **kwargs)

    def _create(self, vm_object, size, storage_type, driver):
        """Performs the creation of a hard drive, using a given storage type"""
        if '_pyroDaemon' in self.__dict__:
            vm_object = self._pyroDaemon.convertRemoteObject(vm_object)

        # Ensure that the user has permissions to add create storage

        # Ensure that the storage type:
        # If the VM's storage type has been defined that the specified storage type
        #   matches or has not been defined.
        # Or that the storage type has been specified if the VM's storage type is
        #   not defined
        if vm_object.getStorageType():
            if storage_type and storage_type != vm_object.getStorageType():
                raise InvalidStorageTypeException(
                    'Storage type does not match VMs current storage type'
                )
            storage_type = vm_object.getStorageType()
            print storage_type
        else:
            available_storage_types = self._getAvailableStorageTypes()
            if len(available_storage_types) > 1 and not storage_type:
                raise InvalidStorageTypeException('Storage type must be specified')
            elif len(available_storage_types) == 1:
                storage_type = available_storage_types[0].__name__
            else:
                raise InvalidStorageTypeException('There are no storage types available')
        return Factory.getClass(storage_type).create(vm_object, size, driver)

    def _getAvailableStorageTypes(self):
        """Returns a list of storage types that are available on the node"""
        available_storage_types = []
        for storage_type in self.STORAGE_TYPES:
            if storage_type.isAvailable():
                available_storage_types.append(storage_type)
        return available_storage_types

    @staticmethod
    def getStorageTypes():
        """Returns the available storage types that MCVirt provides"""
        return Factory.STORAGE_TYPES

    @staticmethod
    def getClass(storage_type):
        """Obtains the hard drive class for a given storage type"""
        for hard_drive_class in Factory.getStorageTypes():
            if (storage_type == hard_drive_class.__name__):
                return hard_drive_class
        raise UnknownStorageTypeException(
            'Attempted to initialise an unknown storage type: %s' %
            (storage_type)
        )

    @staticmethod
    def getDrbdObjectByResourceName(mcvirt_instance, resource_name):
        """Obtains a hard drive object for a DRBD drive, based on the resource name"""
        from mcvirt.node.drbd import DRBD as NodeDRBD
        for hard_drive_object in NodeDRBD.getAllDrbdHardDriveObjects(mcvirt_instance):
            if (hard_drive_object.getConfigObject()._getResourceName() == resource_name):
                return hard_drive_object
        from mcvirt.virtual_machine.hard_drive.base import HardDriveDoesNotExistException
        raise HardDriveDoesNotExistException(
            'DRBD hard drive with resource name \'%s\' does not exist' %
            resource_name
        )
