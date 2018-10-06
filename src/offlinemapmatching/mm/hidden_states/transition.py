from .candidate import *
import math

class Transition:
    
    def __init__(self, start_candidate, end_candidate, network):
        self.start_candidate = start_candidate
        self.end_candidate = end_candidate
        self.network = network
        self.direction_probability = 0.0
        self.routing_probability = 0.0
        self.transition_probability = 0.0
    
    def setDirectionProbability(self, start_observation, end_observation):
        #variables to store the slops
        m_observation = 0.0
        m_candidate = 0.0
        
        #variable to store the intermediate results of the probability
        p_intermediate = 1.0
        
        #calculate the slope of the observations using arctan (we get results between 0 and 180 degrees)
        if (end_observation.point.asPoint().x() - start_observation.point.asPoint().x()) != 0:
            m_observation = math.degrees(math.atan((end_observation.point.asPoint().y() -
                                                    start_observation.point.asPoint().y()) /
                                                   (end_observation.point.asPoint().x() -
                                                    start_observation.point.asPoint().x()))) + 90
        
        #get all vertices of the network between start and end candidate
        points_on_network = self.network.routing(self.start_candidate.point.asPoint(), self.end_candidate.point.asPoint())
        
        #iterate over all points and use their precursor to calculate directions
        for i, current_point in enumerate(points_on_network):
            if i != 0:
                
                #get the precursor of the current point
                precursor = points_on_network[i - 1]
                
                #calculate the slope of the points using arctan (we get results between 0 and 180 degrees)
                if (current_point.x() - precursor.x()) != 0:
                    m_candidate = math.degrees(math.atan((current_point.y() - precursor.y()) /
                                                         (current_point.x() - precursor.x()))) + 90
                
                #calculate the difference of the slopes
                difference = abs(m_observation - m_candidate)
                
                #normalisation of the difference
                p_intermediate *= (180 - difference) / 180
    
        #store the result
        self.direction_probability = p_intermediate
    
    def setRoutingProbability(self, distance_between_observations):
        distance_on_network = self.network.distanceOnNetwork(self.start_candidate.point.asPoint(),
                                                        self.end_candidate.point.asPoint())
        if distance_on_network >= distance_between_observations and distance_on_network != 0.0:
            self.routing_probability = distance_between_observations / distance_on_network
        else:
            self.routing_probability = distance_on_network / distance_between_observations
    
    def setTransitionProbability(self):
        self.transition_probability = self.direction_probability * self.routing_probability
    
    
