from .network import *
from ..hidden_states.candidate import *
from qgis.core import *

class Observation:
    
    def __init__(self, point, id):
        self.point = point
        self.id = id
    
    def getCandidates(self, network_layer, max_distance):
        candidates = []
        for feature in network_layer.getFeatures():
            if self.point.distance(feature.geometry()) <= max_distance:
                candidates.append(Candidate(self.point.nearestPoint(feature.geometry())))
        return candidates
    
