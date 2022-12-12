import sys
import time
import logging
 
class Graph(object):
    def __init__(self, nodes, init_graph):
        #nodes in all graph
        self.nodes = nodes
        # actual graph to be modified during time
        self.graph = self.construct_graph(nodes, init_graph)
        # array containing memory from original graph ([n1, n2, value, age])
        self.memory = []
        # delay to reset graph edge value
        self.delay = 1
        
    def construct_graph(self, nodes, init_graph):
        '''
        This method makes sure that the graph is symmetrical. In other words, if there's a path from node A to B with a value V, there needs to be a path from node B to node A with a value V.
        '''
        graph = {}
        for node in nodes:
            graph[node] = {}
        
        graph.update(init_graph)
        
        for node, edges in graph.items():
            for adjacent_node, value in edges.items():
                if graph[adjacent_node].get(node, False) == False:
                    graph[adjacent_node][node] = value
            
        return graph
    
    def get_nodes(self):
        "Returns the nodes of the graph."
        return self.nodes
    
    def get_outgoing_edges(self, node):
        "Returns the neighbors of a node."
        connections = []
        for out_node in self.nodes:
            if self.graph[node].get(out_node, False) != False:
                connections.append(out_node)
        return connections
    
    def value(self, node1, node2):
        "Returns the value of an edge between two nodes."
        return self.graph[node1][node2]
    
    def modify_weight(self, node1, node2, weight):
        self.memory.append([node1, node2, self.graph[node1][node2], time.time()])
        self.graph[node1][node2] = weight
        self.graph[node2][node1] = weight
        
    def update(self):
        memory_temp = self.memory.copy()
        for i in range(len(memory_temp)):
            n1 = memory_temp[i][0]
            n2 = memory_temp[i][1]
            value = memory_temp[i][2]
            age = memory_temp[i][3]
            if time.time() - age > self.delay:
                self.graph[n1][n2] = value
                self.graph[n2][n1] = value
                self.memory.remove(memory_temp[i])
                logging.debug("edge between {} and {} retrieved in graph".format(n1,n2))

    def refresh_edge(n1, n2):
        for mem in self.memory:
            if (mem[0]==n1 and mem[1]==n2) or (mem[0]==n2 and mem[1]==n1):#if edge is part of memory
                mem[3] = time.time()
                logging.debug("memory of edge between {} and {} refreshed".format(n1, n2))
                break
"""

#init graph
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
print("graph")
print(graph.graph)
print("memory")
print(graph.memory)
graph.modify_weight("B", "A", 100)
print("###")
print("graph")
print(graph.graph)
print("memory")
print(graph.memory)
time.sleep(2)
graph.update()
print("###")
print("graph")
print(graph.graph)
print("memory")
print(graph.memory)
"""