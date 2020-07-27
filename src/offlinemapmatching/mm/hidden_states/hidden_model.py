from ..observation.network import *
from ..observation.trajectory import *
from ..observation.observation import *
from .candidate import *
from .transition import *
from ..helper.measurement_statistics import *
from qgis.core import *
import os, math
from PyQt5.QtWidgets import QProgressBar, QApplication
from PyQt5.QtCore import QVariant, QDir

class HiddenModel:
    
    def __init__(self, trajectory, network):
        self.trajectory = trajectory
        self.network = network
        self.counter_candidates = 0
        self.candidate_graph = []
        self.candidates = {}
        self.candidates_backtracking = {}
        self.observation_measurements = MeasurementStatistics()
        self.transition_measurements = MeasurementStatistics()
        self.pb = None
    
    def createGraph(self, maximum_distance):
        #init progressbar
        self.initProgressbar(len(self.trajectory.observations))
        
        #init data structur
        self.candidate_graph = []
        self.candidates = {}
        self.counter_candidates = 0
        
        #iterate over all observations from our trajectory
        for observation in self.trajectory.observations:
            
            #extract all candidates of the current observation
            candidates = observation.getCandidates(self.network, maximum_distance)
            #candidates = observation.getAllCandidates(self.network, maximum_distance)
            if len(candidates) == 0:
                QgsMessageLog.logMessage('could not find any candidates for trajectory point ' + str(observation.id), level=Qgis.Info)
                return -5
            else:
                #create the current level of the graph and the candidate measurements
                current_graph_level = {}
                for candidate in candidates:
                    
                    #store the observation measurements for a later usage of their statistics
                    #e.g. for calculations of the emission probabilities
                    self.observation_measurements.addMeasurement(candidate.distance_to_observation)
                    
                    #candidate.calculateEmissionProbability(observation, sigma, my)
                    current_graph_level[self.counter_candidates] = {
                                                  #'observation_id' : observation.id,
                                                  #'emitted_probability' : candidate.emission_probability,
                                                  'candidate': candidate,
                                                  'transition_probabilities' : {},
                                                  'transition_probability' : 0.0,
                                                  'curvature_probability' : 0.0,
                                                  'total_probability' : 0.0
                                                  }
                    
                    #store the candidate in a dictionary (key can be used to find the candidate in the graph and vice versa)
                    self.counter_candidates += 1
                
                #add the current graph level to the graph
                self.candidate_graph.append(current_graph_level)
            
            #update progressbar
            self.updateProgressbar()
        
        return 0
    
    def createBacktracking(self):
        #init progressbar
        self.initProgressbar(len(self.candidate_graph))
        
        self.candidates_backtracking = {}
        
        for i, graph_level in enumerate(self.candidate_graph):
            
            #the candidates of the first observation have no parent
            if i != 0:
                for id, entry in graph_level.items():
                    
                    #get all transition probabilities of the current entry and iterate over them to find the highest total probability
                    transition_probabilities = entry['transition_probabilities']
                    for previous_id, transition in transition_probabilities.items():
                        
                        #calculate the probabilities of the current transition
                        start_observation = self.trajectory.observations[i - 1]
                        end_observation = self.trajectory.observations[i]
                        distance_between_observations = start_observation.point.distance(end_observation.point)
                        transition.setDirectionProbability(start_observation, end_observation)
                        transition.setRoutingProbability(distance_between_observations, self.transition_measurements.getStandardDeviation())
                        transition.setTransitionProbability()
                        
                        #calculate the total probability and compare it
                        current_total_probability = transition.transition_probability * entry['candidate'].getEmissionProbability(self.observation_measurements.getStandardDeviation(), self.observation_measurements.getMeanValue())# * self.candidate_graph[i - 1][key]['total_probability']
                        
#                        #calculate the emission probability for the current entry/candidate in the graph level
#                        current_total_probability = value * entry["candidate"].getEmissionProbability(self.observation_measurements.getStandardDeviation(), 0.0) * self.candidate_graph[i - 1][key]['total_probability']
                        
                        if current_total_probability >= entry['total_probability']:
                            entry['total_probability'] = current_total_probability
                            entry['transition_probability'] = transition.transition_probability
                            self.candidates_backtracking[id] = previous_id
            
            #update progressbar
            self.updateProgressbar()
        
        return 0

    def findViterbiPath(self):
        #init an array to store all candidates of the most likely path
        viterbi_path = []
        
        #find the highest total probability in the last graph level
        highest_prob = 0.0
        id = None
        graph_counter = len(self.candidate_graph) - 1
        last_graph_level = self.candidate_graph[graph_counter]
        
        for candidate_id, entry in last_graph_level.items():
            if entry['total_probability'] >= highest_prob:
                highest_prob = entry['total_probability']
                id = candidate_id
        
        #add the last vertex of the path
        last_graph_level_entry = self.candidate_graph[graph_counter][id]
        viterbi_path.insert(0, {'vertex': last_graph_level_entry["candidate"],
                                'total_probability': highest_prob,
                            'emitted_probability': last_graph_level_entry["candidate"].getEmissionProbability(self.observation_measurements.getStandardDeviation(), 0.0),
                            'transition_probability': last_graph_level_entry['transition_probability'],
                            'observation_id': last_graph_level_entry["candidate"].observation_id
                            })
        
        #now find all parents of this vertex/candidate
        graph_counter -= 1
        current_id = self.candidates_backtracking[id]
        while(current_id is not None and graph_counter >= 0):
            searched_graph_level_entry = self.candidate_graph[graph_counter][current_id]
            viterbi_path.insert(0, {'vertex': searched_graph_level_entry["candidate"],
                                    'total_probability': searched_graph_level_entry['total_probability'],
                                    'emitted_probability': searched_graph_level_entry["candidate"].getEmissionProbability(self.observation_measurements.getStandardDeviation(), 0.0),
                                    'transition_probability': searched_graph_level_entry['transition_probability'],
                                    'observation_id': searched_graph_level_entry["candidate"].observation_id
                                    })
            #preparation for the next iteration
            if current_id in self.candidates_backtracking:
                current_id = self.candidates_backtracking[current_id]
            
            graph_counter -= 1
        
        return viterbi_path
    
    def setTransitions(self, fast_map_matching=False):
        #init progressbar
        self.initProgressbar(len(self.trajectory.observations))
        
        for i, observation in enumerate(self.trajectory.observations):
            
            #skip the first observation, because first observation has no parent
            if i != 0:
                
                #get the current and previous graph level
                previous_graph_level = self.candidate_graph[i - 1]
                current_graph_level = self.candidate_graph[i]
                
                for previous_id, previous_entry in previous_graph_level.items():
                    
                    for current_id, current_entry in current_graph_level.items():
                        
                        #get the candidates
                        current_candidate = current_entry["candidate"]
                        previous_candidate = previous_entry["candidate"]
                        
                        #create a new transition
                        transition = None
                        if fast_map_matching is True:
                            transition = Transition(previous_candidate, current_candidate, self.network, False, True)
                        else:
                            transition = Transition(previous_candidate, current_candidate, self.network, self.candidatesHaveDifferentPositions(current_candidate, previous_candidate))
                        
                        #calculate the probabilities of the transition
#                        transition.setDirectionProbability(self.trajectory.observations[i - 1], observation)
#                        transition.setRoutingProbability(observation.point.distance(self.trajectory.observations[i - 1].point), beta)
#                        transition.setTransitionProbability()
                        
                        #calculate the difference of the distances between candidates and observations
                        transition_length = transition.getLengthOfTransition()
                        observation_distance = math.sqrt(math.pow(observation.point.asPoint().x() - self.trajectory.observations[i - 1].point.asPoint().x(), 2) + math.pow(observation.point.asPoint().y() - self.trajectory.observations[i - 1].point.asPoint().y(), 2))
                        self.transition_measurements.addMeasurement(abs(transition_length - observation_distance))
                        
                        #insert the transition into the graph
#                        current_entry['transition_probabilities'] = {previous_id : transition.transition_probability}
                        current_entry['transition_probabilities'] = {previous_id : transition}

            self.updateProgressbar()
            
        return 0
    
    def candidatesHaveDifferentPositions(self, candidate_1, candidate_2):
        #get coordinates of the previous entry and the current candidate
        x_candidate_1 = candidate_1.point.asPoint().x()
        y_candidate_1 = candidate_1.point.asPoint().y()
        x_candidate_2 = candidate_2.point.asPoint().x()
        y_candidate_2 = candidate_2.point.asPoint().y()
                        
        #if points are not equal, return True, otherwise False
        if x_candidate_1 != x_candidate_2 or y_candidate_1 != y_candidate_2:
            return True
        else:
            return False

    def setStartingProbabilities(self):
        first_graph_level = self.candidate_graph[0]
        
        #init progressbar
        self.initProgressbar(len(first_graph_level))
        
        for id, entry in first_graph_level.items():
            entry['total_probability'] = entry['candidate'].getEmissionProbability(self.observation_measurements.getStandardDeviation(), 0.0)
            self.candidates_backtracking[id] = None
            
            self.updateProgressbar()
        
        return 0
    
    def addFeaturesToLayer(self, features, attributes, crs):
        #create a new layer
        layer = QgsVectorLayer('LineString?crs=' + crs + '&index=yes', 'matched trajectory', 'memory')
        
        #load the layer style
        dir = os.path.dirname(__file__)
        filename = os.path.abspath(os.path.join(dir, '..', '..', 'style.qml'))
        layer.loadNamedStyle(filename, loadFromLocalDb=False)
        
        #add the layer to the project
        layer.startEditing()
        layer_data = layer.dataProvider()
        layer_data.addAttributes(attributes)
        layer.updateFields()
        
        #add features to the layer
        layer.addFeatures(features)
        layer.commitChanges()
    
        #add the layer to the map
        QgsProject.instance().addMapLayer(layer)
        
        return layer
    
    def getPathOnNetwork(self, vertices, field_array):
        #init progressbar
        self.initProgressbar(len(vertices))
        
        #create an array to store all features
        features = []
        
        #iterate over the vertices
        for i, vertex in enumerate(vertices):
            
            #if we are in the first loop, we skip them because we have no previous point to create a routing with start and end
            if i != 0:
                
                #check, whether the two current candidates share the same position or not
                if self.candidatesHaveDifferentPositions(vertices[i - 1]['vertex'], vertex['vertex']) == False:
                    self.updateProgressbar()
                    continue
                
                #get all edges of the graph/network along the shortest way from the previous to the current vertex
                points = self.network.routing(vertices[i - 1]['vertex'].point.asPoint(), vertex['vertex'].point.asPoint())
                
                if points == -1:
                    return points
                
                #now create a new line feature and add all needed fields
                fields = QgsFields()
                for field in field_array:
                    fields.append(field)
                feature = QgsFeature(fields)
                
                #create the geometry of the new feature
                feature.setGeometry(QgsGeometry.fromPolylineXY(points))
                
                #insert the attributes and add the feature to the layer
                feature.setAttribute('id', i)
                feature.setAttribute('total_probability_start', vertices[i - 1]['total_probability'])
                feature.setAttribute('total_probability_end', vertex['total_probability'])
                feature.setAttribute('emission_probability_start', vertices[i - 1]['emitted_probability'])
                feature.setAttribute('emission_probability_end', vertex['emitted_probability'])
                feature.setAttribute('transition_probability', vertices[i - 1]['transition_probability'])
                feature.setAttribute('observation_id_start', vertices[i - 1]['observation_id'])
                feature.setAttribute('observation_id_end', vertex['observation_id'])
                features.append(feature)
            
            self.updateProgressbar()
        
        return features
    
    def initProgressbar(self, maximum):
        if self.pb is not None:
            self.pb.setValue(0)
            self.pb.setMaximum(maximum)
            QApplication.processEvents()
    
    def updateProgressbar(self):
        if self.pb is not None:
            self.pb.setValue(self.pb.value() + 1)
            QApplication.processEvents()
    
