import heapq
import ocpa.objects.oc_petri_net.obj as ocpn
from typing import Tuple 
import itertools

class DirectGraph:
    def __init__(self,node,edge):
        self.node = set() if node is None else node
        self.edge = set() if edge is None else edge
        if any([e[0] not in node or e[1] not in node for e in edge]):
            return ValueError('one of the edge contains undefined node')
    def get_neighbors(self,node):
        neighbors=set()
        if node not in self.node:
            return ValueError('the given node is not found')
        for e in self.edge:
            if node in e:
                if node==e[0]:
                    neighbors.add(e[1])
                else:
                    neighbors.add(e[0])


#abstract to a directed graph used for finding the shortest silent path
def PN_to_DG(model:ocpn.ObjectCentricPetriNet):
    DG = DirectGraph
    for pl1 in model.places:
        for arcs1 in pl1.out_arcs:
            if arcs1.target.silent:
                DG.node.add(pl.name)
                for arcs2 in arcs1.target.out_arcs:
                    DG.edge.add((pl1.name,arcs2.target.name))
    return DG

#use informed searching algo to find out the shortest path of the graph

#astar is used to compute for demand
def astar(graph, start, goal):
    open_set = []  # Priority queue for nodes to be evaluated
    #heapq.heappush(open_set, (0, start))  # Start node with priority 0
    heapq.heappush(open_set, start)
    came_from = {}  # Dictionary to store the path
    g_score = {node: float('inf') for node in graph}  # Cost from start to each node
    g_score[start] = 0
    #f_score = {node: float('inf') for node in graph}  # Estimated total cost from start to goal
    #f_score[start] = heuristic(start, goal)
    while open_set:
        current = heapq.heappop(open_set)
        if current == goal:
            path = []
            while True:
                path.insert(0,came_from[current])
                if came_from[current] == start:
                    return path
                current = came_from[current]
        for neighbor in graph[current]:
            tentative_g_score = g_score[current] + 1
            if tentative_g_score < g_score[neighbor]:
                #if the tentative score is lower, then we update its neighbor and its score
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                #f_score[neighbor] = g_score[neighbor] + heuristic(neighbor, goal)
                #heapq.heappush(open_set, (f_score[neighbor], neighbor))
                heapq.heappush(open_set, neighbor)
    return None

# Define your heuristic function, distance function, and graph representation here
'''def heuristic(node, goal):
    # Define a heuristic function to estimate the cost to the goal
    pass'''

'''def distance(node1, node2):
    # Define a function to calculate the distance between two nodes
    pass'''

#Floyed-Warshall is used to compute the shortest path between all pairs
def Floyd_routing(DG:DirectGraph):
    #initialization
    shortestpath={}
    neighbors={}
    shortestcomefrom={}
    mindist={}
    for n in DG.node:
        neighbors[n] = DG.get_neighbors(n)
        for neighbor in neighbors[n]:
            shortestcomefrom[(n,neighbor)]=n
            mindist[(n,neighbor)]=1
        for notneighbor in DG.node-neighbors[n]:
            shortestcomefrom[(n,notneighbor)]=None
            mindist[(n,notneighbor)]=float('inf')
    for n1 in DG.node:
        for n2 in neighbor[n1]:
            shortestcomefrom,mindist = search_next_neighbor(n1,set(),shortestcomefrom,neighbor,n2,mindist)
    for ele in shortestcomefrom.keys():
        shortestpath[ele].insert(0,ele[1])
        while True:
            if ele[0] == shortestcomefrom[ele]:
                shortestpath[ele].insert(0,ele[0])
                break
            else:
                shortestpath[ele].insert(0,shortestcomefrom[ele])
                ele=(ele[0],shortestcomefrom[ele])
    return shortestpath
                
                

def search_next_neighbor(root,visited,shortestcomefrom,neighbor,current,mindist):
    if neighbor[current]==None or all([ele in visited for ele in neighbor[current]]):
        return shortestcomefrom,mindist
    for n in neighbor[current]:
        if n not in visited:
            #closest_node = shortestcomefrom[root,current]
            tentative_length =mindist[root,current]+1
            if tentative_length < mindist[root,n]:
                shortestcomefrom[root,n]=current
                mindist[root,n]=tentative_length
            visited.add(n)
            return search_next_neighbor(root,visited,shortestcomefrom,neighbor,n,mindist)



#detect whether the S-component contains more than 2 tokens
#get the sets of places that belong to the same S-component
def get_S_component(model:ocpn.ObjectCentricPetriNet):
    S_component=set()
    for pl in model.places:
        if pl.initial:
            #suffix is a set of the combination of the places only in next step
            suffix=get_next_places(model,pl)
            oldprefix=set()
            prefix={{pl}}
            #newprefix2=set()
            #suffix=list(itertools.product(*(next+prefix)))
            not_end=True
            #we only need to expand the number and the length of the prefix set\
            #and compute the cardinersian product of each to the each in suffix set!\
            #BUt you have to consider the matching of the prefix and the suffix!
            #Don't have to consider the process ordering! Just do it arbitrary until no\
            #place can be expanded anymore!
            while not_end:
                newprefix=set()
                #newprefix2=set()
                for pre in prefix:
                    for pl in pre-oldprefix:
                        suffix=get_next_places(model,pl)
                        for suf in suffix:
                            #But this is only expanded for one place...
                            newprefix.add(pre|suf)
                        
                #the while loop will end iff all the interesting places are the final places
                not_end=False
                for newpre in newprefix:                    
                    #candidates=set()
                    for pl in newpre-prefix:                   
                        if pl.final:
                            continue
                        else:
                            not_end=True
                            prefix = newprefix
                            suffix.add(get_next_places(model,pl))



#return the next xor places and the next concurrency places
def get_next_places(model:ocpn.ObjectCentricPetriNet,place:ocpn.ObjectCentricPetriNet.Place):
    cartersian_product=set()
    #cartersian_product.add(place)
    for arc1 in place.out_arcs:
        product_set = set()
        for arc2 in arc1.target.out_arcs:
            product_set.add(arc2.target)
        cartersian_product.add(product_set)
    return list(itertools.product(*cartersian_product))
    #return cartersian_product.add(product_set)





#manage the age value and delete the oldest token if superfluous

#compute the transition system of the event log