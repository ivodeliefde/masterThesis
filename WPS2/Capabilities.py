from rdflib import URIRef, BNode, Literal, Graph
from rdflib.namespace import RDF, RDFS, FOAF
import requests

baseURI = ""

def capabilities(SOS):

	prov = rdflib.Namespace('http://www.w3.org/ns/prov#')
	om_lite = rdflib.Namespace('http://def.seegrid.csiro.au/ontology/om/om-lite')
	
	g = Graph()
	try:
		g.parse("sos.ttl", format="turtle")
	except:
		pass

	# Define observation service
	uriSOS = URIRef("{0}/{1}".format(baseURI, SOS.name) )
	g.add( ( uriSOS, RDF.Type, prov.Agent) )
	g.add( ( uriSOS, foaf.name, Literal(SOS.name) ) )
	g.add( ( uriSOS, prov.ActedOnBehalfOf,  URIRef("{0}/{1}".format(baseURI, SOS.provider)) ) )

	# procedure a prov:Activity, omlite:procedure;
	for proc in SOS.procedure:  
		uriProcedure = URIRef("{0}/{1}".format(baseURI, proc) ) 
		g.add( ( uriProcedure, RDF.type, prov.Entity) )
		g.add( ( uriProcedure, RDF.type, om_lite.procedure) )

		for i, feature in enumerate(SOS.procedure[procedure]['FOI']):
			sensor = URIRef("{0}/{1}/{2}".format(baseURI, procedure, i) )
			g.add( ( sensor, RDF.type, prov.Agent ) )
			g.add( ( sensor, RDF.type, om_lite.sensor ) ) # check with om lite ontology
			g.add( ( sensor, prov.used, uriProcedure ) ) # check with prov ontology


	# Retrieve layers
	endpoint = 'localhost:3030/masterThesis?' 

	r = requests.get('{0}query=') # check the endpoint for the exact query
	# Match layer with procedure
	#  


	# Link to layers

	g.serialize('sos.ttl', format='turtle')
