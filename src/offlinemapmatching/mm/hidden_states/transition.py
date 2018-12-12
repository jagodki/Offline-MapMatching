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
        self.pointsOnNetwork = self.getAllPointsOnNetwork(network)
    
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
        elif end_observation.point.asPoint().y() != start_observation.point.asPoint().y():
            m_observation = 90.0
        
        #iterate over all points and use their precursor to calculate directions
        for i, current_point in enumerate(self.pointsOnNetwork):
            if i != 0:
                
                #get the precursor of the current point
                precursor = self.pointsOnNetwork[i - 1]
                
                #calculate the slope of the points using arctan (we get results between 0 and 180 degrees)
                if (current_point.x() - precursor.x()) != 0:
                    m_candidate = math.degrees(math.atan((current_point.y() - precursor.y()) /
                                                         (current_point.x() - precursor.x()))) + 90
                elif current_point.y() - precursor.y():
                    m_candidate = 90.0
                
                #calculate the difference of the slopes
                difference = abs(m_observation - m_candidate)
                
                #normalisation of the difference
                p_intermediate *= (180 - difference) / 180
                
                #clear the slope
                m_candidate = 0.0
    
        #store the result
        self.direction_probability = p_intermediate
    
    def setRoutingProbability(self, distance_between_observations, beta):
        #get the distance of the shortest path between the two candidates of the current transition
        distance_on_network = self.getLengthOfTransition()
        
        #calculate the difference between the distances of the observations and the candidates
        difference = abs(distance_on_network - distance_between_observations)

        #calculate the exponential probability distribution
        self.routing_probability = 1 / beta * math.pow(math.e, -1 * difference / beta)
    
    def setTransitionProbability(self):
        self.transition_probability = self.direction_probability * self.routing_probability
    
    def getAllPointsOnNetwork(self, network):
        #get all points of the shortest path on the network from the start to the end of the transistion and store them
        return network.routing(self.start_candidate.point.asPoint(), self.end_candidate.point.asPoint())
    
    def getLengthOfTransition(self):
        #points == -1, if routing was not possible
        if self.pointsOnNetwork == -1:
            return self.pointsOnNetwork
        else:
            distance = 0
            for i, vertex in enumerate(self.pointsOnNetwork):
                
                #get the distance between the current vertice and the next vertice
                if len(self.pointsOnNetwork) > (i + 1):
                    distance = distance + vertex.distance(self.pointsOnNetwork[i + 1].x(), self.pointsOnNetwork[i + 1].y())
                else:
                    return distance
            return distance
    
