from qgis.core import *
import processing
import math, json

class Routing:
    
    def __init__(self, network):
        self.nodes = {}
        self.edges = {}
        self.routes = {}
        self.matrix = []
        self.dataPreparation(network)
    
    def dataPreparation(self, network):
        #init some data structur for the further work
        self.edges = {}
        self.nodes = {}
        
        #extract all edges and their nodes including some properties to fill up the edges and nodes dictionary
        coords = []
        for index, feature in enumerate(network.getFeatures()):
            #get the vertices
            vertices = feature.geometry().asPolyline()
            
            if len(vertices) == 2:
                #calculate the slope
                slope = 0.0
                if (vertices[1].x() - vertices[0].x()) != 0:
                    slope = math.degrees(math.atan((vertices[1].y() - vertices[0].y()) / (vertices[1].x() - vertices[0].x()))) + 90
                elif vertices[1].y() != vertices[0].y():
                    slope = 90.0
                
                #get the length of this feature
                length = feature.geometry().length()
                
                #now store these information into the data structur initialised before
                start_id = self.addNode(vertices[0].x(), vertices[0].y(), feature["line_id"])
                end_id = self.addNode(vertices[1].x(), vertices[1].y(), feature["line_id"])
                self.edges[feature.id] = {"length": length, "slope": slope, "start_node": start_id, "end_node": end_id}
        
    def addNode(self, x, y, line_id):
        for key, value in self.nodes.items():
            if value["x"] == x and value["y"] == y:
                
                #append the line_id to an already existing node
                self.nodes[key]["line_ids"].append(line_id)
                return key
        
        #create a new entry
        max_id = len(self.nodes)
        self.nodes[max_id] = {"x": x, "y": y, "line_ids": [line_id]}
        return max_id
    
    def initMatrixAndRoutes(self):
        self.matrix = []
        self.routes = {}
        
        #first loop for all rows
        for key, value in self.nodes.items():
            row = []
            
            #second loop for all columns
            for second_key, second_value in self.nodes.items():
                
                #init the distance
                distance = None
                
                #check whether the both nodes are equal
                if key == second_key:
                    distance = 0.0
                    self.routes[str(key) + "-" + str(second_key)] = [key]
                else:
                    #get the start distance between two unequal nodes
                    distance = self.getDistanceBetweenNodes(value, second_value)
                    self.routes[str(key) + "-" + str(second_key)] = [key, second_key]
                    
                row.append(distance)
            self.matrix.append(row)
                
    def getDistanceBetweenNodes(self, first_node, second_node):
        #iterate over all edges interacting with the first node
        for edge_id in first_node["line_ids"]:
            
            #iterate over all edges interacting with the second node
            for second_edge_id in second_node["line_ids"]:
                
                #if they share an edge, than they are neighbours
                if edge_id == second_edge_id:
                    return math.sqrt(math.pow(second_node["x"] - first_node["x"], 2) + math.pow(second_node["y"] - first_node["y"], 2))
        
        #if they are not neighbours, return infinity
        return math.inf
    
    def manyToMany(self, feedback = None):
        #init the data structur
        self.initMatrixAndRoutes()
        
        #Floyd-Warshal-Algorithm
        v = len(self.matrix)
        for k in range(0,v):
            for i in range(0,v):
                for j in range(0,v):
                    if self.matrix[i][j] > self.matrix[i][k] + self.matrix[k][j]:
                        
                        #update the matrix
                        self.matrix[i][j] = self.matrix[i][k] + self.matrix[k][j]
                        
                        #update the shortest routeId
                        first_path = self.routes[str(list(self.nodes)[i]) + "-" + str(list(self.nodes)[k])]
                        second_path = self.routes[str(list(self.nodes)[k]) + "-" + str(list(self.nodes)[j])]
                        if first_path[-1] == second_path[0]:
                            self.routes[str(list(self.nodes)[i]) + "-" + str(list(self.nodes)[j])] =first_path[:-1] + second_path
                        else:
                            self.routes[str(list(self.nodes)[i]) + "-" + str(list(self.nodes)[j])] = first_path + second_path
            
            if feedback is not None:
                feedback.setProgress(int((k / v) * 100))
    
    def writeRoutesToFile(self, path):
        #write the routes into a json-file
        with open(path, 'w') as outfile:
            json.dump(self.routes, outfile)
