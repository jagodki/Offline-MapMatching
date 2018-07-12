from qgis.analysis import *
from qgis.core import *

class Network:
    
    def __init__(self, linestring_layer):
        self.vector_layer = linestring_layer
    
    def routing(self, start, end):
        #create director and strategy
        director = QgsLinevector_layerDirector(self.vector_layer, -1, '', '', '', 3)
        properter = QgsDistanceArcProperter()
        director.addProperter(properter)
        
        #buildiung the graph
        builder = QgsGraphBuilder(self.vector_layer.sourceCrs())
        tiedPoints = director.makeGraph(builder, [start, end])
        graph = builder.graph()
        start_id = graph.findVertex(tiedPoints[0])
        end_id = graph.findVertex(tiedPoints[1])
        
        #start routing
        (tree, cost) = QgsGraphAnalyzer.dijkstra(graph, start_id, 0)
        if tree[end_id] == -1:
            return -1
        else:
            points = []
            cur_pos = end_id
            while cur_pos != start_id:
                points.append(graph.vertex(graph.arc(tree[curPos]).inVertex()).point())
                cur_pos = graph.arc(tree[cur_pos]).outVertex()
            return points
    
    def distanceOnNetwork(self, start, end):
        #get all vertices from the routing result
        vertices = self.routing(start, end)
        
        #points == -1, if routing was not possible
        if vertices == -1:
            return vertices
        else:
            distance = 0
            for i, vertice in enumerate(vertices):
                
                #get the distance between the current vertice and the next vertice
                if len(vertices) > (i + 1):
                    distance = distance + vertice.distance(vertices[i + 1].x(), vertices[i + 1].y())
                else:
                    return distance
            return distance
    

