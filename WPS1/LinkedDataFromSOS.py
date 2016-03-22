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
        self.urlIn = self.addLiteralInput(identifier = "input_url",
                                            title = "Input a string containing an HTTP address of a Sensor Observation Service (SOS). For example: 'http://someaddress.com/sos?'",
                                            default = "http://inspire.rivm.nl/sos/eaq/service?",
                                            type = "StringType")

        self.mappingIn = self.addComplexInput(identifier="input",
                        title="Input turtle file with mappings of observed property identifiers to DBPedia URIs",
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
        # mappingscript = self.mappingIn.getValue()


        # ------------------------#
        # Test mappingScript file #
        # ------------------------#
        mappingscript = "file:///H:\Ivo\Geomatics\Year 2\Thesis\ThesisGitHub\WPS1\observedPropertyMapping.ttl"
        # ------------------------#


        # Create semantic mapping between observed properties used in SOS and semantic 
        # definitions of observed properties
        sendMappingScriptToEndpoint(mappingscript)
       
        # Create SOS instance with the URL as input. This will automatically retrieve 
        # the required information from the SOS service 
        sos = SOS(url)

        # ------------------------#
        # Test input from pickle  #
        # ------------------------#
        # sos.store()
        # sos = pickle.load(open( "SOS of IRCEL - CELINE.p", "rb") )
        # sos.printInformation()
        # ------------------------#

        # Make linked data from the data retrieved above
        capabilities(sos)

        # Notify the client that the WPS has finished succesfully
        self.textOut.setValue( 'The WPS has finished succesfully for {0}'.format(url) )

        return

if (__name__ == "__main__"):
    Process = Process()
    Process.execute()