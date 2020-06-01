import statistics

class MeasurementStatistics:
    
    def __init__(self):
        self.measurments = []
    
    def addMeasurement(self, value):
        self.measurments.append(value)
    
    def getMeanValue(self):
        return statistics.mean(self.measurments)
    
    def getStandardDeviation(self):
        return statistics.stdev(self.measurments)
    
    