#!/usr/bin/env python

# @author   Thomas Holterbach
# @email    thomasholterbach@gmail.com
# @date     16/02/2015

path='/home/lvanbever/sdx/exabgp/etc/exabgp/rs'

import sys
sys.path.append(path)

import json
import re
from netaddr import *
from util import getArgs, write, write_time, write_backup_groups, write_rib
from blist import sortedset
from bgp_route import bgp_route
from backup_group import backup_group, VNH_generator
from StaticFlowPusher import StaticFlowPusher

logfile = path+'/rs.log'
log = open(logfile, "w")

msgfile = path+'/rs.msg'
msg = open(msgfile, "w")

#Instantiate RIB priority queue dictionary
rib = {}

#Instantiate Adj-ribin dictionary
adj_rib_in = {}

# Warning: when the parent dies we are seeing continual newlines, so we only access so many before stopping
counter = 0

# Virtual Next-Hop generator
VNH_generator = VNH_generator ("10.0.0.128/25", MAC_prefix=0x020000000000, vnh_file=path+'/virtual_nexthops')

# Instiantiate the backup groups dictionary
# Each element of this dictionnary is an (ordered?) list of backup-groups
# The Key is the IP address of a next hop
# The Value is a list of its assigned backup-groups
backup_groups = {}

# Initialization of the backup_group dictionnary
backup_groups['None'] = {}
backup_groups['None']['None'] = backup_group('None', 'None', VNH_generator)

# Create the mapping Nexthop IP address to tuple switch port id, MAC address
mapping_file = path+'/mapping'
mapping_id = {}
fd = open(mapping_file, 'r')
for line in fd.readlines():
    linetab = line.split('\t')
    mapping_id[linetab[0]] = (linetab[1], linetab[2].rstrip('\n'))
fd.close()

# Initialize the flow pusher
pusher = StaticFlowPusher('127.0.0.1')

# ID of the openflow switch, we consider only one openflow switch
switch_dpid_file = path+'/switch_dpid'
fd = open(switch_dpid_file, 'r')
switch_dpid = fd.readline().rstrip('\n')
fd.close()


def prefix_to_backup_group (prefix):
 
    try:
        R1 = rib[prefix][0].nextHop
        try:
            R2 = rib[prefix][1].nextHop
        except IndexError:
            R2 = 'None'

    except KeyError:
        R1 = 'None'
        R2 = 'None'

    return backup_groups[R1][R2]

def process_down (ip):

    # First, generate and push rules on the sdn switch to allow the fast BGP
    # convergence
    if ip in backup_groups:
        for bg in sorted(backup_groups[ip].values()):
            if bg.holded_prefixes > 0 and bg.R2 != 'None':
                bg.insert_backup_rule(pusher, switch_dpid, mapping_id, log)

    # Deletion of the bgp routes learned from this neighbor. If necessary, 
    # withdraw this route or announce a new route
    if ip in adj_rib_in:
        for bgpRoute in adj_rib_in[ip]:

            # Get the backup-group before the change
            pre_backup_group = prefix_to_backup_group(bgpRoute.routePrefix)

            # Remove this route from the rib
            rib[bgpRoute.routePrefix].remove(bgpRoute)
            if len(rib[bgpRoute.routePrefix]) == 0:
                del rib[bgpRoute.routePrefix]

            # Get the backup-group after the change
            post_backup_group = prefix_to_backup_group(bgpRoute.routePrefix)

            # Propagate the virtual announcements if the backup-group has changed
            if not pre_backup_group.__eq__(post_backup_group):
                if post_backup_group.R1 == 'None':
                    pre_backup_group.virtual_withdraw(bgpRoute.routePrefix, log)
                else:
                    post_backup_group.virtual_announce(bgpRoute.routePrefix, rib[bgpRoute.routePrefix][0].asPath, None)
                    if post_backup_group.holded_prefixes == 0:
                        post_backup_group.insert_primary_rule(pusher, switch_dpid, mapping_id, log)

                # Update backup-groups hold prefixes value
                pre_backup_group.holded_prefixes -= 1
                post_backup_group.holded_prefixes += 1

    # Remove the out-of-date backup-group
    # First, deletion of each (nexthop, x) backup-groups
    if ip in backup_groups:
        del backup_groups[ip]

        # Second, deletion of each (x, nexthop) backup-groups
        for nextHop in backup_groups:
            del backup_groups[nextHop][ip]

    #Remove entry from adj_rib_in
    if ip in adj_rib_in:
        del adj_rib_in[ip]



def process_attribute(attribute_items):

	asPath = ''
	asPathLength = 0

	for k2,v2 in attribute_items.iteritems():
		if (k2=='as-path'):
			for v3 in v2:
				asPath += ' '.join([str(x) for x in v3])				
				asPathLength = len(re.findall(r'\w+', asPath))

	return asPath, asPathLength

def process_announce(ip, announced_items, asPath, asPathLength):
    for k2,v2 in announced_items.iteritems():
        if (k2=='ipv4 unicast'):
            for k3,v3 in v2.iteritems():

                # bgpRoute construction
                bgpRoute = bgp_route()
                bgpRoute.asPath = asPath
                bgpRoute.asPathLength = asPathLength
                bgpRoute.routePrefix = IPNetwork(k3)
                bgpRoute.nextHop = IPAddress(v3['next-hop'])
   
                #### Backup-group dictionnary update ####
	            # List containing backup-groups where the next-hop is the primary
                # router
                if ip not in backup_groups:
                    backup_groups[ip] = {}

                    # New backup-groups addition
                    for nextHop in backup_groups:
	                    backup_groups[nextHop][ip] = backup_group(nextHop, ip, VNH_generator)
	                    backup_groups[ip][nextHop] = backup_group(ip, nextHop, VNH_generator)
                #### End back up group dictionnary update ####

                
                # Get the backup-group before the change
                pre_backup_group = prefix_to_backup_group(bgpRoute.routePrefix)

                # Rib maps IP destination prefix to list of bgp_routes that lead to that prefix
                # Add bgp_route to a list of possible bgp_routes
                if(bgpRoute.routePrefix not in rib):
                    rib[bgpRoute.routePrefix] = sortedset()
                rib[bgpRoute.routePrefix].add(bgpRoute)

                # Get the back-group after the change
                post_backup_group = prefix_to_backup_group(bgpRoute.routePrefix)

                # Add route to the add-rib-in
                if(ip not in adj_rib_in):
                    adj_rib_in[ip] = []
                adj_rib_in[ip].append(bgpRoute)

                # Propagate the virtual announcements if the backup-group has changed
                if not pre_backup_group.__eq__(post_backup_group):
                    post_backup_group.virtual_announce(bgpRoute.routePrefix, rib[bgpRoute.routePrefix][0].asPath, None)

                    if post_backup_group.holded_prefixes == 0:
                        post_backup_group.insert_primary_rule(pusher, switch_dpid, mapping_id, log)

                    # Update backup-groups hold prefixes value
                    pre_backup_group.holded_prefixes -= 1
                    post_backup_group.holded_prefixes += 1


def process_withdraw(ip, announced_items):
    for k2,v2 in announced_items.iteritems():
        if (k2=='ipv4 unicast'):
            for k3,v3 in v2.iteritems():
                withdrawnPrefix = IPNetwork(k3)

                #Remove from adj-rib-in
                for i in range(0, len(adj_rib_in[ip])):
                    if(adj_rib_in[ip][i].routePrefix == withdrawnPrefix):
                        bgpRoute = adj_rib_in[ip].pop(i)
                        break;

                # Get the backup-group before the change
                pre_backup_group = prefix_to_backup_group(bgpRoute.routePrefix)
                # Get the previous as path
                pre_as_path = rib[withdrawnPrefix][0].asPath

                # Remove from the rib
                rib[withdrawnPrefix].remove(bgpRoute)
                if len(rib[withdrawnPrefix]) == 0:
                    del rib[withdrawnPrefix]

                # Get the backup-group after the change
                post_backup_group = prefix_to_backup_group(bgpRoute.routePrefix)

                # Propagate the virtual announcements if the backup-group has changed
                if not pre_backup_group.__eq__(post_backup_group):
                    if post_backup_group.R1 == 'None':
                        pre_backup_group.virtual_withdraw(bgpRoute.routePrefix, None)
                    else:
                        post_backup_group.virtual_announce(bgpRoute.routePrefix, rib[bgpRoute.routePrefix][0].asPath, None)
                        if post_backup_group.holded_prefixes == 0:
                            post_backup_group.insert_primary_rule(pusher, switch_dpid, mapping_id, log)
                        #pre_backup_group.delete_primary_rule(pusher, log)

                    # Update backup-groups hold prefixes value
                    pre_backup_group.holded_prefixes -= 1
                    post_backup_group.holded_prefixes += 1

                if len(adj_rib_in[ip]) == 0:
                    # Remove the out-of-date backup-group
                    # First, deletion of each (nexthop, x) backup-groups
                    del backup_groups[bgpRoute.nextHop]

                    # Second, deletion of each (x, nexthop) backup-groups
                    for nextHop in backup_groups:
                        del backup_groups[nextHop][bgpRoute.nextHop]


while True:
    try:
        line = sys.stdin.readline().strip()

        msg.write(line + '\n')
        msg.flush()

        bgp_message = json.loads(line)

        for k,v in bgp_message.iteritems():

            ip = ''

            if (k=='neighbor'):
                for k1,v1 in v.iteritems():
                    if (k1=='ip'):
                        ip = IPAddress(v1)

                        #If first time talking to neighbor, add to adj_rib_out
                        if(ip not in adj_rib_in):
                            adj_rib_in[ip] = []

                    #Check to see if TCP connection state is still up
                    if (k1=='state'):
                        if (v1 == 'down'):
	                        process_down (ip)

                    if (k1=='update'):
                        if ('attribute' in v1):
	                        asPath, asPathLength = process_attribute(v1['attribute'])
                        if ('announce' in v1):
	                        process_announce(ip, v1['announce'], asPath, asPathLength)
                        if ('withdraw' in v1):
	                        process_withdraw(ip, v1['withdraw'])


    except KeyboardInterrupt:
	    pass
    except IOError:
	    # most likely a signal during readline
	    pass

log.close()
msg.close()

