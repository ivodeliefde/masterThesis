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
        self.urlIn = self.addLiteralInput(identifier = "spatial_aggregation",
                                            title = "Input a string containing an HTTP address of a Sensor Observation Service (SOS). For example: 'http://someaddress.com/sos?'"
                                            type = "StringType")
                    
        #----------------------------------------------------------------------#
        # Adding process outputs
        #----------------------------------------------------------------------#

        self.textOut = self.addLiteralOutput(identifier = "text",
                title="Output literal data")

    #--------------------------------------------------------------------------#
    # Execution part of the process
    #--------------------------------------------------------------------------#

    def execute(self):


        url = self.urlIn.getValue()
       
        # url = 'http://sos.irceline.be/sos?' # test URL
        sos = SOS(url)
        # sos.store()

#       Test input from pickle
        # sos = pickle.load(open( "SOS of IRCEL - CELINE.p", "rb") )

        # sos.printInformation()
        # print sos.featureofinterest
        # make linked data from the data retrieved above
        capabilities(sos)


        # url = 'http://inspire.rivm.nl/sos/eaq/service?'
        # sos = SOS(url)
        # sos.store()

#       Test input from pickle
        # sos = pickle.load(open( "RIVM SOS Service Air Quality.p", "rb") )

        # sos.printInformation()
        # print sos.featureofinterest
        # make linked data from the data retrieved above
        # capabilities(sos)



        self.textOut.setValue( 'The WPS has finished' )

        return

if (__name__ == "__main__"):
    Process = Process()
    Process.execute()