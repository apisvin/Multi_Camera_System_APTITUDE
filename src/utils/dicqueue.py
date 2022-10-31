from queue import Queue
import logging

class dicqueue:
    """
    la classe dicqueue contient l ensemble des queue necessaire a la communication entre threads.
    Deux queues doivent etre communes à tous les agents agents : Qtosendunicast et Qtosendbroadcast 
    puisque il n y a que un sender par hardware
    """

    def __init__(self, Qtosendunicast, Qtosendbroadcast, QtoHardwareManager):
        """
        This class is used as a dictionnary of all needed queues for the inter thread communication.
        Indeed, in a multi threading environment, the synchronization is necessary. 
        Queues are data structures to exchange information across multiple threads safely.
        Three queues are common to all agents : Qtosendunicast, Qtosendbroadcast, QtoHardwareManager. The others are created unique to an agent.

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
        buf = "length of dicqueue : \n"
        buf = buf + "Qtosendunicast = {}\n".format(self.Qtosendunicast.qsize())
        buf = buf + "Qtosendbroadcast = {}\n".format(self.Qtosendbroadcast.qsize())
        buf = buf + "Qtoidentification = {}\n".format(self.Qtoidentification.qsize())
        logging.debug(buf)
