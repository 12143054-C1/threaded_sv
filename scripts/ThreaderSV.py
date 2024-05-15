from queue import Queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk


# GLOBALS
setup_queue = Queue()
task_queue  = Queue()
indicators_status_dict = {
            'SixShot' : {
                'N/A'  : 'grey',
                'Error' : 'red',
                'Busy'  : 'yellow',
                'Ready' : 'green'
            },
            'Board' : {
                'N/A'   : 'grey',
                'Error' : 'red',
                'Busy'  : 'yellow',
                'Ready' : 'green'
            },
            'Intec' : {
                'N/A'   : 'grey',
                'Error' : 'red',
                'Busy'  : 'yellow',
                'Ready' : 'green'
            },
            'Unit' : {
                'N/A'   : 'grey',
                'Error' : 'red',
                'Busy'  : 'yellow',
                'Ready' : 'green'
            },
            'Switch' : {
                'N/A'   : 'grey',
                'Error' : 'red',
                'Busy'  : 'yellow',
                'Ready' : 'green'
            },
            'Scope' : {
                'N/A'   : 'grey',
                'Error' : 'red',
                'Busy'  : 'yellow',
                'Ready' : 'green'
            },
            'JBERT' : {
                'N/A'   : 'grey',
                'Error' : 'red',
                'Busy'  : 'yellow',
                'Ready' : 'green'
            }
        }
indicators_status = {
            'SixShot' : 'N/A',
            'Board'   : 'N/A',
            'Intec'   : 'N/A',
            'Unit'    : 'N/A',
            'Switch'  : 'N/A',
            'Scope'   : 'N/A',
            'JBERT'   : 'N/A'
        }

## Thread synchronization
change_indicator_event = threading.Event()


class MainGUI:
    def __init__(self, root, setup_queue,empty_task_list,configurations):
        self.root = root
        self.root.title("MTC1 | Main Debug")

        # Define top and bottom frames
        self.top_frame = tk.Frame(root)
        self.top_frame.pack(fill=tk.BOTH, padx=5, pady=5,expand=True)
        self.bottom_frame = tk.Frame(root)
        self.bottom_frame.pack(fill=tk.X, padx=5, pady=5,anchor="s")
        self.bottom_left_frame = tk.Frame(self.bottom_frame)
        self.bottom_left_frame.pack(padx=5, pady=5,anchor="w")
        
        # Build the top frame content

        # Define the columns
        self.columns = ('corner', 'phy', 'port', 'lane', 'protocol', 'test')

        # Create the Treeview
        self.tree = ttk.Treeview(self.top_frame, columns=self.columns, show="headings")
        

        # Define headings and column stretch
        for col in self.columns:
            self.tree.heading(col, text=col.title())
            self.tree.column(col, stretch=tk.YES, width=100)  # Set width of each column

        # Add a scrollbar
        self.scrollbar = ttk.Scrollbar(self.top_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill='y')  # Pack the scrollbar Right to the treeview
        self.tree.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)  # Expand the treeview to take available space
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        # Frame for indicators (boot indicator, equipment indicator, etc...)
        self.indicators_frame = tk.LabelFrame(self.top_frame,text='Equipment Status',labelanchor='n')
        self.indicators_frame.pack(fill=tk.X, padx=5, pady=5)
        self.indicators_frame.configure()

        # Create Indicators
        self.indicators_list = [
            'SixShot',
            'Board',
            'Intec',
            'Unit',
            'Switch',
            'Scope',
            'JBERT'
        ]
        self.indicator_sub_frame_dict ={}
        for indicator in self.indicators_list:
            ind_su_fr = tk.Frame(self.indicators_frame)
            ind_su_fr.pack(fill=tk.X, padx=5, pady=5)
            ind_ind = tk.Label(ind_su_fr,text='N/A',bg='grey',width=8,name="ind_ind",relief='sunken')
            ind_ind.pack(side=tk.RIGHT)
            ind_equip = tk.Label(ind_su_fr,text=indicator,name='ind_equip')
            ind_equip.pack(side=tk.LEFT)
            self.indicator_sub_frame_dict[indicator] = ind_su_fr
        threading.Thread(target=self.update_indicator,daemon=True).start()

        # Frame for controls (add/remove buttons)
        self.controls_frame = tk.Frame(self.top_frame)
        self.controls_frame.pack(fill=tk.X, padx=5, pady=5)
        self.controls_frame.configure()

        # Add button
        self.add_button = tk.Button(self.controls_frame, text="Add Item", command=self.add_item)
        self.add_button.pack(fill=tk.X,pady=2)

        # Remove button
        self.remove_button = tk.Button(self.controls_frame, text="Remove Selected", command=self.remove_item)
        self.remove_button.pack(fill=tk.X,pady=2)

        # Remove all button
        self.remove_all_button = tk.Button(self.controls_frame, text="Remove All", command=self.remove_all)
        self.remove_all_button.pack(fill=tk.X,pady=2)

        # Generate list button
        self.generate_list_button = tk.Button(self.controls_frame, text="Generate List from Setup", command=self.generate_list)
        self.generate_list_button.pack(fill=tk.X,pady=2)

        # Seperator
        self.button_seperator = tk.Label(self.controls_frame,height=3)
        self.button_seperator.pack(fill=tk.X)

        # Run Tests In Queue
        self.run_tests_in_queue_button = tk.Button(self.controls_frame, text="Run Tests In Queue", command=self.run_tests_in_queue)
        self.run_tests_in_queue_button.pack(fill=tk.X,pady=2)

        # Queue for tasks
        self.setup_queue = setup_queue
        self.task_queue = Queue()

        if not empty_task_list:
            self.generate_list()
        
        # Build the bottom frame content
        for global_parameter in configurations['global']:
            gp = tk.Label(self.bottom_left_frame,text=f'{global_parameter} :\t\t{configurations["global"][global_parameter]}',name=global_parameter.lower(),anchor='w',borderwidth=2, relief="ridge")
            gp.pack(fill=tk.X)


    def update_indicator(self):
            color_c1 = {
                'red'    : '#ff0000',
                'green'  : '#00ff00',
                'yellow' : 'yellow',
                'grey'   : 'grey'
            }
            global change_indicator_event
            global indicators_status_dict
            global indicators_status
            while True:
                change_indicator_event.wait()
                for indicator_name in self.indicators_list:
                    # CHAT GPT CHANGE THE NEXT LINE TO MATCH THE CODE!!!
                    self.indicator_sub_frame_dict[indicator_name].children['ind_ind'].configure(
                        bg=color_c1[indicators_status_dict[indicator_name][indicators_status[indicator_name]]],
                        text=indicators_status[indicator_name])
                change_indicator_event.clear()

    def run_tests_in_queue(self):
        print("WIP!")


    def add_item(self):
        """Function to add a new item to the treeview using a custom input frame."""
        def on_submit():
            tests = []
            corners =        [val['text'] for val in Corners_checkbox_vars if val['value'].get() == 1]
            tcss_ports =     [val['text'] for val in tcss_ports_checkbox_vars if val['value'].get() == 1]
            tcss_lanes =     [val['text'] for val in tcss_lanes_checkbox_vars if val['value'].get() == 1]
            tcss_protocols = [val['text'] for val in tcss_protocols_checkbox_vars if val['value'].get() == 1]
            tcss_tests =     [val['text'] for val in tcss_tests_checkbox_vars if val['value'].get() == 1]
            edp_lanes =      [val['text'] for val in edp_lanes_checkbox_vars if val['value'].get() == 1]
            edp_protocols =  [val['text'] for val in edp_protocols_checkbox_vars if val['value'].get() == 1]
            edp_tests =      [val['text'] for val in edp_tests_checkbox_vars if val['value'].get() == 1]
            for corner in corners:
                for port in tcss_ports:
                    for lane in tcss_lanes:
                        for protocol in tcss_protocols:
                            for test in tcss_tests:
                                tests.append([corner,'TCSS',port,lane,protocol,test])
            for corner in corners:
                    for lane in edp_lanes:
                        for protocol in edp_protocols:
                            for test in edp_tests:
                                tests.append([corner,'eDP',0,lane,protocol,test])
            for test in tests:
                self.tree.insert('', 'end', values=test)
                self.task_queue.put(test)
            input_window.destroy()


        input_window = tk.Toplevel(self.root)
        input_window.title("Input")
        top_frame = tk.Frame(input_window)
        bottom_frame = tk.Frame(input_window)
        top_frame.pack()
        bottom_frame.pack()

        # Corners Checkboxes
        corners_frame = tk.LabelFrame(top_frame, text="Corners")
        corners_frame.pack(fill='both', padx=5, pady=5,side="left")
        Corners_checkbox_texts = [
            "NOM",
            "LVHT",
            "LVLT",
            "HVLT",
            "HVHT"
            ]
        Corners_checkbox_vars = []
        for text in Corners_checkbox_texts:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(corners_frame, text=text, variable=var)
            checkbox.pack(anchor='w')
            Corners_checkbox_vars.append({'value':var,'text':text})
        
        
        # tcss
        tcss_frame = tk.LabelFrame(top_frame, text="TCSS")
        tcss_frame.pack(fill='both', padx=5, pady=5,side='left')
        # tcss ports
        tcss_ports_frame = tk.LabelFrame(tcss_frame, text="Ports")
        tcss_ports_frame.pack(fill='both', padx=5, pady=5,side='left')
        tcss_ports_checkbox_texts = ["0","1","2"]
        tcss_ports_checkbox_vars = []
        for text in tcss_ports_checkbox_texts:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(tcss_ports_frame, text=text, variable=var)
            checkbox.pack(anchor='w')
            tcss_ports_checkbox_vars.append({'value':var,'text':text})
        # tcss lanes
        tcss_lanes_frame = tk.LabelFrame(tcss_frame, text="Lanes")
        tcss_lanes_frame.pack(fill='both', padx=5, pady=5,side="left")
        tcss_lanes_checkbox_texts = ["0","1","2","3"]
        tcss_lanes_checkbox_vars = []
        for text in tcss_lanes_checkbox_texts:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(tcss_lanes_frame, text=text, variable=var)
            checkbox.pack(anchor='w')
            tcss_lanes_checkbox_vars.append({'value':var,'text':text})
        # tcss protocols
        tcss_protocols_frame = tk.LabelFrame(tcss_frame, text="Protocols")
        tcss_protocols_frame.pack(fill='both', padx=5, pady=5,side="left")
        tcss_protocols_checkbox_texts = [
            'TBT20',
            'TBT20.6',
            'TBT10',
            'TBT10.3',
            'DP20'
            ]
        tcss_protocols_checkbox_vars = []
        for text in tcss_protocols_checkbox_texts:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(tcss_protocols_frame, text=text, variable=var)
            checkbox.pack(anchor='w')
            tcss_protocols_checkbox_vars.append({'value':var,'text':text})
        #tcss tests
        tcss_tests_frame = tk.LabelFrame(tcss_frame, text="Tests")
        tcss_tests_frame.pack(fill='both', padx=5, pady=5,side="left")
        tcss_tests_checkbox_texts = [
            "TxBaseSigtest_UiOnly",
            "TxBaseSigtest_JitterOnly",
            "tcss_rx_jtol"
            ]
        tcss_tests_checkbox_vars = []
        for text in tcss_tests_checkbox_texts:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(tcss_tests_frame, text=text, variable=var)
            checkbox.pack(anchor='w')
            tcss_tests_checkbox_vars.append({'value':var,'text':text})

        # edp
        edp_frame = tk.LabelFrame(top_frame, text="eDP")
        edp_frame.pack(fill='both', padx=5, pady=5,side='left')
        # edp lanes
        edp_lanes_frame = tk.LabelFrame(edp_frame, text="Lanes")
        edp_lanes_frame.pack(fill='both', padx=5, pady=5,side="left")
        edp_lanes_checkbox_texts = ["0","1","2","3"]
        edp_lanes_checkbox_vars = []
        for text in edp_lanes_checkbox_texts:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(edp_lanes_frame, text=text, variable=var)
            checkbox.pack(anchor='w')
            edp_lanes_checkbox_vars.append({'value':var,'text':text})
        # edp protocols
        edp_protocols_frame = tk.LabelFrame(edp_frame, text="Protocols")
        edp_protocols_frame.pack(fill='both', padx=5, pady=5,side="left")
        edp_protocols_checkbox_texts = [
            '8.1'
            ]
        edp_protocols_checkbox_vars = []
        for text in edp_protocols_checkbox_texts:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(edp_protocols_frame, text=text, variable=var)
            checkbox.pack(anchor='w')
            edp_protocols_checkbox_vars.append({'value':var,'text':text})
        # edp tests
        edp_tests_frame = tk.LabelFrame(edp_frame, text="Tests")
        edp_tests_frame.pack(fill='both', padx=5, pady=5,side="left")
        edp_tests_checkbox_texts = ["EHEW", "Jitters"]
        edp_tests_checkbox_vars = []
        for text in edp_tests_checkbox_texts:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(edp_tests_frame, text=text, variable=var)
            checkbox.pack(anchor='w')
            edp_tests_checkbox_vars.append({'value':var,'text':text})


        # Submit button
        submit_button = tk.Button(bottom_frame, text="Submit", command=on_submit)
        submit_button.pack(pady=10)

    def remove_item(self):
        """Function to remove the selected item from the treeview."""
        selected_items = self.tree.selection()  # Returns a list of selected items
        for selected_item in selected_items:
            self.tree.delete(selected_item)

    def remove_all(self):
        """Function to remove all items from the treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def generate_list(self):
        """Function to generate a list from setup."""
        tmp = Queue()
        while not self.setup_queue.empty():
            values = self.setup_queue.get()
            tmp.put(values)
            if len(values) == len(self.columns):  # Check if the entered values match the number of columns
                self.tree.insert('', tk.END, values=values)
        while not tmp.empty():
            self.setup_queue.put(tmp.get())

class MainClass():
    def __init__(self, empty_task_list=False) -> None:
        self.empty_task_list = empty_task_list
        self.task_queue = Queue()
        self.DoTechnicals()
        self.configurations = {
            "global": {
                "Scope IP": "192.168.137.5",
                "JBERT IP": "7.7.7.7",
                "Switch IP": "1.10.5.59",
                "Switch Map Path": r"T:\ATD_IO\LNL\PCIe5\LNL_6shot_Tx_Switch_Map.csv"
            },
            "tcss": {
                "global": {
                    "bin_file_destination_folder": r"bin\dest",
                    "sigtest_results_folder": r"sigtest\results\dest"
                },
                "TBT10": {
                    "scope_preset_path": r"scope\path",
                    "jbert_preset_path": r"jbert\path",
                    "preset": 2
                },
                "TBT20": {
                    "scope_preset_path": r"scope\path",
                    "jbert_preset_path": r"jbert\path",
                    "preset": 2
                },
                "DP20": {
                    "scope_preset_path": r"scope\path",
                    "jbert_preset_path": r"jbert\path",
                    "preset": 1
                }
            },
            "edp": {
                "global": {
                    "jitter_data_folder": r"jitter\data\folder",
                    "eye_data_folder": r"eye\data\folder",
                },
                "8.1": {
                    "scope_preset_path": r"scope\path",
                    "jbert_preset_path": r"jbert\path",
                    "preset": 0
                }
            }
        }

    def DoTechnicals(self):
        self.setup_tasks = Queue()
        self.TaskGenerator()
        self.RunGUI_in_new_Thread()

    def TaskGenerator(self):
        corners = ["NOM", "LVHT", "LVLT", "HVLT", "HVHT"]
        phy_s = ["tcss", "edp"]
        tests = {
            "tcss": [
                "ui_ssc_eye",
                "rise_fall_time",
                "jitter",
                "ac_common_mode",
                "transmitter_equalization",
                "electrical_idle_voltage"
            ],
            "edp": ["EHEW", "Jitters"],
        }
        instances = {
            "tcss": [0,1,2],
            "edp": [0],
        }
        lanes = {
            "tcss": [0, 3],
            "edp": [0, 2],
        }
        protocols = {
            "tcss": ["TBT20", "TBT10", "DP20"],
            "edp": ["8.1"],
        }
        for corner in corners:
            for phy in phy_s:
                for instance in instances[phy]:
                    for lane in lanes[phy]:
                        for protocol in protocols[phy]:
                            for test in tests[phy]:
                                new_task = [corner, phy, instance, lane, protocol, test]
                                self.setup_tasks.put(new_task)

    def RunGUI_in_new_Thread(self):
        # Create a new thread targeting the function that initializes and runs the GUI.
        threading.Thread(target=self.init_gui).start()

    def init_gui(self):
        root = tk.Tk()
        self.app = MainGUI(root, self.setup_tasks,self.empty_task_list,self.configurations)
        root.mainloop()

if __name__ == "__main__":
    a = MainClass(True)
    indicators_status["Board"] = 'Ready'
    indicators_status['Intec'] = 'Busy'
    indicators_status['Switch'] = 'Error'
    change_indicator_event.set()
