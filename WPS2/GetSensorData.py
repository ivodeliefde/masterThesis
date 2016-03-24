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
                                            default='raster',
                                            type = "StringType")

        self.outputFormat = self.addLiteralInput(identifier = "outputFormat",
                                            title = "Select XML or GeoJSON as output format", 
                                            default='XML',
                                            type = "StringType")


        #----------------------------------------------------------------------#
        # Adding process outputs
        #----------------------------------------------------------------------#

        self.XMLdataOut = self.addComplexOutput(identifier="output_XML",
                title="Output sensor data in XML format",
                formats =  [{
                    'mimeType':'text/xml',
                    # 'schema': None
                    }]
                )

        self.GeoJSONdataOut = self.addComplexOutput(identifier="output_GeoJSON",
                title="Output sensor data in GeoJSON format",
                formats =  [{'mimeType':'text/json'}])

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
        method = '' # not a relevant class parameter for this WPS 
        sensors = self.sensors.getValue()
        outputFormat = self.outputFormat.getValue()
        #----------------------------------------------------------------------------#
        
        # Create Request instance
        # observedProperties, featureCategory, featureNames, tempRange, tempGranularity, spatialAggregation, tempAggregation = self.data
        dataRequest = Request(observedProperties, featureCategory, featureNames, tempRange, tempGranularity, spatialAggregation, tempAggregation)

        dataRequest.sensorFile = open("H:\Ivo\Geomatics\Year 2\Thesis\ThesisGitHub\WPS2\pywpsOutputsja3hs","r")

        # Make SPARQL queries that find the relevant feature geometries
        dataRequest.getGeometries()

        # transform the input GeoJSON string into python dictionary
        dataRequest.GeoJSONTosensors()

        # return

        # Make SOS queries for every found data source to retrieve data for all found sensors
        dataRequest.getObservationData()
            
        # # Check if aggregation method is valid
        # # dataRequest.aggregateCheck()

        # # Aggregate sensor data
        dataRequest.aggregateTemporal()

        if spatialAggregation.lower() != 'false':
            dataRequest.aggregateSpatial()

        # Create output XML file
        dataRequest.createOutput(outputFormat)

        # Output aggregated sensor data
        if outputFormat == '':
            self.XMLdataOut.setValue( dataRequest.outputFile )
        else:
            self.GeoJSONdataOut.setValue( dataRequest.outputFile )
        
        return 


if (__name__ == "__main__"):
    Process = Process()
    Process.execute()