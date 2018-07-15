from .candidate import *
import math

class Transition:
    
    def __init__(self, start_candidate, end_candidate):
        self.start_candidate = start_candidate
        self.end_candidate = end_candidate
        self.direction_probability = 0.0
        self.routing_probability = 0.0
        self.transition_probability = 0.0
    
    def setDirectionProbability(self, start_observation, end_observation):
        #calculate the slopes using arctan, i.e. we get results between 0 and 180 degrees
        m_observation = math.degrees(math.atan((end_observation.point.asPoint().y() -
                                               start_observation.point.asPoint().y()) /
                                               (end_observation.point.asPoint().x() -
                                               start_observation.point.asPoint().x()))) + 90
        m_candidate = math.degrees(math.atan((self.end_candidate.point.asPoint().y() -
                                             self.start_candidate.point.asPoint().y()) /
                                             (self.end_candidate.point.asPoint().x() -
                                             self.start_candidate.point.asPoint().x()))) + 90
        
        #calculate the difference of the slopes
        difference = m_observation - m_candidate
        
        #normalization of the difference
        self.direction_probability = (180 - difference) / 180
    
    def setRoutingProbability(self, network, distance_between_observations):
        distance_on_network = network.distanceOnNetwork(self.start_candidate.point.asPoint(),
                                                        self.end_candidate.point.asPoint())
        if distance_on_network >= distance_between_observations:
            self.routing_probability = distance_between_observations / distance_on_network
        else:
            self.routing_probability = distance_on_network / distance_between_observations
    
    def setTransitionProbability(self):
        self.transition_probability = self.direction_probability * self.routing_probability
    
    
