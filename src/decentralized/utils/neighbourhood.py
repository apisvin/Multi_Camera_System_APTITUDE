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
        self.lockMyself = threading.Lock()
        self.myself = myself

        self.lockCluster = threading.Lock() #acquire and release to protect variable
        self.cluster = {} #dictionnary where keys are hardwareID of agent
        

    def refresh_cluster(self, received_neighbour):
        """
        refresh cluster state with neighbour. If this neighbour is not in cluster, add it. Else pass.
        """
        self.lockCluster.acquire()
        if received_neighbour.hardwareID not in self.cluster:
            logging.debug("New neighbour added to cluster : {}".format(received_neighbour.hardwareID))
            self.cluster[received_neighbour.hardwareID] = received_neighbour
        else:
            self.cluster[received_neighbour.hardwareID].update_age()
        self.lockCluster.release()


    def check_age(self, timeLimit):
        self.lockCluster.acquire()
        for key in self.cluster.copy(): #iterate on copy because it is not allowed to change the size of a dictionary while iterating over it.
            if time.time()-self.cluster[key].age > timeLimit:
                self.cluster.pop(key)
                logging.debug("{} is removed from {}".format(key, self.myself.hardwareID))
                break
        self.lockCluster.release()

    def get_all_neighbours(self):
        """
        return a list of all neighbour of the cluster
        """
        self.lockCluster.acquire()
        ret = list(self.cluster.values())
        self.lockCluster.release()
        return ret


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
    