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
    
    def startViterbiMatchingGui(self, pb, trajectory_name, network_name, attribute_name, sigma, my, beta, max_dist, label, crs):
        check_results = 0
        
        label.setText('initialise data structur...')
        QgsMessageLog.logMessage('initialise data structur...', level=Qgis.Info)
        self.setUp(network_name, trajectory_name, attribute_name, pb)
        
        label.setText('create candidate graph...')
        QgsMessageLog.logMessage('create candidate graph...', level=Qgis.Info)
        check_results = self.hidden_model.createGraph(sigma, my, max_dist)
        if check_results != 0:
            label.setText('error during calculation of candidates...')
            QgsMessageLog.logMessage('the maximum search distance is too low for one trajectory point point to find at least one candidate', level=Qgis.Info)
            return -1
        
        label.setText('calculate starting probabilities...')
        QgsMessageLog.logMessage('calculate starting probabilities...', level=Qgis.Info)
        check_results = self.hidden_model.setStartingProbabilities()
        if check_results != 0:
            label.setText('error during calculation of starting probabilities...')
            QgsMessageLog.logMessage('calculation of starting probabilities was not successfull, maybe an exception was thrown', level=Qgis.Info)
            return -2
        
        
        label.setText('calculate transition probabilities...')
        QgsMessageLog.logMessage('calculate transition probabilities...', level=Qgis.Info)
        check_results = self.hidden_model.setTransitionProbabilities(beta)
        if check_results != 0:
            label.setText('error during calculation of transition probabilities...')
            QgsMessageLog.logMessage('calculation of transition probabilities was not succesfull, have a look on the used parameters and the check the datasets', level=Qgis.Info)
            return -3
        
        
        label.setText('create backtracking...')
        QgsMessageLog.logMessage('create backtracking...', level=Qgis.Info)
        check_results = self.hidden_model.createBacktracking()
        if check_results != 0:
            label.setText('error during calculation of backtracking...')
            QgsMessageLog.logMessage('it was not able to create a complete backtracking, maybe the calculated probabilities are corrupt', level=Qgis.Info)
            return -4
        
        
        label.setText('get most likely path...')
        QgsMessageLog.logMessage('get most likely path...', level=Qgis.Info)
        vertices = self.hidden_model.findViterbiPath()
        if len(vertices) <= 1:
            label.setText('error during calculating the most likely path...')
            QgsMessageLog.logMessage('cannot calculate the most likely path, maybe backtracking went wrong, check your parameters', level=Qgis.Critical)
            return -5
        
        label.setText('get network path...')
        QgsMessageLog.logMessage('get network path...', level=Qgis.Info)
        features = self.hidden_model.getPathOnNetwork(vertices, self.defineAttributes())
        if features == -1:
            label.setText('error during calculating the path on network...')
            QgsMessageLog.logMessage('routing between the points of the most likely path does not work', level=Qgis.Critical)
            return -6
        
        layer = self.hidden_model.addFeaturesToLayer(features, self.defineAttributes(), crs)
        layer.select([])
        QgsProject.instance().addMapLayer(layer)
        
        label.setText('finished ^o^')
        QgsMessageLog.logMessage('finished ^o^', level=Qgis.Info)
        return 0
    
    def startViterbiMatchingProcessing(self, trajectory_name, network_name, attribute_name, sigma, my, beta, max_dist, feature_sink, feedback):
        check_results = 0
        total = 100.0 / 8
        current = 1
        
        QgsMessageLog.logMessage('initialise data structur...', level=Qgis.Info)
        self.setUp(network_name, trajectory_name, attribute_name, None)
        feedback.setProgress(int(current * total))
        current += 1
        
        QgsMessageLog.logMessage('create candidate graph...', level=Qgis.Info)
        check_results = self.hidden_model.createGraph(sigma, my, max_dist)
        feedback.setProgress(int(current * total))
        current += 1
        if check_results != 0:
            QgsMessageLog.logMessage('the maximum search distance is too low for one trajectory point point to find at least one candidate', level=Qgis.Info)
            return -1
        
        QgsMessageLog.logMessage('calculate starting probabilities...', level=Qgis.Info)
        check_results = self.hidden_model.setStartingProbabilities()
        feedback.setProgress(int(current * total))
        current += 1
        if check_results != 0:
            QgsMessageLog.logMessage('calculation of starting probabilities was not successfull, maybe an exception was thrown', level=Qgis.Info)
            return -2
        
        
        QgsMessageLog.logMessage('calculate transition probabilities...', level=Qgis.Info)
        check_results = self.hidden_model.setTransitionProbabilities(beta)
        feedback.setProgress(int(current * total))
        current += 1
        if check_results != 0:
            QgsMessageLog.logMessage('calculation of transition probabilities was not succesfull, have a look on the used parameters and the check the datasets', level=Qgis.Info)
            return -3
        
        QgsMessageLog.logMessage('create backtracking...', level=Qgis.Info)
        check_results = self.hidden_model.createBacktracking()
        feedback.setProgress(int(current * total))
        current += 1
        if check_results != 0:
            QgsMessageLog.logMessage('it was not able to create a complete backtracking, maybe the calculated probabilities are corrupt', level=Qgis.Info)
            return -4
        
        QgsMessageLog.logMessage('get most likely path...', level=Qgis.Info)
        vertices = self.hidden_model.findViterbiPath()
        feedback.setProgress(int(current * total))
        current += 1
        if len(vertices) == 0:
            QgsMessageLog.logMessage('cannot calculate the most likely path, maybe backtracking went wrong, check your parameters', level=Qgis.Critical)
            return -5
        
        QgsMessageLog.logMessage('get network path...', level=Qgis.Info)
        features = self.hidden_model.getPathOnNetwork(vertices, self.defineAttributes())
        feedback.setProgress(int(current * total))
        current += 1
        if features == -1:
            QgsMessageLog.logMessage('routing between the points of the most likely path does not work', level=Qgis.Critical)
            return -6
        
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
            #ignore raster layer, because just vector layers have a wkbType
            if layer.type() == 0:
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
                      QgsField('observation_id_start', QVariant.Int),
                      QgsField('observation_id_end', QVariant.Int),
                      QgsField('emission_probability_start', QVariant.Double),
                      QgsField('emission_probability_end', QVariant.Double),
                      QgsField('transition_probability', QVariant.Double),
                      QgsField('total_probability_start', QVariant.Double),
                      QgsField('total_probability_end', QVariant.Double)]
        return attributes
    
