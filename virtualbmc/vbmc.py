#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import xml.etree.ElementTree as ET

import openstack
import pyghmi.ipmi.bmc as bmc

from virtualbmc import exception
from virtualbmc import log
from virtualbmc import utils

LOG = log.get_logger()

# Power states
POWEROFF = 0
POWERON = 1

# From the IPMI - Intelligent Platform Management Interface Specification
# Second Generation v2.0 Document Revision 1.1 October 1, 2013
# https://www.intel.com/content/dam/www/public/us/en/documents/product-briefs/ipmi-second-gen-interface-spec-v2-rev1-1.pdf
#
# Command failed and can be retried
IPMI_COMMAND_NODE_BUSY = 0xC0
# Invalid data field in request
IPMI_INVALID_DATA = 0xcc

# Boot device maps
GET_BOOT_DEVICES_MAP = {
    'pxe': 4,
    'disk': 8,
    'cdrom': 0x14,
}

SET_BOOT_DEVICES_MAP = {
    'network': 'pxe',
    'hd': 'disk',
    'optical': 'cdrom',
}


class VirtualBMC(bmc.Bmc):

    def __init__(self, username, password, port, address,
                 domain_name, libvirt_uri, libvirt_sasl_username=None,
                 libvirt_sasl_password=None, **kwargs):
        super(VirtualBMC, self).__init__({username: password},
                                         port=port, address=address)
        self.domain_name = domain_name

    def get_boot_device(self):
        LOG.debug('Get boot device called for %(domain)s',
                  {'domain': self.domain_name})
        conn = openstack.connect(cloud='overcloud', region_name='regionOne')
        boot_device = conn.baremetal.get_node_boot_device(self.domain_name).get(
            'boot_device', None)
        return GET_BOOT_DEVICES_MAP.get(boot_device, 0)

    def set_boot_device(self, bootdevice):
        LOG.debug('Set boot device called for %(domain)s with boot '
                  'device "%(bootdev)s"', {'domain': self.domain_name,
                                           'bootdev': bootdevice})
        device = SET_BOOT_DEVICES_MAP.get(bootdevice)
        if device is None:
            # Invalid data field in request
            return IPMI_INVALID_DATA

        conn = openstack.connect(cloud='overcloud', region_name='regionOne')
        conn.baremetal.set_node_boot_device(self.domain_name, device)
        return

    def get_power_state(self):
        LOG.debug('Get power state called for domain %(domain)s',
                  {'domain': self.domain_name})
        conn = openstack.connect(cloud='overcloud', region_name='regionOne')
        node = conn.baremetal.find_node(self.domain_name)
        if node.power_state == 'power on':
            return POWERON
        return POWEROFF

    def pulse_diag(self):
        LOG.debug('Get power state called for domain %(domain)s',
                  {'domain': self.domain_name})
        return IPMI_COMMAND_NODE_BUSY

    def power_off(self):
        LOG.debug('Power off called for domain %(domain)s',
                  {'domain': self.domain_name})
        conn = openstack.connect(cloud='overcloud', region_name='regionOne')
        conn.baremetal.set_node_power_state(self.domain_name, 'power off')
        return

    def power_on(self):
        LOG.debug('Power on called for domain %(domain)s',
                  {'domain': self.domain_name})
        conn = openstack.connect(cloud='overcloud', region_name='regionOne')
        conn.baremetal.set_node_power_state(self.domain_name, 'power on')
        return

    def power_shutdown(self):
        LOG.debug('Soft power off called for domain %(domain)s',
                  {'domain': self.domain_name})
        conn = openstack.connect(cloud='overcloud', region_name='regionOne')
        conn.baremetal.set_node_power_state(self.domain_name, 'power off')
        return

    def power_reset(self):
        LOG.debug('Power reset called for domain %(domain)s',
                  {'domain': self.domain_name})
        conn = openstack.connect(cloud='overcloud', region_name='regionOne')
        conn.baremetal.set_node_power_state(self.domain_name, 'rebooting')
        return
