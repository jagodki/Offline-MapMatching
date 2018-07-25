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
    
    def startViterbiMatching(self, pb, trajectory_name, network_name, attribute_name, sigma, my, max_dist, label, crs):
        label.setText('1/3: initialise data structur')
        QgsMessageLog.logMessage('initialise data structur', level=Qgis.Info)
        self.setUp(network_name, trajectory_name, attribute_name, pb)
        
        label.setText('2/3: start search for viterbi path')
        QgsMessageLog.logMessage('start search for viterbi path', level=Qgis.Info)
        vertices = self.hidden_model.findViterbiPath(max_dist, sigma, my, pb)
        
        if vertices == -5:
            QgsMessageLog.logMessage('The maximum search distance seems too low to find candidates for at least one position.', level=Qgis.Critical)
            label.setText('3/3: search distance is too low')
            return -5
        
        label.setText('3/3: get network path')
        QgsMessageLog.logMessage('get network path', level=Qgis.Info)
        layer = self.hidden_model.getPathOnNetwork(vertices, pb, 'EPSG:' + crs)
        
        if layer == -1:
            label.setText('3/3: cannot map trajectory')
            QgsMessageLog.logMessage('Routing between the result points, i.e. candidates with the highest probability, does not work.', level=Qgis.Critical)
            return -1
        
        layer.select([])
        QgsProject.instance().addMapLayer(layer)
        label.setText('finished ^o^')
        QgsMessageLog.logMessage('finished ^o^', level=Qgis.Info)
        return 0
    
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
    
    def setUp(self, line_layer, point_layer, point_attr, pb):
        #init progressbar
        pb.setValue(0)
        pb.setMaximum(3)
        QApplication.processEvents()
        
        self.trajectory = Trajectory(self.getLayer(point_layer), point_attr)
        pb.setValue(pb.value() + 1)
        QApplication.processEvents()
        
        self.network = Network(self.getLayer(line_layer))
        pb.setValue(pb.value() + 1)
        QApplication.processEvents()
        
        self.hidden_model = HiddenModel(self.trajectory, self.network)
        pb.setValue(pb.value() + 1)
        QApplication.processEvents()
    
    
