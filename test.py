import numpy as np
from dijkstra import Graph, DijkstraSPF
import matplotlib.pyplot as plt

def original_graph():
    graph = Graph()
    graph.add_edge(A, B, 2)
    graph.add_edge(B, A, 2)

    graph.add_edge(B, D, 2)
    graph.add_edge(D, B, 2)

    graph.add_edge(D, C, 2)
    graph.add_edge(C, D, 2)

    graph.add_edge(A, C, 2)
    graph.add_edge(C, A, 2)

    graph.add_edge(A, D, 3)
    graph.add_edge(D, A, 3)

    graph.add_edge(C, B, 3)
    graph.add_edge(B, C, 3)

    return graph

def two_nearest_nodes(graph, trad, obstacle):
    distances = {}
    #compute distance between obstacle and each node 
    for node in graph.get_nodes():
        dist = np.sqrt((obstacle[0]-trad[str(node)][0])**2 + (obstacle[1]-trad[str(node)][1])**2)
        distances[str(node)] = dist
    #keep 2 nearest node
    temp = min(distances.values())
    [first] = [key for key in distances if distances[key] == temp]
    distances.pop(str(first))
    temp = min(distances.values())
    [second] = [key for key in distances if distances[key] == temp]
    return [first, second]

def update_graph(graph, trad, obstacle):
    n1, n2 = two_nearest_nodes(graph, trad, obstacle)
    graph.add_edge(n1, n2, np.Infinity)
    graph.add_edge(n2, n1, np.Infinity)
    return graph

def print_dijkstra(dijkstra, nodes):
    for u in nodes:
        plt.plot(trad[str(u)][0], trad[str(u)][1], 'r.')
        print("%-5s %8d" % (u, dijkstra.get_distance(u)))
        print(" -> ".join(dijkstra.get_path(u)))



A, B, C, D = nodes = list("ABCD")
trad = {"A" : [-100, 100],
        "B" : [100, 100],
        "C" : [-100, -100],
        "D" : [100, -100]}
graph = original_graph()
dijkstra = DijkstraSPF(graph, A)
print("without obstacle")
print_dijkstra(dijkstra, nodes)


obstacles = [[20, 110], [-100, 90], [100, 80]]
for obstacle in obstacles:
    print("###############")
    plt.plot(obstacle[0],obstacle[1], 'b*')
    print("obstacle at "+str(obstacle))
    newgraph = update_graph(original_graph(), trad, obstacle)
    dijkstra = DijkstraSPF(newgraph, A)
    print_dijkstra(dijkstra, nodes)

plt.show()
