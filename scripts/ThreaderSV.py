from queue import Queue
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



# GLOBALS
VERSION = 0.1
YEAR = datetime.datetime.now().year
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


# global functions
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
        self.root.minsize(800, 615)
        self.configurations = configurations
        self.config_file_path = config_file_path

        # Default Preferences
        self.vnc_viewer_path = r"C:\Program Files\RealVNC\VNC Viewer\vncviewer.exe"
        self.generated_from_list = False

        # Add Menu
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # Set the window icon
        self.root.iconbitmap("MTC1_Logo.ico")

        # Call the on_closing method when the window is closed
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

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
        separator = ttk.Separator(root, orient='horizontal')
        separator.pack(fill=tk.X, padx=5, pady=10)
        self.bottom_frame = tk.Frame(root)
        self.bottom_frame.pack(fill=tk.X, anchor="s")
        #self.bottom_gp_frame = tk.Frame(self.bottom_frame)
        self.bottom_gp_frame = tk.LabelFrame(self.bottom_frame,text="Global Parameters")
        self.bottom_gp_frame.pack(padx=5, pady=5, anchor="w",side='left')
        self.bottom_credentials_frame = tk.LabelFrame(self.bottom_frame,text="Credentials")
        self.bottom_credentials_frame.pack(padx=5, pady=5, anchor="nw",side='left')

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
        self.indicators_frame = tk.LabelFrame(self.top_frame, text='Equipment Status', labelanchor='n')
        self.indicators_frame.pack(fill=tk.X, padx=5, pady=5)
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
        self.controls_frame = tk.Frame(self.top_frame)
        self.controls_frame.pack(fill=tk.BOTH, padx=5, pady=0, expand=True)
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

        # Run Tests In Queue
        self.run_tests_in_queue_button = tk.Button(self.controls_frame, text="Run Tests In Queue",command=self.run_tests_in_queue)
        self.run_tests_in_queue_button.pack(fill=tk.X, pady=0, side='bottom')

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
        preferences_window.iconbitmap("MTC1_Logo.ico")
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
        about_window.iconbitmap("MTC1_Logo.ico")
        about_window.title("About")
        about_window.minsize(280, 115)
        about_window.resizable(False, False)

        # Set the window position
        about_window.geometry(f"+{self.root.winfo_x() + 50}+{self.root.winfo_y() + 50}")

        # Load the image and resize it
        image_path = "MTC1_Logo.png"  # Update with your image path
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

    def run_tests_in_queue(self):
        print("Tests in the queue:")
        while not self.task_queue.empty():
            test = self.task_queue.get()
            print(test)
        
        # Start 7 threads
        threads = [
            threading.Thread(target=self.board_thread_function),
            threading.Thread(target=self.intec_thread_function),
            threading.Thread(target=self.unit_thread_function),
            threading.Thread(target=self.switch_thread_function),
            threading.Thread(target=self.scope_thread_function),
            threading.Thread(target=self.jbert_thread_function),
            threading.Thread(target=self.sixshot_thread_function),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    def add_item(self):
        """Function to add a new item to the treeview using a custom input frame."""

        def update_submit_button():
            if (any(var['value'].get() for var in tcss_ports_checkbox_vars + tcss_lanes_checkbox_vars + 
                    tcss_protocols_checkbox_vars + tcss_tests_checkbox_vars) or
                any(var['value'].get() for var in edp_lanes_checkbox_vars + edp_protocols_checkbox_vars + 
                    edp_tests_checkbox_vars)):
                submit_button.config(state='normal')
            else:
                submit_button.config(state='disabled')

        def highlight_frame(frame, highlight=True):
            if highlight:
                frame.configure(fg="red")
            else:
                frame.configure(fg="black")

        def on_submit():
            tcss_condition = (any(var['value'].get() for var in Corners_checkbox_vars) and
                            any(var['value'].get() for var in tcss_ports_checkbox_vars) and
                            any(var['value'].get() for var in tcss_lanes_checkbox_vars) and
                            any(var['value'].get() for var in tcss_protocols_checkbox_vars) and
                            any(var['value'].get() for var in tcss_tests_checkbox_vars))

            edp_condition = (any(var['value'].get() for var in Corners_checkbox_vars) and
                            any(var['value'].get() for var in edp_lanes_checkbox_vars) and
                            any(var['value'].get() for var in edp_protocols_checkbox_vars) and
                            any(var['value'].get() for var in edp_tests_checkbox_vars))

            if tcss_condition or edp_condition:
                # Proceed with adding items
                tests = []
                corners = [val['text'] for val in Corners_checkbox_vars if val['value'].get() == 1]
                tcss_ports = [val['text'] for val in tcss_ports_checkbox_vars if val['value'].get() == 1]
                tcss_lanes = [val['text'] for val in tcss_lanes_checkbox_vars if val['value'].get() == 1]
                tcss_protocols = [val['text'] for val in tcss_protocols_checkbox_vars if val['value'].get() == 1]
                tcss_tests = [val['text'] for val in tcss_tests_checkbox_vars if val['value'].get() == 1]
                edp_lanes = [val['text'] for val in edp_lanes_checkbox_vars if val['value'].get() == 1]
                edp_protocols = [val['text'] for val in edp_protocols_checkbox_vars if val['value'].get() == 1]
                edp_tests = [val['text'] for val in edp_tests_checkbox_vars if val['value'].get() == 1]

                for corner in corners:
                    for port in tcss_ports:
                        for lane in tcss_lanes:
                            for protocol in tcss_protocols:
                                for test in tcss_tests:
                                    tests.append([corner, 'TCSS', port, lane, protocol, test])
                for corner in corners:
                    for lane in edp_lanes:
                        for protocol in edp_protocols:
                            for test in edp_tests:
                                tests.append([corner, 'eDP', 0, lane, protocol, test])
                for test in tests:
                    self.tree.insert('', 'end', values=test)
                    self.task_queue.put(test)
                input_window.destroy()
            else:
                # Highlight frames with missing checkboxes
                highlight_frame(corners_frame, not any(var['value'].get() for var in Corners_checkbox_vars))
                
                tcss_active = any(var['value'].get() for var in tcss_ports_checkbox_vars + tcss_lanes_checkbox_vars + 
                                tcss_protocols_checkbox_vars + tcss_tests_checkbox_vars)
                if tcss_active:
                    highlight_frame(tcss_ports_frame, not any(var['value'].get() for var in tcss_ports_checkbox_vars))
                    highlight_frame(tcss_lanes_frame, not any(var['value'].get() for var in tcss_lanes_checkbox_vars))
                    highlight_frame(tcss_protocols_frame, not any(var['value'].get() for var in tcss_protocols_checkbox_vars))
                    highlight_frame(tcss_tests_frame, not any(var['value'].get() for var in tcss_tests_checkbox_vars))
                else:
                    highlight_frame(tcss_frame, False)
                
                edp_active = any(var['value'].get() for var in edp_lanes_checkbox_vars + edp_protocols_checkbox_vars + 
                                edp_tests_checkbox_vars)
                if edp_active:
                    highlight_frame(edp_lanes_frame, not any(var['value'].get() for var in edp_lanes_checkbox_vars))
                    highlight_frame(edp_protocols_frame, not any(var['value'].get() for var in edp_protocols_checkbox_vars))
                    highlight_frame(edp_tests_frame, not any(var['value'].get() for var in edp_tests_checkbox_vars))
                else:
                    highlight_frame(edp_frame, False)

        input_window = tk.Toplevel(self.root)
        input_window.title("Input")
        input_window.iconbitmap("MTC1_Logo.ico")
        input_window.resizable(False, False)

        # Set the window position
        input_window.geometry(f"+{self.root.winfo_x() + 50}+{self.root.winfo_y() + 50}")

        # Make the input window modal
        input_window.transient(self.root)
        input_window.grab_set()

        top_frame = tk.Frame(input_window)
        bottom_frame = tk.Frame(input_window)
        top_frame.pack()
        bottom_frame.pack()

        # Corners Checkboxes
        corners_frame = tk.LabelFrame(top_frame, text="Corners")
        corners_frame.pack(fill='both', padx=5, pady=5, side="left")
        Corners_checkbox_texts = TG.corners
        Corners_checkbox_vars = []
        for text in Corners_checkbox_texts:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(corners_frame, text=text, variable=var, command=update_submit_button)
            checkbox.pack(anchor='w')
            Corners_checkbox_vars.append({'value': var, 'text': text})

        # TCSS frame
        tcss_frame = tk.LabelFrame(top_frame, text="TCSS")
        tcss_frame.pack(fill='both', padx=5, pady=5, side='left')

        # TCSS ports
        tcss_ports_frame = tk.LabelFrame(tcss_frame, text="Ports")
        tcss_ports_frame.pack(fill='both', padx=5, pady=5, side='left')
        tcss_ports_checkbox_texts = TG.instances["tcss"]
        tcss_ports_checkbox_vars = []
        for text in tcss_ports_checkbox_texts:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(tcss_ports_frame, text=text, variable=var, command=update_submit_button)
            checkbox.pack(anchor='w')
            tcss_ports_checkbox_vars.append({'value': var, 'text': text})

        # TCSS lanes
        tcss_lanes_frame = tk.LabelFrame(tcss_frame, text="Lanes")
        tcss_lanes_frame.pack(fill='both', padx=5, pady=5, side="left")
        tcss_lanes_checkbox_texts = TG.lanes['tcss']
        tcss_lanes_checkbox_vars = []
        for text in tcss_lanes_checkbox_texts:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(tcss_lanes_frame, text=text, variable=var, command=update_submit_button)
            checkbox.pack(anchor='w')
            tcss_lanes_checkbox_vars.append({'value': var, 'text': text})

        # TCSS protocols
        tcss_protocols_frame = tk.LabelFrame(tcss_frame, text="Protocols")
        tcss_protocols_frame.pack(fill='both', padx=5, pady=5, side="left")
        tcss_protocols_checkbox_texts = TG.protocols["tcss"]
        tcss_protocols_checkbox_vars = []
        for text in tcss_protocols_checkbox_texts:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(tcss_protocols_frame, text=text, variable=var, command=update_submit_button)
            checkbox.pack(anchor='w')
            tcss_protocols_checkbox_vars.append({'value': var, 'text': text})

        # TCSS tests
        tcss_tests_frame = tk.LabelFrame(tcss_frame, text="Tests")
        tcss_tests_frame.pack(fill='both', padx=5, pady=5, side="left")
        tcss_tests_checkbox_texts = TG.tests['tcss']
        tcss_tests_checkbox_vars = []
        for text in tcss_tests_checkbox_texts:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(tcss_tests_frame, text=text, variable=var, command=update_submit_button)
            checkbox.pack(anchor='w')
            tcss_tests_checkbox_vars.append({'value': var, 'text': text})

        # eDP frame
        edp_frame = tk.LabelFrame(top_frame, text="eDP")
        edp_frame.pack(fill='both', padx=5, pady=5, side='left')

        # eDP lanes
        edp_lanes_frame = tk.LabelFrame(edp_frame, text="Lanes")
        edp_lanes_frame.pack(fill='both', padx=5, pady=5, side="left")
        edp_lanes_checkbox_texts = TG.lanes['edp']
        edp_lanes_checkbox_vars = []
        for text in edp_lanes_checkbox_texts:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(edp_lanes_frame, text=text, variable=var, command=update_submit_button)
            checkbox.pack(anchor='w')
            edp_lanes_checkbox_vars.append({'value': var, 'text': text})

        # eDP protocols
        edp_protocols_frame = tk.LabelFrame(edp_frame, text="Protocols")
        edp_protocols_frame.pack(fill='both', padx=5, pady=5, side="left")
        edp_protocols_checkbox_texts = TG.protocols['edp']
        edp_protocols_checkbox_vars = []
        for text in edp_protocols_checkbox_texts:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(edp_protocols_frame, text=text, variable=var, command=update_submit_button)
            checkbox.pack(anchor='w')
            edp_protocols_checkbox_vars.append({'value': var, 'text': text})

        # eDP tests
        edp_tests_frame = tk.LabelFrame(edp_frame, text="Tests")
        edp_tests_frame.pack(fill='both', padx=5, pady=5, side="left")
        edp_tests_checkbox_texts = TG.tests['edp']
        edp_tests_checkbox_vars = []
        for text in edp_tests_checkbox_texts:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(edp_tests_frame, text=text, variable=var, command=update_submit_button)
            checkbox.pack(anchor='w')
            edp_tests_checkbox_vars.append({'value': var, 'text': text})

        # Submit button
        submit_button = tk.Button(bottom_frame, text="Submit", command=on_submit, state='disabled')
        submit_button.pack(padx=10, pady=10, side='right')

        # Cancel Button
        cancel_button = tk.Button(bottom_frame, text="Cancel", command=input_window.destroy)
        cancel_button.pack(padx=10, pady=10, side='right')

        # Wait for the input window to be closed before returning to the main window
        self.root.wait_window(input_window)

    def remove_item(self):
        """Function to remove the selected item from the treeview."""
        selected_items = self.tree.selection()  # Returns a list of selected items
        for selected_item in selected_items:
            self.tree.delete(selected_item)

    def remove_all(self):
        self.warn_before_removing_all_jobs("remove all pressed")

    def warn_before_removing_all_jobs(self, cause):
        response = messagebox.askyesno("Warning", "This action will remove all current jobs.\nDo you want to proceed?")
        if response:
            if cause == "generating new list":
                self.generated_from_list = True
            self.remove_all_jobs()

    def remove_all_jobs(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.task_queue.queue.clear()
        self.generated_from_list = False

    def generate_list(self):
        if self.tree.get_children():
            self.warn_before_removing_all_jobs("generating new list")
        tmp = Queue()
        while not self.setup_queue.empty():
            values = self.setup_queue.get()
            tmp.put(values)
            if len(values) == len(self.columns):  # Check if the entered values match the number of columns
                self.tree.insert('', tk.END, values=values)
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
        self.RunGUI_in_new_Thread()

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
