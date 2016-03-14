from pywps.Process import WPSProcess

from observedPropertyMapping import *
from sosRequests import *
from linkedDataCapabilities import *


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
                                            title = "Input a string containing an HTTP address of a Sensor Observation Service (SOS). For example: 'http://someaddress.com/sos?'",
                                            default = "http://sos.irceline.be/sos?",
                                            type = "StringType")

        self.mappingIn = self.addComplexInput(identifier="input",
                        title="Input file",
                        abstract="Input RDF file, in turtle notation",
                        # default = "H:\Ivo\Geomatics\Year 2\Thesis\Thesis Template\WPS1\observedPropertyMapping.ttl" 
                        # formats = [ # Turtle
                        #             {mimeType: 'text/turtle',
                        #             encoding:'utf-8',
                        #             schema: None } 
                        #           ] 
                        
                                )
                        
                       
                    
                    
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
        mappingscript = self.mappingIn.getValue()

        # Test mappingScript file
        # mappingscript = "file///H:\Ivo\Geomatics\Year 2\Thesis\Thesis Template\WPS1\observedPropertyMapping.ttl"

        sendMappingScriptToEndpoint(mappingscript)
       
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