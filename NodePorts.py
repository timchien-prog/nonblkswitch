# models.py
class Port:
    """
    Represents a physical port on a node.
    """
    def __init__(self, name, node):
        self.name = name
        self.node = node
        self.connections = [] 

    def set_connections(self, conn_list):
        self.connections.append(conn_list)

    def get_next(self, incoming_state):
        # incoming_state: 0 (from inside node), 1 (from outside node)
        if self.node.name.startswith("INnode"):
            incoming_state = 0
        try:
            return self.connections[incoming_state]
        except IndexError:
            return None 

class Node:
    """
    Represents a generic node (Switch, Input, or Output).
    """
    def __init__(self, name):
        self.name = name
        self.ports = {}
        self.state = 0  # 0: Bar, 1: Cross
        
    def add_port(self, port_name):
        port = Port(port_name, self)
        self.ports[port_name] = port
        return port