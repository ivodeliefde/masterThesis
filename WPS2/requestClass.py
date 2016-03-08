import requests
from lxml import etree
from rdflib import URIRef, BNode, Literal, Graph
from rdflib.namespace import RDF, RDFS, FOAF
import rdflib
import logging
from shapely.wkt import loads
from shapely.geometry import Point
from functools import partial
import pyproj
from shapely.ops import transform

logging.basicConfig()

DBPedia = 'http://dbpedia.org/sparql'
myEndpoint = 'http://localhost/strabon-endpoint-3.3.2-SNAPSHOT/Query' 


class Request():
	def __init__(self, observedProperties, featureCategory, featureNames, tempRange, spatialAggregation, tempAggregation):

		self.observedProperties = observedProperties
		self.featureCategory = featureCategory
		self.featureNames = featureNames # list with names of input features
		self.featureDict = {} # dictionary with names and corresponding geometries
		self.tempRange = tempRange
		self.spatialAggregation = spatialAggregation
		self.tempAggregation = tempAggregation
		self.sensors = {} # the sensors with their measurements: {obsProperty1: {sensor1: {'location': location, 'sos': sos, 'observations': values}, sensor2: {'location': location, 'sos': sos, 'observations': values} }, obsProperty2: {sensor3: {'location': location, 'sos': sos, 'observations': values} } }
		self.sos = {}
		self.results = {} # the features with their aggregated sensor data: {obsProperty1: { sensor1: [values], sensor2: [values], sensor3: [values] } }

	def getGeometries(self, countries=['the Netherlands', 'Belgium']):
		global myEndpoint
		global DBPedia
		#----------------------------------------------------------------------#
		# Retrieve geometries from DBPedia
		#----------------------------------------------------------------------#
		# if (featureCategory[0] == 'provinces'):
		# 	featureCategory[0] = featureCategory[0].title()
		# 	for i, feature in enumerate(featureNames):
		# 		featureNames[i] = r'?name = "{0}"@en'.format(feature)
		# 	if len(featureNames) == 0:
		# 		featureNames = ''
		# 	else:
		# 		featureNames = "?feature <http://xmlns.com/foaf/0.1/name> ?name . FILTER( {0} )".format(" || ".join(featureNames))

		# for i, country in enumerate(countries):
		# 	countries[i] = r'?adminUnit = <http://dbpedia.org/resource/{0}_of_{1}>'.format( featureCategory[0], country.replace(' ','_'))
		# if len(countries) == 0:
		# 	countries = ''
		# else:
		# 	countries = "FILTER( {0} )".format(" || ".join(countries))

		# 	query = r'SELECT ?feature WHERE {{ ?feature <http://dbpedia.org/ontology/type> ?adminUnit . {0} {1} }}'.format(featureNames, countries)
		
		# print query
		# r = requests.post(DBPedia, data={'query': query}) 
		# tree = etree.fromstring(r.content)
		# nsm = tree.nsmap

		# tag = '{{{0}}}uri'.format(nsm[None])
		# for result in tree.findall('.//{0}'.format(tag)):
		# 	print result.text

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
				print "could not find feature with geometry!"

		# print 'Features:', self.featureDict
		return

		#----------------------------------------------------------------------#
		# Find relevant sensors 
		#----------------------------------------------------------------------#

	def getSensorsVector(self):
		# if self.featureCategory.lower() == 'raster':
		# 	print 'Vector function cannot be applied for a raster request'
		# 	return
		# else:
		# 	print 'Request data for vector geometry'

		# spatialFilter = []
		# for key, value in self.featureDict.iteritems():
		# 	spatialFilter.append('<http://www.opengis.net/def/function/geosparql/sfContains>("{0}"^^<http://www.opengis.net/ont/geosparql#wktLiteral>, ?geom)'.format(value))
		# spatialFilter = 'FILTER ( {0} ) )'.format(' || '.join(spatialFilter))

		# for obsProperty in self.observedProperties:
		# 	# Check out DBPedia to find the observed property and see to which collection of sampling features it links  

		# 	# Retrieve sensors that are linked to the collection of sampling features
		# 	self.sensors[obsProperty] = {}
		# 	query = r"""
		# 		SELECT DISTINCT 
		# 		  ?sensor ?geom ?FOIname ?procName ?sos
							
		# 		WHERE {{

		# 		   ?collection <http://def.seegrid.csiro.au/ontology/om/om-lite#observedProperty> ?obsProperty . 
		# 		   ?obsProperty <http://xmlns.com/foaf/0.1/name> {0} .
		# 		   ?collection <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://def.seegrid.csiro.au/ontology/om/sam-lite#SamplingCollection> . 

		# 		   ?collection <http://def.seegrid.csiro.au/ontology/om/sam-lite#member> ?FOI .  
				 

		# 		   ?sensor <http://def.seegrid.csiro.au/ontology/om/om-lite#featureOfInterest> ?FOI . 
		# 		   ?FOI <http://xmlns.com/foaf/0.1/name> ?FOIname .
		# 		   ?procedure <http://www.w3.org/ns/prov#wasAssociatedWith> ?sensor .
		# 		   ?procedure <http://xmlns.com/foaf/0.1/name> ?procName .
				   
		# 		   ?sensor <http://purl.org/dc/terms/isPartOf> ?sos . 
		# 	  {1}
		# 	}}""".format(obsProperty, spatialFilter) 
			
		# 	# print query
		# 	r = requests.post(myEndpoint, data={'view':'HTML', 'query': query, 'format':'SPARQL/XML', 'handle':'download', 'submit':'Query' })  
		# 	# print r.content
		# 	tree = etree.fromstring(r.content)
		# 	nsm = tree.nsmap

		# 	tag = '{{{0}}}result'.format(nsm[None])
		# 	for result in tree.findall('.//{0}'.format(tag)):
		# 		sensor = ''
		# 		sensorFOI = ''
		# 		sensorSOS = ''
		# 		sensorOffering = ''
		# 		sensorProcedure = ''
		# 		sensorGeom = ''
		# 		for each in result.getchildren():
		# 			if each.attrib['name'] == 'sensor':
		# 				sensor = each[0].text
		# 			elif each.attrib['name'] == 'FOIname':
		# 				sensorFOI = each[0].text
		# 			elif each.attrib['name'] == 'sos':
		# 				sensorSOS = each[0].text
		# 			elif each.attrib['name'] == 'geom':
		# 				sensorGEOM = each[0].text
		# 			elif each.attrib['name'] == 'procName':
		# 				sensorProcedure = each[0].text
		# 		if self.sensors[obsProperty][sensor] in self.sensors[obsProperty]:
		# 			self.sensors[obsProperty][sensor] = {'location': sensorGEOM, 'sos': sensorSOS, 'FOI': sensorFOI, 'procedure': sensorProcedure, 'offerings':[], 'observations': []}

		# 		if sensorSOS in self.sos:
		# 			self.sos[sensorSOS].append(sensor)
		# 		else:
		# 			self.sos[sensorSOS] = [sensor]

		
		return

	def getSensorsBBOX(self):
		if self.featureCategory.lower() == 'raster':
			print 'Create bounding box around grid cells'
		else:
			print 'Create bounding box around vector geometry'

		return

	def getSensorsRaster(self):
		if self.featureCategory.lower() == 'raster':
			spatialFilter = []
			for key, value in self.featureDict.iteritems():
				spatialFilter.append('<http://strdf.di.uoa.gr/ontology#contains>("{0}"^^<http://strdf.di.uoa.gr/ontology#WKT>, ?geom)'.format(value[1]))
			spatialFilter = "FILTER ( {0} )".format(' || '.join(spatialFilter))
			# print spatialFilter
		else:
			print 'Find raster cells intersecting the vector geometry'
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


		print 'Retrieve sensors inside raster cells'
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
							
						   {1} }}
					""".format(obsProperty, spatialFilter)
			# print query
			r = requests.post(myEndpoint, data={'view':'HTML', 'query': query, 'format':'XML', 'handle':'download', 'submit':'Query' }) 
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
						geom, CRS = WKTdata.split(';')
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
								newPointWKT = 'POINT( {0} {1} )'.format(newPoint.y, newPoint.x)
							else:
								newPointWKT = 'POINT( {0} {1} {2} )'.format(newPoint.y, newPoint.x, newPoint.z)
							# print newPointWKT
							# return
							WKTdata = '{0};<http://www.opengis.net/def/crs/EPSG/0/4326>'.format(newPointWKT)

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
						# 	self.parseSOS(sos)
		
		# print self.sensors

		if self.featureCategory.lower() != 'raster':
			print 'filter out redundant sensors'
			
			featureList = []
			for each in self.featureDict:
				featureList.append(loads(self.featureDict[each][1]))

			# print len(str(self.sensors))
			for obsProperty in self.observedProperties:
				excessSensors = []
				for sensor in self.sensors[obsProperty]:
					theGeom = loads(self.sensors[obsProperty][sensor]['location'])
					
					excess = True
					for feature in featureList:
						if feature.contains(theGeom) :
							excess = False
					
					if excess == True:
						excessSensors.append( (obsProperty,sensor) )

			for each in excessSensors:
				obsProperty, sensor = each
				del self.sensors[obsProperty][sensor]

		print len(str(self.sensors))

		return

	def parseSOS(sosURI):
		print "Retrieve data about", sosURI
		self.sos[sosURI] = {'resourceDescriptionFormat': set(), 'responseFormat': set()}
		# retrieve the formats to be used in the GetObservation requests
			
		g = Graph()
		# retrieve RDF document from SOS URI (which is a PURL that resolves to a describe URI request at the endpoint)
		g.parse(sosURI)

		print g.serialize(format='turtle')
		dc = rdflib.Namespace('http://purl.org/dc/terms/')

		# Loop through RDF graph to find data about formats accepted by SOS 
		for s,p,o in g.triples( (None, dc.hasFormat, None) ):
			# print s,p,o
			for s2,p2, label in g.triples( (o, RDFS.label, None ) ):
				if label == "responseFormat":
					self.sos[sosURI]['responseFormat'].add(label)
				elif label == "resourceDescriptionFormat":
					self.sos[sosURI]['resourceDescriptionFormat'].add(label)

		return

	def getObservationData(self):
		print "Get Observation Data"
		# print self.sensors
		temporalFilter = '&temporalFilter=om:resultTime,after,{0}&temporalFilter=om:resultTime,before,{1}'.format(self.tempRange[0], self.tempRange[1])
		for obsProperty in self.sensors:
			for sensor in self.sensors[obsProperty]:
				GetObservation = '{0}service=SOS&version=2.0.0&request=GetObservation&procedure={1}&offering={2}&observedproperty={3}&responseformat=http://www.opengis.net/om/2.0&featureOfInterest={4}'.format(self.sensors[obsProperty][sensor]['sos'], self.sensors[obsProperty][sensor]['procedure'], self.sensors[obsProperty][sensor]['offering'], self.sensors[obsProperty][sensor]['obsPropertyName'],self.sensors[obsProperty][sensor]['FOI'])
				
				temporalFilterUsed = True
				GetObservationWtempfilter = GetObservation + temporalFilter
				# print 'With Filter:', GetObservationWtempfilter

				try:
					r = requests.get(GetObservationWtempfilter)
					tree = etree.fromstring(r.content)
				except:
					r = requests.get(GetObservation)
					tree = etree.fromstring(r.content)
					temporalFilterUsed = False

				nsm = tree.nsmap

				if len(tree.findall('.//{http://www.opengis.net/ows/1.1}Exception')) > 0 and temporalFilterUsed == True:
					r = requests.get(GetObservation)
					tree = etree.fromstring(r.content)
					nsm = tree.nsmap
					temporalFilterUsed = False
					print GetObservation
				else:
					print GetObservationWtempfilter
				
				# print r.content
				# print 'Without Filter', GetObservation
				# retrieve the sensor data from the request response 
				# tag = '{{{0}}}result'.format(nsm[None])
				# for result in tree.findall('.//{0}'.format(tag)):
				# 	for each in result.getchildren():
				# 		print each
				
				print "Done"
				return
				

			# if temporalFilterUsed == False:
			# 	# manually filter the sensor data outside the temporal range
			# 	pass
	
		return


	def aggregateCheck(self):
		pass

		return


	def aggregate(self):
		pass

		return