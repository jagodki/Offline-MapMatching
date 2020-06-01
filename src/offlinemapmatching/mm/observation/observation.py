from .network import *
from ..hidden_states.candidate import *
from qgis.core import *

class Observation:
    
    def __init__(self, point, id):
        self.point = point
        self.id = id
    
    def getCandidates(self, network_layer, max_distance):
        candidates = []
        
        #iterate over all lines of the network to check for candidates on this lines
        for feature in network_layer.getFeatures():
            polyline = feature.geometry()
            distance = self.point.distance(polyline)
            if distance <= max_distance:
                candidates.append(Candidate(polyline.nearestPoint(self.point), distance, self.id))
        return candidates
    
