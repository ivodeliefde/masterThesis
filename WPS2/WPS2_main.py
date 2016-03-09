from pywps.Process import WPSProcess
from datetime import datetime
from requestClass import *

class Process(WPSProcess):


    def __init__(self):

        #----------------------------------------------------------------------#
        # Process initialization
        #----------------------------------------------------------------------#

        WPSProcess.__init__(self,
            identifier = "GetSensorData",
            title="Automatically retrieves, integrates and aggregates heterogenous sensor data using the semantic web",
            abstract="""This process takes a sensor data request and finds all relevant sensor data sources on the semantic web. Data from these sources will be automatically retrieved, integrated and aggregated.""",
            version = "1.0",
            storeSupported = True,
            statusSupported = True)

        #----------------------------------------------------------------------#
        # Adding process inputs
        #----------------------------------------------------------------------#

        # have to add the input parameters here
        self.data = self.addComplexInput(identifier = "data",
                                            title = " An xml document with input parameters: observedProperties, featureCategory, featureNames, tempRange, tempGranularity, spatialAggregation, tempAggregation")

        #----------------------------------------------------------------------#
        # Adding process outputs
        #----------------------------------------------------------------------#

        # have to add the output parameters here
        self.textOut = self.addLiteralOutput(identifier = "text",
                title="Output processed sensor data")

    #--------------------------------------------------------------------------#
    # Execution part of the process
    #--------------------------------------------------------------------------#

    def execute(self):
        # receive the Request parameters
        inputString = self.textIn.getValue() # should be replaced with request input parameters
        

        #----------------------------------------------------------------------------#
        # Test data
        #----------------------------------------------------------------------------#
        # observedProperties = ['http://dbpedia.org/resource/Nitrogen_dioxide']
        # featureCategory = 'Province'
        # featureNames = ["Antwerpen"]
        # tempRange = ['2016-01-04T09:42:47.151000', '2016-01-05T09:42:47.151000']
        # tempGranularity = '2 hours'
        # spatialAggregation = 'average'
        # tempAggregation = 'average'
        #----------------------------------------------------------------------------#
        
        # Create Request instance
        observedProperties, featureCategory, featureNames, tempRange, tempGranularity, spatialAggregation, tempAggregation = self.data
        dataRequest = Request(observedProperties, featureCategory, featureNames, tempRange, tempGranularity, spatialAggregation, tempAggregation)

        # Make SPARQL queries that find the relevant feature geometries
        dataRequest.getGeometries()

        # Make SPARQL queries that find the sensors that are within the feature geometries with one of the three methods
        # getSensorsVector()
        # getSensorsBBOX()
        dataRequest.getSensorsRaster()

        # Make SOS queries for every found data source to retrieve data for all found sensors
        dataRequest.getObservationData()

        # # Check if aggregation method is valid
        # dataRequest.aggregateCheck()

        # # Aggregate sensor data
        # dataRequest.aggregateTemporal()

        # # Output aggregated sensor data
        # self.textOut.setValue( 'The WPS has finished' ) # have to be replaced with sensor data output

        return

if (__name__ == "__main__"):
    Process = Process()
    Process.execute()