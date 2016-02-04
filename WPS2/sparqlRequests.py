

endpoint = 'http://localhost:8089/parliament/sparql?' 

def sparqlQuery(observedProperties, features, tempRange, aggregation):
	global endpoint

	for obsProperty in observedProperties:
		# Check out DBPedia to find the observed property and see to which collection of sampling features it links  


		# Retrieve sensors that are linked to the collection of sampling features
		query = "SELECT * WHERE "