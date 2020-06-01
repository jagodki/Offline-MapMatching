import math
from ..observation.observation import *

class Candidate:
    
    def __init__(self, point, distance, observation_id):
        self.point = point
        self.distance_to_observation = distance
        self.observation_id = observation_id
    
    def getEmissionProbability(self, sigma, my):
        return (1 / math.sqrt(2 * math.pi * sigma)) * math.pow(math.e, -1 * math.pow(self.distance_to_observation - my, 2) / (2 * math.pow(sigma, 2)))
    
