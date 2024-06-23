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


# GLOBALS
VERSION = 0.1
YEAR = datetime.datetime.now().year
setup_queue = Queue()
task_queue = Queue()
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
                "Scope IP": "HA03ESIO0004",
                "JBERT IP": "7.7.7.7",
                "Switch IP": "1.10.5.59",
                "Switch Map Path": r"T:\ATD_IO\LNL\PCIe5\LNL_6shot_Tx_Switch_Map.csv",
                "6-Shot Host": r"ha03hfst0021"
            }
        }


def save_configurations(configurations, file_path):
    with open(file_path, 'w') as file:
        json.dump(configurations, file, indent=4)


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

        label = tk.Label(tw, text=self.widget.get(), justify=tk.LEFT, background="#ffffe0", relief=tk.SOLID,
                         borderwidth=1, font=("consolas", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


class MainGUI:
    def __init__(self, root, setup_queue, empty_task_list, configurations, config_file_path):
        self.root = root
        self.root.title("MTC1 | Main Debug")
        self.root.minsize(800, 615)
        self.configurations = configurations
        self.config_file_path = config_file_path

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
        self.menu.add_command(label="Exit", command=self.root.quit)
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
        self.bottom_left_frame = tk.Frame(self.bottom_frame)
        self.bottom_left_frame.pack(padx=5, pady=5, anchor="w")

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
        self.add_button = tk.Button(self.controls_frame, text="Add Item", command=self.add_item)
        self.add_button.pack(fill=tk.X, pady=2)

        # Remove button
        self.remove_button = tk.Button(self.controls_frame, text="Remove Selected", command=self.remove_item)
        self.remove_button.pack(fill=tk.X, pady=2)

        # Remove all button
        self.remove_all_button = tk.Button(self.controls_frame, text="Remove All", command=self.remove_all)
        self.remove_all_button.pack(fill=tk.X, pady=2)

        # Generate list button
        self.generate_list_button = tk.Button(self.controls_frame, text="Generate List from Setup",
                                              command=self.generate_list)
        self.generate_list_button.pack(fill=tk.X, pady=2)

        # Seperator
        self.button_seperator = tk.Label(self.controls_frame, height=3)
        self.button_seperator.pack(fill=tk.X)

        # Run Tests In Queue
        self.run_tests_in_queue_button = tk.Button(self.controls_frame, text="Run Tests In Queue",
                                                   command=self.run_tests_in_queue)
        self.run_tests_in_queue_button.pack(fill=tk.X, pady=0, side='bottom')

        # Queue for tasks
        self.setup_queue = setup_queue
        self.task_queue = Queue()

        if not empty_task_list:
            self.generate_list()

        # Build the bottom frame content
        for global_parameter in configurations['global']:
            gp_frame = tk.Frame(self.bottom_left_frame, borderwidth=1, relief='ridge', name=f"_{global_parameter}_frame")
            gp_frame.pack(fill=tk.X, pady=0)

            label = tk.Label(gp_frame, text=f'{global_parameter}:', anchor='w', width=15)
            label.pack(side=tk.LEFT)

            entry_var = tk.StringVar(value=configurations['global'][global_parameter])
            entry = tk.Entry(gp_frame, textvariable=entry_var, state='disabled', width=16,
                             name=f"_{global_parameter}_entry")
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

        # Default Preferences
        self.vnc_viewer_path = r"C:\Program Files\RealVNC\VNC Viewer\vncviewer.exe"

    def show_preferences(self):
        preferences_window = tk.Toplevel(self.root)
        preferences_window.title("Preferences")
        preferences_window.iconbitmap("MTC1_Logo.ico")
        preferences_window.resizable(False, False)

        # VNC Viewer path frame
        vnc_frame = tk.Frame(preferences_window, borderwidth=1, relief='ridge')
        vnc_frame.pack(fill=tk.X, padx=10, pady=10)

        # Label for VNC Viewer path
        vnc_label = tk.Label(vnc_frame, text="VNC Viewer Path:", anchor='w', width=20)
        vnc_label.pack(side=tk.LEFT, padx=5, pady=5)

        # Entry for VNC Viewer path
        self.vnc_viewer_path_var = tk.StringVar(value=self.vnc_viewer_path)
        vnc_entry = tk.Entry(vnc_frame, textvariable=self.vnc_viewer_path_var, width=50, state='readonly')
        vnc_entry.pack(side=tk.LEFT, padx=5, pady=5)

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
        change_path_button.pack(side=tk.LEFT, padx=5, pady=5)

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
                messagebox.showerror("Error", "The specified VNC Viewer executable path does not exist.")
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
        print("WIP!")

    def add_item(self):
        """Function to add a new item to the treeview using a custom input frame."""

        def on_submit():
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

        input_window = tk.Toplevel(self.root)
        input_window.title("Input")
        top_frame = tk.Frame(input_window)
        bottom_frame = tk.Frame(input_window)
        top_frame.pack()
        bottom_frame.pack()

        # Corners Checkboxes
        corners_frame = tk.LabelFrame(top_frame, text="Corners")
        corners_frame.pack(fill='both', padx=5, pady=5, side="left")
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
            Corners_checkbox_vars.append({'value': var, 'text': text})

        # tcss
        tcss_frame = tk.LabelFrame(top_frame, text="TCSS")
        tcss_frame.pack(fill='both', padx=5, pady=5, side='left')
        # tcss ports
        tcss_ports_frame = tk.LabelFrame(tcss_frame, text="Ports")
        tcss_ports_frame.pack(fill='both', padx=5, pady=5, side='left')
        tcss_ports_checkbox_texts = ["0", "1", "2"]
        tcss_ports_checkbox_vars = []
        for text in tcss_ports_checkbox_texts:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(tcss_ports_frame, text=text, variable=var)
            checkbox.pack(anchor='w')
            tcss_ports_checkbox_vars.append({'value': var, 'text': text})
        # tcss lanes
        tcss_lanes_frame = tk.LabelFrame(tcss_frame, text="Lanes")
        tcss_lanes_frame.pack(fill='both', padx=5, pady=5, side="left")
        tcss_lanes_checkbox_texts = ["0", "1", "2", "3"]
        tcss_lanes_checkbox_vars = []
        for text in tcss_lanes_checkbox_texts:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(tcss_lanes_frame, text=text, variable=var)
            checkbox.pack(anchor='w')
            tcss_lanes_checkbox_vars.append({'value': var, 'text': text})
        # tcss protocols
        tcss_protocols_frame = tk.LabelFrame(tcss_frame, text="Protocols")
        tcss_protocols_frame.pack(fill='both', padx=5, pady=5, side="left")
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
            tcss_protocols_checkbox_vars.append({'value': var, 'text': text})
        # tcss tests
        tcss_tests_frame = tk.LabelFrame(tcss_frame, text="Tests")
        tcss_tests_frame.pack(fill='both', padx=5, pady=5, side="left")
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
            tcss_tests_checkbox_vars.append({'value': var, 'text': text})

        # edp
        edp_frame = tk.LabelFrame(top_frame, text="eDP")
        edp_frame.pack(fill='both', padx=5, pady=5, side='left')
        # edp lanes
        edp_lanes_frame = tk.LabelFrame(edp_frame, text="Lanes")
        edp_lanes_frame.pack(fill='both', padx=5, pady=5, side="left")
        edp_lanes_checkbox_texts = ["0", "1", "2", "3"]
        edp_lanes_checkbox_vars = []
        for text in edp_lanes_checkbox_texts:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(edp_lanes_frame, text=text, variable=var)
            checkbox.pack(anchor='w')
            edp_lanes_checkbox_vars.append({'value': var, 'text': text})
        # edp protocols
        edp_protocols_frame = tk.LabelFrame(edp_frame, text="Protocols")
        edp_protocols_frame.pack(fill='both', padx=5, pady=5, side="left")
        edp_protocols_checkbox_texts = [
            '8.1'
        ]
        edp_protocols_checkbox_vars = []
        for text in edp_protocols_checkbox_texts:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(edp_protocols_frame, text=text, variable=var)
            checkbox.pack(anchor='w')
            edp_protocols_checkbox_vars.append({'value': var, 'text': text})
        # edp tests
        edp_tests_frame = tk.LabelFrame(edp_frame, text="Tests")
        edp_tests_frame.pack(fill='both', padx=5, pady=5, side="left")
        edp_tests_checkbox_texts = ["EHEW", "Jitters"]
        edp_tests_checkbox_vars = []
        for text in edp_tests_checkbox_texts:
            var = tk.IntVar()
            checkbox = tk.Checkbutton(edp_tests_frame, text=text, variable=var)
            checkbox.pack(anchor='w')
            edp_tests_checkbox_vars.append({'value': var, 'text': text})

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

    def on_closing(self):
        save_configurations(self.configurations, self.config_file_path)
        self.root.destroy()


class MainClass():
    def __init__(self, empty_task_list=False) -> None:
        self.empty_task_list = empty_task_list
        self.task_queue = Queue()
        self.config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mtc1.json')
        self.configurations = self.load_configurations(self.config_file_path)
        self.DoTechnicals()

    def load_configurations(self, file_path):
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                return json.load(file)
        else:
            # Return default configurations if the file doesn't exist
            print("Problem loading configuration file !!!")
            return {
                "global": {
                    "Scope IP": "HA03ESIO0004",
                    "JBERT IP": "7.7.7.7",
                    "Switch IP": "1.10.5.59",
                    "Switch Map Path": r"T:\ATD_IO\LNL\PCIe5\LNL_6shot_Tx_Switch_Map.csv",
                    "6-Shot Host": r"ha03hfst0021"
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
            "tcss": [0, 1, 2],
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
        self.app = MainGUI(root, self.setup_tasks, self.empty_task_list, self.configurations, self.config_file_path)
        root.mainloop()


if __name__ == "__main__":
    a = MainClass(True)
    # indicators_status["Board"] = 'Ready'
    # indicators_status['Intec'] = 'Busy'
    # indicators_status['Switch'] = 'Error'
    # change_indicator_event.set()
