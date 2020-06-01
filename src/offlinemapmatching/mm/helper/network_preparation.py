from qgis.core import *
import processing
from PyQt5.QtCore import QVariant

class NetworkPreparation:
    
    def __init__(self, network):
        self.network = network
    
    def createLinesWithOnlyTwoVertices(self, feedback=None):
        
        #split the lines to get vertices on each intersection
        if feedback is not None:
            feedback.pushInfo('split lines')
        
        result_split = processing.run("native:splitwithlines", {
            'INPUT': self.network,
            'LINES': self.network,
            'OUTPUT': 'memory:split'
        })
        
        #create single geometries
        if feedback is not None:
            feedback.pushInfo('create single geometries')
        
        result_single = processing.run("native:multiparttosingleparts", {
            'INPUT': result_split['OUTPUT'],
            'OUTPUT': 'memory:single'
        })
        
        #now create a new layer and its fields
        vl = QgsVectorLayer('LineString?crs=' + self.network.crs().authid() + '&index=yes', 'Ripped up Lines', 'memory')
        
        field_array = [
            QgsField('line_id', QVariant.Int),
            QgsField('original_line_fid', QVariant.Int)
        ]
        
        fields = QgsFields()
        for field in field_array:
            fields.append(field)
        
        #add the fields to the new layer
        vl.startEditing()
        vl_data = vl.dataProvider()
        vl_data.addAttributes(fields)
        vl.updateFields()
        
        #now iterate over all single geometries and rip them up
        if feedback is not None:
            feedback.pushInfo('rip up network')
            feedback.setProgress(0)
        
        id_counter = 0
        feature_count = result_single['OUTPUT'].featureCount()
        for index, feature in enumerate(result_single['OUTPUT'].getFeatures()):
            
            #get the vertices of the current feature
            vertices = feature.geometry().asPolyline()
            
            #iterate over the vertices to create new linestring features
            last_vertex = None
            for index_2, vertex in enumerate(vertices):
                if last_vertex is not None:
                    
                    #create the new feature
                    new_feature = QgsFeature(fields)
                    new_feature.setAttribute('line_id', id_counter)
                    new_feature.setAttribute('original_line_fid', feature.id())
                    new_feature.setGeometry(QgsGeometry.fromPolylineXY([last_vertex, vertex]))
                    
                    #add the new feature to the target layer and increase the id counter
                    vl.addFeature(new_feature)
                    id_counter += 1
                    
                #update the last vertex for the next iteration step
                last_vertex = vertex
            
            #update the progressbar
            if feedback is not None:
                feedback.setProgress(int((index / feature_count) * 100))
        
        #commit the changes and return the layer
        vl.commitChanges()
        return vl
    