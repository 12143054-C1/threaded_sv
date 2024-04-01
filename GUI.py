'''
This module is a test environment for GUI development
'''

import tkinter as tk

class SimpleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Tkinter GUI in a Thread")
        self.initialize_gui_elements()
        
    def initialize_gui_elements(self):
        self.label = tk.Label(self.root, text="Hello, Tkinter!")
        self.label.pack()
