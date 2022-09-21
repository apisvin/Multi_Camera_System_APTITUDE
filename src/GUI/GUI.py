from tkinter import *
from tkinter import ttk
from utils.launcher import *

class App(Tk):
    def __init__(self, neighbourhood_h, Qtosendunicast, Qtosendbroadcast):
        super().__init__()

        self.neighbourhood_h = neighbourhood_h
        self.Qtosendunicast = Qtosendunicast
        self.Qtosendbroadcast = Qtosendbroadcast

        self.title("Add agent")
        self.geometry("300x200")

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


        #Button
        button = ttk.Button(self, text='Add agent',command=lambda : self.button_clicked(DNS_entry.get(), agenttype.get(), level.get()))
        button.pack()

    def button_clicked(self, DNS, agenttype, level):
        #launcher thread
        print("New agent created (type : "+ agenttype + ", DNS : " + DNS + ", level : " + level)
        task = launcher(agenttype=agenttype, level=int(level), DNS=DNS, Qtosendunicast=self.Qtosendunicast, Qtosendbroadcast=self.Qtosendbroadcast)
        self.neighbourhood_h.add(task)
        threading.Thread(target=task.launch, args=()).start()
        pass

