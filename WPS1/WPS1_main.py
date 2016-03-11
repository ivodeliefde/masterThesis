# -*- coding: utf-8 -*-
import os
from rdflib import URIRef, BNode, Literal, Graph
from rdflib.namespace import RDF, RDFS, FOAF
import rdflib
import requests
from lxml import etree
from postPURLS import CreatePurls, postPURLbatch
import  progressbar

import logging
# logging.basicConfig(level=logging.INFO)
from pywps.Process import WPSProcess
# Load pickle for testing purposes
try:
    import cPickle as pickle
except:
    import pickle
# -*- coding: utf-8 -*-
import requests
from lxml import etree
from datetime import datetime, timedelta

try:
    import cPickle as pickle
except:
    import pickle

baseURI = "http://localhost:8099/masterThesis_tudelft" 
# endpoint = 'http://localhost:8089/parliament/sparql?' 
endpoint = "http://localhost:8083/strabon-endpoint-3.3.2-SNAPSHOT/Query"
purlBatch = 'D:/purlBatches/SOS/SOSbatch'

class SOS:

    def __init__(self, url, name="", organisation="", costs="", accessConstraints="", version=set(), resourceDescriptionFormat=set(), responseFormat=set()):
        self.error = False

        # Information that needs to be retrieved from the SOS
        self.name = name
        self.organisation = organisation
        self.costs = costs 
        self.accessConstraints = accessConstraints
        self.version = version
        self.resourceDescriptionFormat = resourceDescriptionFormat
        self.responseFormat = responseFormat 
        self.procedure = {} # contains dictionary instances with structure 'ID1': {'obsProperty1': {'offerings': [],  '...' ,'FOI': set() }, 'obsProperty2': {'offerings': [],  '...' ,'FOI': set() }  }
        self.featureofinterest = {} # contains dictionary instance with structure 'ID1': {'coords': [coords, crs], 'offerings': [] }

        
        # Check if the user input URL is correct
        url = self.checkURL(url)
        
        if url == False:
            return "The input URL is invalid. Could not create SOS instance"
        else:
            # Store the approved url
            self.url = url

        return self.Request()


    def checkURL(self, url):
        if type(url) != str:
            self.log("input URL is not of type string")
            try:
                url = str(url)
                self.log("Input URL converted to string")
            except:
                self.log("Could not convert input URL to string")
                return False

        if url[:4] != "http":
            self.log("Input URL is not an HTTP address")
            return False 

        self.log("URL '{0}' is valid".format(url))

        return url


    def Request(self):
        featureofinterest = {} # contains all the features of interest and their location
    
        #-------------------------------------------------------------------------------#
        # Get Capabilities --> find the general metadata and the offerings per procedure
        #-------------------------------------------------------------------------------#

        # Retrieve the GetCapabilities document
        GetCapabilities = '{0}service=SOS&request=GetCapabilities'.format(self.url)
        
        try:
            r = requests.get(GetCapabilities)
        except:
            self.log("Could not send the request: {0}".format(GetCapabilities))

        # Print the request URL
        self.log("Get request: {0}".format(GetCapabilities))
        print GetCapabilities

        # Store the retrieved document as an etree object
        tree = etree.fromstring(r.content)
        nsm = tree.nsmap

        # Check for errors
        if len(tree.findall('.//ows:Exception', nsm)) >= 1:
            print 'The server responded with an error message'
            error = etree.tostring(tree, pretty_print=True)
            self.log('ERROR url: {0} \n response:\n{1}'.format(GetCapabilities, etree.tostring(tree, pretty_print=True)))
            self.error = True
            return

        # Retrieving information from the capabilities document 
        self.costs = tree.find('.//ows:Fees', nsm).text
        self.name = tree.find('.//ows:Title', nsm).text
        self.accesConstraints = tree.find('.//ows:AccessConstraints', nsm).text
        self.organisation = tree.find('.//ows:ProviderName', nsm).text  
        # self.minTime = tree.find(".//ows:Parameter[@name='temporalFilter']/ows:AllowedValues/ows:Range/ows:MinimumValue", nsm).text
        
        versions = tree.findall('.//ows:ServiceTypeVersion', nsm)
        for version in versions:
            self.version.add(version.text)

        resourceDescriptionFormats = tree.findall('.//ows:Parameter[@name="procedureDescriptionFormat"]', nsm)
        for format in resourceDescriptionFormats:
            self.resourceDescriptionFormat.add(format.text)

        FOI = tree.find(".//ows:Operation[@name='GetObservation']/ows:Parameter[@name='featureOfInterest']/ows:AllowedValues", nsm)
        for feature in FOI:
            if feature.text in featureofinterest:
                print feature.text, 'already exists'
            else:
                self.featureofinterest[feature.text] = {}
        
        procedures = tree.find(".//ows:Operation[@name='GetObservation']/ows:Parameter[@name='procedure']/ows:AllowedValues", nsm)
        for procedure in procedures:
            self.procedure[procedure.text] = {}

        responseformat = tree.find(".//ows:Operation[@name='GetObservation']/ows:Parameter[@name='responseFormat']/ows:AllowedValues", nsm)
        for format in responseformat:
            self.responseFormat.add(format.text)

        contents = tree.findall(".//sos:ObservationOffering", nsm)
        for offering in contents:
            currentOffering = offering.find('.//swes:identifier', nsm).text
            obsProperty = offering.find('.//swes:observableProperty', nsm).text
            procedure = offering.find('.//swes:procedure', nsm).text

                    
            if obsProperty not in self.procedure[procedure]:
                self.procedure[procedure][obsProperty] = {'offerings': [], 'FOI': set()}
                # print 'Already:', self.procedure[procedure]['obsProperty']
                # print 'New:',obsProperty
                # print procedure
            self.procedure[procedure][obsProperty]['offerings'].append(currentOffering)
        # for each in self.procedure:
        #   print each, self.procedure[each]
        # return

        #-------------------------------------------------------------------------------#
        # GetFeatureOfInterest --> retrieve the features-of-interest per procedure
        #-------------------------------------------------------------------------------#
        

        GetFeatureOfInterest = '{0}service=SOS&version=2.0.0&request=GetFeatureOfInterest'.format(self.url)

        r = requests.get(GetFeatureOfInterest)
        
        tree = etree.fromstring(r.content)
        for section in tree:
            if 'exception' in section.tag.lower():  
                GetFeatureOfInterest += '&featureOfInterest=allFeatures'
                r = requests.get(GetFeatureOfInterest)
                tree = etree.fromstring(r.content)
                break

        nsm = tree.nsmap
            

        print GetFeatureOfInterest

        self.log("Get request: {0}".format(GetFeatureOfInterest))

        for featureMember in tree:
            currentFOI = False
            for info in featureMember:
                if 'sf_spatialsamplingfeature' in info.tag.lower():
                    for attributes in info:
                        if 'identifier' in attributes.tag.lower():
                            currentFOI = attributes.text
                        elif 'shape' in attributes.tag.lower():
                            coords = attributes[0][0].text
                            # coordsList = coords.split()
                            # if len(coordsList) > 2:
                            #   coords = ' '.join(coordsList[:2])
                            CRS = attributes[0][0].attrib['srsName']
                    # else:
                    #   print info.tag

            # Check if the coordinate order is lat,lon or lon,lat
            SampledFeature = featureMember.find(".//sf:sampledFeature", nsm)
            # print SampledFeature.attrib['{http://www.w3.org/1999/xlink}href']
            # return
            if "http://www.opengis.net/" in SampledFeature.attrib['{http://www.w3.org/1999/xlink}href']:
                coordsList = coords.split()
                coords = " ".join([coordsList[1], coordsList[0], coordsList[2]])
            elif "urn:ogc:def" in SampledFeature.attrib['{http://www.w3.org/1999/xlink}href']:
                pass
            else:
                print "order unknown" 

            self.featureofinterest[currentFOI]['coords'] = [coords, CRS]
            self.featureofinterest[currentFOI]['offerings'] = []
                
        #-------------------------------------------------------------------------------#
        # GetObservation --> retrieve small amounts of data to link a procedure to a FOI
        #-------------------------------------------------------------------------------#
        

        someTimeAgo = (datetime.now() - timedelta(days=7)).isoformat()
        temporalFilter = '&temporalFilter=om:resultTime,after,{0}'.format(someTimeAgo)


        for procedure in self.procedure:
            for obsProperty in self.procedure[procedure]:
                for offering in self.procedure[procedure][obsProperty]['offerings']:
                    
                    GetObservation = '{0}service=SOS&version=2.0.0&request=GetObservation&procedure={1}&offering={2}&observedproperty={3}&responseformat=http://www.opengis.net/om/2.0'.format(self.url, procedure, offering, obsProperty)
                    temporalFilterUsed = True
                    GetObservationWtempfilter = GetObservation + temporalFilter
                    try:
                        r = requests.get(GetObservationWtempfilter)
                        tree = etree.fromstring(r.content)
                    except:
                        self.log("Could not send the request with temporal filter: {0}".format(GetObservationWtempfilter))
                        r = requests.get(GetObservation)
                        tree = etree.fromstring(r.content)
                        temporalFilterUsed = False

                    nsm = tree.nsmap

                    # Print the request URL
                    if temporalFilterUsed:
                        self.log("Get request: {0}".format(GetObservation+temporalFilter))
                        print GetObservationWtempfilter
                    else:
                        self.log("Get request: {0}".format(GetObservation))
                        print GetObservation

                    # print etree.tostring(tree, pretty_print=True)
                    
                    try:
                        FOI = tree.findall(".//om:featureOfInterest", nsm)
                        # print "no. om:featureofinterest",len(FOI), FOI
                        for feature in FOI:
                            try:
                                # in case FOI is in attributes:
                                for attribute, value in feature.attrib.iteritems():
                                    if value in self.featureofinterest:
                                        self.procedure[procedure][obsProperty]['FOI'].add(value)
                                        self.featureofinterest[value]['offerings'].append(offering)
                                        continue
        
                            except:
                                pass
                            
                            self.log("featureofinterest not in attributes")
                            # in case FOI is not in attributes:
                            value = tree.findall(".//om:featureOfInterest/sams:SF_SpatialSamplingFeature/gml:identifier", nsm)
                            # print "no. gml:identifier", len(value)
                            if len(value) > 0:
                                for each in value:
                                    self.procedure[procedure][obsProperty]['FOI'].add(each.text)
                                    self.featureofinterest[each.text]['offerings'].append(offering)
                                    # print "new: ", self.procedure[procedure]['FOI']
                            # else:
                                # print "no observations available"

                    except:
                        self.log("no observations available")
                        # print "not an observations available"

        # print self.procedure      
        return

    def printInformation(self):
        # prints the variables of a SOS instance
        if self.error == False:
            results = "Information for {0}\n\tProvided by: {1}\n\tCosts: {2}\n\tAccess constraints: {3}\n\tSupported version: {4}\n\tSupported response formats: {5}\n".format(self.name, self.organisation, self.costs, self.accesConstraints, self.version, self.responseFormat)
            print results 
        else:
            print "I'm in a state of error!"
        
        return


    def log(self, event):
        # logs an event to the log.txt file
        with open('log.txt', 'a') as f:
            f.write("at {0}\t-->\t{1}\n".format(datetime.now().isoformat(), event))

        return

    def store(self):
        # stores the SOS instance and it's variables
        pickle.dump(self, open( "{0}.p".format(self.name), "wb" ) )

        return

def capabilities(SOS):
    global baseURI
    global endpoint
    global purlBatch

    # Create PURL batch file to store PURLs 
    CreatePurls('open', purlBatch)

    prov = rdflib.Namespace('http://www.w3.org/ns/prov#')
    om_lite = rdflib.Namespace('http://def.seegrid.csiro.au/ontology/om/om-lite#')
    sam_lite = rdflib.Namespace('http://def.seegrid.csiro.au/ontology/om/sam-lite#')
    geo = rdflib.Namespace('http://strdf.di.uoa.gr/ontology#')
    owl = rdflib.Namespace('http://www.w3.org/2002/07/owl#')
    dc = rdflib.Namespace('http://purl.org/dc/terms/')
    dbpedia = rdflib.Namespace("http://dbpedia.com/ontology/")

    g = Graph()

    # Define observation service
    uriSOS = URIRef("{0}/{1}".format(baseURI, SOS.name.replace(' ','')))
    g.add( ( uriSOS, RDF.type, prov.Agent) )
    g.add( ( uriSOS, FOAF.name, Literal(SOS.name) ) )
    g.add( ( uriSOS, prov.ActedOnBehalfOf,  URIRef("{0}/{1}".format(baseURI, SOS.organisation.replace(' ', '') ) ) ) )
    # g.add( ( uriSOS, dc.accessRights, Literal(SOS.accessConstraints) ) )
    # g.add( ( uriSOS, dbpedia.cost , Literal(SOS.accessConstraints) ) )
    g.add( ( uriSOS, owl.sameAs, URIRef(SOS.url) ) )

    for version in SOS.version:
        g.add( ( uriSOS, dc.hasVersion, Literal(version) ) )
    for i,format in enumerate(SOS.responseFormat):
        print format
        uriFormat = URIRef("{0}/{1}".format(baseURI, i))
        g.add( ( uriSOS, dc.hasFormat, uriFormat ) )
        g.add( ( uriFormat, RDFS.label, Literal('responseFormat') ) )
        g.add( ( uriFormat, FOAF.name, Literal(format.replace(' ','') ) ) ) 
        CreatePurls([uriFormat], purlBatch)
    # for i,format in enumerate(SOS.resourceDescriptionFormat):
    #   uriFormat = URIRef("{0}/{1}".format(baseURI, i))
    #   g.add( ( uriSOS, dc.hasFormat, uriFormat ) )
    #   g.add( ( uriFormat, RDFS.label, Literal('resourceDescriptionFormat') ) )
    #   g.add( ( uriFormat, FOAF.name, Literal(format.replace(' ','') )) )
    #   CreatePurls([uriFormat], purlBatch)


    # Create a PURL for every SOS URI 
    CreatePurls([uriSOS], purlBatch)

    definedCollections = []

    # procedure a prov:Activity, omlite:procedure;
    count = 0
    print "Creating linked data from sensor data"
    with progressbar.ProgressBar(max_value=len(SOS.procedure)) as bar:
        for proc, value in SOS.procedure.iteritems():  
            count += 1
            bar.update(count)

            # if (proc[:4].lower() == 'http'):
            #   uriProcedure = URIRef(proc)
            # else:
            uriProcedure = URIRef("{0}/PROC/{1}".format(baseURI, count).replace(' ','') ) 
            # Create a PURL for every procedure URI 
            CreatePurls([uriProcedure], purlBatch)

            for observedProperty in SOS.procedure[proc]:
                # if (observedProperty[:4] == 'http'):
                #   obsProperty = URIRef(observedProperty)
                # else:
                obsProperty = URIRef("{0}/OBSERVED/{1}".format(baseURI, observedProperty.replace(' ','').replace('http://','').replace('.','_')) ) 
                # Create a PURL for every observed property URI 
                CreatePurls([obsProperty], purlBatch)
                
                # check the mapping between observed properties from SOS and as defined by DBPedia 
                # the collections of samplign features are based on the DBPedia definitions
                query = """
                    SELECT ?observedProperty
                    WHERE {{
                      ?observedProperty <http://www.w3.org/2002/07/owl#sameAs> <{0}> .
                    }}""".format(obsProperty)

                r = requests.post(endpoint, data={'view':'HTML', 'query': query, 'format':'SPARQL/XML' , 'handle':'download', 'submit':'Query' })
                # print r
                # print r.text 
                tree = etree.fromstring(r.content)
                nsm = tree.nsmap

                StandardObsProperty = ''
                try:
                    tag = '{{{0}}}result'.format(nsm[None])
                    for result in tree.findall('.//{0}'.format(tag)):
                        for each in result.getchildren():
                            if each.attrib['name'] == 'observedProperty':
                                StandardObsProperty = URIRef(each[0].text)
                except:
                    continue

                if StandardObsProperty == '':
                    # print "I have no clue what {0} is...".format(obsProperty)
                    continue
                # else: 
                #   print obsProperty, "==", StandardObsProperty

                StandardCollection = URIRef("{0}/FOI_Collection/{1}".format(baseURI, StandardObsProperty).replace(' ','') )
                if StandardCollection in definedCollections:
                    # the collection is already defined 
                    pass
                else:
                    # the collection has not yet been defined
                    g.add( ( StandardCollection, RDF.type, sam_lite.SamplingCollection ) ) 
                    g.add( ( StandardCollection, om_lite.observedProperty, StandardObsProperty) )
                    # add collection to list with defined collections
                    definedCollections.append(StandardCollection)


                g.add( ( uriProcedure, RDF.type, prov.Activity) )
                g.add( ( uriProcedure, RDF.type, om_lite.process) )
                g.add( ( uriProcedure, FOAF.name, Literal(proc) ) )
                g.add( ( uriProcedure, om_lite.observedProperty, obsProperty ) )
                g.add( ( obsProperty, FOAF.name, Literal(observedProperty) ))

            
                # Create a PURL for every collection URI 
                CreatePurls([StandardCollection], purlBatch)

                for i, feature in enumerate(SOS.procedure[proc][observedProperty]['FOI']):
                    sensor = URIRef("{0}/{1}/PROC/{2}/SENSOR/{3}".format(baseURI, SOS.organisation, count, i+1).replace(' ', '') )
                    g.add( ( sensor, RDF.type, prov.Agent ) )
                    g.add( ( sensor, RDF.type, om_lite.process ) ) 
                    g.add( ( sensor, om_lite.procedure, uriProcedure ) )
                    g.add( ( uriProcedure, prov.wasAssociatedWith, sensor ) )
                    g.add( ( sensor, dc.isPartOf, uriSOS) )

                    # if (feature[:4].lower() == 'http'):
                    #   FOI = URIRef(feature)
                    # else:
                    FOI = URIRef("{0}/{1}/FOI/{2}".format(baseURI, SOS.organisation, feature.replace('http://','').replace('.','_')).replace(' ', '') )

                    g.add( ( FOI, FOAF.name, Literal(feature) ) )

                    geometry = SOS.featureofinterest[feature]
                    g.add( ( FOI, RDF.type, prov.Entity ) )
                    g.add( ( FOI, RDF.type, sam_lite.SamplingPoint ) ) 
                    g.add( ( FOI, geo.hasGeometry, Literal("POINT({0}); <{1}>".format(geometry['coords'][0], geometry['coords'][1]), datatype=geo.WKT ) ) )
                    g.add( ( FOI, om_lite.observedProperty, StandardObsProperty) )
                    g.add( ( StandardCollection, sam_lite.member, FOI ) )
                    g.add( ( sensor, om_lite.featureOfInterest, FOI ) )
                        

                    # Create a PURL for every FOI and sensor URI 
                    CreatePurls([FOI, sensor], purlBatch)

                    for i, offeringName in enumerate(SOS.featureofinterest[feature]['offerings']):
                        # print count, offeringName
                        offering = URIRef("{0}/{1}/PROC/{2}/OFFERING/{3}".format(baseURI, SOS.organisation, count, offeringName.replace('.','_') ).replace(' ', '') )
                        # Create a PURL for every offering URI 
                        CreatePurls([offering], purlBatch)
                        
                        g.add( ( offering, RDF.type, prov.Entity ) )
                        g.add( ( offering, prov.specializationOf, StandardCollection ) )
                        g.add( ( offering, FOAF.name, Literal(offeringName) ) )
                        g.add( ( offering, sam_lite.member, FOI ) )
                        g.add( ( offering, om_lite.procedure, Literal(proc) ) )



    print "Sending triples to endpoint"
    # with progressbar.ProgressBar(max_value=len(g)) as bar:
        # print "send data to endpoint"
            # countTriples = 0
        # triples = ""
        # for s,p,o in g.triples((None, None, None)):
        #   if str(type(o)) == "<class 'rdflib.term.Literal'>":
        #       if o.datatype != None:
        #           # print o
        #           # print o.datatype
        #           triples += u'<{0}> <{1}> "{2}"^^<{3}> . \n'.format(s,p,o,o.datatype)
        #           # print u'<{0}> <{1}> "{2}"^^<{3}> . \n'.format(s,p,o,o.datatype)
        #       else:
        #           triples += u'<{0}> <{1}> "{2}" . \n'.format(s,p,o)
        #   elif str(type(o)) == "<class 'rdflib.term.URIRef'>":
        #       triples += u'<{0}> <{1}> <{2}> . \n'.format(s,p,o)
        #   if (countTriples % 100 == 0) and (countTriples > 0):
        #       # send data to enpoint
        #       query = "INSERT DATA { " + triples + "}"
        #       # print query
        #       r = requests.post(endpoint, data={'view':'HTML', 'query': query, 'format':'HTML', 'outputformat':'SPARQL/XML' , 'handle':'plain', 'submit':'Update' }) 
        #       # print r
        #       if str(r) != '<Response [200]>':
        #           print "Response: {0}".format(r)
        #           # print query
        #           print r.text
                
        #       triples = ""
        #       countTriples += 1
        #   else:
        #       countTriples += 1
        #   bar.update(countTriples)
    # Storing the remaining triples
    # query = "INSERT DATA { " + triples + "}"
    # r = requests.post(endpoint, data={'view':'HTML', 'query': query, 'format':'HTML', 'outputformat':'SPARQL/XML' , 'handle':'plain', 'submit':'Update' }) 
    # # print r
    
    # Create directory for temporary files 
    # if not os.path.exists('D:/tempFiles/'):
    #     os.makedirs('D:/tempFiles/')

    payload = {'dbname': 'endpoint', 'username': 'Ivo', 'password':'gps', 'port':'5432', 'hostname':'localhost', 'dbengine':'postgis'}
    session = requests.Session()
    r = session.post('http://localhost:8083/strabon-endpoint-3.3.2-SNAPSHOT/DBConnect', data=payload)
    # with open('D:/tempFiles/sensors{0}.xml'.format(SOS.organisation.replace(' ', '')), "w") as f:
    #   # print type(g.serialize(format="turtle"))
    #   f.write(unicode(g.serialize(format="turtle")))
    g.serialize('sensors{0}.xml'.format(SOS.organisation.replace(' ', '')),format="turtle")
    g = Graph()
    print 'file:///{0}/sensors{1}.xml'.format(os.getcwd(),SOS.organisation.replace(' ', ''))
    r = session.post(endpoint[:-5]+'Store', data={'view':'HTML', 'format':'Turtle', 'url':'file:///{0}/sensors{1}.xml'.format(os.getcwd(),SOS.organisation.replace(' ', '')), 'fromurl':'Store from URI' }) 



    if str(r) != '<Response [200]>':
        print "Response: {0}".format(r)
        # print query
        print r.text

    # bar.update(countTriples)

    # postPURLbatch(purlBatch,'admin', 'password')

    return






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