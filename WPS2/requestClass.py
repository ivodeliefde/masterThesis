import requests
from lxml import etree

DBPedia = 'http://dbpedia.org/sparql'
myEndpoint = 'http://localhost/strabon-endpoint-3.3.2-SNAPSHOT/Query' 


class Request():
	def __init__(self, observedProperties, featureCategory, featureNames, tempRange, aggregation):


		self.observedProperties = observedProperties
		self.featureCategory = featureCategory
		self.featureNames = featureNames # list with names of input features
		self.featureDict = {} # dictionary with names and corresponding geometries
		self.tempRange = tempRange
		self.aggregation = aggregation
		self.sensors = {} # the sensors with their measurements: {obsProperty1: {sensor1: {'location': location, 'sos': sos, 'observations': values}, sensor2: {'location': location, 'sos': sos, 'observations': values} }, obsProperty2: {sensor3: {'location': location, 'sos': sos, 'observations': values} } }
		self.sos = {}
		self.results = {} # the features with their aggregated sensor data: {feature1: {obsProperty1: value, obsProperty2: value}, feature2: {obsProperty1: value, obsProperty2: value} }

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
		  ?feature ?geom 
		WHERE {{ 
		  ?feature <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/resource/{0}> . 
		  ?feature <http://www.opengis.net/ont/geosparql#hasGeometry> ?geom . 
		  ?feature <http://xmlns.com/foaf/0.1/name> ?name . 
		  {1}
		}}""".format(self.featureCategory.title(), featureNamesFilter)
		print 'QUERY:', query
		# print query 
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
					name = each[0].text
				elif each.attrib['name'] == 'geom':
					geom = each[0].text 
			try:
				self.featureDict[name] = geom
			except:
				print "could not find feature with geometry!"

		for key, value in self.featureDict.iteritems():
			print key, value
		return

		#----------------------------------------------------------------------#
		# Find relevant sensors 
		#----------------------------------------------------------------------#

		
		return

	def getSensorsVector(self):
		if self.featureCategory.lower() == 'raster':
			print 'Vector function cannot be applied for a raster request'
			return
		else:
			print 'Request data for vector geometry'

		spatialFilter = []
		for key, value in self.featureDict.iteritems():
			spatialFilter.append('<http://www.opengis.net/def/function/geosparql/sfContains>(?geom,"{0}"^^<http://www.opengis.net/ont/geosparql#wktLiteral>'.format(value))
		spatialFilter = 'FILTER ( {0} ) )'.format(' || '.join(spatialFilter))

		for obsProperty in self.observedProperties:
			# Check out DBPedia to find the observed property and see to which collection of sampling features it links  

			# Retrieve sensors that are linked to the collection of sampling features
			self.sensors[obsProperty] = {}
			query = r"""
				SELECT DISTINCT 
				  ?sensor ?geom ?FOIname ?procName ?sos
							
				WHERE {{

				   ?collection <http://def.seegrid.csiro.au/ontology/om/om-lite#observedProperty> ?obsProperty . 
				   ?obsProperty <http://xmlns.com/foaf/0.1/name> {0} .
				   ?collection <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://def.seegrid.csiro.au/ontology/om/sam-lite#SamplingCollection> . 

				   ?collection <http://def.seegrid.csiro.au/ontology/om/sam-lite#member> ?FOI .  
				 

				   ?sensor <http://def.seegrid.csiro.au/ontology/om/om-lite#featureOfInterest> ?FOI . 
				   ?FOI <http://xmlns.com/foaf/0.1/name> ?FOIname .
				   ?procedure <http://www.w3.org/ns/prov#wasAssociatedWith> ?sensor .
				   ?procedure <http://xmlns.com/foaf/0.1/name> ?procName .
				   
				   ?sensor <http://purl.org/dc/terms/isPartOf> ?sos . 
			  {1}
			}}""".format(obsProperty, spatialFilter) 
			
			print query
			r = requests.post(myEndpoint, data={'view':'HTML', 'query': query, 'format':'HTML', 'handle':'plain', 'submit':'Update' }) 
			print r.content
			tree = etree.fromstring(r.content)
			nsm = tree.nsmap

			tag = '{{{0}}}result'.format(nsm[None])
			for result in tree.findall('.//{0}'.format(tag)):
				sensor = ''
				sensorFOI = ''
				sensorSOS = ''
				sensorOffering = ''
				sensorProcedure = ''
				sensorGeom = ''
				for each in result.getchildren():
					if each.attrib['name'] == 'sensor':
						sensor = each[0].text
					elif each.attrib['name'] == 'FOIname':
						sensorFOI = each[0].text
					elif each.attrib['name'] == 'sos':
						sensorSOS = each[0].text
					elif each.attrib['name'] == 'geom':
						sensorGEOM = each[0].text
					elif each.attrib['name'] == 'procName':
						sensorProcedure = each[0].text
				if self.sensors[obsProperty][sensor] in self.sensors[obsProperty]:
					self.sensors[obsProperty][sensor] = {'location': sensorGEOM, 'sos': sensorSOS, 'FOI': sensorFOI, 'procedure': sensorProcedure, 'offerings':[], 'observations': []}

				if sensorSOS in self.sos:
					self.sos[sensorSOS].append(sensor)
				else:
					self.sos[sensorSOS] = [sensor]

		
		return

	def getSensorsBBOX(self):
		if self.featureCategory.lower() == 'raster':
			print 'Create bounding box around grid cells'
		else:
			print 'Create bounding box around vector geometry'

		return

	def getSensorsRaster(self):
		if self.featureCategory.lower() == 'raster':
			print 'Request data for raster cells'
		else:
			print 'Find raster cells intersecting the vector geometry'

		for sos, sensors in self.sos.iteritems():
			# offerings are required in the get observation request. Therefore, the offerings need to be part of the semantic description of the sos
			# GetObservation = '{0}service=SOS&version=2.0.0&request=GetObservation&procedure={1}&offering={2}&observedproperty={3}&responseformat=http://www.opengis.net/om/2.0'.format(sos, procedure, offering, self.procedure[procedure]['obsProperty'])
			
			pass
		return

	def getObservationData(self):
		for sos, sensors in self.sos.iteritems():
			# offerings are required in the get observation request. Therefore, the offerings need to be part of the semantic description of the sos
			# GetObservation = '{0}service=SOS&version=2.0.0&request=GetObservation&procedure={1}&offering={2}&observedproperty={3}&responseformat=http://www.opengis.net/om/2.0'.format(sos, procedure, offering, self.procedure[procedure]['obsProperty'])
			
			pass
		return


	def integrateSources(self):
		pass

		return


	def aggregateCheck(self):
		pass

		return


	def aggregate(self):
		pass

		return