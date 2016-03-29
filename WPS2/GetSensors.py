from pywps.Process import WPSProcess

from requestClass import *


class Process(WPSProcess):


    def __init__(self):

        #----------------------------------------------------------------------#
        # Process initialization
        #----------------------------------------------------------------------#

        WPSProcess.__init__(self,
            identifier = "GetSensors",
            title="Automatically retrieves sensors from heterogenous sources using the semantic web",
            abstract="""This process takes a sensor data request with parameters for spatial features of interest, observed property, temporal range and granularity, and finds all relevant sensor data sources on the semantic web.""",
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

        self.method = self.addLiteralInput(identifier = "Query method",
                                            title = "Using vector queries, raster cells to the endpoint or sending direct bbox requests to the SOS", 
                                            default='raster',
                                            type = "StringType")




        #----------------------------------------------------------------------#
        # Adding process outputs
        #----------------------------------------------------------------------#

        self.SensorsOut = self.addComplexOutput(identifier="output",
                title="Output sensor data",
                formats= [{
                            # json
                            'mimeType': 'text/plain',
                            'encoding': 'iso-8859-2',
                            'schema': None
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
        method = self.method.getValue()
        #----------------------------------------------------------------------------#
        
        # # Create Request instance
        # # observedProperties, featureCategory, featureNames, tempRange, tempGranularity, spatialAggregation, tempAggregation = self.data
        dataRequest = Request(observedProperties, featureCategory, featureNames, tempRange, tempGranularity= '', spatialAggregation= '', tempAggregation= '', sensors= '')

        # Make SPARQL queries that find the relevant feature geometries
        dataRequest.getGeometries()

        # Make SPARQL queries that find the sensors that are within the feature geometries with one of the three methods
        if method.lower() == "vector":
            dataRequest.getSensorsVector()
        # elif method.lower() == "bbox":
            # Makes SOS requests with bounding box filter
        #     dataRequest.getSensorDataBBOX()
        else:
            dataRequest.getSensorsRaster()

        # make sensor output file in GeoJSON format
        dataRequest.sensorsToGeoJSON()

        self.SensorsOut.setValue( dataRequest.outputSensors )


        return 

if (__name__ == "__main__"):
    Process = Process()
    Process.execute()