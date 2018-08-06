import math
from ..observation.observation import *

class Candidate:
    
    def __init__(self, point):
        self.point = point
        self.emission_probability = 0.0
    
    def calculateEmissionProbability(self, observer, sigma, my):
        distance = self.point.distance(observer.point)
        self.emitted_probability = (1 / math.sqrt(2 * math.pi * sigma)) * math.pow(math.e, -1 * math.pow(distance - my, 2) / (2 * math.pow(sigma, 2)))
    
