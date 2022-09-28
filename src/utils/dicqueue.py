from queue import Queue

class dicqueue:
    """
    la classe dicqueue contient l ensemble des queue necessaire a la communication entre threads.
    Deux queues doivent etre communes à tous les agents agents : Qtosendunicast et Qtosendbroadcast 
    puisque il n y a que un sender par hardware
    """

    def __init__(self, Qtosendunicast, Qtosendbroadcast, QtoHardwareManager):
        self.Qtosendunicast =       Qtosendunicast
        self.Qtosendbroadcast =     Qtosendbroadcast
        self.QtoHardwareManager =   QtoHardwareManager
        self.Qtoidentification =    Queue()
        self.Qtowatcher =           Queue()
        self.Qfromrectokalman =     Queue()
        self.Qfromtrackers =        Queue()
        self.Qtoplot =              Queue()
