import logging
from rdflib import URIRef, BNode, Literal, Graph
from rdflib.namespace import RDF, RDFS, FOAF
import rdflib
import requests
from lxml import etree

logging.basicConfig()

baseURI = "http://localhost:3030"
endpoint = 'http://localhost:8089/parliament/sparql?' 

def capabilities(SOS):
	global baseURI
	global endpoint

	prov = rdflib.Namespace('http://www.w3.org/ns/prov#')
	om_lite = rdflib.Namespace('http://def.seegrid.csiro.au/ontology/om/om-lite#')
	sam_lite = rdflib.Namespace('http://def.seegrid.csiro.au/ontology/om/sam-lite#')
	geo = rdflib.Namespace('http://www.opengis.net/ont/geosparql#')
	owl = rdflib.Namespace('http://www.w3.org/2002/07/owl#')
	dc = rdflib.Namespace('http://purl.org/dc/terms/')
	owl = rdflib.Namespace('https://www.w3.org/2002/07/owl#')
	dbpedia = rdflib.Namespace("http://dbpedia.com.com/ontology/")

	g = Graph()

	# Define observation service
	uriSOS = URIRef(SOS.url)
	g.add( ( uriSOS, RDF.type, prov.Agent) )
	g.add( ( uriSOS, FOAF.name, Literal(SOS.name) ) )
	g.add( ( uriSOS, prov.ActedOnBehalfOf,  URIRef("{0}/{1}".format(baseURI, SOS.organisation.replace(' ', '') ) ) ) )
	g.add( ( uriSOS, dc.accessRights, Literal(SOS.accessConstraints) ) )
	g.add( ( uriSOS, dbpedia.cost , Literal(SOS.accessConstraints) ) )

	for version in SOS.version:
		g.add( ( uriSOS, dc.hasVersion, Literal(version) ) )
	for fomat in SOS.responseFormat:
		g.add( ( uriSOS, dc.hasFormat, Literal(version) ) )

	# procedure a prov:Activity, omlite:procedure;
	count = 1
	for proc, value in SOS.procedure.iteritems():  
		if (proc[:4].lower() == 'http'):
			uriProcedure = URIRef(proc)
		else:
			uriProcedure = URIRef("{0}/PROC/{1}".format(baseURI, proc) ) 

		if (value['obsProperty'][:4] == 'http'):
			obsProperty = URIRef(value['obsProperty'])
		else:
			obsProperty = URIRef("{0}/OBSERVED/{1}".format(baseURI, value['obsProperty'].replace(' ','')) ) 
		
		# check the mapping between observed properties from SOS and as defined by DBPedia 
		# the collections of samplign features are based on the DBPedia definitions
		query = """
			SELECT ?observedProperty
			WHERE {{
			  ?observedProperty <http://www.w3.org/2002/07/owl#sameAs> <{0}> .
			}}""".format("{0}/OBSERVED/{1}".format(baseURI, value['obsProperty'].replace(' ','')))

		r = requests.post(endpoint, data={'query': query}) 
		tree = etree.fromstring(r.content)
		nsm = tree.nsmap

		StandardObsProperty = ''
		try:
			tag = '{{{0}}}result'.format(nsm[None])
			for result in tree.findall('.//{0}'.format(tag)):
				for each in result.getchildren():
					if each.attrib['name'] == 'observedProperty':
						StandardObsProperty = URIRef(each[0].text)
		except:
			continue

		if StandardObsProperty == '':
			print "I have no clue what {0} is...".format(obsProperty)
			continue
		else: 
			print obsProperty, "==", StandardObsProperty

		StandardCollection = URIRef("{0}/FOI_Collection/{1}".format(baseURI, StandardObsProperty) )
		
		g.add( ( StandardCollection, RDF.type, sam_lite.SamplingCollection ) ) 
		g.add( ( StandardCollection, om_lite.observedProperty, StandardObsProperty) )
		g.add( ( uriProcedure, RDF.type, prov.Activity) )
		g.add( ( uriProcedure, RDF.type, om_lite.process) )
		g.add( ( uriProcedure, FOAF.name, Literal(proc) ) )
		g.add( ( uriProcedure, om_lite.observedProperty, obsProperty ) )
		g.add( ( obsProperty, FOAF.name, Literal(SOS.procedure[proc]['obsProperty']) ))

		for i, feature in enumerate(SOS.procedure[proc]['FOI']):
			sensor = URIRef("{0}/{1}/PROC/{2}/SENSOR/{3}".format(baseURI, SOS.organisation.replace(' ', ''), count, i+1) )
			g.add( ( sensor, RDF.type, prov.Agent ) )
			g.add( ( sensor, RDF.type, om_lite.process ) ) 
			g.add( ( sensor, om_lite.procedure, uriProcedure ) )
			g.add( ( uriProcedure, prov.wasAssociatedWith, sensor ) )
			g.add( ( sensor, dc.isPartOf, uriSOS) )

			FOI = URIRef("{0}/{1}/FOI/{2}".format(baseURI, SOS.organisation.replace(' ', ''), feature) )
			if (feature[:4].lower() == 'http'):
				FOI = URIRef(feature)
				
			g.add( ( FOI, FOAF.name, Literal(feature) ) )

			geometry = SOS.featureofinterest[feature]
			g.add( ( FOI, RDF.type, prov.Entity ) )
			g.add( ( FOI, RDF.type, sam_lite.SamplingPoint ) ) 
			g.add( ( FOI, geo.hasGeometry, Literal("<{0}>POINT({1})".format(geometry['coords'][1], geometry['coords'][0]), datatype=geo.wktLiteral ) ) )
			g.add( ( FOI, om_lite.observedProperty, StandardObsProperty) )
			g.add( ( StandardCollection, sam_lite.member, FOI ) )
			g.add( ( sensor, om_lite.featureOfInterest, FOI ) )

			for i, offeringName in enumerate(SOS.featureofinterest[feature]['offerings']):
				offering = URIRef("{0}/{1}/PROC/{2}/OFFERING/{3}".format(baseURI, SOS.organisation.replace(' ', ''), count, i+1 ) )
				
				g.add( ( offering, RDF.type, prov.Entity ) )
				g.add( ( offering, prov.specializationOf, StandardCollection ) )
				g.add( ( offering, FOAF.name, Literal(offeringName) ) )
				g.add( ( offering, sam_lite.member, FOI ) )
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

