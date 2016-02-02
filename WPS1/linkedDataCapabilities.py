from rdflib import URIRef, BNode, Literal, Graph
from rdflib.namespace import RDF, RDFS, FOAF
import rdflib
import requests


baseURI = "http://localhost:3030"

def capabilities(SOS):

	prov = rdflib.Namespace('http://www.w3.org/ns/prov#')
	om_lite = rdflib.Namespace('http://def.seegrid.csiro.au/ontology/om/om-lite')
	sam_lite = rdflib.Namespace('http://def.seegrid.csiro.au/ontology/om/sam-lite')
	
	g = Graph()
	try:
		g.parse("sos.ttl", format="turtle")
	except:
		pass

	# Defined a 'sam_lite.SamplingCollection' for every observed property

	# Define observation service
	uriSOS = URIRef("{0}/{1}".format(baseURI, SOS.name.replace(' ','-')) )
	g.add( ( uriSOS, RDF.type, prov.Agent) )
	g.add( ( uriSOS, FOAF.name, Literal(SOS.name) ) )
	g.add( ( uriSOS, prov.ActedOnBehalfOf,  URIRef(SOS.organisation) ) )

	# procedure a prov:Activity, omlite:procedure;
	for proc, value in SOS.procedure.iteritems():  
		uriProcedure = URIRef(proc) 
		g.add( ( uriProcedure, RDF.type, prov.Entity) )
		g.add( ( uriProcedure, RDF.type, om_lite.procedure) )

		for i, feature in enumerate(SOS.procedure[proc]['FOI']):
			sensor = URIRef("{1}/{2}".format(baseURI, proc, i) )
			g.add( ( sensor, RDF.type, prov.Agent ) )
			g.add( ( sensor, RDF.type, om_lite.sensor ) ) # check with om lite ontology
			g.add( ( sensor, prov.used, uriProcedure ) ) # check with prov ontology


	# Retrieve layers
	# endpoint = 'localhost:3030/masterThesis?' 

	# r = requests.get('{0}query=') # check the endpoint for the exact query
	# Match layer with procedure
	#  


	# Link to layers

	# g.serialize('sos.ttl', format='turtle')


	print g.serialize(format='turtle')
