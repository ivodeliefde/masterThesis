from pywps.Process import WPSProcess


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

        self.InputFeatures = self.addLiteralInput(identifier = "feature_names",
                                            title = "Input feature name strings, seperated by comma's", 
                                            default="Antwerpen,Utrecht",
                                            type = "StringType")

        self.InputObsProperties = self.addLiteralInput(identifier = "observed_properties",
                                            title = "Input DBPedia URIs of observed properties", 
                                            default="http://dbpedia.org/resource/Nitrogen_dioxide",
                                            type = "StringType")

        self.InputTempRange = self.addLiteralInput(identifier = "temporal_range",
                                            title = "Input start and end time in ISO format seperated by comma's", 
                                            default='2016-01-04T09:42:47.151000,2016-01-05T09:42:47.151000',
                                            type = "StringType")

        self.InputFeatureCategory = self.addLiteralInput(identifier = "feature_category",
                                            title = "Input feature category: municipality, province, raster or landcover", 
                                            default='Municipality',
                                            type = "StringType")

        self.InputTempGranularity = self.addLiteralInput(identifier = "temporal_granularity",
                                            title = "Input temporal granularity as an integer followed by a temporal unit: minute, hour, day or week", 
                                            default='1 hours',
                                            type = "StringType")

        self.InputTempAggregation = self.addLiteralInput(identifier = "temporal_aggregation",
                                            title = "Input temporal aggregation method: average, median, maximum, minimum or sum", 
                                            default='average',
                                            type = "StringType")

        self.InputSpatialAggregation = self.addLiteralInput(identifier = "spatial_aggregation",
                                            title = "Input spatial aggregation method: average, median, maximum, minimum or sum. Set it to False for no spatial aggregation.", 
                                            default='average',
                                            type = "StringType")

        self.method = self.addLiteralInput(identifier = "Query method",
                                            title = "Using vector queries, raster cells to the endpoint or sending direct bbox requests to the SOS", 
                                            default='raster',
                                            type = "StringType")


        #----------------------------------------------------------------------#
        # Adding process outputs
        #----------------------------------------------------------------------#

        self.dataOut = self.addComplexOutput(identifier="output",
                title="Output sensor data",
                formats =  [{'mimeType':'text/xml'}])

    #--------------------------------------------------------------------------#
    # Execution part of the process
    #--------------------------------------------------------------------------#

    def execute(self):
        #----------------------------------------------------------------------------#
        # Input data
        #----------------------------------------------------------------------------#
        observedProperties = self.InputObsProperties.getValue().split(',')
        featureCategory = self.InputFeatureCategory.getValue()
        featureNames = self.InputFeatures.getValue().split(',')
        tempRange = self.InputTempRange.getValue().split(',')
        tempGranularity = self.InputTempGranularity.getValue()
        spatialAggregation = self.InputSpatialAggregation.getValue()
        tempAggregation = self.InputTempAggregation.getValue()
        method = self.method.getValue()
        #----------------------------------------------------------------------------#
        
        # Create Request instance
        # observedProperties, featureCategory, featureNames, tempRange, tempGranularity, spatialAggregation, tempAggregation = self.data
        dataRequest = Request(observedProperties, featureCategory, featureNames, tempRange, tempGranularity, spatialAggregation, tempAggregation)

        # Make SPARQL queries that find the relevant feature geometries
        dataRequest.getGeometries()

        # Make SPARQL queries that find the sensors that are within the feature geometries with one of the three methods
        # The data is also automatically retrieved from the relevant Sensor Observation Services
        if method.lower() == "vector":
            dataRequest.getSensorDataVector()
        elif method.lower() == "bbox":
            dataRequest.getSensorDataBBOX()
        else:
            dataRequest.getSensorDataRaster()
            
        # # Check if aggregation method is valid
        # # dataRequest.aggregateCheck()

        # # Aggregate sensor data
        dataRequest.aggregateTemporal()

        if spatialAggregation.lower() != 'false':
            dataRequest.aggregateSpatial()

        # Create output XML file
        dataRequest.createOutput()
        # Output aggregated sensor data
        self.dataOut.setValue( dataRequest.outputFile )

        return 

if (__name__ == "__main__"):
    Process = Process()
    Process.execute()