from rdflib import URIRef, BNode, Literal, Graph
from rdflib.namespace import RDF, RDFS, FOAF
import rdflib
import requests
from bs4 import BeautifulSoup


baseURI = "http://localhost:3030"

def capabilities(SOS):

	prov = rdflib.Namespace('http://www.w3.org/ns/prov#')
	om_lite = rdflib.Namespace('http://def.seegrid.csiro.au/ontology/om/om-lite#')
	sam_lite = rdflib.Namespace('http://def.seegrid.csiro.au/ontology/om/sam-lite#')
	geo = rdflib.Namespace("http://www.opengis.net/ont/geosparql#")
	
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
	g.add( ( uriSOS, prov.ActedOnBehalfOf,  URIRef("{0}/{1}".format(baseURI, SOS.organisation) ) ) )

	uniqueObsProperties = set()

	# procedure a prov:Activity, omlite:procedure;
	for proc, value in SOS.procedure.iteritems():  
		obsProperty = URIRef("{0}/OP/{1}".format(baseURI, SOS.procedure[proc]['obsProperty']) )
		uriProcedure = URIRef("{0}/OP/{1}/PROC/{2}".format(baseURI, SOS.procedure[proc]['obsProperty'], proc) ) 
		g.add( ( uriProcedure, RDF.type, prov.Activity) )
		g.add( ( uriProcedure, RDF.type, om_lite.procedure) )

		uniqueObsProperties.add(SOS.procedure[proc]['obsProperty'])
		if (SOS.procedure[proc]['obsProperty'][:4] == 'http'):
			# Make a get request to the address
			r = requests.get(SOS.procedure[proc]['obsProperty'])
				# Look for the name of the observed propert that is being described.





		for i, feature in enumerate(SOS.procedure[proc]['FOI']):
			sensor = URIRef("{0}/{1}/PROC/{2}/SENSOR/{3}".format(baseURI, SOS.organisation, proc, i) )
			g.add( ( sensor, RDF.type, prov.Agent ) )
			g.add( ( sensor, RDF.type, om_lite.procedure ) ) 
			g.add( ( uriProcedure, prov.wasAssociatedWith, sensor ) )

			FOI = URIRef("{0}/{1}/PROC/{2}/FOI/{3}".format(baseURI, SOS.organisation, proc, i) )
			geometry = SOS.featureofinterest[feature]
			g.add( ( FOI, RDF.type, prov.Entity ) )
			g.add( ( FOI, RDF.type, sam_lite.SamplingPoint ) ) 
			g.add( ( FOI, geo.hasGeometry, Literal("<{0}> POINT({1})".format(geometry['coords'][1], geometry['coords'][0]), datatype=geo.wktLiteral ) ) )

			g.add( ( sensor, om_lite.featureOfInterest, FOI ) )


	# Retrieve layers
	# endpoint = 'localhost:3030/masterThesis?' 

	# r = requests.get('{0}query=') # check the endpoint for the exact query
	# Match layer with procedure
	#  


	# Link to layers

	# g.serialize('sos.ttl', format='turtle')


	# print g.serialize(format='turtle')



