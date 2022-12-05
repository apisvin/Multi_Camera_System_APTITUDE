import time
import json
from utils.neighbour import *
import threading

class neighbourhood:
            
    def __init__(self, myself):
        """
        This class contains neighbours of a agent. As agents are organized in a hierarchy, 
        it has a parent, one or several children and cluster members. A cluster is definied as 
        agent with the same parent.
        Args : 
            myself : neighbour class that represents the agent 
        """
        self.lockParent = threading.Lock() #acquire and release to protect variable
        self.parent = 0
        
        self.lockChildren = threading.Lock() #acquire and release to protect variable
        self.children = []
        
        self.lockMyself = threading.Lock()
        self.myself = myself

        self.lockCluster = threading.Lock() #acquire and release to protect variable
        self.cluster = []
        
    def get_parent(self):
        """
        return the parent of the neighbourhood
        """
        return self.parent
    
    def get_children(self):
        """
        return list of children of the neighbourhood
        """
        return self.children
    
    def is_leader(self):
        """
        return True is neighbourhood has children
        """
        ret = False
        self.lockChildren.acquire()
        if self.children:
            ret = True
        self.lockChildren.release()
        return ret
    
    def isInChildren(self, agent):
        """
        return the index of the coerrespond agent in children. -1 is not in children
        """
        index = 0
        self.lockChildren.acquire()
        for n in self.children:
            if n.hardwareID == agent.hardwareID:
                self.lockChildren.release()
                return index
            index=index+1
        self.lockChildren.release()
        return -1
    
    def isDNSinChildren(self, DNS):
        """
        return True if DNS is a child's DNS. False otherwise.
        """
        self.lockChildren.acquire()
        existing_DNS = [c.DNS for c in self.children] #list of existing DNS
        self.lockChildren.release()
        return DNS in existing_DNS
    
    def isDNSinCluster(self, DNS):
        """
        return True if DNS is a cluster's DNS. False otherwise.
        a DNS is concidered as in cluster if only the last element is different
        """
        self.lockMyself.acquire()
        myDNSlist = self.myself.DNS.split(".")
        self.lockMyself.release()
        mycluster = ".".join(myDNSlist[0:-1])
        DNSlist = DNS.split(".")
        cluster = ".".join(DNSlist[0:-1])
        return mycluster == cluster
    
    def isChildrenFollower(self, DNS):
        """
        return True if neighbour with DNS is in children 
        AND is only a follower (not a leader)
        """
        if self.isDNSinChildren(DNS):
            self.lockChildren.acquire()
            for c in self.children:
                if c.DNS == DNS and not c.isLeader:
                    self.lockChildren.release()
                    return True
            self.lockChildren.release()
        return False
            
            
    
    def update_agent_age_leader(self, DNS, isLeader):
        """
        update age of agent with DNS
        """
        self.lockChildren.acquire()
        for child in self.children:
            if(child.DNS == DNS):
                child.update_age()
                child.isLeader = isLeader
        self.lockChildren.release()
        
        self.lockParent.acquire()
        if(self.parent != 0 and self.parent.DNS == DNS):
            self.parent.update_age()
            self.parent.isLeader = isLeader
        self.lockParent.release()

    
    def IP_is_not_in_children(self, newagent):
        """
        return boolean to tell if newagent IP is in children
        """
        self.lockChildren.acquire()
        for n in self.children:
            if n.ip == newagent.ip:
                return False
            self.lockChildren.release()
        
        self.lockChildren.release()
        return True
    
    def update_parent(self, newParent):
        """
        update the parent with newparent
        """
        if (newParent.level == self.myself.level +1):
            self.lockParent.acquire()
            self.parent = newParent #add parent to neighbourhood
            self.lockParent.release()
    
    
    #update the parent list 
    def update_children(self, newNeighbour):
        """
        add newNeighbour in children list
        """
        index = self.isInChildren(newNeighbour)
        if (index == -1 and newNeighbour.level == self.myself.level - 1): 
            self.lockChildren.acquire()
            self.children.append(newNeighbour) #add client to neighbourhood
            self.lockChildren.release()

    
    #delete from the list
    def deleteChild(self, deletedchildID):
        """
        remove neighbour with deletedchildID in children list
        """
        self.lockChildren.acquire()
        for child in self.children:
            if(deletedchildID == child.hardwareID):
                self.children.remove(child)
                self.lockChildren.release()
                return
        self.lockChildren.release()
                
    def deleteChildwithDNS(self, DNSchild):
        """
        remove neighbour with DNSchild in children list
        """
        self.lockChildren.acquire()
        for child in self.children:
            if(DNSchild == child.DNS):
                self.children.remove(child)
                self.lockChildren.release()
                return
        self.lockChildren.release()

    def deleteClusterwhitDNS(self, DNScluster):
        """
        remove neighbour with DNS DNScluster from cluster list
        """
        self.lockCluster.acquire()
        for c in self.cluster:
            if(DNScluster == c.DNS):
                self.cluster.remove(c)
                self.lockCluster.release()
                return
        self.lockCluster.release()
    
    def add_to_cluster(self, newNeighbour):
        """
        add newNeighbour to cluster list
        """
        self.cluster.append(newNeighbour)

    def cluster_str(self):
        """
        return a string containing DNS's of neighbours composing cluster
        """
        val = ""
        for c in self.cluster:
            val = val + "   " + c.DNS
        return val

    def get_all_neighbours(self):
        """
        return a list of all neighbour of the neighbourhood (parent, children and cluster)
        """
        val = []
        if(self.parent != 0):
            val.append(self.parent)
        val.extend(self.children)
        val.extend(self.cluster)
        return val

    def get_children_asdict(self):
        """
        retrun a list of dictionnary containing all children
        """
        val = []
        for child in self.children:
            val.append(child.__dict__)
        return val

    def get_hardware_manager_cluster(self):
        """
        return a list of neighbour
        this list contains one neighbour per different ip address in self.cluster
        """
        ret = []
        for c in self.cluster:
            existing_ip = [d["ip"] for d in ret]
            if c.ip not in existing_ip and c.ip != self.myself.ip:
                ret.append(c.__dict__)
        return ret
    
    
    def get_hardware_manager_children(self):
        """
        return a list of neighbour
        this list contains one neighbour per different ip address in self.children
        """
        ret = []
        for c in self.children:
            existing_ip = [d["ip"] for d in ret]
            if c.ip not in existing_ip and c.ip != self.myself.ip:
                ret.append(c.__dict__)
        return ret

    def get_children_info(self):
        """
        return a string with DNS's of all children
        """
        ret = ""
        for c in self.children:
            ret = ret + c.DNS + " "
        return ret

    def create_new_DNS(self, newagent):
        """
        create a new DNS to newagent based on existing agent
        A name is constructed as "agenttypeX" where X is an unique positive integer
        """
        i = 0
        existing_DNS = [c.DNS for c in self.children] #list of different DNS in children
        while self.myself.DNS+"."+newagent.agenttype+str(i) in existing_DNS:
            i=i+1
            time.sleep(1)
        return self.myself.DNS+"."+newagent.agenttype+str(i)
    
    def matchingDNSasParent(self, DNS):
        """
        check if DNS is a potential child
        condition is verified if first fields of DNS are my DNS
        """
        return ".".join(DNS.split(".")[:-1]) == self.myself.DNS