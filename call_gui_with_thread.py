import threading,sys,os
import tkinter as tk
# Get the current working directory
cwd = os.getcwd()

# Append the current working directory to sys.path
if cwd not in sys.path:
    sys.path.append(cwd)
from GUI import SimpleGUI  # Assuming your Tkinter class is saved as simple_gui.py

def run_gui():
    root = tk.Tk()
    app = SimpleGUI(root)
    root.mainloop()

if __name__ == "__main__":
    gui_thread = threading.Thread(target=run_gui, daemon=True)
    gui_thread.start()
    
    # The following lines are just an example to show that the rest of your application can run 
    # while the GUI is open. Replace this with the rest of your application.
    try:
        print("SAdasd")
        input()
    except KeyboardInterrupt:
        print("Application closed.")