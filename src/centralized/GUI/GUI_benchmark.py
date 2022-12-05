from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from utils.launcher import *
import logging
import time

class App(Tk):
    def __init__(self, hardware_manager, Qtosendunicast, Qtosendbroadcast):
        """
        This class is used to managed all agents implemented on this hardware during a predifined benchmark.
        The goal is to create a listing of the different actions (create, wait and remove) during the benchmark on this hardware.
        Specificities of buttons : 
            Add agent : add the creation of an agent with DNS, type and level specified above.
            Add time interval : add a delay in te timeline of the benchmark
            Remove agent : the selected agent is removed 
            Save config : Save all the command in a file 
            Load config : Load a saved file with the commands 
            Begin benchmark : Launch the benchmark. User must choose if the hardware is master or slave. 
                              If slave, it will waits until master is launched. This necessary to synchronized all benchmark.

        Args : 
            hardware_manager : the hardware_manager of the hardware
            Qtosendunicast (Queue) : a queue used by the unicast sender thread 
            Qtosendbroadcast (Queue) : a queue used by the broadcast sender thread 
        """

        super().__init__()

        self.hardware_manager = hardware_manager
        self.Qtosendunicast = Qtosendunicast
        self.Qtosendbroadcast = Qtosendbroadcast

        self.delay = 0 #for synchronization in offline processing 

        self.title("Benchmark")
        self.geometry("500x800")
        #counter for row 
        r = 0
        #############################
        #Title
        ttk.Label(self, text="ADD AGENT").grid(row=r, column=0)
        r+=1

        #DNS 
        DNS = StringVar()

        DNS_label = ttk.Label(self, text="DNS:")
        DNS_label.grid(row=r, column=0)
        r+=1

        DNS_entry = ttk.Entry(self, textvariable=DNS)
        DNS_entry.grid(row=r, column=0)
        r+=1
        DNS_entry.focus()
        
        #Agent type
        type_label = ttk.Label(self, text="Agent type :")
        type_label.grid(row=r, column=0)
        r+=1
        types = ("Detector", "OfflineDetector", "Tracker", "VIVE", "evaluator", "Recorder", "Blank")
        agenttype = StringVar()
        for t in types:
            rb = ttk.Radiobutton(
                self,
                text=t,
                value=t,
                variable=agenttype
            )
            rb.grid(row=r, column=0)
            r+=1
        
        #level
        level_label = ttk.Label(self, text="Level :")
        level_label.grid(row=r, column=0)
        r+=1
        level = StringVar(value=0)
        spin_box = ttk.Spinbox(
            self,
            from_=0,
            to=30,
            textvariable=level,
            wrap=True)
        spin_box.grid(row=r, column=0)
        r+=1

        #folder for offline detector
        folder = StringVar()

        videopath_label = ttk.Label(self, text="select a forlder for offlinedetecor:")
        videopath_label.grid(row=r, column=0)
        r+=1
        def select_folder():
            path= filedialog.askdirectory()
            folder.set(path)
            print("selected folder = ", folder.get())
        r+=1
        

        videopath_button = ttk.Button(self, text="Select a folder", command= select_folder)
        videopath_button.grid(row=r, column=0)
        r+=1
        videopath_button.focus()


        #Button ADD
        button = ttk.Button(self, text='Add agent',command=lambda : self.add_clicked(DNS_entry.get(), agenttype.get(), level.get(), folder.get()))
        button.grid(row=r, column=0)
        r+=1
        ###################################################

        #Title
        ttk.Label(self, text="").grid(row=r, column=0)
        r+=1
        ttk.Label(self, text="ADD TIME INTERVAL [s]").grid(row=r, column=0)
        r+=1

        time_var = StringVar()

        time_entry = ttk.Entry(self, textvariable=time_var)
        time_entry.grid(row=r, column=0)
        r+=1
        time_entry.focus()

        #Button TIME
        button = ttk.Button(self, text='Add time interval',command=lambda : self.add_time(time_var.get()))
        button.grid(row=r, column=0)
        r+=1

        ###################################################
        #Title 
        ttk.Label(self, text="").grid(row=r, column=0)
        r+=1
        ttk.Label(self, text="SELECT AGENT TO REMOVE").grid(row=r, column=0)
        r+=1

        button = ttk.Button(self, text='Remove agent',command=lambda : self.remove_clicked())
        button.grid(row=r, column=0)
        r+=1


        ###################################################
        ttk.Label(self, text="").grid(row=r, column=0)
        r+=1

        button = ttk.Button(self, text='Save config',command=lambda : self.save_clicked())
        button.grid(row=r, column=0)
        r+=1
        
        button = ttk.Button(self, text='Load config',command=lambda : self.load_clicked())
        button.grid(row=r, column=0)
        r+=1

        ###################################################

        #Listing agents 
        ttk.Label(self, text="SUMMARY COMMAND").grid(row=0, column=1)
        self.list_command = Listbox(height=r, width=40)
        self.list_command.grid(row=1, column=1, rowspan=r, columnspan=2)
        self.index = 1


        types = ("Master", "Slave")
        self.Master = StringVar()
        for t in types:
            rb = ttk.Radiobutton(
                self,
                text=t,
                value=t,
                variable=self.Master
            )
            rb.grid(row=r, column=1)
            r+=1



        button = ttk.Button(self, text='Begin benchmark',command=lambda : self.launch_benchmark())
        button.grid(row=r, column=1)
        r+=1
        
        self.lineID=0


        


    def add_clicked(self, DNS, agenttype, level, folder=None):
        #create lauuncher in hardware manager 
        l = launcher(agenttype=str.lower(agenttype), level=int(level), DNS=DNS, Qtosendunicast=self.Qtosendunicast, Qtosendbroadcast=self.Qtosendbroadcast, QtoHardwareManager=self.hardware_manager.QtoHardwareManager, folder=folder, delay=self.delay)
        self.hardware_manager.add(l)
        self.list_command.insert(END, ("ADD", agenttype, level, DNS, l.n.myself.hardwareID, self.lineID, folder))
        self.lineID+=1
        


    def remove_clicked(self):
        index = self.list_command.curselection()[0]           #get index of selected item in list_command
        if self.list_command.get(index)[0]!="ADD":
            logging.warning("please select an agent that exists.")
        else:
            removed_type = self.list_command.get(index)[1]
            removed_hardwareID = self.list_command.get(index)[4]  #extract corresponding hardwareID
            removed_lineID = self.list_command.get(index)[5]
            #self.list_command.delete(index)                       #delete line
            self.list_command.insert(END, ("REMOVE", removed_type, removed_hardwareID, removed_lineID))
        self.lineID+=1

    def add_time(self, interval):
        if not interval.isdigit():
            logging.warning("please type an integer for time interval.")
        else:
            self.list_command.insert(END, ("INTERVAL", int(interval)))
            self.delay = self.delay + int(interval)
        self.lineID+=1

        
    def save_clicked(self):
        #read all command and save in a file
        with open("/home/pi/Multi_Camera_System_APTITUDE/local_data/config.pickle", "wb") as fd:
            commands=[]
            for index in range(self.list_command.size()):
                command = []
                line = self.list_command.get(index)
                for c in line:
                    command.append(c)
                commands.append(command)
            pickle.dump(commands, fd)
            
                
    def load_clicked(self):
        #load all command from a txt file 
        with open("/home/pi/Multi_Camera_System_APTITUDE/local_data/config.pickle", "rb") as fd:
            commands = pickle.load(fd)
            for command in commands:
                if command[0]=="ADD":
                    agenttype = command[1]
                    level = command[2]
                    DNS = command[3]
                    self.add_clicked(DNS, agenttype, level)
                elif command[0] == "REMOVE":
                    removed_type = command[1]
                    removed_lineID = command[3]
                    removed_hardwareID = self.list_command.get(removed_lineID)[4]
                    self.list_command.insert(END, ("REMOVE", removed_type, removed_hardwareID, removed_lineID))
                elif command[0] == "INTERVAL":
                    interval = command[1]
                    self.list_command.insert(END, ("INTERVAL", int(interval)))
                
                
                    

    def launch_benchmark(self):
        #synchronization between hardware
        if self.Master.get()=="Master":
            blank_l = launcher(agenttype="blank", level=0, DNS="blankdns", Qtosendunicast = self.Qtosendunicast, Qtosendbroadcast = self.Qtosendbroadcast, QtoHardwareManager = self.hardware_manager.QtoHardwareManager)
            #self.hardware_manager.add(blank_l)
            #threading.Thread(target=blank_l.launch, args=()).start()
            msg = {"source" : blank_l.n.myself.__dict__,
                    "destination" : "all_agent",
                    "method" : "benchmark",
                    "spec" :""}
            self.Qtosendbroadcast.put(msg)
            msgremove = {"source" : "benchmarck",
                    "destination" : "hardware_manager",
                    "method" : "remove",
                    "spec" : {"hardwareID" : blank_l.n.myself.hardwareID}}
            #self.hardware_manager.QtoHardwareManager.put(msgremove)
        else:
            #create balnk agent to wait for benchmark message from master 
            blank_l = launcher(agenttype="blank", level=0, DNS="blankdns", Qtosendunicast = self.Qtosendunicast, Qtosendbroadcast = self.Qtosendbroadcast, QtoHardwareManager = self.hardware_manager.QtoHardwareManager)
            self.hardware_manager.add(blank_l)
            threading.Thread(target=blank_l.launch, args=()).start()
            #wait for message
            logging.debug("waiting to begin benchmark")
            msg = blank_l.dicqueue.Qtobenchmark.get()
            while msg["method"]!="benchmark":
                msg = blank_l.dicqueue.Qtobenchmark.get()
            #remove blank agent from hardware
            msgremove = {"source" : "benchmarck",
                    "destination" : "hardware_manager",
                    "method" : "remove",
                    "spec" : {"hardwareID" : blank_l.n.myself.hardwareID}}
            self.hardware_manager.QtoHardwareManager.put(msgremove)

        
        for index in range(self.list_command.size()):
            line = self.list_command.get(0)
            print(line)
            if line[0] == "ADD":
                #launch agent 
                hardwareID = line[4]
                l = self.hardware_manager.get(hardwareID)
                threading.Thread(target=l.launch, args=()).start()
            elif line[0] == "INTERVAL":
                print("wait {} s".format(line[1]))
                time.sleep(line[1])
            elif line[0] == "REMOVE":
                hardwareID = line[2]
                msg = {"source" : "GUI",
                    "destination" : "hardware_manager",
                    "method" : "remove",
                    "spec" : {"hardwareID" : hardwareID}}
                self.hardware_manager.QtoHardwareManager.put(msg)
            self.list_command.delete(0)                       #delete line
        print("end benchmark")


