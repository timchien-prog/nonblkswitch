# main.py
import tkinter as tk
from GUI import OpticalSwitchGUI

if __name__ == "__main__":
    # Create the root window
    root = tk.Tk()
    
    # Initialize the Application
    app = OpticalSwitchGUI(root)
    
    # Start the event loop
    root.mainloop()