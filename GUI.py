# gui.py
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog
from Simulation import SimulationEngine

class OpticalSwitchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Photonic Switch Builder")
        self.root.geometry("1200x800")
        
        # Instantiate the backend engine
        self.engine = SimulationEngine()
        
        # GUI State
        self.selected_port = None 
        self.port_coords = {}     
        self.lines_data = []      
        self.drag_data = {"x": 0, "y": 0, "item": None, "node_name": None}

        self.setup_ui()
        self.draw_initial_nodes()

    def setup_ui(self):
        control_frame = tk.Frame(self.root, height=50, bg="#e0e0e0")
        control_frame.pack(side=tk.TOP, fill=tk.X)
        
        btn_run = tk.Button(control_frame, text="Run Simulation", command=self.run_sim, bg="#4CAF50", fg="white", font=("Arial", 11, "bold"))
        btn_run.pack(side=tk.LEFT, padx=10, pady=5)
        
        btn_clear = tk.Button(control_frame, text="Clear Lines", command=self.clear_connections, bg="#f44336", fg="white", font=("Arial", 11))
        btn_clear.pack(side=tk.LEFT, padx=10, pady=5)
        
        btn_add = tk.Button(control_frame, text="+ Add Node", command=self.add_node_handler, bg="#2196F3", fg="white", font=("Arial", 11, "bold"))
        btn_add.pack(side=tk.LEFT, padx=10, pady=5)
        
        lbl_instr = tk.Label(control_frame, text="Drag nodes to move. Click ports OR numbers to connect.", bg="#e0e0e0")
        lbl_instr.pack(side=tk.LEFT, padx=20)

        paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(paned, bg="white", width=850)
        paned.add(self.canvas)
        
        self.result_area = scrolledtext.ScrolledText(paned, width=35, state='disabled', font=("Consolas", 10))
        paned.add(self.result_area)

    def draw_initial_nodes(self):
        start_x, start_y = 50, 100
        y_gap, x_gap = 150, 180
        
        # Inputs
        for i, name in enumerate(self.engine.input_node):
            self.create_visual_node(start_x, start_y + i*y_gap, name, ["in1", "in2"], side="right")

        # Switches
        switches = self.engine.node_name_list
        for i, name in enumerate(switches):
            col = i // 2
            row = i % 2
            self.create_visual_node(start_x + (col+1)*x_gap, start_y + row*y_gap, name, inputs=["1", "2"], outputs=["3", "4"])

        # Outputs
        for i, name in enumerate(self.engine.output_node):
            self.create_visual_node(start_x + 4*x_gap, start_y + i*y_gap, name, ["out3", "out4"], side="left")

    def add_node_handler(self):
        new_name = simpledialog.askstring("Add Node", "Enter new node name (e.g., X7):")
        if not new_name: return

        success = self.engine.add_dynamic_node(new_name, node_type="switch")
        if not success:
            messagebox.showerror("Error", f"Node name '{new_name}' already exists.")
            return

        default_x, default_y = 50, 450 
        self.create_visual_node(default_x, default_y, new_name, inputs=["1", "2"], outputs=["3", "4"])
        self.log(f"Added new node: {new_name}")

    def create_visual_node(self, x, y, name, inputs=[], outputs=[], side="both"):
        w, h = 80, 60
        node_tag = f"node_group_{name}"
        
        rect_id = self.canvas.create_rectangle(x, y, x+w, y+h, fill="#ddd", outline="black", width=2, tags=(node_tag, "draggable_node"))
        text_id = self.canvas.create_text(x+w/2, y+h/2, text=name, font=("Arial", 10, "bold"), tags=(node_tag, "draggable_node"))
        
        for item in [rect_id, text_id]:
            self.canvas.tag_bind(item, "<ButtonPress-1>", lambda e, n=name: self.on_node_press(e, n))
            self.canvas.tag_bind(item, "<B1-Motion>", self.on_node_drag)
            self.canvas.tag_bind(item, "<ButtonRelease-1>", self.on_node_release)

        if side in ["left", "both"] or inputs:
            for i, p_name in enumerate(inputs):
                py = y + (h * (i+1) / (len(inputs)+1))
                px = x
                self.draw_port_circle(px, py, name, p_name, node_tag)

        if side in ["right", "both"] or outputs:
            for i, p_name in enumerate(outputs):
                py = y + (h * (i+1) / (len(outputs)+1))
                px = x + w
                self.draw_port_circle(px, py, name, p_name, node_tag)

    def draw_port_circle(self, x, y, node_name, port_name, group_tag):
        r = 6
        tag = f"{node_name}:{port_name}"
        
        oval_id = self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="orange", outline="black", tags=(tag, "port", group_tag))
        text_id = self.canvas.create_text(x, y-15, text=port_name, font=("Arial", 8, "bold"), tags=(group_tag,))
        
        self.port_coords[tag] = [x, y]
        
        for item in [oval_id, text_id]:
            self.canvas.tag_bind(item, "<Button-1>", lambda event, n=node_name, p=port_name: self.on_port_click(n, p))
            self.canvas.tag_bind(item, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
            self.canvas.tag_bind(item, "<Leave>", lambda e: self.canvas.config(cursor=""))

    # Drag Logic
    def on_node_press(self, event, node_name):
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.drag_data["node_name"] = node_name

    def on_node_drag(self, event):
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        node_name = self.drag_data["node_name"]
        group_tag = f"node_group_{node_name}"
        
        self.canvas.move(group_tag, dx, dy)
        self.update_port_coords_by_delta(node_name, dx, dy)
        self.update_connected_lines(node_name)
        
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_node_release(self, event):
        self.drag_data["item"] = None
        self.drag_data["node_name"] = None

    def update_port_coords_by_delta(self, node_name, dx, dy):
        prefix = f"{node_name}:"
        for tag, coords in self.port_coords.items():
            if tag.startswith(prefix):
                coords[0] += dx
                coords[1] += dy

    def update_connected_lines(self, moving_node_name):
        for line_obj in self.lines_data:
            (n1, p1), (n2, p2) = line_obj['u'], line_obj['v']
            if n1 == moving_node_name or n2 == moving_node_name:
                x1, y1 = self.port_coords[f"{n1}:{p1}"]
                x2, y2 = self.port_coords[f"{n2}:{p2}"]
                self.canvas.coords(line_obj['id'], x1, y1, x2, y2)

    # Connection Logic
    def on_port_click(self, node_name, port_name):
        tag = f"{node_name}:{port_name}"
        x, y = self.port_coords[tag]
        
        if self.selected_port is None:
            self.selected_port = (node_name, port_name, x, y)
            self.canvas.create_oval(x-8, y-8, x+8, y+8, outline="red", width=2, tags="highlight")
        else:
            n1, p1, _, _ = self.selected_port
            if n1 == node_name and p1 == port_name:
                self.reset_selection()
                return

            x1, y1 = self.port_coords[f"{n1}:{p1}"]
            x2, y2 = self.port_coords[f"{node_name}:{port_name}"]
            
            line_id = self.canvas.create_line(x1, y1, x2, y2, fill="blue", width=2, arrow=tk.LAST)
            self.lines_data.append({'id': line_id, 'u': (n1, p1), 'v': (node_name, port_name)})
            
            print(f"Connected: {n1}.{p1} <-> {node_name}.{port_name}")
            self.reset_selection()

    def reset_selection(self):
        self.selected_port = None
        self.canvas.delete("highlight")

    def clear_connections(self):
        for line_obj in self.lines_data:
            self.canvas.delete(line_obj['id'])
        self.lines_data = []
        self.log("Connections cleared.")

    def run_sim(self):
        self.log("Running Simulation...")
        if not self.lines_data:
            messagebox.showwarning("Warning", "No connections defined.")
            return
        connections = [(obj['u'][0], obj['u'][1], obj['v'][0], obj['v'][1]) for obj in self.lines_data]
        result_text = self.engine.run_simulation(connections)
        self.result_area.config(state='normal')
        self.result_area.delete(1.0, tk.END)
        self.result_area.insert(tk.END, result_text)
        self.result_area.config(state='disabled')

    def log(self, msg):
        print(f"[GUI] {msg}")