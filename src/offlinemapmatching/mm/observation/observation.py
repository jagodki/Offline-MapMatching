from .network import *
from .intersection import *
from ..hidden_states.candidate import *
from qgis.core import *

class Observation:
    
    def __init__(self, point, id):
        self.point = point
        self.id = id
    
    def getAllCandidates(self, network, max_distance):
        #iterate over all lines of the network to check for candidates on this lines
        for feature in network.vector_layer.getFeatures():
            #init some vars
            linestring = feature.geometry()
            distance = self.point.distance(linestring)
            
            #check whether the distance is equal or less the search distance
            if distance <= max_distance:
                candidates.append(Candidate(linestring.nearestPoint(self.point), distance, self.id))
    
    def getCandidates(self, network, max_distance):
        candidates = []
        intersections_within_distance = []
        
        #get all intersection points within the search distance
        for intersection in network.intersections:
            if intersection.geometry.distance(self.point) <= max_distance:
                intersections_within_distance.append(intersection)
        
        # #iterate over all lines of the network to check for candidates on this lines
        # for feature in network.vector_layer.getFeatures():
            
            # #check if the current edge intersects an intersection within search distance
            # skip_iteration_step = False
            # for intersection in intersections_within_distance:
                # if feature.id() in intersection.edge_ids:
                    # skip_iteration_step = True
                    # break
            
            # #skip the iteration step if necessary
            # if skip_iteration_step is True:
                # continue
            
            # #init some vars
            # linestring = feature.geometry()
            # distance = self.point.distance(linestring)
            
            # #check whether the distance is equal or less the search distance
            # if distance <= max_distance:
                # candidates.append(Candidate(linestring.nearestPoint(self.point), distance, self.id))
        
        #iterate over all lines of the network to check for candidates on this lines
        candidate_points = []
        for feature in network.vector_layer.getFeatures():
            #init some vars
            linestring = feature.geometry()
            distance = self.point.distance(linestring)
            
            #check whether the distance is equal or less the search distance
            if distance <= max_distance:
                nearest_point = linestring.nearestPoint(self.point)
                candidate_is_not_near_to_intersection = True
                
                #check, whether the possible candidate is within the range to an intersection
                for intersection in intersections_within_distance:
                    if intersection.geometry.distance(nearest_point) <= max_distance:
                        candidate_is_not_near_to_intersection = False
                        break
                
                if candidate_is_not_near_to_intersection is True:
                    candidates.append(Candidate(nearest_point, distance, self.id))
        
        #now add the intersections to the candidates
        for intersection in intersections_within_distance:
            candidates.append(Candidate(intersection.geometry, intersection.geometry.distance(self.point), self.id))
        
        return candidates
    
    def isIntersectionInSearchDistance(self, edges, candidates):
        
        for index, edge in edges.enumerate():
            
            intersection_count = 0
            intersected_edges = []
            
            for other_index, other_edge in edges.enumerate():
                
                if other_index != index:
                    if edge.geometry().intersects(other_edge.geometry()):
                        intersection_count += 1
                        intersected_edges.append(other_index)
        
        
        
        #init a variable to count the intersections
        counter = 0
        
        #iterate over all network features
        for feature in network.getFeatures():
            
            #increase the counter if the geometries intersect each other
            if feature.geometry().insersects(self.point):
                counter += 1
            
            #break up the iteration when the counter reached a specific number
            if counter == 3:
                return True
        
        return False
    
