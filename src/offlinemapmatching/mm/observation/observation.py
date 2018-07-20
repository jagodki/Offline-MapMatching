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
            polyline = feature.geometry()
            if self.point.distance(polyline) <= max_distance:
                candidates.append(Candidate(polyline.nearestPoint(self.point)))
        return candidates
    
