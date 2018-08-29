from PyQt5.QtWidgets import QProgressBar, QComboBox, QLabel, QApplication
from qgis.core import *
from .hidden_states.hidden_model import *
from .observation.network import *
from .observation.trajectory import *

class MapMatcher:
    
    def __init__(self):
        self.layers = []
        self.attributes = []
        self.hidden_model = None
        self.network = None
        self.trajectoy = None
    
    def startViterbiMatchingGui(self, pb, trajectory_name, network_name, attribute_name, sigma, my, max_dist, label, crs):
        check_results = 0
        
        label.setText('initialise data structur')
        QgsMessageLog.logMessage('initialise data structur', level=Qgis.Info)
        self.setUp(network_name, trajectory_name, attribute_name, pb)
        
        label.setText('create candidate graph')
        QgsMessageLog.logMessage('create candidate graph', level=Qgis.Info)
        check_results = self.hidden_model.createGraph(sigma, my, max_dist)
        if check_results != 0:
            label.setText('cannot create candidate graph')
            QgsMessageLog.logMessage('cannot create candidate graph', level=Qgis.Info)
            return -1
        
        label.setText('calculate starting probabilities')
        QgsMessageLog.logMessage('calculate starting probabilities', level=Qgis.Info)
        check_results = self.hidden_model.setStartingProbabilities()
        if check_results != 0:
            label.setText('cannot calculate starting probabilities')
            QgsMessageLog.logMessage('cannot calculate starting probabilities', level=Qgis.Info)
            return -3
        
        
        label.setText('calculate transition probabilities')
        QgsMessageLog.logMessage('calculate transition probabilities', level=Qgis.Info)
        check_results = self.hidden_model.setTransitionProbabilities()
        if check_results != 0:
            label.setText('cannot calculate transition probabilities')
            QgsMessageLog.logMessage('cannot calculate transition probabilities', level=Qgis.Info)
            return -3
        
        
        label.setText('create backtracking')
        QgsMessageLog.logMessage('create backtracking', level=Qgis.Info)
        check_results = self.hidden_model.createBacktracking()
        if check_results != 0:
            label.setText('cannot create backtracking')
            QgsMessageLog.logMessage('cannot create backtracking', level=Qgis.Info)
            return -3
        
        
        label.setText('get most likely path')
        QgsMessageLog.logMessage('get most likely path', level=Qgis.Info)
        vertices = self.hidden_model.findViterbiPath()
        if len(vertices) == 0:
            QgsMessageLog.logMessage('Cannot get a most likely path. Try to change settings.', level=Qgis.Critical)
            label.setText('cannot get path')
            return -3
        
        label.setText('get network path')
        QgsMessageLog.logMessage('get network path', level=Qgis.Info)
        features = self.hidden_model.getPathOnNetwork(vertices, self.defineAttributes)
        if layer == -1:
            label.setText('cannot map trajectory')
            QgsMessageLog.logMessage('Routing between the result points, i.e. candidates with the highest total probability, does not work.', level=Qgis.Critical)
            return -5
        
        layer = self.hidden_model.addFeaturesToLayer(features, self.defineAttributes, crs)
        self.hidden_model.addLayerToTheMap(layer)
        layer.select([])
        QgsProject.instance().addMapLayer(layer)
        
        label.setText('finished ^o^')
        QgsMessageLog.logMessage('finished ^o^', level=Qgis.Info)
        return 0
    
    def startViterbiMatchingProcessing(self, trajectory_name, network_name, attribute_name, sigma, my, max_dist, feature_sink, feedback):
        check_results = 0
        total = 100.0 / 8
        current = 1
        
        QgsMessageLog.logMessage('initialise data structur', level=Qgis.Info)
        self.setUp(network_name, trajectory_name, attribute_name, None)
        feedback.setProgress(int(current * total))
        current += 1
        
        QgsMessageLog.logMessage('create candidate graph', level=Qgis.Info)
        check_results = self.hidden_model.createGraph(sigma, my, max_dist)
        feedback.setProgress(int(current * total))
        current += 1
        if check_results != 0:
            QgsMessageLog.logMessage('cannot create candidate graph', level=Qgis.Info)
            return -1
        
        QgsMessageLog.logMessage('calculate starting probabilities', level=Qgis.Info)
        check_results = self.hidden_model.setStartingProbabilities()
        feedback.setProgress(int(current * total))
        current += 1
        if check_results != 0:
            QgsMessageLog.logMessage('cannot calculate starting probabilities', level=Qgis.Info)
            return -3
        
        
        QgsMessageLog.logMessage('calculate transition probabilities', level=Qgis.Info)
        check_results = self.hidden_model.setTransitionProbabilities()
        feedback.setProgress(int(current * total))
        current += 1
        if check_results != 0:
            QgsMessageLog.logMessage('cannot calculate transition probabilities', level=Qgis.Info)
            return -3
        
        QgsMessageLog.logMessage('create backtracking', level=Qgis.Info)
        check_results = self.hidden_model.createBacktracking()
        feedback.setProgress(int(current * total))
        current += 1
        if check_results != 0:
            QgsMessageLog.logMessage('cannot create backtracking', level=Qgis.Info)
            return -3
        
        QgsMessageLog.logMessage('get most likely path', level=Qgis.Info)
        vertices = self.hidden_model.findViterbiPath()
        feedback.setProgress(int(current * total))
        current += 1
        if len(vertices) == 0:
            QgsMessageLog.logMessage('Cannot get a most likely path. Try to change settings.', level=Qgis.Critical)
            return -3
        
        QgsMessageLog.logMessage('get network path', level=Qgis.Info)
        features = self.hidden_model.getPathOnNetwork(vertices)
        feedback.setProgress(int(current * total))
        current += 1
        if layer == -1:
            QgsMessageLog.logMessage('Routing between the result points, i.e. candidates with the highest total probability, does not work.', level=Qgis.Critical)
            return -5
        
        feature_sink.addFeatures(features)
        feedback.setProgress(int(current * total))
        current += 1
        
        return 0
    
    def fillLayerComboBox(self, iface, combobox, geom_type):
        #first clear the combobox
        combobox.clear()
        
        #get all layers in the current QGIS project
        self.layers = []
        self.layers = iface.mapCanvas().layers()
        
        #populate the combobox
        for layer in self.layers:
            if (QgsWkbTypes.flatType(layer.wkbType()) == QgsWkbTypes.Point and geom_type == 'POINT') or (QgsWkbTypes.flatType(layer.wkbType()) == QgsWkbTypes.LineString and geom_type == 'LINESTRING'):
                combobox.addItem(layer.name())
    
    def fillAttributeComboBox(self, combobox, layername):
        #first clear the combobox
        combobox.clear()
        
        #extract all attributes
        layer = self.getLayer(layername)
        if layer is not None:
            self.attributes = layer.fields()
        
        #populate the combobox
        for attr in self.attributes:
            combobox.addItem(attr.name())
    
    def getLayer(self, layername):
        for layer in self.layers:
            if layer.name() == layername:
                return layer
        return None
    
    def setUp(self, line_layer, point_layer, point_attr, pb):
        if type(line_layer) is str:
            self.network = Network(self.getLayer(line_layer))
        else:
            self.network = Network(line_layer)
        
        
        if type(line_layer) is str:
            self.trajectory = Trajectory(self.getLayer(point_layer), point_attr)
        else:
            self.trajectory = Trajectory(point_layer, point_attr)
        
        self.hidden_model = HiddenModel(self.trajectory, self.network)
        self.hidden_model.pb = pb
    
    def defineAttributes(self):
        attributes = [QgsField('id', QVariant.Int),
                      QgsField('total_probability_start', QVariant.Double),
                      QgsField('total_probability_end', QVariant.Double),
                      QgsField('emission_probability_start', QVariant.Double),
                      QgsField('emission_probability_end', QVariant.Double),
                      QgsField('transition_probability_start', QVariant.Double),
                      QgsField('transition_probability_end', QVariant.Double),
                      QgsField('observation_id_start', QVariant.Int),
                      QgsField('observation_id_end', QVariant.Int)]
        return attributes
    
