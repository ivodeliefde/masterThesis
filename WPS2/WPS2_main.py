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
            abstract="""This process takes a sensor data request and finds all relevant sensor data sources on the semantic web. These sources will be automatically integrated and aggregated.""",
            version = "1.0",
            storeSupported = True,
            statusSupported = True)

        #----------------------------------------------------------------------#
        # Adding process inputs
        #----------------------------------------------------------------------#

        # have to add the input parameters here
        self.textIn = self.addLiteralInput(identifier="text",
                    title = "Input Key Value Pairs containing the spatial feature, the type of sensor data, the temporal range and the aggregation method")

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
        observedProperties = ['http://dbpedia.org/resource/Nitrogen_dioxide']
        featureCategory = 'Province'
        featureNames = ['Utrecht']
        tempRange = ['2016-01-04T09:42:47.151000', '2016-02-04T09:42:47.151000']
        # tempGranularity = 
        spatialAggregation = ['average']
        tempAggregation = ['average']
        #----------------------------------------------------------------------------#
        # Create Request instance
        dataRequest = Request(observedProperties, featureCategory, featureNames, tempRange, spatialAggregation, tempAggregation)

        # Make SPARQL queries that find the relevant feature geometries
        dataRequest.getGeometries()

        # Make SPARQL queries that find the sensors that are within the feature geometries with one of the three methods
        # getSensorsVector()
        # getSensorsBBOX()
        dataRequest.getSensorsRaster()

        # # Make SOS queries for every found data source to retrieve data for all found sensors
        dataRequest.getObservationData()

        # # Check if aggregation method is valid
        # dataRequest.aggregateCheck()

        # # Aggregate sensor data
        # dataRequest.aggregate()

        # # Output aggregated sensor data
        # self.textOut.setValue( 'The WPS has finished' ) # have to be replaced with sensor data output

        return

if (__name__ == "__main__"):
    Process = Process()
    Process.execute()