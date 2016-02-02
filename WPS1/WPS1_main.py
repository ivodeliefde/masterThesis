from pywps.Process import WPSProcess
from sosRequests import SOS
from linkedDataCapabilities import capabilities


# Load pickle for testing purposes
try:
    import cPickle as pickle
except:
    import pickle

class Process(WPSProcess):


    def __init__(self):

        #----------------------------------------------------------------------#
        # Process initialization
        #----------------------------------------------------------------------#

        WPSProcess.__init__(self,
            identifier = "LinkedDataFromSOS",
            title="Creates Linked Data of SOS metadata",
            abstract="""This process takes an HTTP address of a Sensor Observation Service (SOS) as input and converts the metadata to linked data.""",
            version = "1.0",
            storeSupported = True,
            statusSupported = True)

        #----------------------------------------------------------------------#
        # Adding process inputs
        #----------------------------------------------------------------------#

        self.textIn = self.addLiteralInput(identifier="text",
                    title = "Input a string containing an HTTP address of a Sensor Observation Service (SOS). For example: 'http://someaddress.com/sos?'")

        #----------------------------------------------------------------------#
        # Adding process outputs
        #----------------------------------------------------------------------#

        self.textOut = self.addLiteralOutput(identifier = "text",
                title="Output literal data")

    #--------------------------------------------------------------------------#
    # Execution part of the process
    #--------------------------------------------------------------------------#

    def execute(self):

#       Original input
        # url = self.textIn.getValue()
        # sos = SOS(url)

#       Test input
        sos = pickle.load(open( "RIVM SOS Service Air Quality.p", "rb") )

        sos.printInformation()

        # make linked data from the data retrieved above
        capabilities(sos)


        self.textOut.setValue( 'The WPS has finished' )

        return

if (__name__ == "__main__"):
    Process = Process()
    Process.execute()