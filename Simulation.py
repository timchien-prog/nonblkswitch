# engine.py
import itertools
from NodePorts import Node, Port

class SimulationEngine:
    """
    Handles the mathematical logic, topology construction, and path tracing algorithm.
    """
    def __init__(self):
        self.node_dict = {}
        # Default nodes
        self.node_name_list = ["X1", "X2", "X3", "X4", "X5", "X6"]
        self.input_node = ["INnode1", "INnode2"]
        self.output_node = ["OUTnode1", "OUTnode2"]
        
    def add_dynamic_node(self, name, node_type="switch"):
        """
        Dynamically registers a new node to the simulation scope.
        """
        if name in self.node_name_list or name in self.input_node or name in self.output_node:
            return False # Duplicate name
        
        if node_type == "switch":
            self.node_name_list.append(name)
        elif node_type == "input":
            self.input_node.append(name)
        elif node_type == "output":
            self.output_node.append(name)
        return True

    def initialize_nodes(self, state):
        self.node_dict = {} 
        # Initialize Input Nodes
        for input_name in self.input_node:
            node = Node(input_name)
            self.node_dict[input_name] = node
            for port in ["in1", "in2"]: node.add_port(port)
            
        # Initialize Output Nodes
        for output_name in self.output_node:
            node = Node(output_name)
            self.node_dict[output_name] = node
            for port in ["out3", "out4"]: node.add_port(port)
            
        # Initialize Switch Nodes
        for i, node_name in enumerate(self.node_name_list):
            node = Node(node_name)
            self.node_dict[node_name] = node
            try: node.state = state[i]
            except IndexError: node.state = 0
            for port in ["1", "2", "3", "4"]: node.add_port(port)

    def set_port_interconnection(self, node_name, port_name, connected_node_name, connected_port_name):
        if node_name not in self.node_dict or connected_node_name not in self.node_dict: return
        port_obj_a = self.node_dict[node_name].ports[port_name]
        port_obj_b = self.node_dict[connected_node_name].ports[connected_port_name]
        port_obj_a.set_connections(port_obj_b)
        port_obj_b.set_connections(port_obj_a)

    def set_intra_connection(self):
        for node_name in self.node_name_list:
            node = self.node_dict[node_name]
            if node.state == 0: # Bar state
                self.set_port_interconnection(node_name, "1", node_name, "3")
                self.set_port_interconnection(node_name, "2", node_name, "4")
            else: # Cross state
                self.set_port_interconnection(node_name, "1", node_name, "4")
                self.set_port_interconnection(node_name, "2", node_name, "3")

    def follow_path_port(self, start_port, light_paths):
        """
        DFS-like traversal to trace the light path.
        """
        current = start_port
        visited = set()
        incoming_state = 0
        while True:
            if current in visited: return "LOOP"
            visited.add(current)
            node = current.node
            
            if node.name.startswith("OUTnode"): 
                return f"{node.name}.{current.name}"
            if node.name.startswith("INnode") and current is not start_port: 
                return "INVALID"
            
            # Toggle state: 0 (inside) <-> 1 (outside)
            incoming_state = 1 if incoming_state == 0 else 0
            
            next_port = current.get_next(incoming_state)
            if next_port is None: return "BROKEN_LINK"
            
            light_paths.append(f"Current: {current.node.name} {current.name} -> Next: {next_port.node.name} {next_port.name}")
            current = next_port

    def run_simulation(self, user_connections):
        """
        Iterates through all 2^N state permutations to find valid mappings.
        """
        all_states = itertools.product([0, 1], repeat=len(self.node_name_list))
        seen_mappings = []
        results_text = ""
        config_count = 0
        
        for state in all_states:
            self.initialize_nodes(state)
            self.set_intra_connection()
            
            # Apply GUI connections
            for conn in user_connections:
                n1, p1, n2, p2 = conn
                self.set_port_interconnection(n1, p1, n2, p2)
            
            invalid_flag = False
            mapping = []
            
            for inputname in self.input_node:
                if invalid_flag: break
                for inport in ["in1", "in2"]:
                    light_paths = []
                    # Safety check if node was deleted or renamed (though distinct in this logic)
                    if inputname not in self.node_dict: continue
                    
                    start_port = self.node_dict[inputname].ports[inport]
                    # Logic assumes input ports always exist
                    result = self.follow_path_port(start_port, light_paths)
                    
                    if result in ["LOOP", "INVALID", "BROKEN_LINK"]:
                        invalid_flag = True; break
                    
                    mapping.append(f"{inputname}.{inport}->{result}")

            if invalid_flag: continue
            
            mapping_tuple = tuple(mapping)
            if mapping_tuple in seen_mappings: continue
            
            seen_mappings.append(mapping_tuple)
            config_count += 1
            results_text += f"\n=== Configuration {config_count} | State: {state} ===\nMapping: {mapping_tuple}\n" + "-"*30 + "\n"
            
        return results_text if results_text else "No valid configurations found (Check connections)."