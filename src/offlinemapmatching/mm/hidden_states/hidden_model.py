from ..observation.network import *
from ..observation.trajectory import *
from ..observation.observation import *
from .candidate import *
from .transition import *
from qgis.core import *
from PyQt5.QtWidgets import QProgressBar, QApplication
from PyQt5.QtCore import QVariant

class HiddenModel:
    
    def __init__(self, trajectory, network):
        self.trajectory = trajectory
        self.network = network
    
    def findViterbiPath(self, maximum_distance, sigma, my, pb):
        #init progressbar
        pb.setValue(0)
        pb.setMaximum(len(self.trajectory.observations))
        
        #init an empty viterbi path to store candidates
        viterbi_path = []
        
        #init the previous observation
        previous_observation = None
        
        #iterate over all observations from our trajectory
        for observation in self.trajectory.observations:
            
            #extract all candidates for the current observation
            candidates = observation.getCandidates(self.network.vector_layer, maximum_distance)
            if len(candidates) == 0:
                return -5
            
            #calculate the probabilities for all candidates to be emitted by the current observation (and vice versa)
            for candidate in candidates:
                candidate.calculateEmittedProbability(observation, sigma, my)
            
            #check whether we have the starting observation or not
            if previous_observation is not None and len(viterbi_path) > 0:
                #get the last entry of the viterbi path
                last_viterbi_entry = viterbi_path[len(viterbi_path) - 1]
                
                #create transitions between candidates and last viterbi vertex
                transitions = []
                for candidate in candidates:
                    #get coordinates of the last viterbi entry and the current candidate
                    x_viterbi = last_viterbi_entry['vertex'].point.asPoint().x()
                    y_viterbi = last_viterbi_entry['vertex'].point.asPoint().y()
                    x_candidate = candidate.point.asPoint().x()
                    y_candidate = candidate.point.asPoint().y()
                    
                    #just create a new Transition, if the current candidate and the last viterbi entry are different
                    if x_viterbi != x_candidate and y_viterbi != y_candidate:
                        transitions.append(Transition(last_viterbi_entry['vertex'], candidate))
                
                #calculate probabilities of the transitions (direction and length) and totalise them
                sum_routing_probability = 0.0
                sum_direction_probability = 0.0
                for transition in transitions:
                    transition.setRoutingProbability(self.network, observation.point.distance(previous_observation.point))
                    transition.setDirectionProbability(previous_observation, observation)
                    
                    #totalise
                    sum_routing_probability += transition.routing_probability
                    sum_direction_probability += transition.direction_probability
                
                #normalize the probabilities of the transitions, i.e. sum of probabilities over all transitions is equal 1
                for transition in transitions:
                    if sum_routing_probability != 0.0:
                        transition.routing_probability = transition.routing_probability / sum_routing_probability
                    if sum_direction_probability != 0.0:
                        transition.direction_probability = transition.direction_probability / sum_direction_probability
                    transition.setTransitionProbability()
                
                #calculate the highest probability (product of previous prob., trans. prob. and em. prob.)
                max_prob = 0.0
                for transition in transitions:
                    max_prob = (last_viterbi_entry['probability'] * transition.transition_probability * transition.end_candidate.emitted_probability)
                
                #find the transition with the highest probability
                for transition in transitions:
                    if (last_viterbi_entry['probability'] * transition.transition_probability * transition.end_candidate.emitted_probability) == max_prob:
                        
                        #add the candidate with the highest prob. product to the viterbi path
                        viterbi_path.append({'vertex': transition.end_candidate,
                                             'probability': max_prob})
                        break
            else:
                #find the candidate of the start observer with the highest probability
                candidate_with_max_prob = None
                max_prob = 0.0
                for candidate in candidates:
                    if candidate.emitted_probability > max_prob:
                        candidate_with_max_prob = candidate
                        max_prob = candidate.emitted_probability
            
                #add the start vertice to the viterbi path, if we are at the first observation of our trajectory
                viterbi_path.append({'vertex': candidate_with_max_prob,
                                     'probability': max_prob})
            
            #edit the previous observation
            previous_observation = observation
            pb.setValue(pb.value() + 1)
            QApplication.processEvents()
            
        return viterbi_path
    
    def getPathOnNetwork(self, vertices, pb, crs):
        #create a new layer
        layer = QgsVectorLayer('LineString?crs=' + crs + '&index=yes', 'matched trajectory', 'memory')
        QgsProject.instance().addMapLayer(layer)
        layer.startEditing()
        layer_data = layer.dataProvider()
        layer_data.addAttributes([QgsField('id', QVariant.Int),
                                  QgsField('probability_start_vertex', QVariant.Double),
                                  QgsField('probability_end_vertex', QVariant.Double)])
        layer.updateFields()
        
        #init progressbar
        pb.setValue(0)
        pb.setMaximum(len(vertices))
        #iterate over the vertices
        for i, vertex in enumerate(vertices):
            
            #if we are in the first loop, we skip them because we have no previous point to create a routing with start and end
            if i != 0:
                
                #get all edges of the graph/network along the shortest way from the previous to the current vertex
                points = self.network.routing(vertices[i - 1]['vertex'].point.asPoint(), vertex['vertex'].point.asPoint())
                if points == -1:
                    return points
                
                #now create a new line feature
                feature = QgsFeature(layer.fields())
                
                #create the geometry of the new feature
                linestring_vertices = []
                for point in points:
                    linestring_vertices.append(point)
                feature.setGeometry(QgsGeometry.fromPolylineXY(linestring_vertices))
                
                #insert the attributes and add the feature to the layer
                feature.setAttribute('id', i)
                feature.setAttribute('probability_start_vertex', vertices[i - 1]['probability'])
                feature.setAttribute('probability_end_vertex', vertex['probability'])
                layer.addFeatures([feature])
            
            pb.setValue(pb.value() + 1)
            QApplication.processEvents()
        
        layer.commitChanges()
        return layer
    
