from netaddr import *

class bgp_route:
    def __init__(self):
        self.nextHop = None
        self.asPath = ''
        self.asPathLength = 0
        self.routePrefix = None

    def compareTo(self,other):
        #Positive and negative reversed since this is being used for a max pq, not a minpq
        if(self.asPathLength < other.asPathLength):
            return -1
        if(self.asPathLength > other.asPathLength):
            return 1
            
        #If two AS share the same path length, compare based on IP Address
        if(self.nextHop < other.nextHop):
            return -1
        elif(self.nextHop > other.nextHop):
            return 1

    def __cmp__(self, other):
        #Positive and negative reversed since this is being used for a max pq, not a minpq
        if(self.asPathLength < other.asPathLength):
            return -1
        if(self.asPathLength > other.asPathLength):
            return 1
            
        #If two AS share the same path length, compare based on IP Address
        if(self.nextHop < other.nextHop):
            return -1
        elif(self.nextHop > other.nextHop):
            return 1

        return 0

    def __str__(self):
        return str(self.routePrefix)+" Next-Hop : "+str(self.nextHop)+" AS-Path : "+str(self.asPath)+" ("+str(self.asPathLength)+")" 


                                                                                                                        
                                                                                                                        
