import threading
import tkinter as tk
from tkinter import ttk
from queue import Queue
import time

# Define the thread task
def thread_task(duration, gui_queue):
    time.sleep(duration)
    gui_queue.put(f"Thread with {duration} seconds finished")

# GUI application
class ThreadStatusGUI:
    def __init__(self, master):
        self.master = master
        master.title("Thread Status")
        
        self.label = ttk.Label(master, text="Thread Completion Status")
        self.label.pack()

        self.text_area = tk.Text(master, height=10, width=50)
        self.text_area.pack()

        self.queue = Queue()
        self.update_me()

    def update_me(self):
        while not self.queue.empty():
            message = self.queue.get()
            self.text_area.insert(tk.END, message + "\n")
        self.master.after(100, self.update_me)

def main():
    root = tk.Tk()
    gui = ThreadStatusGUI(root)

    # Creating threads
    durations = [5, 6, 7, 8, 9]
    threads = [threading.Thread(target=thread_task, args=(d, gui.queue)) for d in durations]

    # Starting threads
    for thread in threads:
        thread.start()

    root.mainloop()

    # Join threads to ensure they've finished before exiting the main program
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
