#  Author:
#  Muhammad Shahbaz (muhammad.shahbaz@gatech.edu)

import sys
import os
import getopt
import time

'''Function for parsing arguments'''
def getArgs():
    logfile = '';
    
    try:
        opts, args = getopt.getopt(sys.argv[1:],"h",["help", "logfile="])
    except getopt.GetoptError:
        print 'rs.py [--logfile <file name>]'
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print 'rs.py [--logfile <file name>]'
            sys.exit()
        elif opt == '--logfile':
            logfile = arg
    
    if(logfile==''):
        print 'rs.py [--logfile <file name>]'
        sys.exit()
    
    return logfile

def write_time ():
    return "["+time.asctime( time.localtime(time.time()) )+"]"

'''Write output to stdout'''
def write (data, fd):
    sys.stdout.write(data + '\n')
    sys.stdout.flush()
    if fd != None:
        fd.write(write_time()+" "+data+"\n")
        fd.flush

def write_backup_groups (backup_groups):
	message = "START BACKUP-GROUPS\n"
	for g in backup_groups:
		for bg in backup_groups[g]:
			message += str(backup_groups[g][bg])
			message += '\n'
	message += "END BACK-UP GROUP\n"
	return message

def write_rib (rib):
    message = "START RIB\n"
    for prefix in rib:
        message += str(prefix)+"\n"
        for bgpRoute in rib[prefix]:
            message += "\t"+str(bgpRoute)+"\n"
    message += "END RIB\n"
    return message

