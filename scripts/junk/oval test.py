import tkinter as tk
import time

arr = [5, 6, 7, 8, 3, 2, 4, 9]  # Set the list of numbers


def start_indicators():
    """
    This function updates the widgets based on your list
    :return: None
    """

    for x in arr:  # Iterate through the list.
        label_text = "Current value: {}".format(x)  # Set the text of Label
        if x < 3:
            print("Value: {} - Danger!".format(x))
            my_canvas.itemconfig(my_oval, fill="red")  # Fill the circle with RED
            label_var.set(label_text)  # Updating the label
        elif 3 < x < 7:
            print("Value: {} - Warning!".format(x))
            my_canvas.itemconfig(my_oval, fill="yellow")  # Fill the circle with YELLOW
            label_var.set(label_text)  # Updating the label
        elif x > 7:
            print("Value: {} - Safe!".format(x))
            my_canvas.itemconfig(my_oval, fill="green")  # Fill the circle with GREED
            label_var.set(label_text)  # Updating the label
        root.update()  # Update the complete GUI.
        time.sleep(2)  # Sleep two secs
    print("FINISH")


root = tk.Tk()  # Set Tk instance

my_canvas = tk.Canvas(root, width=200, height=200)  # Create 200x200 Canvas widget
my_canvas.pack()

my_oval = my_canvas.create_oval(50, 50, 100, 100)  # Create a circle on the Canvas

label_var = tk.StringVar()  # Set the string variable for Label widget

my_label = tk.Label(root, textvariable=label_var)  # Set the LAbel widget
my_label.pack()

my_button = tk.Button(root, text="START", command=start_indicators)  # Set a "Start button". The "start_indicators" function is a call-back.
my_button.pack()

root.mainloop()