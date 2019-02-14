from ..observation.network import *
from ..observation.trajectory import *
from ..observation.observation import *
from .candidate import *
from .transition import *
from qgis.core import *
import os
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
        self.pb = None
    
    def createGraph(self, sigma, my, maximum_distance):
        #init progressbar
        self.initProgressbar(len(self.trajectory.observations))
        
        #init data structur
        self.candidate_graph = []
        self.candidates = {}
        self.counter_candidates = 0
        
        #iterate over all observations from our trajectory
        for observation in self.trajectory.observations:
            
            #extract all candidates of the current observation
            candidates = observation.getCandidates(self.network.vector_layer, maximum_distance)
            if len(candidates) == 0:
                QgsMessageLog.logMessage('could not find any candidates for trajectory point ' + str(observation.id), level=Qgis.Info)
                return -5
            else:
                #create the current level of the graph
                current_graph_level = []
                for candidate in candidates:
                    candidate.calculateEmissionProbability(observation, sigma, my)
                    current_graph_level.append({'id' : str(self.counter_candidates),
                                                  'observation_id' : observation.id,
                                                  'emitted_probability' : candidate.emission_probability,
                                                  'transition_probabilities' : {},
                                                  'transition_probability' : 0.0,
                                                  'curvature_probability' : 0.0,
                                                  'total_probability' : 0.0})
                    self.candidates.update({str(self.counter_candidates) : candidate})
                    self.counter_candidates += 1
                
                #normalise the probabilities and add the current graph level to the graph
                self.candidate_graph.append(current_graph_level)
            
            #update progressbar
            self.updateProgressbar()
        
        return 0
    
    def getCandidateById(self, id, level):
        for entry in self.candidate_graph[level]:
            if entry.get('id') == id:
                return entry
    
    def createBacktracking(self):
        #init progressbar
        self.initProgressbar(len(self.candidate_graph))
        
        self.candidates_backtracking = {}
        
        for i, graph_level in enumerate(self.candidate_graph):
            
            #the candidates of the first observation have no parent
            if i != 0:
                for entry in graph_level:
                    
                    #get all transition probabilities of the current entry and iterate over them to find the highest total probability
                    transition_probabilities = entry.get('transition_probabilities')
                    for key, value in transition_probabilities.items():
                        current_total_probability = value * entry.get('emitted_probability') * self.getCandidateById(key, i - 1).get('total_probability')
                        if current_total_probability > entry.get('total_probability'):
                            entry.update({'total_probability' : current_total_probability})
                            entry.update({'transition_probability' : value})
                            self.candidates_backtracking.update({entry.get('id') : key})
            
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
        for entry in last_graph_level:
            if entry.get('total_probability') >= highest_prob:
                highest_prob = entry.get('total_probability')
                id = entry.get('id')
        
        #add the last vertex of the path
        last_candidate = self.getCandidateById(id, graph_counter)
        viterbi_path.insert(0, {'vertex': self.candidates.get(id),
                                'total_probability': highest_prob,
                                'emitted_probability': last_candidate.get('emitted_probability'),
                                'transition_probability': last_candidate.get('transition_probability'),
                                'observation_id': last_candidate.get('observation_id')})
        
        #now find all parents of this vertex/candidate
        graph_counter -= 1
        current_id = self.candidates_backtracking.get(id)
        while(current_id is not None and graph_counter >= 0):
            searched_candidate = self.getCandidateById(current_id, graph_counter)
            viterbi_path.insert(0, {'vertex': self.candidates.get(current_id),
                                    'total_probability': searched_candidate.get('total_probability'),
                                    'emitted_probability': searched_candidate.get('emitted_probability'),
                                    'transition_probability': searched_candidate.get('transition_probability'),
                                    'observation_id': searched_candidate.get('observation_id')})
            current_id = self.candidates_backtracking.get(current_id)
            graph_counter -= 1
        
        return viterbi_path
    
    def setTransitionProbabilities(self, beta):
        #init progressbar
        self.initProgressbar(len(self.trajectory.observations))
        
        for i, observation in enumerate(self.trajectory.observations):
            
            #skip the first observation, because first observation has no parent
            if i != 0:
                
                #get the current and previous graph level
                previous_graph_level = self.candidate_graph[i - 1]
                current_graph_level = self.candidate_graph[i]
                
                for previous_entry in previous_graph_level:
                    
                    for current_entry in current_graph_level:
                        
                        #get the candidates
                        current_candidate = self.candidates.get(current_entry.get('id'))
                        previous_candidate = self.candidates.get(previous_entry.get('id'))
                        
                        #create a new transition
                        transition = Transition(previous_candidate, current_candidate, self.network, self.candidatesHaveDifferentPositions(current_candidate, previous_candidate))
                        
                        #calculate the probabilities of the transition
                        transition.setDirectionProbability(self.trajectory.observations[i - 1], observation)
                        transition.setRoutingProbability(observation.point.distance(self.trajectory.observations[i - 1].point), beta)
                        result = transition.setTransitionProbability()
                        
                        #insert the probability into the graph
                        if result == False: 
                            return -1
                        
                        current_entry.get('transition_probabilities').update({previous_entry.get('id') : transition.transition_probability})

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
        first_tellis_level = self.candidate_graph[0]
        
        #init progressbar
        self.initProgressbar(len(first_tellis_level))
        
        for entry in first_tellis_level:
            entry.update({'total_probability' : entry.get('emitted_probability')})
            self.candidates_backtracking.update({entry.get('id') : None})
            self.updateProgressbar()
        
        return 0
    
    def addFeaturesToLayer(self, features, attributes, crs):
        #create a new layer
        layer = QgsVectorLayer('LineString?crs=EPSG:' + crs + '&index=yes', 'matched trajectory', 'memory')
        
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
    
