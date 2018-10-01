from qgis.analysis import *
from qgis.core import *

class Network:
    
    def __init__(self, linestring_layer):
        self.vector_layer = linestring_layer
    
    def routing(self, start, end):
        #create director and strategy
        director = QgsVectorLayerDirector(self.vector_layer, -1, '', '', '', 2)
        strategy = QgsNetworkDistanceStrategy()
        director.addStrategy(strategy)
        
        #buildiung the graph
        builder = QgsGraphBuilder(self.vector_layer.sourceCrs())
        tied_points = director.makeGraph(builder, [start, end])
        graph = builder.graph()
        start_id = graph.findVertex(tied_points[0])
        end_id = graph.findVertex(tied_points[1])
        
        #start routing
        (tree, cost) = QgsGraphAnalyzer.dijkstra(graph, start_id, 0)
        if tree[end_id] == -1:
            return -1
        else:
            points = []
            cur_pos = end_id
            
            #get the first vertex
            if cur_pos != start_id:
                if cur_pos == graph.edge(tree[cur_pos]).toVertex():
                    #insert the vertices to the result list
                    points.insert(0, graph.vertex(graph.edge(tree[cur_pos]).toVertex()).point())
                    points.insert(0, graph.vertex(graph.edge(tree[cur_pos]).fromVertex()).point())
                    
                    #set cur_pos to the next vertex
                    cur_pos = graph.edge(tree[cur_pos]).fromVertex()
                else:
                    #insert the vertices to the result list
                    points.insert(0, graph.vertex(graph.edge(tree[cur_pos]).fromVertex()).point())
                    points.insert(0, graph.vertex(graph.edge(tree[cur_pos]).toVertex()).point())
                    
                    #set cur_pos to the next vertex
                    cur_pos = graph.edge(tree[cur_pos]).toVertex()
                    
            
            while cur_pos != start_id:
                #just insert the vertex of the current edge, which does not already exist in the result list
                if cur_pos == graph.edge(tree[cur_pos]).toVertex():
                    points.insert(0, graph.vertex(graph.edge(tree[cur_pos]).fromVertex()).point())
                    
                    #set cur_pos to the next vertex
                    cur_pos = graph.edge(tree[cur_pos]).fromVertex()
                else:
                    points.insert(0, graph.vertex(graph.edge(tree[cur_pos]).toVertex()).point())
                    
                    #set cur_pos to the next vertex
                    cur_pos = graph.edge(tree[cur_pos]).toVertex()
                
            return points
    
    def distanceOnNetwork(self, start, end):
        #get all vertices from the routing result
        vertices = self.routing(start, end)
        
        #points == -1, if routing was not possible
        if vertices == -1:
            return vertices
        else:
            distance = 0
            for i, vertex in enumerate(vertices):
                
                #get the distance between the current vertice and the next vertice
                if len(vertices) > (i + 1):
                    distance = distance + vertex.distance(vertices[i + 1].x(), vertices[i + 1].y())
                else:
                    return distance
            return distance
    

