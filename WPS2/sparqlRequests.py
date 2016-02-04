

endpoint = 'http://localhost:8089/parliament/sparql?' 

def sparqlQuery(observedProperties, features, tempRange, aggregation):
	global endpoint

	# Retrieve the geometries of the features
	

	for obsProperty in observedProperties:
		# Check out DBPedia to find the observed property and see to which collection of sampling features it links  


		# Retrieve sensors that are linked to the collection of sampling features
		query = r"SELECT DISTINCT ?sos WHERE {{ ?collection <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://def.seegrid.csiro.au/ontology/om/sam-lite#SamplingCollection> . ?collection <http://def.seegrid.csiro.au/ontology/om/om-lite#observedProperty> {0} . ?collection <http://def.seegrid.csiro.au/ontology/om/sam-lite#member> ?FOI .  ?FOI <http://www.opengis.net/ont/geosparql#hasGeometry> ?geom . ?sensor <http://def.seegrid.csiro.au/ontology/om/om-lite#featureOfInterest> ?FOI . ?sensor <http://purl.org/dc/terms/isPartOf> ?sos . }}".format(obsProperty) # still have to add a spatial filter based on the input features
		print query

