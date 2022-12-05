from tkinter import *
from tkinter import ttk
from utils.launcher import *
import logging

class App(Tk):
    def __init__(self, hardware_manager, Qtosendunicast, Qtosendbroadcast):
        """
        This class is used to managed all agents implemented on this hardware.
        The Graphic User Interface permits to create, observe and remove agents. 
        The first part of the interface is used to create an agent. We must give its DNS, type and level in the hierarchy.
        The second part is composed of the list of all agents created on this hardware. Each agent is followed by two fields : member of its cluster and its children (if any).
        "Refresh DNS" button is pressed to update the information displayed. "Remove" button is pressed to remove the selected agent.

        Args : 
            hardware_manager : the hardware_manager of the hardware
            Qtosendunicast (Queue) : a queue used by the unicast sender thread 
            Qtosendbroadcast (Queue) : a queue used by the broadcast sender thread 
        """
        super().__init__()

        self.hardware_manager = hardware_manager
        self.Qtosendunicast = Qtosendunicast
        self.Qtosendbroadcast = Qtosendbroadcast

        self.title("Managing agents")
        self.geometry("500x800")

        #Title
        ttk.Label(self, text="").pack()
        ttk.Label(self, text="ADD AGENT").pack()


        #Agent type
        type_label = ttk.Label(self, text="Agent type :")
        type_label.pack()
        types = ("Decentralized", "OfflineDecentralized", "VIVE", "Blank")
        agenttype = StringVar()
        for t in types:
            r = ttk.Radiobutton(
                self,
                text=t,
                value=t,
                variable=agenttype
            )
            r.pack()


        #Button ADD
        button = ttk.Button(self, text='Add agent',command=lambda : self.add_clicked(agenttype.get()))
        button.pack()

        #Title
        ttk.Label(self, text="").pack()
        ttk.Label(self, text="REMOVE AGENT").pack()

        #Listing agents 
        self.list_agent = Listbox(height=15)
        self.list_agent.pack()
        self.index = 1

        #Button REFRESH DNS
        button = ttk.Button(self, text='Refresh DNS',command=lambda : self.refresh_clicked())
        button.pack()

        #Button REMOVE
        button = ttk.Button(self, text='Remove agent',command=lambda : self.remove_clicked())
        button.pack()



    def add_clicked(self, agenttype):
        """
        Activated procedure when "Add agent" button is pressed. 
        Creates a launcher for the agent and add it to the list 
        """
        #launcher thread
        l = launcher(agenttype=str.lower(agenttype), Qtosendunicast=self.Qtosendunicast, Qtosendbroadcast=self.Qtosendbroadcast, QtoHardwareManager=self.hardware_manager.QtoHardwareManager)
        self.hardware_manager.add(l)
        threading.Thread(target=l.launch, args=()).start()
        self.list_agent.insert(END, (l.n.myself.hardwareID))

        


    def refresh_clicked(self):
        """
        Activated procedure when "Refresh agent" button is pressed.
        Update the listing of agents on the GUI 
        """
        self.list_agent.delete(0, self.list_agent.size()-1) #delete all lines 
        for hardwareID, launcher in self.hardware_manager.launchers.items():
            self.list_agent.insert(END, (launcher.n.myself.DNS, hardwareID))
            if launcher.n.children:
                self.list_agent.insert(END, "Children : ")
                for c in launcher.n.children:
                    self.list_agent.insert(END, ("     ", c.DNS))
            if launcher.n.cluster:
                self.list_agent.insert(END, "Cluster : ")
                for c in launcher.n.cluster:
                    self.list_agent.insert(END, ("     ", c.DNS))


    def remove_clicked(self):
        """
        Activated procedure when "Remove agent" button is pressed.
        Remove the selected agent on the listing and send the information to the hardware_manager 
        """
        index = self.list_agent.curselection()[0]           #get index of selected item in list_agent
        removed_hardwareID = self.list_agent.get(index)  #extract corresponding hardwareID
        msg = {"source" : "GUI",
                "destination" : "hardware_manager",
                "method" : "remove",
                "spec" : {"hardwareID" : removed_hardwareID}}
        self.hardware_manager.QtoHardwareManager.put(msg)
        self.list_agent.delete(index)                       #delete line


        pass

