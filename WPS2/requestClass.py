import requests
from lxml import etree, objectify
from rdflib import URIRef, BNode, Literal, Graph
from rdflib.namespace import RDF, RDFS, FOAF
import rdflib
import logging
from shapely.wkt import loads
from shapely.geometry import Point
from functools import partial
import pyproj
from shapely.ops import transform
import csv
import dateutil.parser
import pytz
from datetime import datetime, timedelta
import numpy
import StringIO
import json


logging.basicConfig()

DBPedia = 'http://dbpedia.org/sparql'
myEndpoint = 'http://localhost:8083/strabon-endpoint-3.3.2-SNAPSHOT/Query' 


class Request():
    def __init__(self, observedProperties, featureCategory, featureNames, tempRange=[(datetime.now() - timedelta(days=7)).isoformat(), datetime.now().isoformat()], tempGranularity='1 day', spatialAggregation='average', tempAggregation='average', sensors={} ):

        self.observedProperties = observedProperties
        self.featureCategory = featureCategory
        self.featureNames = featureNames # list with names of input features
        self.featureDict = {} # dictionary with names and corresponding geometries
        self.tempRange = tempRange
        self.tempGranularity = tempGranularity
        self.spatialAggregation = spatialAggregation
        self.tempAggregation = tempAggregation
        self.sensors = {}
        self.procedures = {}
        self.sos = {}
        self.results = {} 
        self.output = {}
        self.sensorFile = sensors



    #=======================================================================================================================================#
    #====================================================         WPS 1 methods         ====================================================#
    #=======================================================================================================================================#

    def getGeometries(self, countries=['the Netherlands', 'Belgium']):
        # print "Get geometries"
        global myEndpoint
        global DBPedia
        #----------------------------------------------------------------------#
        # Retrieve geometries from DBPedia
        #----------------------------------------------------------------------#
        # if (featureCategory[0] == 'provinces'):
        #   featureCategory[0] = featureCategory[0].title()
        #   for i, feature in enumerate(featureNames):
        #       featureNames[i] = r'?name = "{0}"@en'.format(feature)
        #   if len(featureNames) == 0:
        #       featureNames = ''
        #   else:
        #       featureNames = "?feature <http://xmlns.com/foaf/0.1/name> ?name . FILTER( {0} )".format(" || ".join(featureNames))

        # for i, country in enumerate(countries):
        #   countries[i] = r'?adminUnit = <http://dbpedia.org/resource/{0}_of_{1}>'.format( featureCategory[0], country.replace(' ','_'))
        # if len(countries) == 0:
        #   countries = ''
        # else:
        #   countries = "FILTER( {0} )".format(" || ".join(countries))

        #   query = r'SELECT ?feature WHERE {{ ?feature <http://dbpedia.org/ontology/type> ?adminUnit . {0} {1} }}'.format(featureNames, countries)
        
        # print query
        # r = requests.post(DBPedia, data={'query': query}) 
        # tree = etree.fromstring(r.content)
        # nsm = tree.nsmap

        # tag = '{{{0}}}uri'.format(nsm[None])
        # for result in tree.findall('.//{0}'.format(tag)):
        #   print result.text

        #----------------------------------------------------------------------#
        # Retrieve geometries from own endpoint
        #----------------------------------------------------------------------#

        featureNamesDict = {}
        for i, feature in enumerate(self.featureNames):
            featureNamesDict[i] = r'?name = "{0}"'.format(feature)
        if len(featureNamesDict) == 0:
            featureNamesFilter = ''
        else:
            filterFeatures = " || ".join([value for key, value in featureNamesDict.iteritems()])
            featureNamesFilter = "FILTER( {0} )".format(filterFeatures)


        query = r"""
        SELECT 
          ?feature ?geom ?name
        WHERE {{ 
          ?feature <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/resource/{0}> . 
          ?feature <http://strdf.di.uoa.gr/ontology#hasGeometry> ?geom . 
          ?feature <http://xmlns.com/foaf/0.1/name> ?name . 
          {1}
        }}""".format(self.featureCategory.title(), featureNamesFilter)
        # print 'QUERY:', query

        r = requests.post(myEndpoint, data={'view':'HTML', 'query': query, 'format':'SPARQL/XML', 'handle':'download', 'submit':'Query' }) 
        tree = etree.fromstring(r.content)
        nsm = tree.nsmap

        # print r.content
        self.featureDict = {}
        tag = '{{{0}}}result'.format(nsm[None])
        for result in tree.findall('.//{0}'.format(tag)):
            name = '' 
            geom = ''
            for each in result.getchildren():
                if each.attrib['name'] == 'feature':
                    uri = each[0].text
                elif each.attrib['name'] == 'geom':
                    geom = each[0].text
                elif each.attrib['name'] == 'name':
                    name = each[0].text 
            try:
                self.featureDict[name] = uri, geom
            except:
                pass
                # print "could not find feature with geometry!"

        # print 'Features:', self.featureDict
        return

        #----------------------------------------------------------------------#
        # Find relevant sensors 
        #----------------------------------------------------------------------#

    def getSensorsVector(self):
        if self.featureCategory.lower() == 'raster':
          # print 'Vector function cannot be applied for a raster request'
          return
        # else:
          # print 'Request data for vector geometry'

        spatialFilter = []
        for key, value in self.featureDict.iteritems():
          spatialFilter.append('<http://www.opengis.net/def/function/geosparql/sfContains>("{0}"^^<http://www.opengis.net/ont/geosparql#wktLiteral>, ?geom)'.format(value[1]))
        spatialFilter = 'FILTER ( {0} )'.format(' || '.join(spatialFilter))

        # Retrieve sensors and their SOS source using the spatial filter created here
        self.retrieveSensors(spatialFilter)
        
        

        return


    # def getSensorDataBBOX(self):
    #     coords = set()
    #     for name, (uri, WKT) in self.featureDict.iteritems():
    #         if len(WKT.split(';')) == 2:
    #             geometry, CRS = WKT.split(';')
    #         else:
    #             # if no CRS is provided it is assumed that it is in WGS-84 (EPGS 4326)
    #             CRS = 'http://www.opengis.net/def/crs/EPSG/0/4326'

    #         EPSG = CRS.split('/')[-1].strip('>')
    #         # print EPSG      

    #         if EPSG != "4258":
    #             project = partial(
    #                           pyproj.transform,
    #                           pyproj.Proj(init='epsg:{0}'.format(EPSG) ),
    #                           pyproj.Proj(init='epsg:4258'))
    #             newFeature = transform(project, feature)

    #         geom = loads(WKT)
    #         # print geom.geom_type
    #         if geom.geom_type == "MultiPolygon":
    #             for polygon in geom.geoms:
    #                 for point in polygon.exterior.coords:
    #                     coords.add(point)
    #         elif geom.geom_type == "Polygon":
    #             for point in geom.exterior.coords:
    #                 coords.add(point)
    #         # else:
    #         #     print "It is not a Polygon or MultiPolygon, but a {0}".format(geom.geom_type)

    #     # print coords
    #     Xmin = min(coords, key=lambda x:x[0])[0]
    #     Xmax = max(coords, key=lambda x:x[0])[0]
    #     Ymin = min(coords, key=lambda y:y[1])[1]
    #     Ymax = max(coords, key=lambda y:y[1])[1]

    #     BBOX = '"POLYGON (( {0} {1}, {2} {1}, {2} {3}, {0} {3}, {0} {1} ));<http://www.opengis.net/def/crs/EPSG/0/4258>"^^<http://strdf.di.uoa.gr/ontology#WKT>'.format(Xmin, Ymin, Xmax, Ymax)
    #     spatialFilter = "FILTER (<http://strdf.di.uoa.gr/ontology#contains>({0}, ?geom) )".format(BBOX)

    #     # print Xmin, Xmax
    #     # print Ymin, Ymax
    #     # print BBOX
    #     # print spatialFilter
    #     # return

    #     # Retrieve sensors and their SOS source using the spatial filter created here
    #     self.retrieveSensors(spatialFilter)

    #     # Filter out sensors that are outside the area of interest and outside the temporal range
    #     self.filterSensors()

    #     # spatialFilterSOS = "spatialFilter=featureOfInterest/*/shape,{0},{1},{2},{3},http://www.opengis.net/def/crs/EPSG/0/4258".format(Xmin, Ymin, Xmax, Ymax)
    #     # print spatialFilterSOS
    #     sosServices = set()
    #     parametersCollection = set()
    #     for obsProperty in self.sensors:
    #         self.results[obsProperty] = {}
    #         for sensor in self.sensors[obsProperty]:
    #             parameters = self.sensors[obsProperty][sensor]['sos'], self.sensors[obsProperty][sensor]['procedure'], self.sensors[obsProperty][sensor]['offering'], self.sensors[obsProperty][sensor]['obsPropertyName'], self.sensors[obsProperty][sensor]['location']
    #             parametersCollection.add(parameters)
    #             sosServices.add(self.sensors[obsProperty][sensor]['sos'])
    #     # print parametersCollection

    #     # print sosServices
    #     sosDict = {}
    #     for sos in sosServices:
    #         sosDict[sos] = {"post":'',"spatialFilters":[]}
    #         # Retrieve the capabilities document
    #         GetCapabilities = '{0}service=SOS&request=GetCapabilities'.format(sos)
    #         r = requests.get(GetCapabilities)

    #         # Store the retrieved document as an etree object
    #         tree = etree.fromstring(r.content)
    #         nsm = tree.nsmap

    #         # find the http address for POST requests
    #         PostAdresses = tree.findall('.//ows:OperationsMetadata//ows:Post', nsm)
    #         if len(PostAdresses) >= 1:
    #             for address in PostAdresses:
    #                 values = address.findall('.//ows:Constraint[@name="Content-Type"]/ows:AllowedValues/ows:Value', nsm)
    #                 for value in values:
    #                     if "text/xml" == value.text:
    #                         # print "text",address
    #                         sosDict[sos]["post"] = address.attrib["{http://www.w3.org/1999/xlink}href"]
    #         else:
    #             sosDict[sos]["post"] = PostAdresses.attrib["{http://www.w3.org/1999/xlink}href"]
    #             # print "len < 1",PostAdresses

    #         # if no specification is provided for the post addresses the last one is selected
    #         if sosDict[sos]["post"] == '':
    #             # print "nothing specified"
    #             sosDict[sos]["post"] = address.attrib["{http://www.w3.org/1999/xlink}href"]

    #         # find the type of spatialFilters
    #         spatialFilters = tree.findall('.//fes:Spatial_Capabilities/fes:SpatialOperators/fes:SpatialOperator', nsm)
    #         for spatialFilter in spatialFilters: 
    #             name = spatialFilter.attrib["name"]
    #             geometryOperand = spatialFilter.find('.//fes:GeometryOperand',nsm).attrib["name"]
    #             sosDict[sos]["spatialFilters"].append( (name, geometryOperand) )
    #     # print sosDict
    #     # return

    #     spatialFilterUsed = True
    #     for parameters in parametersCollection:
    #         # print parameters
    #         sos, procedureName, offeringName, obsPropertyName, sensorLocation = parameters

    #         getObservation = etree.Element('{http://www.opengis.net/sos/2.0}GetObservation') 
    #         getObservation.attrib['service'] = "SOS"
    #         getObservation.attrib['version'] = "2.0.0"

    #         procedure = etree.SubElement(getObservation,'{http://www.opengis.net/sos/2.0}procedure')
    #         procedure.text = procedureName
            

    #         offering = etree.SubElement(getObservation,'{http://www.opengis.net/sos/2.0}offering')
    #         offering.text = offeringName

            
    #         observedProperty = etree.SubElement(getObservation,'{http://www.opengis.net/sos/2.0}observedProperty')
    #         observedProperty.text = obsPropertyName

    #         if len(sosDict[sos]["spatialFilters"]) == 0:
    #             spatialFilterUsed = False
    #             # print 'No spatial filter implemented'
    #         # elif len([spatialFilter for spatialFilter in sosDict[sos]["spatialFilters"] if spatialFilter[0] == 'BBOX']) == 0:
    #         #     print 'no BBOX'

    #         # else:
    #         #     print 'BBOX'
            

    #             spatialFilter = etree.SubElement(getObservation, "{http://www.opengis.net/sos/2.0}spatialFilter")


    #             bbox = etree.SubElement(spatialFilter, "{http://www.opengis.net/fes/2.0}BBOX" )

                
    #             valueReference = etree.SubElement(bbox, "{http://www.opengis.net/fes/2.0}ValueReference")
    #             valueReference.text = "om:featureOfInterest/sams:SF_SpatialSamplingFeature/sams:shape"
       

    #             envelope = etree.SubElement(bbox, "{http://www.opengis.net/gml/3.2}Envelope")
    #             envelope.attrib["srsName"] = "http://www.opengis.net/def/crs/EPSG/0/4258"

    #             LLcorner = etree.SubElement(envelope, "{http://www.opengis.net/gml/3.2}lowerCorner")
    #             LLcorner.text = "{1} {0}".format(Xmin, Ymin)

    #             URcorner = etree.SubElement(envelope, "{http://www.opengis.net/gml/3.2}upperCorner")
    #             URcorner.text = "{1} {0}".format(Xmax, Ymax)

    #             responseFormat = etree.SubElement(getObservation,'{http://www.opengis.net/sos/2.0}responseFormat')
    #             responseFormat.text = "http://www.opengis.net/om/2.0"

    #         # Create XML string and POST it to the endpoint
    #         XML = etree.tostring(getObservation, pretty_print=True)
    #         r = requests.post(sosDict[sos]["post"], XML)
    #         if str(r) != "<Response [200]>":
    #             spatialFilterUsed = False
    #             # print "SpatialFilter failed"
    #         tree = etree.fromstring(r.content)
    #         nsm = tree.nsmap



    #         # Get observation data from the response document
    #         for observation in tree.findall('.//sos:observationData', nsm):
    #             dataType = tree.find('.//om:type', nsm).attrib['{http://www.w3.org/1999/xlink}href']
    #             if dataType == 'http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement':
    #                 # print 'OM measurement data'
    #                 resultTime = observation.find('.//om:resultTime/gml:TimeInstant/gml:timePosition',nsm).text

    #                 result = observation.find('.//om:result',nsm)
    #                 uom = result.attrib['uom']
    #                 value = result.text
    #                 csvData = '{0},{1}'.format(resultTime, value)
    #                 # print csvData

    #             elif dataType == 'http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_SWEObservation':
    #                 if tree.find('.//om:result', nsm).attrib['{http://www.w3.org/2001/XMLSchema-instance}type'] == 'swe:DataArrayPropertyType':
    #                     # print 'SWE Data Array'
    #                     uom = tree.find(".//swe:Quantity[@definition='{0}']/swe:uom".format(self.sensors[obsProperty][sensor]['obsPropertyName']), nsm).attrib['code']

    #                     try:
    #                         encoding = tree.find(".//swe:TextEncoding",nsm)
    #                         blockSeparator = encoding.attrib["blockSeparator"]
    #                         decimalSeparator = encoding.attrib["decimalSeparator"]
    #                         tokenSeparator = encoding.attrib["tokenSeparator"]
    #                         # make sure all csv data is using the same separators
    #                         csvData = tree.find('.//swe:values', nsm).text.replace(blockSeparator,";").replace(decimalSeparator, ".").replace(tokenSeparator, ",")
    #                         # print csvData
    #                         # return 
    #                     except:
    #                         continue
                
    #             if sensorLocation in self.results[obsProperty]:
    #                 self.results[obsProperty][sensorLocation][uom]['raw'] += '{0};'.format(csvData)
    #             else:
    #                 self.results[obsProperty][sensorLocation] = { uom: { 'raw': '{0};'.format(csvData) } }
    #             # print self.results[obsProperty][sensorLocation][uom]['raw']


    #         # manually filter the sensor data outside the temporal range
    #         # print 'filter out data outside the temporal range'
    #         utc = pytz.UTC
    #         startTime = dateutil.parser.parse(self.tempRange[0]).replace(tzinfo=utc)
    #         endTime = dateutil.parser.parse(self.tempRange[1]).replace(tzinfo=utc)
    #         for obsProperty in self.results:
    #             # print obsProperty
    #             for sensorLocation in self.results[obsProperty]:
    #                 # print sensorLocation
    #                 for uom in self.results[obsProperty][sensorLocation]:
    #                     # print uom
    #                     data = self.results[obsProperty][sensorLocation][uom]['raw']
    #                     if data[-1:] == ';':
    #                         data = data[:-1]
    #                     dataList = data.split(';')
    #                     for each in dataList:
    #                         # print each
    #                         # return
    #                         # print each.split(',')
    #                         # return
    #                         try:
    #                             resultTimeString, value = each.split(',')
    #                         except:
    #                             # print "remove:", each
    #                             # dataList.remove(each)
    #                             continue
    #                         resultTime = dateutil.parser.parse(resultTimeString).replace(tzinfo=utc)
    #                         if resultTime < startTime or resultTime > endTime:
    #                             # The resultTime is outside the temporal range
    #                             # print "Remove:", resultTime, "Not in range:",startTime, endTime
    #                             # print 'Before:', len(dataList), resultTime
    #                             dataList.remove(each)

    #                             # if each in dataList:
    #                             #   print each
    #                             # print 'After:', len(dataList)
    #                             # return
    #                     # return
    #                     self.results[obsProperty][sensorLocation][uom]['raw'] = ';'.join(dataList)
    #         # return
    #     # print "results:",self.results
        



    #     return


    def getSensorsRaster(self):
        if self.featureCategory.lower() == 'raster':
            spatialFilter = []
            for key, value in self.featureDict.iteritems():
                spatialFilter.append('<http://strdf.di.uoa.gr/ontology#contains>("{0}"^^<http://strdf.di.uoa.gr/ontology#WKT>, ?geom)'.format(value[1]))
            spatialFilter = "FILTER ( {0} )".format(' || '.join(spatialFilter))
            # print spatialFilter
        else:
            # print 'Find raster cells intersecting the vector geometry'
            featureFilter = []
            for key, value in self.featureDict.iteritems():
                featureFilter.append('?name = "{0}"'.format(key))
            featureFilter = "FILTER ( {0} )".format(' || '.join(featureFilter))
            query = r"""SELECT 
                       ?cellGeom ?cellName
                    WHERE {{
                        ?cell <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/resource/Raster> .
                        ?cell <http://strdf.di.uoa.gr/ontology#hasGeometry> ?cellGeom . 
                        ?cell <http://purl.org/dc/terms/isPartOf> <http://localhost:8099/masterThesis_tudelft/raster/10km> .
                        ?cell <http://xmlns.com/foaf/0.1/name> ?cellName . 
                        
                        ?feature <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/resource/{0}> .
                        ?feature <http://strdf.di.uoa.gr/ontology#hasGeometry> ?featureGeom .
                        ?feature <http://xmlns.com/foaf/0.1/name> ?name . 
                        
                        {1}
                        FILTER(<http://strdf.di.uoa.gr/ontology#intersects>(?featureGeom, ?cellGeom ) )
                    }}
                    """.format(self.featureCategory.replace(' ','_').title(), featureFilter)
            # print query
            # return    
            r = requests.post(myEndpoint, data={'view':'HTML', 'query': query, 'format':'XML', 'handle':'download', 'submit':'Query' })
            # print r.content
            
            tree = etree.fromstring(r.content)
            nsm = tree.nsmap
            tag = '{{{0}}}result'.format(nsm[None])
            cellList = []
            for result in tree.findall('.//{0}'.format(tag)):
                for each in result.getchildren():
                    if each.attrib['name'] == 'cellGeom':
                        value = each[0].text
                    elif each.attrib['name'] == 'cellName':
                        name = each[0].text
                cellList.append( (value,name) )

            spatialFilter = []
            for value, name in cellList:
                spatialFilter.append('<http://strdf.di.uoa.gr/ontology#contains>("{0}"^^<http://strdf.di.uoa.gr/ontology#WKT>, ?geom)'.format(value))
            spatialFilter = "FILTER ( {0} )".format(' || '.join(spatialFilter))


        # print 'Retrieve sensors inside raster cells'
        # Retrieve sensors and their SOS source using the spatial filter created here
        self.retrieveSensors(spatialFilter)
        
        # print self.sensors

        if self.featureCategory.lower() != 'raster':
            # print 'filter out redundant sensors'
            # Filter out sensors that are outside the area of interest and outside the temporal range
            self.filterSensors()
            

        # print len(str(self.sensors))
        # print self.sensors

        return

    def filterSensors(self):
        featureList = []
        for each in self.featureDict:
            feature = loads(self.featureDict[each][1])
            # project = partial(
            #               pyproj.transform,
            #               pyproj.Proj(init='epsg:4258'),
            #               pyproj.Proj(init='epsg:4326'))
            # newFeature = transform(project, feature)
            # featureList.append(newFeature)
            featureList.append(feature)

        # print len(str(self.sensors))
        for obsProperty in self.observedProperties:
            excessSensors = []
            for sensor in self.sensors[obsProperty]:
                theGeom = loads(self.sensors[obsProperty][sensor]['location'])
                
                excess = True
                for feature in featureList:
                    # print feature
                    if feature.contains(theGeom) :
                        excess = False
                # print theGeom
                # return
                if excess == True:
                    # print theGeom
                    excessSensors.append( (obsProperty,sensor) )
                else:
                    if len(list(theGeom.coords)[0]) == 2:
                        point = 'POINT( {0} {1} )'.format(theGeom.x, theGeom.y)
                    else:
                        point = 'POINT( {0} {1} {2} )'.format(theGeom.x, theGeom.y, theGeom.z)
                    WKTdata = '{0};<http://www.opengis.net/def/crs/EPSG/0/4326>'.format(point)
                    self.sensors[obsProperty][sensor]['location'] = WKTdata

            for each in excessSensors:
                obsProperty, sensor = each
                del self.sensors[obsProperty][sensor]

        return

    def retrieveSensors(self, spatialFilter):
        for obsProperty in self.observedProperties:
            # print obsProperty
            query = r"""SELECT 
                           ?sensor ?geom ?FOIname ?procName ?obsPropertyName ?offeringName ?sosAddress
                        WHERE {{
                           ?collection <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://def.seegrid.csiro.au/ontology/om/sam-lite#SamplingCollection> .
                           ?collection <http://def.seegrid.csiro.au/ontology/om/om-lite#observedProperty> <{0}> .
                           <http://dbpedia.org/resource/Nitrogen_dioxide> <http://www.w3.org/2002/07/owl#sameAs> ?obsProperty .
                           ?obsProperty <http://xmlns.com/foaf/0.1/name> ?obsPropertyName .
                           ?collection <http://def.seegrid.csiro.au/ontology/om/sam-lite#member> ?FOI .

                           ?offering <http://def.seegrid.csiro.au/ontology/om/sam-lite#member> ?FOI .
                           ?offering <http://www.w3.org/ns/prov#specializationOf> ?collection . 
                           ?offering <http://xmlns.com/foaf/0.1/name> ?offeringName .

                           ?FOI <http://strdf.di.uoa.gr/ontology#hasGeometry> ?geom . 
                           ?FOI <http://xmlns.com/foaf/0.1/name> ?FOIname  .

                           ?sensor <http://def.seegrid.csiro.au/ontology/om/om-lite#featureOfInterest> ?FOI .
                           ?sensor <http://def.seegrid.csiro.au/ontology/om/om-lite#procedure> ?procedure .
                           ?sensor <http://purl.org/dc/terms/isPartOf> ?sos .
                           ?sos <http://www.w3.org/2002/07/owl#sameAs> ?sosAddress .

                           ?procedure <http://def.seegrid.csiro.au/ontology/om/om-lite#observedProperty> ?obsProperty .
                           ?procedure <http://xmlns.com/foaf/0.1/name> ?procName .
                           ?offering <http://def.seegrid.csiro.au/ontology/om/om-lite#procedure> ?procName .
                            
                           {1} }}
                    """.format(obsProperty, spatialFilter)
            # print query
            r = requests.post(myEndpoint, data={'view':'HTML', 'query': query, 'format':'XML', 'handle':'download', 'submit':'Query' }) 
            # if r != 
            # print r
            # print r.content
            # return

            tree = etree.fromstring(r.content)
            nsm = tree.nsmap

            self.sensors[obsProperty] = {}
            tag = '{{{0}}}result'.format(nsm[None])
            for result in tree.findall('.//{0}'.format(tag)):
                for each in result.getchildren():
                    if each.attrib['name'] == 'sensor':
                        sensor = each[0].text
                        self.sensors[obsProperty][sensor] = {}
                    elif each.attrib['name'] == 'geom':
                        # transform all geometries to WGS84
                        WKTdata = each[0].text
                        if len(WKTdata.split(';')) == 2:
                            geom, CRS = WKTdata.split(';')
                        else:
                            # if no CRS is provided it is assumed that it is in WGS-84 (EPGS 4326)
                            geom = each[0].text
                            CRS = 'http://www.opengis.net/def/crs/EPSG/0/4326'
                            WKTdata = '{0};<http://www.opengis.net/def/crs/EPSG/0/4326>'.format(geom)

                        CRSlist = CRS.split('/')
                        if CRSlist[-1:] != '4326':
                            point = loads(geom)
                            project = partial(
                                pyproj.transform,
                                pyproj.Proj(init='epsg:{0}'.format(CRSlist[-1:][0])),
                                pyproj.Proj(init='epsg:4326'))
                            newPoint = transform(project, point)
                            # print newPoint, list(newPoint.coords)[0]
                            if len(list(newPoint.coords)[0]) == 2:
                                newPointWKT = 'POINT( {0} {1} )'.format(newPoint.x, newPoint.y)
                            else:
                                newPointWKT = 'POINT( {0} {1} {2} )'.format(newPoint.x, newPoint.y, newPoint.z)
                            # print newPointWKT
                            # return
                            WKTdata = '{0};<http://www.opengis.net/def/crs/EPSG/0/4326>'.format(newPointWKT)
                            # print WKTdata

                        self.sensors[obsProperty][sensor]['location'] = WKTdata
                    elif each.attrib['name'] == 'FOIname':
                        self.sensors[obsProperty][sensor]['FOI'] = each[0].text
                    elif each.attrib['name'] == 'procName':
                        self.sensors[obsProperty][sensor]['procedure'] = each[0].text
                    elif each.attrib['name'] == 'obsPropertyName':
                        self.sensors[obsProperty][sensor]['obsPropertyName'] = each[0].text
                    elif each.attrib['name'] == 'offeringName':
                        self.sensors[obsProperty][sensor]['offering'] = each[0].text
                    elif each.attrib['name'] == 'sosAddress':
                        sos = each[0].text
                        self.sensors[obsProperty][sensor]['sos'] = sos
                        # if sos not in self.sos:
                        #   self.parseSOS(sos)

    def sensorsToGeoJSON(self):
        outputData = {
            "type": "FeatureCollection", 
            "features": []
            }

        for obsProperty in self.sensors:
            for sensor in self.sensors[obsProperty]:
                wkt = loads(self.sensors[obsProperty][sensor]['location'])
                # print self.sensors[obsProperty][sensor]['location']

                feature = { "type": "Feature",
                    "geometry": {
                        "type": "Point", 
                        "coordinates": [list(wkt.coords)[0][0],list(wkt.coords)[0][1]]
                        },
                    "properties": {
                        "name": self.sensors[obsProperty][sensor]['FOI'],
                        "sos": self.sensors[obsProperty][sensor]['sos'],
                        "procedure": self.sensors[obsProperty][sensor]['procedure'],
                        "observedProperty": [self.sensors[obsProperty][sensor]['obsPropertyName'], obsProperty],
                        "offering": self.sensors[obsProperty][sensor]['offering'],
                        "sensorUri": sensor
                        }
                }

                outputData["features"].append(feature)

        # print outputData
        self.outputSensors = StringIO.StringIO()
        json.dump(outputData, self.outputSensors)

        return

    #=======================================================================================================================================#
    #====================================================         WPS 2 methods         ====================================================#
    #=======================================================================================================================================#

    def GeoJSONTosensors(self):
        # try:
        inputFile = requests.get(self.sensorFile).text
        # print inputFile
        # except:
        #     inputFile = open(self.sensorFile, "r").read()
        geoJSON = json.loads(inputFile)
        
        for features in geoJSON:
            if features == "type":
                continue
            # print features
            for feature in geoJSON[features]:
                # print feature
                for data in feature:
                    if data == "geometry":
                        geometry = feature[data]['coordinates']
                        # print "geometry", geometry
                    elif data == "properties":
                        # print "properties", feature[data] 
                        sensor = feature[data]['sensorUri']
                        obsProperty = feature[data]['observedProperty'][1]

                        if not obsProperty in self.sensors:
                            self.sensors[obsProperty] = {}
                        if not sensor in self.sensors[obsProperty]:
                           self.sensors[obsProperty][sensor] = {} 

                        self.sensors[obsProperty][sensor]['FOI'] = feature[data]['name']
                        self.sensors[obsProperty][sensor]['offering'] = feature[data]['offering']
                        self.sensors[obsProperty][sensor]['sos'] = feature[data]['sos']
                        self.sensors[obsProperty][sensor]['obsPropertyName'] = feature[data]['observedProperty'][0]
                        self.sensors[obsProperty][sensor]['procedure'] = feature[data]['procedure']
                self.sensors[obsProperty][sensor]['location'] = "POINT( {0} {1} );<http://www.opengis.net/def/crs/EPSG/0/4326>".format(geometry[1], geometry[0])

        # print self.sensors

        return


    # def parseSOS(sosURI):
    #     print "Retrieve data about", sosURI
    #     self.sos[sosURI] = {'resourceDescriptionFormat': set(), 'responseFormat': set()}
    #     # retrieve the formats to be used in the GetObservation requests
            
    #     g = Graph()
    #     # retrieve RDF document from SOS URI (which is a PURL that resolves to a describe URI request at the endpoint)
    #     g.parse(sosURI)

    #     print g.serialize(format='turtle')
    #     dc = rdflib.Namespace('http://purl.org/dc/terms/')

    #     # Loop through RDF graph to find data about formats accepted by SOS 
    #     for s,p,o in g.triples( (None, dc.hasFormat, None) ):
    #         # print s,p,o
    #         for s2,p2, label in g.triples( (o, RDFS.label, None ) ):
    #             if label == "responseFormat":
    #                 self.sos[sosURI]['responseFormat'].add(label)
    #             elif label == "resourceDescriptionFormat":
    #                 self.sos[sosURI]['resourceDescriptionFormat'].add(label)

    #     return

    def getObservationData(self, spatialFilter=''):
        # print "Get Observation Data"
        # print self.sensors
        temporalFilter = '&temporalFilter=om:resultTime,{0}/{1}'.format(self.tempRange[0], self.tempRange[1])
        for obsProperty in self.sensors:
            self.results[obsProperty] = {}
            for sensor in self.sensors[obsProperty]:
                if spatialFilter == '':
                    GetObservation = '{0}service=SOS&version=2.0.0&request=GetObservation&procedure={1}&offering={2}&observedproperty={3}&responseformat=http://www.opengis.net/om/2.0&featureOfInterest={4}'.format(self.sensors[obsProperty][sensor]['sos'], self.sensors[obsProperty][sensor]['procedure'], self.sensors[obsProperty][sensor]['offering'], self.sensors[obsProperty][sensor]['obsPropertyName'],self.sensors[obsProperty][sensor]['FOI'])
                else:
                    GetObservation = '{0}service=SOS&version=2.0.0&request=GetObservation&procedure={1}&offering={2}&observedproperty={3}&responseformat=http://www.opengis.net/om/2.0&{4}'.format(self.sensors[obsProperty][sensor]['sos'], self.sensors[obsProperty][sensor]['procedure'], self.sensors[obsProperty][sensor]['offering'], self.sensors[obsProperty][sensor]['obsPropertyName'], spatialFilter)

                temporalFilterUsed = True
                GetObservationWtempfilter = GetObservation + temporalFilter
                # print 'With Filter:', GetObservationWtempfilter

                try:
                    r = requests.get(GetObservationWtempfilter)
                    tree = etree.fromstring(r.content)
                except:
                    r = requests.get(GetObservation)
                    try:
                        tree = etree.fromstring(r.content)
                        temporalFilterUsed = False
                    except:
                        # print r.content
                        return

                nsm = tree.nsmap

                # if temporalFilterUsed == True:
                    # r = requests.get(GetObservation)
                    # tree = etree.fromstring(r.content)
                    # nsm = tree.nsmap
                    # temporalFilterUsed = False
                #     print GetObservationWtempfilter
                # else:
                #     print GetObservation
                
                # prevResultTime = ""
                # print r.content
                sensorLocation = self.sensors[obsProperty][sensor]['location']
                for observation in tree.findall('.//sos:observationData', nsm):
                    dataType = tree.find('.//om:type', nsm).attrib['{http://www.w3.org/1999/xlink}href']
                    if dataType == 'http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement':
                        # print 'OM measurement data'
                        resultTime = observation.find('.//om:resultTime/gml:TimeInstant/gml:timePosition',nsm).text

                        # if resultTime == prevResultTime:
                        #   pass
                        # else:
                        #   print resultTime
                        #   prevResultTime = resultTime

                        result = observation.find('.//om:result',nsm)
                        uom = result.attrib['uom']
                        value = result.text
                        csvData = '{0},{1}'.format(resultTime, value)
                        procedure = observation.find('.//om:procedure', nsm).attrib['{http://www.w3.org/1999/xlink}href']
                        # print csvData

                    elif dataType == 'http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_SWEObservation':
                        if tree.find('.//om:result', nsm).attrib['{http://www.w3.org/2001/XMLSchema-instance}type'] == 'swe:DataArrayPropertyType':
                            # print 'SWE Data Array'
                            uom = tree.find(".//swe:Quantity[@definition='{0}']/swe:uom".format(self.sensors[obsProperty][sensor]['obsPropertyName']), nsm).attrib['code']

                            try:
                                encoding = tree.find(".//swe:TextEncoding",nsm)
                                blockSeparator = encoding.attrib["blockSeparator"]
                                decimalSeparator = encoding.attrib["decimalSeparator"]
                                tokenSeparator = encoding.attrib["tokenSeparator"]
                                # make sure all csv data is using the same separators

                                csvData = tree.find('.//swe:values', nsm).text.replace(blockSeparator,";").replace(decimalSeparator, ".").replace(tokenSeparator, ",")
                                # print data
                                # return 
                                procedure = observation.find('.//om:procedure', nsm).attrib['{http://www.w3.org/1999/xlink}href']
                            except:
                                continue
                    
                    if sensorLocation in self.results[obsProperty]:
                        self.results[obsProperty][sensorLocation][uom]['raw'] += '{0};'.format(csvData)
                    else:
                        self.results[obsProperty][sensorLocation] = { uom: { 'raw': '{0};'.format(csvData) } }
                    # print self.results[obsProperty][sensorLocation][uom]['raw']
                    self.procedures[obsProperty] = procedure


                if temporalFilterUsed == False:
                    # manually filter the sensor data outside the temporal range
                    # print 'filter out data outside the temporal range'
                    utc = pytz.UTC
                    startTime = dateutil.parser.parse(self.tempRange[0]).replace(tzinfo=utc)
                    endTime = dateutil.parser.parse(self.tempRange[1]).replace(tzinfo=utc)
                    for obsProperty in self.results:
                        # print obsProperty
                        for sensorLocation in self.results[obsProperty]:
                            # print sensorLocation
                            for uom in self.results[obsProperty][sensorLocation]:
                                # print uom
                                data = self.results[obsProperty][sensorLocation][uom]['raw']
                                if data[-1:] == ';':
                                    data = data[:-1]
                                dataList = data.split(';')
                                for each in dataList:
                                    # print each
                                    # return
                                    # print each.split(',')
                                    # return
                                    try:
                                        resultTimeString, value = each.split(',')
                                    except:
                                        # print "remove:", each
                                        # dataList.remove(each)
                                        continue
                                    resultTime = dateutil.parser.parse(resultTimeString).replace(tzinfo=utc)
                                    if resultTime < startTime or resultTime > endTime:
                                        # The resultTime is outside the temporal range
                                        # print "Remove:", resultTime, "Not in range:",startTime, endTime
                                        # print 'Before:', len(dataList), resultTime
                                        dataList.remove(each)

                                        # if each in dataList:
                                        #   print each
                                        # print 'After:', len(dataList)
                                        # return
                                # return
                                self.results[obsProperty][sensorLocation][uom]['raw'] = ';'.join(dataList)
                                

        # print self.results
        return


    # def aggregateCheck(self):
    #   pass

    #   return


    def aggregateTemporal(self):
        # print "Perform temporal aggregation: {0}".format(self.tempAggregation)

        # Convert the input parameter tempGranularity to a timedelta object.
        tempGranularityList = self.tempGranularity.split(' ')
        if 'minute' in self.tempGranularity.lower():
            tempGranularity = timedelta(minutes = int(tempGranularityList[0]))
            # print tempGranularity
        elif 'hour' in self.tempGranularity.lower():
            tempGranularity = timedelta(hours = int(tempGranularityList[0]))
            # print tempGranularity
        elif 'day' in self.tempGranularity.lower():
            tempGranularity = timedelta(days = int(tempGranularityList[0]))
            # print tempGranularity
        elif 'week' in self.tempGranularity.lower():
            tempGranularity = timedelta(days = 7*int(tempGranularityList[0]))
            # print tempGranularity
        # elif 'month' in self.tempGranularity.lower():
        #   tempGranularity = timedelta(months = int(tempGranularityList[0]))
        #   # print tempGranularity
        # elif 'year' in self.tempGranularity.lower():
        #   tempGranularity = timedelta(years = int(tempGranularityList[0]))
        
        # print "Temporal granularity:", tempGranularity
        # return

        aggregatedDataList = []
        utc = pytz.UTC
        startTime = dateutil.parser.parse(self.tempRange[0]).replace(tzinfo=utc)
        endTime = dateutil.parser.parse(self.tempRange[1]).replace(tzinfo=utc)
        # print "Temporal range:", endTime - startTime

        # Sort the data into lists based on the temporal granularity 
        for obsProperty in self.results:
            for sensorLocation in self.results[obsProperty]:
                for uom in self.results[obsProperty][sensorLocation]:
                    data = self.results[obsProperty][sensorLocation][uom]['raw']
                    # print data
                    self.results[obsProperty][sensorLocation][uom]['tempOrdered'] = dict()
                    if data[-1:] == ';':
                        data = data[:-1]
                    dataList = data.split(';')
                    for each in dataList:
                        try:
                            resultTimeString, value = each.split(',')
                        except:
                            # print each
                            continue
                        resultTime = dateutil.parser.parse(resultTimeString).replace(tzinfo=utc)

                        # double check that the result time is in between start and end time
                        if resultTime < startTime or resultTime > endTime:
                            # print "Result time is outside temporal range"
                            continue

                            # return

                        difference = resultTime - startTime
                        # Calculate the remainder after the temporal granularity fits as many times as possible
                        remainderDifference = timedelta(seconds = (difference.total_seconds() % tempGranularity.total_seconds() ) )
                        # Calculate how many times the temporal granularity fits in the difference after the remainder is removed
                        division = int( (difference - remainderDifference).total_seconds() / tempGranularity.total_seconds() )

                        if "{0},{1}".format((startTime + tempGranularity * division).isoformat(), (startTime + tempGranularity * (division + 1) ).isoformat() ) in self.results[obsProperty][sensorLocation][uom]['tempOrdered']:
                            self.results[obsProperty][sensorLocation][uom]['tempOrdered']["{0},{1}".format((startTime + tempGranularity * division).isoformat(), (startTime + tempGranularity * (division + 1) ).isoformat() )].append(each)
                        else:
                            # print startTime, tempGranularity, division
                            # print str(startTime + tempGranularity * division)
                            self.results[obsProperty][sensorLocation][uom]['tempOrdered']["{0},{1}".format((startTime + tempGranularity * division).isoformat(), (startTime + tempGranularity * (division + 1) ).isoformat() )] = [each]

                        # print self.results[obsProperty][sensorLocation][uom]['tempOrdered']

        # Aggregate the data inside each list to a single value
        for obsProperty in self.results:
            for sensorLocation in self.results[obsProperty]:
                for uom in self.results[obsProperty][sensorLocation]:
                    # print self.results[obsProperty][sensorLocation][uom], 'temp{0}'.format(self.tempAggregation.title())
                    # return
                    self.results[obsProperty][sensorLocation][uom]['temp{0}'.format(self.tempAggregation.title())] = {}
                    for timeRange, values in self.results[obsProperty][sensorLocation][uom]['tempOrdered'].iteritems():
                    
                        # check the type of temporal aggregation
                        if self.tempAggregation.lower() == 'average':
                            aggregatedData = (sum([float(x.split(',')[1]) for x in values]) ) / float(len(values))
                        elif self.tempAggregation.lower() == 'minimum':
                            aggregatedData = min([float(x.split(',')[1]) for x in values])
                        elif self.tempAggregation.lower() == 'maximum':
                            aggregatedData = max([float(x.split(',')[1]) for x in values])
                        elif self.tempAggregation.lower() == 'sum':
                            aggregatedData = sum([float(x.split(',')[1]) for x in values])
                        elif self.tempAggregation.lower() == 'median':
                            aggregatedData = numpy.median(numpy.array([float(x.split(',')[1]) for x in values]))



                        self.results[obsProperty][sensorLocation][uom]['temp{0}'.format(self.tempAggregation.title())][timeRange] = aggregatedData 
                        # print self.results[obsProperty][sensorLocation][uom]['temp{0}'.format(self.tempAggregation.title())][timeRange]

        return

    def aggregateSpatial(self):
        # print "Perform spatial aggregation"

        featureList = []
        for name, data in self.featureDict.iteritems():
            uri, geom = data
            self.output[name] = {}
            # coords, CRS = geom.strip('>').split(';')
            # CRSlist = CRS.split('/')
            polygon = loads(geom)
            # project = partial(
            #   pyproj.transform,
            #   pyproj.Proj(init='epsg:{0}'.format(CRSlist[-1:][0])),
            #   pyproj.Proj(init='epsg:4326'))
            # newPolygon = transform(project, polygon)
            # print newPolygon
            # return
            featureList.append( (name, polygon) )
        # print len(featureList), featureList[0]


        # Order the observation data per feature
        for obsProperty in self.results:
            # print "observed property", obsProperty
            for sensorLocation in self.results[obsProperty]:
                # print sensorLocation
                for name, polygon in featureList:
                    # Check if sensor location overlaps with feature
                    point = loads(sensorLocation)
                    reversedPoint = loads('POINT({0} {1})'.format(point.y, point.x))      
                    if polygon.contains(reversedPoint):
                        # print "point in polygon"
                        if obsProperty not in self.output[name]:
                            self.output[name][obsProperty] = {}
                        # print self.output

                        # Append data to list per feature
                        for uom in self.results[obsProperty][sensorLocation]:
                            # print uom
                            # Check if unit of measurement is already defined for this feature
                            if uom not in self.output[name][obsProperty]:
                                self.output[name][obsProperty][uom] = {}
                                
                            # Loop through the observation data and add to feature 
                            for timeRange, data in self.results[obsProperty][sensorLocation][uom]['temp{0}'.format(self.tempAggregation.title())].iteritems():
                                # print timeRange
                                if timeRange not in self.output[name][obsProperty][uom]:
                                    self.output[name][obsProperty][uom][timeRange] = []

                                self.output[name][obsProperty][uom][timeRange].append(data)
                    # else:
                    #     print "point not in polygon"
                    #     print point, list(polygon.geoms[0].exterior.coords)[50]

        # Aggregate the order data to a single value per feature per timerange
        for name in self.output:
            for obsProperty in self.output[name]:
                for uom in self.output[name][obsProperty]:
                    for timeRange, values in self.output[name][obsProperty][uom].iteritems():

                        # check the type of temporal aggregation
                        if self.tempAggregation.lower() == 'average':
                            aggregatedData = (sum([float(x) for x in values]) ) / float(len(values))
                        elif self.tempAggregation.lower() == 'minimum':
                            aggregatedData = min([float(x) for x in values])
                        elif self.tempAggregation.lower() == 'maximum':
                            aggregatedData = max([float(x) for x in values])
                        elif self.tempAggregation.lower() == 'sum':
                            aggregatedData = sum([float(x) for x in values])
                        elif self.tempAggregation.lower() == 'median':
                            aggregatedData = numpy.median(numpy.array([float(x) for x in values]))

                        # Replace list with single aggregated value
                        self.output[name][obsProperty][uom][timeRange] = aggregatedData 

        # print self.results
        # print self.output

        return



    def createOutput(self, outputFormat):
        # create file like object for the output file
        self.outputFile = StringIO.StringIO()

        if outputFormat == 'XML':
            # print "Create output XML"
            # print self.output
            

            sos_NS = "http://www.opengis.net/sos/2.0"
            sos = "{{{0}}}".format(sos_NS)
            om_NS = "http://www.opengis.net/om/2.0"
            om = "{{{0}}}".format(om_NS)
            swe_NS = "http://www.opengis.net/swe/2.0"
            swe = "{{{0}}}".format(swe_NS)
            gml_NS = "http://www.opengis.net/gml/3.2"
            gml = "{{{0}}}".format(gml_NS)
            xlink_NS = "http://www.w3.org/1999/xlink"
            xlink = "{{{0}}}".format(xlink_NS)

            NSMAP = {
                'sos': sos_NS,
                'om': om_NS,
                'swe': swe_NS,
                'gml': gml_NS,
                'xlink': xlink_NS

            }
            # print NSMAP


            if self.spatialAggregation.lower() == 'false':
                # output points with temporally aggregated observation data

                # self.results[obsProperty][sensorLocation][uom]['temp{0}'.format(self.tempAggregation.title())][timeRange]
                
                root = etree.Element("{http://www.opengis.net/sos/2.0}observationData", nsmap=NSMAP)
                for i,obsProperty in enumerate(self.results):     
                    for sensorLocation in self.results[obsProperty]:
                        for uom in self.results[obsProperty][sensorLocation]:
                            count = 0
                            for timeRange, value in self.results[obsProperty][sensorLocation][uom]['temp{0}'.format(self.tempAggregation.title())].iteritems():
                                obsPropertyTag = etree.Element("{http://www.opengis.net/om/2.0}observedProperty")
                                obsPropertyTag.attrib["{http://www.w3.org/1999/xlink}href"] = obsProperty

                                phenomenonTime = etree.Element("{http://www.opengis.net/om/2.0}phenomenonTime")
                                timePeriod = etree.SubElement(phenomenonTime, "{http://www.opengis.net/gml/3.2}TimePeriod")
                                timePeriod.attrib[gml+"id"] = "t_{0}".format(count)
                                begin = etree.SubElement(timePeriod, "{http://www.opengis.net/gml/3.2}beginPosition")
                                end = etree.SubElement(timePeriod, "{http://www.opengis.net/gml/3.2}endPosition")
                                timeRangeLst = timeRange.split(',')
                                begin.text = timeRangeLst[0]
                                end.text = timeRangeLst[1]
                                # phenomenonTime.attrib[gml+"id"] = "phenomenonTime_{0}".format(count)

                                Observation = etree.SubElement(root,"{http://www.opengis.net/om/2.0}OM_Observation")
                                Observation.attrib[gml+"id"] = "o_{0}".format(count)
                                etree.SubElement(Observation, "{http://www.opengis.net/om/2.0}type").attrib["{http://www.w3.org/1999/xlink}href"] = "http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement"
                                Observation.append(phenomenonTime)
                                etree.SubElement(Observation, "{http://www.opengis.net/om/2.0}resultTime").attrib["{http://www.w3.org/1999/xlink}href"] = "t_{0}".format(count)
                                
                                # procedure
                                procedure = etree.SubElement(Observation, "{http://www.opengis.net/om/2.0}procedure").attrib["{http://www.w3.org/1999/xlink}href"] = self.procedures[obsProperty]
                                
                                # Observed Property
                                Observation.append(obsPropertyTag)

                                # Feature of interest
                                FOI = etree.Element("{http://www.opengis.net/om/2.0}featureOfInterest")
                                # samplingFeature = etree.SubElement(FOI, "{http://www.opengis.net/samplingSpatial/2.0}SF_SpatialSamplingFeature")
                                shape = etree.SubElement(FOI, "{http://www.opengis.net/gml/3.2}AbstractFeature")
                                CRSType = etree.SubElement(FOI, "{http://www.opengis.net/samplingSpatial/2.0}sampledFeature").attrib["{http://www.w3.org/1999/xlink}href"] = "urn:ogc:def:nil:OGC:unknown"
                                point = etree.SubElement(shape, "{http://www.opengis.net/gml/3.2}Point")
                                point.attrib[gml+"id"] = "p_{0}".format(count)
                                coords = etree.SubElement(point, "{http://www.opengis.net/gml/3.2}pos")
                                geom, CRS = sensorLocation.split(';')
                                CRS = CRS.strip('<').strip('>')
                                coords.attrib["srsName"] = CRS
                                pointObj = loads(geom)
                                if len(list(pointObj.coords)[0]) == 2:
                                    coords.text = "{0} {1}".format(pointObj.x, pointObj.y)
                                else:
                                    coords.text = "{0} {1} {2}".format(pointObj.x, pointObj.y, pointObj.z)
                                Observation.append(FOI)
                                
                                

                                
                                # result
                                result = etree.SubElement(Observation, "{http://www.opengis.net/om/2.0}result")
                                result.attrib['uom'] = uom
                                result.attrib['{http://www.w3.org/2001/XMLSchema-instance}type'] = "{http://www.opengis.net/gml/3.2}MeasureType"
                                result.text = str(value)
                                # if type(value) == list:
                                #     print "More values;", value
                                count += 1
            else:
                # print "create XML document"
                # output feature names with temporally and spatially aggregated observation data
                root = etree.Element(sos+"observationData", nsmap = NSMAP)
                for i,name in enumerate(self.output):
                    Observation = etree.SubElement(root,om+"OM_Observation")
                    Observation.attrib[gml+"id"] = "o_{0}".format(i)
                    for obsProperty in self.output[name]:
                        for uom in self.output[name][obsProperty]:
                            # uom = etree.Element()
                            encoding = etree.Element(swe+"Encoding")
                            textEncoding = etree.SubElement(encoding, swe+"TextEncoding")
                            textEncoding.attrib["blockSeparator"] = ";"
                            textEncoding.attrib["decimalSeparator"] = "."
                            textEncoding.attrib["tokenSeparator"] = ","
                            sweType = etree.Element(swe+"elementType")
                            fixedRecords = etree.SubElement(sweType, swe+"DataRecord")
                            time = objectify.Element(swe+"Time")
                            time.attrib["definition"] = "http://www.opengis.net/def/property/OGC/0/SamplingTime"
                            timeEncoding = objectify.SubElement(time, swe+"uom")
                            timeEncoding.attrib[xlink+"href"] = "http://www.opengis.net/def/uom/ISO-8601/0/Gregorian"  
                            field1 = etree.SubElement(fixedRecords, swe+"field")
                            field1.attrib["name"] = "StartTime"
                            field1.append(time)
                            time = objectify.Element(swe+"Time")
                            time.attrib["definition"] = "http://www.opengis.net/def/property/OGC/0/SamplingTime"
                            timeEncoding = objectify.SubElement(time, swe+"uom")
                            timeEncoding.attrib[xlink+"href"] = "http://www.opengis.net/def/uom/ISO-8601/0/Gregorian"  
                            field2 = etree.SubElement(fixedRecords, swe+"field")
                            field2.attrib["name"] = "EndTime"
                            field2.append(time)
                            field3 = etree.SubElement(fixedRecords, swe+"field")
                            field3.attrib["name"] = "Value"
                            quantity = etree.SubElement(field3, swe+"Quantity")
                            uomTag = etree.SubElement(quantity, swe+"uom")
                            uomTag.text = uom

                            result = etree.Element(om+"result") 
                            # result.append(sweType)
                            result.attrib["{http://www.w3.org/2001/XMLSchema-instance}type"] = "{http://www.opengis.net/swe/2.0}DataArrayPropertyType"
                            dataArray = etree.SubElement(result, swe+"DataArray")
                            dataArray.append(sweType)
                            dataArray.append(encoding)
                            values = etree.SubElement(dataArray, swe+"values")
                            
                            valuesList = [] 
                            startDates = []
                            endDates = []
                            for timeRange, value in self.output[name][obsProperty][uom].iteritems():
                                start, end = timeRange.split(",")
                                start = dateutil.parser.parse(start)
                                startDates.append(start)
                                end = dateutil.parser.parse(end)
                                endDates.append(end)
                                valuesList.append("{0},{1},{2}".format(start.isoformat(), end.isoformat(), value))
                            values.text = ";".join(valuesList)  
                            minimum = min(startDates)
                            maximum = max(endDates)

                            # phenomenonTime
                            phenomenonTime = etree.SubElement(Observation, om+"phenomenonTime")
                            timePeriod = etree.SubElement(phenomenonTime, "{http://www.opengis.net/gml/3.2}TimePeriod")
                            timePeriod.attrib[gml+"id"] = "phenomenonTime_{0}".format(name)
                            begin = etree.SubElement(timePeriod, gml+"beginPosition")
                            begin.text = minimum.isoformat()
                            end = etree.SubElement(timePeriod, gml+"endPosition")
                            end.text = maximum.isoformat()
                            # resultTime
                            resultTime = etree.SubElement(Observation, om+"resultTime")
                            resultTime.attrib[xlink+"href"] = "phenomenonTime_{0}".format(name)

                            # procedure is missing

                            # Observed Property
                            obsPropertyTag = etree.Element(om+"observedProperty")
                            obsPropertyTag.attrib[xlink+"href"] = obsProperty
                            Observation.append(obsPropertyTag)

                            # Feature of Interest
                            FOI = etree.Element(om+"featureOfInterest")
                            FOI.attrib[xlink+"href"] = self.featureDict[name][0]
                            FOI.attrib[xlink+"title"] = name
                            Observation.append(FOI)

                            # Result
                            Observation.append(result)

                            objectify.deannotate(root, xsi_nil=True, cleanup_namespaces=True)

            # etree.cleanup_namespaces(root)
            XML = etree.tostring(root, pretty_print=True)
            # print XML
            
            self.outputFile.write(XML)

        else:
            # print "Make GeoJSON output file"

            if self.spatialAggregation.lower() == 'false':
                # make GeoJSON output of only temporally aggregated sensor data 
                pass
            else:
                # make GeoJSON output of temporally and spatially aggregated sensor data
                outputData = {
                    "type": "FeatureCollection", 
                    "features": []
                    }
                for i,name in enumerate(self.output):
                    # print name
                    for obsProperty in self.output[name]:
                        for uom in self.output[name][obsProperty]:
                            wkt = self.featureDict[name][1]
                            # print self.featureDict[name]
                            geom = loads(wkt)
                            coordinates = []
                            if geom.geom_type == "MultiPolygon":
                                for polygon in geom.geoms:
                                    for point in polygon.exterior.coords:
                                        # print point
                                        coordinates.append([point[1], point[0]])
                            
                            feature = { "type": "Feature",
                                        "geometry": {
                                            "type": "Polygon", 
                                            "coordinates": coordinates
                                            },
                                        "properties": {
                                            "observedProperty" : obsProperty,
                                            "name": name,
                                            "uri": self.featureDict[name][0],
                                            "blockSeparator": ";",
                                            "decimalSeparatorSeparator": ".",
                                            "tokenSeparator": ",",
                                            "observationDataArray": [] 
                                        }
                                    }
                            valuesList = []
                            for timeRange, value in self.output[name][obsProperty][uom].iteritems():
                                start, end = timeRange.split(",")
                                start = dateutil.parser.parse(start)
                                # startDates.append(start)
                                end = dateutil.parser.parse(end)
                                # endDates.append(end)
                                feature['properties']['observationDataArray'].append("{0},{1},{2}".format(start.isoformat(), end.isoformat(), value))
                            feature['properties']['observationDataArray'] = ";".join(feature['properties']['observationDataArray'])
                            outputData['features'].append(feature)

                            
        json.dump(outputData, self.outputFile)
                            

        return