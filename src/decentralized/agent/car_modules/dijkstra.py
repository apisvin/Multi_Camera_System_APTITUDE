import sys
import numpy as np

def dijkstra_algorithm(graph, start_node):
    unvisited_nodes = list(graph.get_nodes())
 
    # We'll use this dict to save the cost of visiting each node and update it as we move along the graph   
    shortest_path = {}
 
    # We'll use this dict to save the shortest known path to a node found so far
    previous_nodes = {}
 
    # We'll use max_value to initialize the "infinity" value of the unvisited nodes   
    max_value = sys.maxsize
    for node in unvisited_nodes:
        shortest_path[node] = max_value
    # However, we initialize the starting node's value with 0   
    shortest_path[start_node] = 0
    
    # The algorithm executes until we visit all nodes
    while unvisited_nodes:
        # The code block below finds the node with the lowest score
        current_min_node = None
        for node in unvisited_nodes: # Iterate over the nodes
            if current_min_node == None:
                current_min_node = node
            elif shortest_path[node] < shortest_path[current_min_node]:
                current_min_node = node
                
        # The code block below retrieves the current node's neighbors and updates their distances
        neighbors = graph.get_outgoing_edges(current_min_node)
        for neighbor in neighbors:
            tentative_value = shortest_path[current_min_node] + graph.value(current_min_node, neighbor)
            if tentative_value < shortest_path[neighbor]:
                shortest_path[neighbor] = tentative_value
                # We also update the best path to the current node
                previous_nodes[neighbor] = current_min_node
 
        # After visiting its neighbors, we mark the node as "visited"
        unvisited_nodes.remove(current_min_node)
    
    return previous_nodes, shortest_path

def print_result(previous_nodes, shortest_path, start_node, target_node):
    path = []
    node = target_node
    
    while node != start_node:
        path.append(node)
        node = previous_nodes[node]
 
    # Add the start node manually
    path.append(start_node)
    
    print("We found the following best path with a value of {}.".format(shortest_path[target_node]))
    print(" -> ".join(reversed(path)))
    
def next_target(start_node, target_node, graph):
    previous_nodes, shortest_path = dijkstra_algorithm(graph=graph, start_node=start_node)
    path = []
    node = target_node
    
    while node != start_node:
        path.append(node)
        node = previous_nodes[node]
 
    return path[-1]
"""

nodes = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]
 
init_graph = {}
for node in nodes:
    init_graph[node] = {}
    
init_graph["A"]["B"] = 2
init_graph["B"]["C"] = 2
init_graph["C"]["F"] = 2
init_graph["F"]["I"] = 2
init_graph["I"]["H"] = 2
init_graph["H"]["G"] = 2
init_graph["G"]["D"] = 2
init_graph["D"]["A"] = 2

init_graph["D"]["E"] = 3
init_graph["B"]["E"] = 3
init_graph["F"]["E"] = 3
init_graph["H"]["E"] = 3

graph = Graph(nodes, init_graph)
previous_nodes, shortest_path = dijkstra_algorithm(graph=graph, start_node="A")
print_result(previous_nodes, shortest_path, start_node="A", target_node="I")
print(next_target(start_node="A", target_node="I", graph=graph))

graph.modify_weight("A", "B", 9)
graph.modify_weight("D", "G", 9)
previous_nodes, shortest_path = dijkstra_algorithm(graph=graph, start_node="A")
print_result(previous_nodes, shortest_path, start_node="A", target_node="I")
print(next_target(start_node="A", target_node="I", graph=graph))
"""

