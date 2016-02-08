import logging
from rdflib import URIRef, BNode, Literal, Graph
from rdflib.namespace import RDF, RDFS, FOAF
import rdflib
import requests

logging.basicConfig()

baseURI = "http://localhost:3030"

def capabilities(SOS):
	global baseURI

	prov = rdflib.Namespace('http://www.w3.org/ns/prov#')
	om_lite = rdflib.Namespace('http://def.seegrid.csiro.au/ontology/om/om-lite#')
	sam_lite = rdflib.Namespace('http://def.seegrid.csiro.au/ontology/om/sam-lite#')
	geo = rdflib.Namespace('http://www.opengis.net/ont/geosparql#')
	owl = rdflib.Namespace('http://www.w3.org/2002/07/owl#')
	dc = rdflib.Namespace('http://purl.org/dc/terms/')
	owl = rdflib.Namespace('https://www.w3.org/2002/07/owl#')

	g = Graph()

	try:
		g.parse("sos.ttl", format="turtle")
	except:
		pass

	# Define observation service
	uriSOS = URIRef(SOS.url)
	g.add( ( uriSOS, RDF.type, prov.Agent) )
	g.add( ( uriSOS, FOAF.name, Literal(SOS.name) ) )
	g.add( ( uriSOS, prov.ActedOnBehalfOf,  URIRef("{0}/{1}".format(baseURI, SOS.organisation.replace(' ', '') ) ) ) )


	# procedure a prov:Activity, omlite:procedure;
	count = 1
	for proc, value in SOS.procedure.iteritems():  
		if (proc[:4].lower() == 'http'):
			uriProcedure = URIRef(proc)
		else:
			uriProcedure = URIRef("{0}/PROC/{1}".format(baseURI, count, proc) ) 
		
		# check the mapping between observed properties from SOS and as defined by DBPedia 
		# the collections of samplign features are based on the DBPedia definitions
		query = """
			SELECT ?observedProperty
			WHERE {
			  ?observedProperty <https://www.w3.org/2002/07/owl#sameAs> <{0}> .
			}""".format(obsProperty)

		r = requests.post(endpoint, data={'query': query}) 
		tree = etree.fromstring(r.content)
		nsm = tree.nsmap

		try:
			tag = '{{{0}}}result'.format(nsm[None])
			for result in tree.findall('.//{0}'.format(tag)):
				for each in result.getchildren():
					if each.attrib['name'] == 'observedProperty':
						StandardObsProperty = each[0].text
		except:
			StandardCollection = URIRef("{0}/FOI_Collection/{2}".format(baseURI, SOS.organisation.replace(' ', ''), SOS.procedure[proc]['obsProperty']) )

		StandardCollection = URIRef("{0}/FOI_Collection/{2}".format(baseURI, StandardObsProperty) )
		
		g.add( ( StandardCollection, RDF.type, sam_lite.SamplingCollection ) ) 
		g.add( ( StandardCollection, om_lite.observedProperty, StandardObsProperty) )
		g.add( ( uriProcedure, RDF.type, prov.Activity) )
		g.add( ( uriProcedure, RDF.type, om_lite.process) )
		g.add( ( uriProcedure, FOAF.name, Literal(proc) ) )
		g.add( ( uriSOS, om_lite.observedProperty, Literal(SOS.procedure[proc]['obsProperty']) ) )

		for i, feature in enumerate(SOS.procedure[proc]['FOI']):
			sensor = URIRef("{0}/{1}/PROC/{2}/SENSOR/{3}".format(baseURI, SOS.organisation.replace(' ', ''), count, i+1) )
			g.add( ( sensor, RDF.type, prov.Agent ) )
			g.add( ( sensor, RDF.type, om_lite.process ) ) 
			g.add( ( sensor, om_lite.procedure, Literal(proc) ) )
			g.add( ( uriProcedure, prov.wasAssociatedWith, sensor ) )
			g.add( ( sensor, dc.isPartOf, uriSOS) )

			if (feature[:4].lower() == 'http'):
				FOI = URIRef(feature)
			else:
				FOI = URIRef("{0}/{1}/FOI/{2}".format(baseURI, SOS.organisation.replace(' ', ''), feature) )
			g.add( ( FOI, FOAF.name, Literal(feature) ) )

			geometry = SOS.featureofinterest[feature]
			g.add( ( FOI, RDF.type, prov.Entity ) )
			g.add( ( FOI, RDF.type, sam_lite.SamplingPoint ) ) 
			g.add( ( FOI, geo.hasGeometry, Literal("<{0}>POINT({1})".format(geometry['coords'][1], geometry['coords'][0]), datatype=geo.wktLiteral ) ) )
			g.add( ( FOI, om_lite.observedProperty, obsProperty) )
			g.add( ( StandardCollection, sam_lite.member, FOI ) )
			g.add( ( sensor, om_lite.featureOfInterest, FOI ) )

		for i, offeringName in enumerate(SOS.procedure[proc]['offerings']):
			offering = URIRef("{0}/{1}/PROC/{2}/OFFERING/{3}".format(baseURI, SOS.organisation.replace(' ', ''), count, i+1 ) )
			
			g.add( ( offering, RDF.type, prov.Entity ) )
			g.add( ( offering, prov.specializationOf, StandardCollection ) )
			g.add( ( offering, FOAF.name, offeringName ) )
			g.add( ( offering, om_lite.procedure, Literal(proc) ) )

		count += 1

	endpoint = 'http://localhost:8089/parliament/sparql?' 
	
	count = 0
	triples = ""
	for s,p,o in g.triples((None, None, None)):
		if o[:4].lower() == 'http':
			triples += '<{0}> <{1}> <{2}> .'.format(s,p,o)
		else:
			triples += '<{0}> <{1}> "{2}" .'.format(s,p,o)
		if (count % 50 == 0) and (count > 0):
			# send data to enpoint
			query = "INSERT DATA { " + triples + "}"
			# print query
			r = requests.post(endpoint, data={'update': query}) 
			
			triples = ""
			count += 1
		else:
			count += 1
	# Storing the remaining triples
	query = "INSERT DATA { " + triples + "}"
	r = requests.post(endpoint, data={'update': query}) 
	# print query

