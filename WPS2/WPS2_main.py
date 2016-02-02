from pywps.Process import WPSProcess


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

        # Make SPARQL queries that finds the relevant sensors via: observed properties -> collections of features of interest (with locations) -> sensors (with SOS HTTP addresses)


        # Make SOS queries for every found data source to retrieve data for all found sensors


        # integrate the sensor data


        # Check if aggregation method is valid


        # Aggregate sensor data


        # Output aggregated sensor data
        self.textOut.setValue( 'The WPS has finished' ) # have to be replaced with sensor data output

        return

if (__name__ == "__main__"):
    Process = Process()
    Process.execute()