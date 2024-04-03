'''
Main module. calls all the other modules, creates threads.
'''
import threading,sys,os
import tkinter as tk
from tkinter import simpledialog, ttk
from queue import Queue

global_setup_tasks = []
global_gui_tasks = []

class SimpleGUI:
    def __init__(self, root, empty_task_list):
        self.root = root
        self.root.title("Scrollable Table GUI")

        # Define the columns
        self.columns = ('corner', 'phy', 'instance', 'lane', 'protocol', 'test')

        # Create the Treeview
        self.tree = ttk.Treeview(root, columns=self.columns, show="headings")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)  # Expand the treeview to take available space

        # Define headings and column stretch
        for col in self.columns:
            self.tree.heading(col, text=col.title())
            self.tree.column(col, stretch=tk.YES, width=100)  # Set width of each column

        # Add a scrollbar
        self.scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=self.tree.yview)
        self.scrollbar.pack(side=tk.LEFT, fill='y')  # Pack the scrollbar next to the treeview
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        # Insert the items into the treeview
        if not empty_task_list:
            global global_setup_tasks
            for item in global_setup_tasks:
                self.tree.insert('', tk.END, values=item)

        # Frame for controls (add/remove buttons)
        self.controls_frame = tk.Frame(root)
        self.controls_frame.pack(fill=tk.X, padx=5, pady=5)

        # Add button
        self.add_button = tk.Button(self.controls_frame, text="Add Item", command=self.add_item)
        self.add_button.grid(row=0, column=0, padx=(0, 10))

        # Remove button
        self.remove_button = tk.Button(self.controls_frame, text="Remove Selected", command=self.remove_item)
        self.remove_button.grid(row=0, column=1)

        # Remove all button
        self.remove_all_button = tk.Button(self.controls_frame, text="Remove All", command=self.remove_all)
        self.remove_all_button.grid(row=1, column=0, padx=(0, 10))

        # Generate list button
        self.generate_list_button = tk.Button(self.controls_frame, text="Generate List from Setup", command=self.generate_list)
        self.generate_list_button.grid(row=1, column=1)

    def add_item(self):
        """Function to add a new item to the treeview."""
        item = simpledialog.askstring("Input", "Enter comma-separated values for new item:")
        if item:  # Proceed only if something was entered
            values = item.split(',')
            if len(values) == len(self.columns):  # Check if the entered values match the number of columns
                self.tree.insert('', tk.END, values=values)
                global global_gui_tasks
                global_gui_tasks.append(list(values))
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
        global global_setup_tasks
        for values in global_setup_tasks:  # Proceed only if something was entered
            if len(values) == len(self.columns):  # Check if the entered values match the number of columns
                self.tree.insert('', tk.END, values=values)

class MainClass():
    def __init__(self,empty_task_list = False) -> None:
        self.empty_task_list = empty_task_list
        self.DoTechnicals()
        self.configurations = {
                "global" : {
                    "scope_ip"        : "0.0.0.0",
                    "jbert_ip"        : "0.0.0.0",
                    "switch_ip"       : "0.0.0.0",
                    "switch_map_path" : r"switch\map\path",
                    
                },
                "tcss" : {
                    "global" : {
                        "bin_file_destination_folder" : r"bin\dest",
                        "sigtest_results_folder"      : r"sigtest\results\dest"
                    },
                    "TBT10" : {
                        "scope_preset_path" : r"scope\path",
                        "jbert_preset_path" : r"jbert\path",
                        "preset" : 2
                    },
                    "TBT20" : {
                        "scope_preset_path" : r"scope\path",
                        "jbert_preset_path" : r"jbert\path",
                        "preset" : 2
                    },
                    "DP20" : {
                        "scope_preset_path" : r"scope\path",
                        "jbert_preset_path" : r"jbert\path",
                        "preset" : 1
                    }
                },
                "edp" : {
                    "global"  : {
                        "jitter_data_folder" : r"jitter\data\folder",
                        "eye_data_folder"    : r"eye\data\folder",
                    },
                    "8.1" : {
                        "scope_preset_path" : r"scope\path",
                        "jbert_preset_path" : r"jbert\path",
                        "preset" : 0
                    }
                }
            }
    
    def DoTechnicals(self):
        global global_setup_tasks
        global_setup_tasks = self.TaskGenerator()
        self.RunGUI()

    def TaskGenerator(self) -> list:
        tasks = []
        corners =  ["NOM","LVHT","LVLT","HVLT","HVHT"] 
        phy_s = ["tcss","edp"]
        tests = {
            "tcss"  : [
                "ui_ssc_eye",
                "rise_fall_time",
                "jitter",
                "ac_common_mode",
                "transmitter_equalization",
                "electrical_idle_voltage"
            ],
            "edp"   : ["EHEW","Jitters"],
        }
        instances = {
            "tcss"  : [1],
            "edp"   : [0],
        }
        lanes = {
            "tcss"  : [0,3],
            "edp"   : [0,2],
        }
        protocols = {
            "tcss"  : ["TBT20","TBT10","DP20"],
            "edp"   : ["8.1"],
        }
        for corner in corners:
            for phy in phy_s:
                for instance in instances[phy]:
                    for lane in lanes[phy]:
                        for protocol in protocols[phy]:
                            for test in tests[phy]:
                                new_task = [corner,phy,instance,lane,protocol,test]
                                #print(f"Adding task to list: {new_task}")
                                tasks.append(new_task)
        return tasks
    
    def RunGUI(self):
        # Create a new thread targeting the function that initializes and runs the GUI.
        threading.Thread(target=self.init_gui).start()
    
    def init_gui(self):
        root = tk.Tk()
        app = SimpleGUI(root,self.empty_task_list)
        root.mainloop()


if __name__ == "__main__":
    A = MainClass(False)