import threading
import tkinter as tk
from tkinter import messagebox, ttk, filedialog, PhotoImage
import subprocess
import os
import sys
import datetime
from PIL import Image, ImageTk
import json
import tkinter.ttk as ttk
import inspect



# GLOBALS
VERSION = 0.1
YEAR = datetime.datetime.now().year
DEBUG = True
indicators_status_dict = {
    'SixShot': {
        'N/A': 'grey',
        'Error': 'red',
        'Busy': 'yellow',
        'Ready': 'green'
    },
    'Board': {
        'N/A': 'grey',
        'Error': 'red',
        'Busy': 'yellow',
        'Ready': 'green'
    },
    'Intec': {
        'N/A': 'grey',
        'Error': 'red',
        'Busy': 'yellow',
        'Ready': 'green'
    },
    'Unit': {
        'N/A': 'grey',
        'Error': 'red',
        'Busy': 'yellow',
        'Ready': 'green'
    },
    'Switch': {
        'N/A': 'grey',
        'Error': 'red',
        'Busy': 'yellow',
        'Ready': 'green'
    },
    'Scope': {
        'N/A': 'grey',
        'Error': 'red',
        'Busy': 'yellow',
        'Ready': 'green'
    },
    'JBERT': {
        'N/A': 'grey',
        'Error': 'red',
        'Busy': 'yellow',
        'Ready': 'green'
    }
}
indicators_status = {
    'SixShot': 'N/A',
    'Board': 'N/A',
    'Intec': 'N/A',
    'Unit': 'N/A',
    'Switch': 'N/A',
    'Scope': 'N/A',
    'JBERT': 'N/A'
}

## Thread synchronization
change_indicator_event = threading.Event()
jobber_wait_event = threading.Event()
jobber_continue_event = threading.Event()
stop_event = threading.Event()
anti_lock_event = threading.Event()




# global functions
def print_call_stack():
    stack = inspect.stack()
    for frame in stack[1:2]:
        #print(f"File: {frame.filename}, Line: {frame.lineno}, Function: {frame.function}")
        print(f"Line: {frame.lineno}, Function: {frame.function}")


class State:
    def __init__(self):
        self.state = ""
        self.lock = threading.Lock()

    def set(self,state: str):
        with self.lock:
            self.state = state
    
    def get(self):
        with self.lock:
            return self.state


class Queue:
    def __init__(self):
        self.queue = []
        self.lock = threading.Lock()

    def put(self, item):
        with self.lock:
            self.queue.append(item)

    def get(self):
        with self.lock:
            if len(self.queue) == 0:
                return None
            return self.queue.pop(0)

    def size(self):
        with self.lock:
            return len(self.queue)
        
    def empty(self):
        with self.lock:
            return len(self.queue) == 0
    
    def show_all(self):
        with self.lock:
            return self.queue


def load_configurations(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    else:
        return {
            "global": {
                "Scope IP":        "mtc1.json not found !!!",
                "JBERT IP":        "mtc1.json not found !!!",
                "Switch IP":       "mtc1.json not found !!!",
                "Switch Map Path": "mtc1.json not found !!!",
                "6-Shot Host":     "mtc1.json not found !!!"
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
                    "eye_data_folder": r"eye\data\folder"
                },
                "8.1": {
                    "scope_preset_path": r"scope\path",
                    "jbert_preset_path": r"jbert\path",
                    "preset": 0
                }
            }
        }

def save_configurations(configurations, file_path):
    with open(file_path, 'w') as file:
        json.dump(configurations, file, indent=4)

class TaskGenerator():
    def __init__(self) -> None:
        self.corners = [
            "NOM",
            "LVHT",
            "LVLT",
            "HVLT",
            "HVHT"
            ]
        self.phy_s = ["tcss", "edp"]
        self.tests = {
            "tcss": [
                "ui_ssc_eye",
                "rise_fall_time",
                "jitter",
                "ac_common_mode",
                "transmitter_equalization",
                "electrical_idle_voltage"
                ],
            "edp": [
                "EHEW",
                "Jitters"
                ],
        }
        self.instances = {
            "tcss": [0, 1, 2, 3],
            "edp": [0],
        }
        self.lanes = {
            "tcss": [0, 1, 2, 3],
            "edp": [0, 1, 2, 3],
        }
        self.protocols = {
            "tcss": [
                "TBT20",
                "TBT20.6",
                "TBT10",
                "TBT10.3",
                "DP20"
                ],
            "edp": ["8.1"],
        }
    def TaskGenerator(self,setup_tasks):
            for corner in self.corners:
                for phy in self.phy_s:
                    for instance in self.instances[phy]:
                        for lane in self.lanes[phy]:
                            for protocol in self.protocols[phy]:
                                for test in self.tests[phy]:
                                    new_task = [corner, phy, instance, lane, protocol, test]
                                    setup_tasks.put(new_task)
            return setup_tasks
    
TG = TaskGenerator()

class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

        

    def show_tip(self, event=None):
        x, y, _cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))

        label = tk.Label(tw, text=self.widget.get(), justify=tk.LEFT, background="#ffffe0", relief=tk.SOLID,borderwidth=1, font=("consolas", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


class MainGUI:
    def __init__(self, root, task_queue, empty_task_list, configurations, config_file_path):
        self.root = root
        self.root.title("MTC1 | Main Debug")
        self.root.minsize(1000, 630)
        self.configurations = configurations
        self.config_file_path = config_file_path

        # Default Preferences
        self.vnc_viewer_path = r"C:\Program Files\RealVNC\VNC Viewer\vncviewer.exe"
        self.generated_from_list = False
        self.state = State()
        self.state.set("stopped")

        # Mutexes and Events
        self.tree_lock  = threading.Lock()
        self.pause_lock = threading.Lock()
        anti_lock_event.set()

        # Add Menu
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # Set the window icon
        self.root.iconbitmap("Images/MTC1_Logo.ico")

        # Call the on_closing method when the window is closed
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Load Images
        self.play_stop_buttons_paths_array = [r'Images\stop.png',r'Images\play.png']
        self.play_stop_buttons_array = []
        for path in self.play_stop_buttons_paths_array:
            image = Image.open(path)
            image = image.resize((25, 25), Image.LANCZOS)
            image = ImageTk.PhotoImage(image)
            self.play_stop_buttons_array.append(image)
        self.stop_image = self.play_stop_buttons_array[0]
        self.play_image = self.play_stop_buttons_array[1]


        # Add "Menu" to the menu bar
        self.menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu.add_command(label="Preferences", command=self.show_preferences)
        self.menu.add_separator()
        self.menu.add_command(label="Exit", command=self.on_closing)
        self.menu_bar.add_cascade(label="Menu", menu=self.menu)

        # Add "Help" to the menu bar
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="About", command=self.show_about)
        self.help_menu.add_command(label="Help", command=self.show_help)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)

        # Define top and bottom frames
        self.top_frame = tk.Frame(root)
        self.top_frame.pack(fill=tk.BOTH, expand=True)
        self.top_controls_frame = tk.Frame(self.top_frame)
        self.top_controls_frame.pack(fill=tk.BOTH,side='left',padx=5)
        self.top_trees_frame = tk.Frame(self.top_frame)
        self.top_trees_frame.pack(fill=tk.BOTH,expand=True)
        separator = ttk.Separator(root, orient='horizontal')
        separator.pack(fill=tk.X, padx=5, pady=5)
        self.bottom_frame = tk.Frame(root)
        self.bottom_frame.pack(fill=tk.X, anchor="s")
        #self.bottom_gp_frame = tk.Frame(self.bottom_frame)
        self.bottom_gp_frame = tk.LabelFrame(self.bottom_frame,text="Global Parameters")
        self.bottom_gp_frame.pack(padx=5, pady=5, anchor="w",side='left')
        self.bottom_credentials_frame = tk.LabelFrame(self.bottom_frame,text="Credentials")
        self.bottom_credentials_frame.pack(padx=5, pady=5, anchor="nw",side='left')

        # Build the top frame content

        # Define the columns (add 'finished_time' for finished jobs tree)
        self.columns = ('corner', 'phy', 'port', 'lane', 'protocol', 'test')
        self.finished_columns = ('finish time', 'corner', 'phy', 'port', 'lane', 'protocol', 'test')

        # Define top frames for job queue and finished jobs
        self.job_queue_frame = tk.LabelFrame(self.top_trees_frame, text="Job Queue")
        self.job_queue_frame.grid(row=0,column=0,sticky='nsew',padx=5)
        #self.job_queue_frame.pack(padx=5, pady=5,expand=True,fill=tk.BOTH)#,side=tk.LEFT, fill=tk.BOTH, expand=True, anchor="w")

        self.finished_jobs_frame = tk.LabelFrame(self.top_trees_frame, text="Finished Jobs")
        self.finished_jobs_frame.grid(row=0,column=1,sticky='nsew',padx=5)
        #self.finished_jobs_frame.pack(padx=5, pady=5,expand=True,fill=tk.BOTH)#,side=tk.LEFT, fill=tk.BOTH, expand=True, anchor="w")

        self.top_trees_frame.columnconfigure(0, weight=1)
        self.top_trees_frame.columnconfigure(1, weight=1)
        self.top_trees_frame.rowconfigure(0, weight=1)

        # Create the Job Queue Treeview
        self.job_queue_tree = ttk.Treeview(self.job_queue_frame, columns=self.columns, show="headings")
        for col in self.columns:
            self.job_queue_tree.heading(col, text=col.title())
            if col in ['corner','phy']:
                self.job_queue_tree.column(col, stretch=tk.NO, width=50,minwidth=50)
            elif col in ['protocol']:
                self.job_queue_tree.column(col, stretch=tk.NO, width=55,minwidth=55)
            elif col in ['lane','port']:
                self.job_queue_tree.column(col, stretch=tk.NO, width=35,minwidth=35)
            else:
                self.job_queue_tree.column(col, stretch=tk.YES, width=100)
        self.job_queue_scrollbar = ttk.Scrollbar(self.job_queue_frame, orient=tk.VERTICAL, command=self.job_queue_tree.yview)
        self.job_queue_scrollbar.pack(side=tk.RIGHT, fill='y')
        self.job_queue_tree.pack(fill=tk.BOTH, expand=True)
        self.job_queue_tree.configure(yscrollcommand=self.job_queue_scrollbar.set)

        # Create the Finished Jobs Treeview with the new column
        self.finished_jobs_tree = ttk.Treeview(self.finished_jobs_frame, columns=self.finished_columns, show="headings")
        for col in self.finished_columns:
            self.finished_jobs_tree.heading(col, text=col.title())
            if col == 'finish time':
                self.finished_jobs_tree.column(col, stretch=tk.NO, width=115,minwidth=115)
            elif col in ['corner','phy']:
                self.finished_jobs_tree.column(col, stretch=tk.NO, width=50,minwidth=50)
            elif col in ['protocol']:
                self.finished_jobs_tree.column(col, stretch=tk.NO, width=55,minwidth=55)
            elif col in ['lane','port']:
                self.finished_jobs_tree.column(col, stretch=tk.NO, width=35,minwidth=35)
            else:
                self.finished_jobs_tree.column(col, stretch=tk.YES, width=100)
        self.finished_jobs_scrollbar = ttk.Scrollbar(self.finished_jobs_frame, orient=tk.VERTICAL, command=self.finished_jobs_tree.yview)
        self.finished_jobs_scrollbar.pack(side=tk.RIGHT, fill='y')
        self.finished_jobs_tree.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.finished_jobs_tree.configure(yscrollcommand=self.finished_jobs_scrollbar.set)

        # Frame for indicators (boot indicator, equipment indicator, etc...)
        self.indicators_frame = tk.LabelFrame(self.top_controls_frame, text='Equipment Status', labelanchor='n')
        self.indicators_frame.pack(fill=tk.X, padx=0)
        self.indicators_frame.configure()

        # Create Indicators
        self.indicators_list = [
            'Board',
            'Intec',
            'Unit',
            'Switch',
            'Scope',
            'JBERT',
            'SixShot',
        ]
        self.indicator_sub_frame_dict = {}
        for indicator in self.indicators_list:
            ind_su_fr = tk.Frame(self.indicators_frame)
            ind_su_fr.pack(fill=tk.X, padx=5, pady=5)
            ind_ind = tk.Label(ind_su_fr, text='N/A', bg='grey', width=8, name="ind_ind", relief='sunken')
            ind_ind.pack(side=tk.RIGHT)
            ind_equip = tk.Label(ind_su_fr, text=indicator, name='ind_equip')
            ind_equip.pack(side=tk.LEFT)
            self.indicator_sub_frame_dict[indicator] = ind_su_fr
        threading.Thread(target=self.update_indicator, daemon=True).start()

        # Frame for controls (add/remove buttons)
        self.controls_frame = tk.Frame(self.top_controls_frame)
        self.controls_frame.pack(fill=tk.BOTH, padx=0, pady=0, expand=True)
        self.controls_frame.configure()

        # Add button
        self.add_button = tk.Button(self.controls_frame, text="Add Item", command=self.add_item, background="#e5f0e5")
        self.add_button.pack(fill=tk.X, pady=2)

        # Remove button
        self.remove_button = tk.Button(self.controls_frame, text="Remove Selected", command=self.remove_item, background="#f0e5e5")
        self.remove_button.pack(fill=tk.X, pady=2)

        # Remove all button
        self.remove_all_button = tk.Button(self.controls_frame, text="Remove All", command=self.remove_all, background="#f0e5e5")
        self.remove_all_button.pack(fill=tk.X, pady=2)

        # Generate list button
        self.generate_list_button = tk.Button(self.controls_frame, text="Generate List from Setup",command=self.generate_list)
        self.generate_list_button.pack(fill=tk.X, pady=2)

        # Seperator
        self.button_seperator = tk.Label(self.controls_frame, height=3)
        self.button_seperator.pack(fill=tk.X)

        # Play stop pause frame
        self.play_stop_pause_frame = tk.Frame(self.controls_frame)
        self.play_stop_pause_frame.pack(fill=tk.X, pady=0, side='bottom')

        # Configure the columns to expand
        self.play_stop_pause_frame.columnconfigure(0, weight=1)
        self.play_stop_pause_frame.columnconfigure(1, weight=1)

        # Stop button and indicator
        self.stop_button = tk.Button(self.play_stop_pause_frame, command=self.stop_tests, image=self.stop_image,state='disabled')
        self.stop_button.grid(row=0, column=0, sticky='ew', padx=3)

        self.stop_indicator = tk.Frame(self.play_stop_pause_frame, height=10, relief='sunken', bd=2,bg="red")
        self.stop_indicator.grid(row=1, column=0, sticky='ew', padx=2,pady=2)

        # Play button and indicator
        self.play_button = tk.Button(self.play_stop_pause_frame, command=self.run_tests_in_queue, image=self.play_image)
        self.play_button.grid(row=0, column=1, sticky='ew', padx=3)

        self.play_indicator = tk.Frame(self.play_stop_pause_frame, height=10, relief='sunken', bd=2,bg="grey")
        self.play_indicator.grid(row=1, column=1, sticky='ew', padx=2,pady=2)


        # Queue for tasks
        self.setup_queue = task_queue
        self.task_queue = Queue()

        if not empty_task_list:
            self.generate_list()

        # Build the bottom gp frame content
        for global_parameter in configurations['global']:
            gp_frame = tk.Frame(
                self.bottom_gp_frame,
                padx=5,
                #borderwidth=1,
                #relief='ridge',
                name=f"_{global_parameter}_frame")
            gp_frame.pack(fill=tk.X, pady=0)
            label = tk.Label(gp_frame, text=f'{global_parameter}:', anchor='w', width=15)
            label.pack(side=tk.LEFT)
            entry_var = tk.StringVar(value=configurations['global'][global_parameter])
            entry = tk.Entry(gp_frame, textvariable=entry_var, state='disabled', width=16,name=f"_{global_parameter}_entry")
            entry.pack(side=tk.LEFT)
            if global_parameter == 'Switch Map Path':
                ToolTip(entry)
            def toggle_edit(entry=entry, entry_var=entry_var, global_parameter=global_parameter):
                if global_parameter == 'Switch Map Path':
                    initial_dir = os.path.dirname(entry_var.get())
                    file_path = filedialog.askopenfilename(initialdir=initial_dir)
                    if file_path:
                        entry_var.set(file_path)
                else:
                    if entry['state'] == 'normal':
                        entry.config(state='disabled')
                        self.configurations['global'][global_parameter] = entry_var.get()
                        save_configurations(self.configurations, self.config_file_path)
                    else:
                        entry.config(state='normal')
            edit_button = tk.Button(gp_frame, text='Edit',
                                    command=lambda e=entry, ev=entry_var, gp=global_parameter: toggle_edit(e, ev, gp))
            edit_button.pack(side=tk.LEFT)
            def open_action(global_parameter=global_parameter, entry_var=entry_var):
                self.gp_open_function(global_parameter, entry_var.get())
            open_button = tk.Button(gp_frame, text='Open', command=open_action)
            open_button.pack(side=tk.LEFT)
        
        # add a little space in the gp_frame
        gp_space_frame = tk.Frame(self.bottom_gp_frame,height=5)
        gp_space_frame.pack()

        # Build the bottom Credentials frame content
        # Username frame
        username_frame = tk.Frame(
            self.bottom_credentials_frame,
            #borderwidth=1,
            #relief='ridge'
            )
        username_frame.pack(fill=tk.X, pady=0)
        username_label = tk.Label(username_frame, text="Username:")
        username_label.pack(side=tk.LEFT, padx=5)
        self.username_var = tk.StringVar()
        self.username_entry = tk.Entry(username_frame, textvariable=self.username_var)
        self.username_entry.pack(side=tk.RIGHT, padx=5)
        # Password frame
        password_frame = tk.Frame(
            self.bottom_credentials_frame,
            #borderwidth=1,
            #relief='ridge'
            )
        password_frame.pack(fill=tk.X, pady=0)
        password_label = tk.Label(password_frame, text="Password:")
        password_label.pack(side=tk.LEFT, padx=5)
        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(password_frame, textvariable=self.password_var, show="*")
        self.password_entry.pack(side=tk.RIGHT, padx=5)
        # Buttons frame
        buttons_frame = tk.Frame(self.bottom_credentials_frame)
        buttons_frame.pack(fill=tk.X, pady=5)
        self.commit_button = tk.Button(buttons_frame, text="Commit", command=self.commit_credentials,width=7)
        self.commit_button.pack(side=tk.LEFT, padx=5)
        self.clear_button = tk.Button(buttons_frame, text="Clear", command=self.clear_credentials)
        self.clear_button.pack(side=tk.LEFT, padx=0)

    def commit_credentials(self):
        if self.commit_button.cget("text") == "Commit":
            self.username_entry.config(state='disabled')
            self.password_entry.config(state='disabled')
            self.commit_button.config(text="Edit")
        else:
            self.username_entry.config(state='normal')
            self.password_entry.config(state='normal')
            self.commit_button.config(text="Commit")

    def clear_credentials(self):
        self.username_var.set("")
        self.password_var.set("")
        if self.commit_button.cget("text") == "Edit":
            self.username_entry.config(state='normal')
            self.password_entry.config(state='normal')
            self.commit_button.config(text="Commit")

    def show_preferences(self):

        y_pad = 2

        preferences_window = tk.Toplevel(self.root)
        preferences_window.title("Preferences")
        preferences_window.iconbitmap("Images/MTC1_Logo.ico")
        preferences_window.resizable(False, False)

        # Set the window position

        window_x = 10
        window_y = 10

        preferences_window.geometry(f"+{window_x}+{window_y}")


        # Create a notebook widget
        notebook = ttk.Notebook(preferences_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=y_pad)

        # Global preferences frame
        global_frame = tk.Frame(notebook)
        notebook.add(global_frame, text='Global')

        # VNC Viewer path frame
        vnc_frame = tk.Frame(global_frame)
        vnc_frame.pack(anchor='nw')


        # Label for VNC Viewer path
        vnc_label = tk.Label(vnc_frame, text="VNC Viewer Path:", anchor='w', width=20)
        vnc_label.pack(side=tk.LEFT, padx=5, pady=y_pad)

        # Entry for VNC Viewer path
        self.vnc_viewer_path_var = tk.StringVar(value=self.vnc_viewer_path)
        vnc_entry = tk.Entry(vnc_frame, textvariable=self.vnc_viewer_path_var, width=50, state='readonly')
        vnc_entry.pack(side=tk.LEFT, padx=5, pady=y_pad)

        # Button to change the VNC Viewer path
        def change_vnc_path():
            current_path = self.vnc_viewer_path_var.get()
            initial_dir = os.path.dirname(current_path) if current_path else '/'
            file_path = filedialog.askopenfilename(initialdir=initial_dir, filetypes=[("Executable files", "*.exe")])
            if file_path:
                self.vnc_viewer_path_var.set(file_path)
                vnc_entry.config(state='normal')
                vnc_entry.delete(0, tk.END)
                vnc_entry.insert(0, file_path)
                vnc_entry.config(state='readonly')
                self.vnc_viewer_path = file_path

        change_path_button = tk.Button(vnc_frame, text="Change Path", command=change_vnc_path)
        change_path_button.pack(side=tk.LEFT, padx=5, pady=y_pad)

        # TCSS LabelFrame
        tcss_frame = tk.Frame(notebook)
        notebook.add(tcss_frame, text='TCSS')

        # TCSS .bin files destination folder
        def edit_tcss_bin_folder():
            folder_path = filedialog.askdirectory(initialdir=self.configurations['tcss']['global']['bin_file_destination_folder'])
            if folder_path:
                self.tcss_bin_var.set(folder_path)
                self.configurations['tcss']['global']['bin_file_destination_folder'] = folder_path
                save_configurations(self.configurations, self.config_file_path)

        tcss_bin_frame = tk.Frame(tcss_frame)
        tcss_bin_frame.pack(fill="x")
        tcss_bin_label = tk.Label(tcss_bin_frame, text=".bin files destination folder:", anchor='w', width=20)
        tcss_bin_label.pack(side=tk.LEFT, padx=5, pady=y_pad)
        self.tcss_bin_var = tk.StringVar(value=self.configurations['tcss']['global']['bin_file_destination_folder'])
        tcss_bin_entry = tk.Entry(tcss_bin_frame, textvariable=self.tcss_bin_var, width=50, state='readonly')
        tcss_bin_entry.pack(side=tk.LEFT, padx=5, pady=y_pad)
        tcss_bin_button = tk.Button(tcss_bin_frame, text="Change Path", command=edit_tcss_bin_folder)
        tcss_bin_button.pack(side=tk.LEFT, padx=5, pady=y_pad)

        # TCSS SigTest results folder
        def edit_tcss_sigtest_folder():
            folder_path = filedialog.askdirectory(initialdir=self.configurations['tcss']['global']['sigtest_results_folder'])
            if folder_path:
                self.tcss_sigtest_var.set(folder_path)
                self.configurations['tcss']['global']['sigtest_results_folder'] = folder_path
                save_configurations(self.configurations, self.config_file_path)

        tcss_sigtest_frame = tk.Frame(tcss_frame)
        tcss_sigtest_frame.pack(fill="x")
        tcss_sigtest_label = tk.Label(tcss_sigtest_frame, text="SigTest results folder:", anchor='w', width=20)
        tcss_sigtest_label.pack(side=tk.LEFT, padx=5, pady=y_pad)
        self.tcss_sigtest_var = tk.StringVar(value=self.configurations['tcss']['global']['sigtest_results_folder'])
        tcss_sigtest_entry = tk.Entry(tcss_sigtest_frame, textvariable=self.tcss_sigtest_var, width=50, state='readonly')
        tcss_sigtest_entry.pack(side=tk.LEFT, padx=5, pady=y_pad)
        tcss_sigtest_button = tk.Button(tcss_sigtest_frame, text="Change Path", command=edit_tcss_sigtest_folder)
        tcss_sigtest_button.pack(side=tk.LEFT, padx=5, pady=y_pad)

        # Add USB4 Gen2, USB4 Gen3, and DP2.0 LabelFrames
        def create_protocol_frame(parent, protocol_name):
            protocol_frame = tk.LabelFrame(parent, text=protocol_name)
            protocol_frame.pack(fill=tk.X, padx=10, pady=y_pad)

            def create_test_frame(test_name):
                test_frame = tk.Frame(protocol_frame)
                test_frame.pack(fill="x")

                test_label = tk.Label(test_frame, text=f"{test_name} Scope setup path:", anchor='w', width=30)
                test_label.pack(side=tk.LEFT, padx=5, pady=y_pad)
                test_var = tk.StringVar(value=self.configurations['tcss'][protocol_name.lower()][test_name+" scope setup path"])
                test_entry = tk.Entry(test_frame, textvariable=test_var, width=50, state='readonly')
                test_entry.pack(side=tk.LEFT, padx=5, pady=y_pad)
                def edit_test_folder():
                    folder_path = filedialog.askdirectory(initialdir=test_var.get())
                    if folder_path:
                        test_var.set(folder_path)
                        self.configurations['tcss'][protocol_name.lower()][test_name+" scope setup path"] = folder_path
                        save_configurations(self.configurations, self.config_file_path)
                test_button = tk.Button(test_frame, text="Change Path", command=edit_test_folder)
                test_button.pack(side=tk.LEFT, padx=5, pady=y_pad)

                if test_name == 'jitter':
                    jbert_frame = tk.Frame(protocol_frame)
                    jbert_frame.pack(fill="x")
                    jbert_label = tk.Label(jbert_frame, text=f"{test_name} JBERT setup path:", anchor='w', width=30)
                    jbert_label.pack(side=tk.LEFT, padx=5, pady=y_pad)
                    jbert_var = tk.StringVar(value=self.configurations['tcss'][protocol_name.lower()][test_name+" jbert setup path"])
                    jbert_entry = tk.Entry(jbert_frame, textvariable=jbert_var, width=50, state='readonly')
                    jbert_entry.pack(side=tk.LEFT, padx=5, pady=y_pad)
                    def edit_jbert_folder():
                        folder_path = filedialog.askdirectory(initialdir=jbert_var.get())
                        if folder_path:
                            jbert_var.set(folder_path)
                            self.configurations['tcss'][protocol_name.lower()][test_name+" jbert setup path"] = folder_path
                            save_configurations(self.configurations, self.config_file_path)
                    jbert_button = tk.Button(jbert_frame, text="Change Path", command=edit_jbert_folder)
                    jbert_button.pack(side=tk.LEFT, padx=5, pady=y_pad)

            tests = TG.tests['tcss']
            for test in tests:
                create_test_frame(test)

        # Add the protocol frames
        create_protocol_frame(tcss_frame, "USB4 Gen2")
        create_protocol_frame(tcss_frame, "USB4 Gen3")
        create_protocol_frame(tcss_frame, "DP2.0")

        # eDP LabelFrame
        edp_frame = tk.Frame(notebook)
        notebook.add(edp_frame, text='eDP')

        # eDP Jitter data folder
        def edit_edp_jitter_folder():
            folder_path = filedialog.askdirectory(initialdir=self.configurations['edp']['global']['jitter_data_folder'])
            if folder_path:
                self.edp_jitter_var.set(folder_path)
                self.configurations['edp']['global']['jitter_data_folder'] = folder_path
                save_configurations(self.configurations, self.config_file_path)

        edp_jitter_frame = tk.Frame(edp_frame)
        edp_jitter_frame.pack(fill="x")
        edp_jitter_label = tk.Label(edp_jitter_frame, text="Jitter data folder:", anchor='w', width=20)
        edp_jitter_label.pack(side=tk.LEFT, padx=5, pady=y_pad)
        self.edp_jitter_var = tk.StringVar(value=self.configurations['edp']['global']['jitter_data_folder'])
        edp_jitter_entry = tk.Entry(edp_jitter_frame, textvariable=self.edp_jitter_var, width=50, state='readonly')
        edp_jitter_entry.pack(side=tk.LEFT, padx=5, pady=y_pad)
        edp_jitter_button = tk.Button(edp_jitter_frame, text="Change Path", command=edit_edp_jitter_folder)
        edp_jitter_button.pack(side=tk.LEFT, padx=5, pady=y_pad)

        # eDP EH EW data folder
        def edit_edp_ehew_folder():
            folder_path = filedialog.askdirectory(initialdir=self.configurations['edp']['global']['eye_data_folder'])
            if folder_path:
                self.edp_ehew_var.set(folder_path)
                self.configurations['edp']['global']['eye_data_folder'] = folder_path
                save_configurations(self.configurations, self.config_file_path)

        edp_ehew_frame = tk.Frame(edp_frame)
        edp_ehew_frame.pack(fill="x")
        edp_ehew_label = tk.Label(edp_ehew_frame, text="EH EW data folder:", anchor='w', width=20)
        edp_ehew_label.pack(side=tk.LEFT, padx=5, pady=y_pad)
        self.edp_ehew_var = tk.StringVar(value=self.configurations['edp']['global']['eye_data_folder'])
        edp_ehew_entry = tk.Entry(edp_ehew_frame, textvariable=self.edp_ehew_var, width=50, state='readonly')
        edp_ehew_entry.pack(side=tk.LEFT, padx=5, pady=y_pad)
        edp_ehew_button = tk.Button(edp_ehew_frame, text="Change Path", command=edit_edp_ehew_folder)
        edp_ehew_button.pack(side=tk.LEFT, padx=5, pady=y_pad)

        # Make the preferences window modal
        preferences_window.transient(self.root)
        preferences_window.grab_set()
        self.root.wait_window(preferences_window)

    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.iconbitmap("Images/MTC1_Logo.ico")
        about_window.title("About")
        about_window.minsize(280, 115)
        about_window.resizable(False, False)

        # Set the window position
        about_window.geometry(f"+{self.root.winfo_x() + 50}+{self.root.winfo_y() + 50}")

        # Load the image and resize it
        image_path = "Images/MTC1_Logo.png"  # Update with your image path
        img = Image.open(image_path)
        img = img.resize((50, 50), Image.LANCZOS)
        logo = ImageTk.PhotoImage(img)

        # Display the image
        image_label = tk.Label(about_window, image=logo)
        image_label.image = logo  # Keep a reference to avoid garbage collection
        image_label.pack(pady=5)

        # Display the text
        text = f"Multi Threading C1\nVersion {VERSION}\n© {YEAR} Sivan Zusin"
        text_label = tk.Label(about_window, text=text)
        text_label.pack()

    def show_help(self, topic=""):
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

        # Search for a .chm file in the directory
        chm_files = [f for f in os.listdir(script_dir) if f.endswith('.chm')]

        if chm_files:
            # If there are multiple .chm files, choose the first one
            chm_file = os.path.join(script_dir, chm_files[0])
            # Append the topic to the CHM file path if specified
            if topic:
                chm_path_with_topic = f"mk:@MSITStore:{chm_file}::{topic}"
            else:
                chm_path_with_topic = chm_file
            # Open the CHM file using the default CHM viewer
            subprocess.Popen(["hh.exe", chm_path_with_topic])
        else:
            messagebox.showerror("Error", "Help file not found!")

    def gp_open_function(self, gp, path):
        if gp in ['Scope IP', 'JBERT IP', '6-Shot Host']:

            print(self.vnc_viewer_path, path)
            try:
                subprocess.run([self.vnc_viewer_path, path], check=True)
                print("VNC Viewer launched successfully.")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Failed to launch VNC Viewer: {e}")
            except FileNotFoundError:
                messagebox.showerror("Error", "The specified VNC Viewer executable path does not exist.\nSpecify the correct VNC Viewer in `Menu -> Preferences` or install it.")
        elif gp == 'Switch IP':
            url = f"http://{path}"
            try:
                subprocess.run(['start', url], check=True, shell=True)
                print(f"Opened web browser to {url} successfully.")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Failed to open web browser: {e}")
        elif gp == 'Switch Map Path':
            try:
                os.startfile(path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")

    def update_indicator(self):
        color_c1 = {
            'red': '#ff0000',
            'green': '#00ff00',
            'yellow': 'yellow',
            'grey': 'grey'
        }
        global change_indicator_event
        global indicators_status_dict
        global indicators_status
        while True:
            change_indicator_event.wait()
            for indicator_name in self.indicators_list:
                self.indicator_sub_frame_dict[indicator_name].children['ind_ind'].configure(
                    bg=color_c1[indicators_status_dict[indicator_name][indicators_status[indicator_name]]],
                    text=indicators_status[indicator_name])
            change_indicator_event.clear()

    def configure_play_stop_indicators(self,indicator):
        self.play_indicator.config(bg='grey')
        self.stop_indicator.config(bg='grey')
        self.play_button.config(state='disabled')
        self.stop_button.config(state='disabled')
        if indicator == 'play':
            self.play_indicator.config(bg='#00ff00')
            self.stop_button.config(state='normal')
            self.generate_list_button.configure(state='disabled')
        elif indicator == 'stop':
            self.stop_indicator.config(bg='red')
            self.play_button.config(state='normal')
            self.generate_list_button.configure(state='normal')

    def stop_tests(self):
        pass

    def run_tests_in_queue(self):
        pass


    def add_item(self):
        pass

    def remove_item(self):
        pass

    def remove_all(self):
        pass

    def generate_list(self):
        if self.job_queue_tree.get_children():
            self.warn_before_removing_all_jobs("generating new list")
        tmp = Queue()
        while not self.setup_queue.empty():
            values = self.setup_queue.get()
            tmp.put(values)
            if len(values) == len(self.columns):  # Check if the entered values match the number of columns
                self.job_queue_tree.insert('', tk.END, values=values)
        while not tmp.empty():
            task = tmp.get()
            self.task_queue.put(task)
            self.setup_queue.put(task)

    def board_thread_function(self):
        print("Board Thread running")

    def intec_thread_function(self):
        print("Intec Thread running")

    def unit_thread_function(self):
        print("Unit Thread running")

    def switch_thread_function(self):
        print("Switch Thread running")

    def scope_thread_function(self):
        print("Scope Thread running")

    def jbert_thread_function(self):
        print("Jbert Thread running")

    def sixshot_thread_function(self):
        print("SixShot Thread running")
    
    def data_transfer_function(self,src,dst):
        print(f"Transferring data from {src} to {dst}")

    def on_closing(self):
        save_configurations(self.configurations, self.config_file_path)
        self.root.destroy()
        exit()


class MainClass():
    def __init__(self, empty_task_list=True) -> None:
        self.empty_task_list = empty_task_list
        self.task_queue = Queue()
        self.config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mtc1.json')
        self.configurations = load_configurations(self.config_file_path)
        self.DoTechnicals()

    def DoTechnicals(self):
        self.setup_tasks = Queue()
        self.setup_tasks = TG.TaskGenerator(self.setup_tasks)
        #self.RunGUI_in_new_Thread()
        self.init_gui()

    def RunGUI_in_new_Thread(self):
        # Create a new thread targeting the function that initializes and runs the GUI.
        threading.Thread(target=self.init_gui).start()

    def init_gui(self):
        root = tk.Tk()
        self.app = MainGUI(root, self.setup_tasks, self.empty_task_list, self.configurations, self.config_file_path)
        root.mainloop()


if __name__ == "__main__":
    a = MainClass(True)
    # indicators_status["Board"] = 'Ready'
    # indicators_status['Intec'] = 'Busy'
    # indicators_status['Switch'] = 'Error'
    # change_indicator_event.set()
