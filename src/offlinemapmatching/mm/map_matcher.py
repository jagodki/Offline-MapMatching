from PyQt5.QtWidgets import QProgressBar, QComboBox, QLabel
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
    
    def startViterbiMatching(self, pb, trajectory_name, network_name, attribute_name, sigma, my, max_dist, label):
        label.setText("1/3: set up the hidden model")
        self.setUp(network_name, trajectory_name, attribute_name)
        
        label.setText("2/3: start search for viterbi path")
        vertices = self.hidden_model.findViterbiPath(max_dist, sigma, my, pb)
        
        label.setText("3/3: get network path")
        layer = self.hidden_model.getPathOnNetwork(vertices, pb)
        
        layer.select([])
        QgsProject.instance().addMapLayer(layer)
        label.setText("finished ^o^")
    
    def startDijkstraMatching(self, pb, trajectory_name, network_name, sigma, my, host, port, database, user, password, label, crs):
        label.setText("1/3: set up the hidden model")
        self.setUp(network_name, trajectory_name, attribute_name)
        
        label.setText("2/3: start search for dijkstra path")
        vertices = self.hidden_model.findDijkstraPath(host, port, database, user, password, crs, pb)
        
        label.setText("3/3: get network path")
        layer = self.hidden_model.getPathOnNetwork(vertices, pb)
        
        layer.select([])
        QgsProject.instance().addMapLayer(layer)
        label.setText("finished ^o^")
    
    def fillLayerComboBox(self, iface, combobox, geom_type):
        #first clear the combobox
        combobox.clear()
        
        #get all layers in the current QGIS project
        self.layers = []
        self.layers = iface.mapCanvas().layers()
        
        #populate the combobox
        for layer in self.layers:
            if (layer.wkbType() == QgsWkbTypes.Point and geom_type == "POINT") or (layer.wkbType() == QgsWkbTypes.LineString and geom_type == "LINESTRING"):
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
    
    def setUp(self, line_layer, point_layer, point_attr):
        self.trajectory = Trajectory(self.getLayer(point_layer), point_attr)
        self.network = Network(self.getLayer(line_layer))
        self.hidden_model = HiddenModel(self.trajectory, self.network)
    
    
