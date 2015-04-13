#!/usr/bin/env python

# @author   Thomas Holterbach
# @email    thomasholterbach@gmail.com
# @date     16/02/2015

from util import getArgs, write
from VNH_generator import VNH_generator


class backup_group:

    # Consider the backup group (R1, R2) where R1 is the primary router and
    # R2 is the backup router
    R1 = None
    R2 = None

    # A Virtual Next-Hop IP address and a Virtual Next-Hop MAC address are
    # assigned to this backup_group
    VNH_IP = None
    VNH_MAC = None

    # Number of holded prefixes by this backup_group
    holded_prefixes = 0

    def __init__(self, R1, R2, VNH_generator, nb_prefixes=0):
	    self.R1 = R1
	    self.R2 = R2
	    self.nb_prefixes = nb_prefixes
	    self.VNH_IP, self.VNH_MAC = VNH_generator.get_next_VNH()

    def __str__(self):
	    return "("+str(self.R1)+", "+str(self.R2)+") --> ("+str(self.VNH_IP)+", "+str(self.VNH_MAC)+"), "+str(self.holded_prefixes)

    def __eq__(self, other):
        return True if (self.R1 == other.R1 and self.R2 == other.R2) else False

    def __cmp__(self, other):
        if self.holded_prefixes > other.holded_prefixes:
            return -1
        elif self.holded_prefixes < other.holded_prefixes:
            return 1
        else:
            return 0

    def virtual_announce(self, routePrefix, as_path=None, log=None):
        if self.R2 == 'None':
            write('announce route %s next-hop %s as-path [ %s ]' % (routePrefix, self.R1, as_path), log)
        else:
            write('announce route %s next-hop %s as-path [ %s ]' % (routePrefix, self.VNH_IP, as_path), log)
        # Push rule in the switch

    def virtual_withdraw(self, routePrefix, log=None):
        if self.R2 == 'None':
            write('withdraw route %s next-hop %s' % (routePrefix, self.R1), log)
        else:
            write('withdraw route %s next-hop %s' % (routePrefix, self.VNH_IP), log)
        # Push rule in the switch

    def insert_primary_rule(self, pusher, switch_dpid, mapping, log=None):
        if self.R2 != 'None':
            flow = {
            'switch':switch_dpid,
            "name":"("+str(self.R1)+", "+str(self.R2)+") PRIMARY",
            "priority":"30000",
            "eth_type":"0x0800",
            "eth_dst":str(self.VNH_MAC).replace('-', ':'),
            "active":"true",
            "actions":"output="+str(mapping[str(self.R1)][0])+",set_eth_dst="+str(mapping[str(self.R1)][1]).replace('-', ':')
            }
            pusher.set(flow)
            if log != 'None':
                log.write(str(flow)+'\n')

    def delete_primary_rule(self, pusher, log=None):
            if self.R2 != 'None':
                flow = {"name":"("+str(self.R1)+", "+str(self.R2)+") PRIMARY"   }
                pusher.remove(None, flow)
                if log != 'None':
                    log.write(str(flow))

    def insert_backup_rule(self, pusher, switch_dpid, mapping, log=None):
        if self.R2 != 'None':
            flow = {
            'switch':switch_dpid,
            "name":"("+str(self.R1)+", "+str(self.R2)+") BACKUP",
            "priority":"35002",
            "eth_type":"0x0800",
            "eth_dst":str(self.VNH_MAC).replace('-',':'),
            "active":"true",
            "actions":"output="+str(mapping[str(self.R2)][0])+",set_eth_dst="+str(mapping[str(self.R2)][1]).replace('-',':')
            }
            pusher.set(flow)
            if log != 'None':
                log.write(str(flow))

