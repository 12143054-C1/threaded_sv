from queue import Queue
import threading
import tkinter as tk
from tkinter import simpledialog, ttk


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
        """Function to add a new item to the treeview."""
        item = simpledialog.askstring("Input", "Enter comma-separated values for new item:")
        if item:  # Proceed only if something was entered
            values = item.split(',')
            if len(values) == len(self.columns):  # Check if the entered values match the number of columns
                self.tree.insert('', tk.END, values=values)
                self.task_queue.put(values)
            else:
                tk.messagebox.showerror("Error", f"The number of values entered does not match the number of columns: {len(self.columns)}.")

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
