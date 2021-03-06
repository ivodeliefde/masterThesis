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
            abstract="""This process takes sensors found by the WPS 'GetSensors' and automatically integrates and aggregates the data from different sources on the web.""",
            version = "1.0",
            storeSupported = True,
            statusSupported = True)

        #----------------------------------------------------------------------#
        # Adding process inputs
        #----------------------------------------------------------------------#

        self.InputFeatures = self.addLiteralInput(identifier = "feature_names",
                                            title = "Input feature name strings, seperated by comma's", 
                                            default="100kmE39N31",
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
                                            default='raster',
                                            type = "StringType")

        self.InputTempGranularity = self.addLiteralInput(identifier = "temporal_granularity",
                                            title = "Input temporal granularity as an integer followed by a temporal unit: minute, hour, day or week", 
                                            default='1 day',
                                            type = "StringType")

        self.InputTempAggregation = self.addLiteralInput(identifier = "temporal_aggregation",
                                            title = "Input temporal aggregation method: average, median, maximum, minimum or sum", 
                                            default='average',
                                            type = "StringType")

        self.InputSpatialAggregation = self.addLiteralInput(identifier = "spatial_aggregation",
                                            title = "Input spatial aggregation method: average, median, maximum, minimum or sum. Set it to False for no spatial aggregation.", 
                                            default='average',
                                            type = "StringType")

        self.sensors = self.addLiteralInput(identifier = "Sensors",
                                            title = "Sensors to be queried and temporally (and spatially) aggregated", 
                                            default=' ',
                                            type = "StringType")

        self.outputFormat = self.addLiteralInput(identifier = "outputFormat",
                                            title = "Select XML or GeoJSON as output format", 
                                            default='GeoJSON',
                                            type = "StringType")


        #----------------------------------------------------------------------#
        # Adding process outputs
        #----------------------------------------------------------------------#

        self.dataOut = self.addComplexOutput(identifier="output_data",
                title="Output sensor data",
                formats =  [{
                    'mimeType':'text/xml',
                    'mimeType':'text/json'
                    # 'schema': None
                    }]
                )

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
        sensors = self.sensors.getValue()
        outputFormat = self.outputFormat.getValue()
        #----------------------------------------------------------------------------#
        
        # Create Request instance
        # observedProperties, featureCategory, featureNames, tempRange, tempGranularity, spatialAggregation, tempAggregation = self.data
        dataRequest = Request(observedProperties, featureCategory, featureNames, tempRange, tempGranularity, spatialAggregation, tempAggregation, sensors)

        # dataRequest.sensorFile = "H:\Ivo\Geomatics\Year 2\Thesis\ThesisGitHub\WPS2\pywpsOutputsja3hs"
        # dataRequest.sensorFile = "http://localhost:5000/static/uploads/sensors_1.json"

        # Make SPARQL queries that find the relevant feature geometries
        dataRequest.getGeometries()

        # transform the input GeoJSON string into python dictionary
        dataRequest.GeoJSONTosensors()

        # Make SOS queries for every found data source to retrieve data for all found sensors
        dataRequest.getObservationData()
            
        # Check if aggregation method is valid
        # dataRequest.aggregateCheck()

        # Aggregate sensor data
        dataRequest.aggregateTemporal()

        if spatialAggregation.lower() != 'false':
            dataRequest.aggregateSpatial()

        # Create output XML file
        dataRequest.createOutput(outputFormat)

        # Output aggregated sensor data
        self.dataOut.setValue( dataRequest.outputFile )

        # print dataRequest.outputFile
        
        return 


if (__name__ == "__main__"):
    Process = Process()
    Process.execute()