from queue import Queue
import logging

class dicqueue:

    def __init__(self, Qtosendunicast, Qtosendbroadcast, QtoHardwareManager):
        """
        This class is used as a dictionnary of all needed queues for the inter thread communication.
        Indeed, in a multi threading environment, the synchronization is necessary. 
        Queues are data structures to exchange information across multiple threads safely.
        Three queues are common to all agents : Qtosendunicast, Qtosendbroadcast, QtoHardwareManager. 
        The others are created unique to an agent.

        Args : 
            Qtosendunicast (Queue) : a queue used by the unicast sender thread 
            Qtosendbroadcast (Queue) : a queue used by the broadcast sender thread 
            QtoHardwareManager (Queue) : a queue used by the hardware manager
        """
        self.Qtosendunicast =       Qtosendunicast
        self.Qtosendbroadcast =     Qtosendbroadcast
        self.QtoHardwareManager =   QtoHardwareManager
        self.Qtoidentification =    Queue()
        self.Qtowatcher =           Queue()
        self.Qtotracker =           Queue()
        self.Qfromtrackers =        Queue()
        self.Qtoplot =              Queue()
        self.QtoVIVE =              Queue()
        self.Qtoeval =              Queue()
        self.Qtobenchmark =         Queue()
        
    def length(self):
        """
        Function that give a string containg length of different queues.
        """
        buf = "length of dicqueue : \n"
        buf = buf + "Qtosendunicast = {}\n".format(self.Qtosendunicast.qsize())
        buf = buf + "Qtosendbroadcast = {}\n".format(self.Qtosendbroadcast.qsize())
        buf = buf + "Qtoidentification = {}\n".format(self.Qtoidentification.qsize())
        buf = buf + "QtoHardwareManager = {}\n".format(self.QtoHardwareManager.qsize())
        buf = buf + "Qtotracker = {}\n".format(self.Qtotracker.qsize())
        buf = buf + "Qtoplot = {}\n".format(self.Qtoplot.qsize())
        return buf
