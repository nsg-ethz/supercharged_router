#!/usr/bin/env python

# @author   Thomas Holterbach
# @email    thomasholterbach@gmail.com
# @date     16/02/2015

from netaddr import *

class VNH_generator:

    # The Virtual Next-Hop IP address prefix
    VNH_IP_prefix = None

    # The Virtual Next-Hop Mac prefix. We use private MAC addresses,
    # the second least-significant bit of the most significant byte must be 1
    VNH_MAC_prefix = None

    counter = 0

    vnh_file = None

    def __init__(self, IP_prefix="10.0.0.0/24", MAC_prefix="02-00-00-00-00-00", vnh_file="/home/lvanbever/config/virtual_nexthops"):
        self.VNH_IP_prefix = int(IPNetwork(IP_prefix).network)
        self.VNH_MAC_prefix = int(EUI(MAC_prefix))
        self.vnh_file = vnh_file
        fd = open(self.vnh_file, 'w+')
        fd.close()

    # Use this function if you want to have a new available Virtual Next-Hop
    def get_next_VNH (self):
        self.counter += 1

        vnh_ip = IPAddress(self.VNH_IP_prefix+self.counter)
        vnh_mac = EUI(self.VNH_MAC_prefix+self.counter)

        # Update mapping file        
        fd = open(self.vnh_file, "a+")
        fd.write(str(vnh_ip)+"\t"+str(int(vnh_mac))+"\n")
        fd.close()

        return vnh_ip, vnh_mac

    # Mapping IP to MAC
    def ip_to_mac (self, ip):
        return str(EUI(self.VNH_MAC_prefix+(int(ip)-self.VNH_IP_prefix)))

