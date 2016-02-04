import requests
from lxml import etree

DBPedia = 'http://dbpedia.org/sparql'
myEndpoint = 'http://localhost:8089/parliament/sparql?' 

def sparqlQuery(observedProperties, featureCategory, featureNames, tempRange, aggregation, countries=['the Netherlands', 'Belgium']):
	global myEndpoint

#	Retrieve the geometries of the features via DBPedia
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

#	Retrieve geometries via own endpoint
	if (featureCategory == 'province') or (featureCategory == 'municipality'):
		for i, feature in enumerate(featureNames):
			featureNames[i] = r'?name = "{0}"'.format(feature.title())
		if len(featureNames) == 0:
			featureNames = ''
		else:
			featureNames = "FILTER( {0} )".format(" || ".join(featureNames))
	else: 
		print "wrong featureCategory input"

	query = r"SELECT ?feature ?geom WHERE {{ ?feature <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.com.com/resource/{0}> . ?feature <http://www.opengis.net/ont/geosparql#hasGeometry> ?geom . ?feature <http://xmlns.com/foaf/0.1/name> ?name . {1} }}".format(featureCategory.title(), featureNames)

	# print query 
	r = requests.post(myEndpoint, data={'query': query}) 
	tree = etree.fromstring(r.content)
	nsm = tree.nsmap

	# print r.content
	featureDict = {}
	tag = '{{{0}}}result'.format(nsm[None])
	for result in tree.findall('.//{0}'.format(tag)):
		name = '' 
		geom = ''
		for each in result.getchildren():
			if each.attrib['name'] == 'feature':
				name = each[0].text
			elif each.attrib['name'] == 'geom':
				geom = each[0].text + r"<http://www.opengis.net/ont/geosparql#wktLiteral"
		try:
			featureDict[name] = geom
		except:
			print "could not find feature with geometry!"

	spatialFilter = []
	for key, value in featureDict.iteritems():
		spatialFilter.append("<http://www.opengis.net/def/function/geosparql/sfContains>(?geom,{0}".format(value))
	spatialFilter = "FILTER ( {0} )".format(" || ".join(spatialFilter))

	for obsProperty in observedProperties:
		# Check out DBPedia to find the observed property and see to which collection of sampling features it links  


		# Retrieve sensors that are linked to the collection of sampling features
		query = r"SELECT DISTINCT ?sos WHERE {{ ?collection <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://def.seegrid.csiro.au/ontology/om/sam-lite#SamplingCollection> . ?collection <http://def.seegrid.csiro.au/ontology/om/om-lite#observedProperty> {0} . ?collection <http://def.seegrid.csiro.au/ontology/om/sam-lite#member> ?FOI .  ?FOI <http://www.opengis.net/ont/geosparql#hasGeometry> ?geom . ?sensor <http://def.seegrid.csiro.au/ontology/om/om-lite#featureOfInterest> ?FOI . ?sensor <http://purl.org/dc/terms/isPartOf> ?sos . {1} }}".format(obsProperty, spatialFilter) 
		
		# r = requests.post(myEndpoint, data={'query': query}) 
		print query