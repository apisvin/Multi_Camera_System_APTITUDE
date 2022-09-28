from tkinter import *
from tkinter import ttk
from utils.launcher import *
import logging

class App(Tk):
    def __init__(self, hardware_manager, Qtosendunicast, Qtosendbroadcast):
        super().__init__()

        self.hardware_manager = hardware_manager
        self.Qtosendunicast = Qtosendunicast
        self.Qtosendbroadcast = Qtosendbroadcast

        self.title("Managing agents")
        self.geometry("300x500")

        #Title
        ttk.Label(self, text="").pack()
        ttk.Label(self, text="ADD AGENT").pack()

        #DNS 
        DNS = StringVar()

        DNS_label = ttk.Label(self, text="DNS:")
        DNS_label.pack()

        DNS_entry = ttk.Entry(self, textvariable=DNS)
        DNS_entry.pack()
        DNS_entry.focus()

        #Agent type
        type_label = ttk.Label(self, text="Agent type :")
        type_label.pack()
        types = ("Detection", "Tracking", "Blank")
        agenttype = StringVar()
        for t in types:
            r = ttk.Radiobutton(
                self,
                text=t,
                value=t,
                variable=agenttype
            )
            r.pack()

        #level
        level_label = ttk.Label(self, text="Level :")
        level_label.pack()
        level = StringVar(value=0)
        spin_box = ttk.Spinbox(
            self,
            from_=0,
            to=30,
            textvariable=level,
            wrap=True)
        spin_box.pack()


        #Button ADD
        button = ttk.Button(self, text='Add agent',command=lambda : self.add_clicked(DNS_entry.get(), agenttype.get(), level.get()))
        button.pack()

        #Title
        ttk.Label(self, text="").pack()
        ttk.Label(self, text="REMOVE AGENT").pack()

        #Listing agents 
        self.list_agent = Listbox()
        self.list_agent.pack()
        self.index = 1

        #Button REFRESH DNS
        button = ttk.Button(self, text='Refresh DNS',command=lambda : self.refresh_clicked())
        button.pack()

        #Button REMOVE
        button = ttk.Button(self, text='Remove agent',command=lambda : self.remove_clicked())
        button.pack()



    def add_clicked(self, DNS, agenttype, level):
        #launcher thread
        l = launcher(agenttype=agenttype, level=int(level), DNS=DNS, Qtosendunicast=self.Qtosendunicast, Qtosendbroadcast=self.Qtosendbroadcast, QtoHardwareManager=self.hardware_manager.QtoHardwareManager)
        self.hardware_manager.add(l)
        threading.Thread(target=l.launch, args=()).start()
        self.list_agent.insert(END, (l.n.myself.DNS, l.n.myself.hardwareID))
        """msg = {"source" : "GUI",
                "destination" : "hardware_manager",
                "method" : "create",
                "spec" : {"DNS" : DNS,
                            "agenttype" : agenttype,
                            "level" : level}}
        self.hardware_manager.QtoHardwareManager.put(msg)"""
        


    def refresh_clicked(self):
        self.list_agent.delete(0, self.list_agent.size()-1) #delete all lines 
        for hardwareID, launcher in self.hardware_manager.launchers.items():
            self.list_agent.insert(END, (launcher.n.myself.DNS, hardwareID))


    def remove_clicked(self):
        index = self.list_agent.curselection()[0]           #get index of selected item in list_agent
        removed_hardwareID = self.list_agent.get(index)[1]  #extract corresponding hardwareID
        msg = {"source" : "GUI",
                "destination" : "hardware_manager",
                "method" : "remove",
                "spec" : {"hardwareID" : removed_hardwareID}}
        self.hardware_manager.QtoHardwareManager.put(msg)
        self.list_agent.delete(index)                       #delete line


        pass

