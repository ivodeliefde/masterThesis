# -*- coding: utf-8 -*-
import os
from rdflib import URIRef, BNode, Literal, Graph
from rdflib.namespace import RDF, RDFS, FOAF
import rdflib
import requests
from lxml import etree
from postPURLS import CreatePurls, postPURLbatch
import  progressbar

import logging
# logging.basicConfig(level=logging.INFO)

baseURI = "http://localhost:8099/masterThesis_tudelft" 
# endpoint = 'http://localhost:8089/parliament/sparql?' 
endpoint = "http://localhost:8083/strabon-endpoint-3.3.2-SNAPSHOT/Query"
purlBatch = 'D:/purlBatches/SOS/SOSbatch'

def capabilities(SOS):
	global baseURI
	global endpoint
	global purlBatch

	# Create PURL batch file to store PURLs 
	CreatePurls('open', purlBatch)

	prov = rdflib.Namespace('http://www.w3.org/ns/prov#')
	om_lite = rdflib.Namespace('http://def.seegrid.csiro.au/ontology/om/om-lite#')
	sam_lite = rdflib.Namespace('http://def.seegrid.csiro.au/ontology/om/sam-lite#')
	geo = rdflib.Namespace('http://strdf.di.uoa.gr/ontology#')
	owl = rdflib.Namespace('http://www.w3.org/2002/07/owl#')
	dc = rdflib.Namespace('http://purl.org/dc/terms/')
	dbpedia = rdflib.Namespace("http://dbpedia.com/ontology/")

	g = Graph()

	# Define observation service
	uriSOS = URIRef("{0}/{1}".format(baseURI, SOS.name.replace(' ','')))
	g.add( ( uriSOS, RDF.type, prov.Agent) )
	g.add( ( uriSOS, FOAF.name, Literal(SOS.name) ) )
	g.add( ( uriSOS, prov.ActedOnBehalfOf,  URIRef("{0}/{1}".format(baseURI, SOS.organisation.replace(' ', '') ) ) ) )
	# g.add( ( uriSOS, dc.accessRights, Literal(SOS.accessConstraints) ) )
	# g.add( ( uriSOS, dbpedia.cost , Literal(SOS.accessConstraints) ) )
	g.add( ( uriSOS, owl.sameAs, URIRef(SOS.url) ) )

	for version in SOS.version:
		g.add( ( uriSOS, dc.hasVersion, Literal(version) ) )
	for i,format in enumerate(SOS.responseFormat):
		# print format
		uriFormat = URIRef("{0}/responseFormat_{1}".format(baseURI, i))
		g.add( ( uriSOS, dc.hasFormat, uriFormat ) )
		g.add( ( uriFormat, RDFS.label, Literal('responseFormat') ) )
		g.add( ( uriFormat, FOAF.name, Literal(format.replace(' ','') ) ) ) 
		CreatePurls([uriFormat], purlBatch)
	# for i,format in enumerate(SOS.resourceDescriptionFormat):
	#   uriFormat = URIRef("{0}/{1}".format(baseURI, i))
	#   g.add( ( uriSOS, dc.hasFormat, uriFormat ) )
	#   g.add( ( uriFormat, RDFS.label, Literal('resourceDescriptionFormat') ) )
	#   g.add( ( uriFormat, FOAF.name, Literal(format.replace(' ','') )) )
	#   CreatePurls([uriFormat], purlBatch)


	# Create a PURL for every SOS URI 
	CreatePurls([uriSOS], purlBatch)

	definedCollections = []

	# procedure a prov:Activity, omlite:procedure;
	count = 0
	# print "Creating linked data from sensor data"
	with progressbar.ProgressBar(max_value=len(SOS.procedure)) as bar:
		for proc, value in SOS.procedure.iteritems():  
			count += 1
			bar.update(count)

			# if (proc[:4].lower() == 'http'):
			#   uriProcedure = URIRef(proc)
			# else:
			uriProcedure = URIRef("{0}/PROC_{1}".format(baseURI, count).replace(' ','') ) 
			# Create a PURL for every procedure URI 
			CreatePurls([uriProcedure], purlBatch)

			for observedProperty in SOS.procedure[proc]:
				# if (observedProperty[:4] == 'http'):
				#   obsProperty = URIRef(observedProperty)
				# else:
				obsProperty = URIRef("{0}/OBSERVED_{1}".format(baseURI, observedProperty.replace(' ','').replace('http://','').replace('.','_').replace('/','_') ) ) 
				# Create a PURL for every observed property URI 
				CreatePurls([obsProperty], purlBatch)
				
				# check the mapping between observed properties from SOS and as defined by DBPedia 
				# the collections of samplign features are based on the DBPedia definitions
				query = """
					SELECT ?observedProperty
					WHERE {{
					  ?observedProperty <http://www.w3.org/2002/07/owl#sameAs> <{0}> .
					}}""".format(obsProperty)

				r = requests.post(endpoint, data={'view':'HTML', 'query': query, 'format':'SPARQL/XML' , 'handle':'download', 'submit':'Query' })
				# print r
				# print r.text 
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

				StandardCollection = URIRef("{0}/FOI_Collection_{1}".format(baseURI, StandardObsProperty).replace(' ','') )
				if StandardCollection in definedCollections:
					# the collection is already defined 
					pass
				else:
					# the collection has not yet been defined
					g.add( ( StandardCollection, RDF.type, sam_lite.SamplingCollection ) ) 
					g.add( ( StandardCollection, om_lite.observedProperty, StandardObsProperty) )
					# add collection to list with defined collections
					definedCollections.append(StandardCollection)


				g.add( ( uriProcedure, RDF.type, prov.Activity) )
				g.add( ( uriProcedure, RDF.type, om_lite.process) )
				g.add( ( uriProcedure, FOAF.name, Literal(proc) ) )
				g.add( ( uriProcedure, om_lite.observedProperty, obsProperty ) )
				g.add( ( obsProperty, FOAF.name, Literal(observedProperty) ))

			
				# Create a PURL for every collection URI 
				CreatePurls([StandardCollection], purlBatch)

				for i, feature in enumerate(SOS.procedure[proc][observedProperty]['FOI']):
					sensor = URIRef("{0}/{1}_PROC_{2}_SENSOR_{3}".format(baseURI, SOS.organisation, count, i+1).replace(' ', '') )
					g.add( ( sensor, RDF.type, prov.Agent ) )
					g.add( ( sensor, RDF.type, om_lite.process ) ) 
					g.add( ( sensor, om_lite.procedure, uriProcedure ) )
					g.add( ( uriProcedure, prov.wasAssociatedWith, sensor ) )
					g.add( ( sensor, dc.isPartOf, uriSOS) )

					# if (feature[:4].lower() == 'http'):
					#   FOI = URIRef(feature)
					# else:
					FOI = URIRef("{0}/{1}_FOI_{2}".format(baseURI, SOS.organisation, feature.replace('http://','').replace('.','_')).replace(' ', '') )

					g.add( ( FOI, FOAF.name, Literal(feature) ) )

					geometry = SOS.featureofinterest[feature]
					g.add( ( FOI, RDF.type, prov.Entity ) )
					g.add( ( FOI, RDF.type, sam_lite.SamplingPoint ) ) 
					g.add( ( FOI, geo.hasGeometry, Literal("POINT({0}); <{1}>".format(geometry['coords'][0], geometry['coords'][1]), datatype=geo.WKT ) ) )
					g.add( ( FOI, om_lite.observedProperty, StandardObsProperty) )
					g.add( ( StandardCollection, sam_lite.member, FOI ) )
					g.add( ( sensor, om_lite.featureOfInterest, FOI ) )
						

					# Create a PURL for every FOI and sensor URI 
					CreatePurls([FOI, sensor], purlBatch)

					for i, offeringName in enumerate(SOS.featureofinterest[feature]['offerings']):
						# print count, offeringName
						offering = URIRef("{0}/{1}_PROC_{2}_OFFERING_{3}".format(baseURI, SOS.organisation, count, offeringName.replace('.','_') ).replace(' ', '') )
						# Create a PURL for every offering URI 
						CreatePurls([offering], purlBatch)
						
						g.add( ( offering, RDF.type, prov.Entity ) )
						g.add( ( offering, prov.specializationOf, StandardCollection ) )
						g.add( ( offering, FOAF.name, Literal(offeringName) ) )
						g.add( ( offering, sam_lite.member, FOI ) )
						g.add( ( offering, om_lite.procedure, Literal(proc) ) )



	# print "Sending triples to endpoint"
	# with progressbar.ProgressBar(max_value=len(g)) as bar:
		# print "send data to endpoint"
			# countTriples = 0
		# triples = ""
		# for s,p,o in g.triples((None, None, None)):
		#   if str(type(o)) == "<class 'rdflib.term.Literal'>":
		#       if o.datatype != None:
		#           # print o
		#           # print o.datatype
		#           triples += u'<{0}> <{1}> "{2}"^^<{3}> . \n'.format(s,p,o,o.datatype)
		#           # print u'<{0}> <{1}> "{2}"^^<{3}> . \n'.format(s,p,o,o.datatype)
		#       else:
		#           triples += u'<{0}> <{1}> "{2}" . \n'.format(s,p,o)
		#   elif str(type(o)) == "<class 'rdflib.term.URIRef'>":
		#       triples += u'<{0}> <{1}> <{2}> . \n'.format(s,p,o)
		#   if (countTriples % 100 == 0) and (countTriples > 0):
		#       # send data to enpoint
		#       query = "INSERT DATA { " + triples + "}"
		#       # print query
		#       r = requests.post(endpoint, data={'view':'HTML', 'query': query, 'format':'HTML', 'outputformat':'SPARQL/XML' , 'handle':'plain', 'submit':'Update' }) 
		#       # print r
		#       if str(r) != '<Response [200]>':
		#           print "Response: {0}".format(r)
		#           # print query
		#           print r.text
				
		#       triples = ""
		#       countTriples += 1
		#   else:
		#       countTriples += 1
		#   bar.update(countTriples)
	# Storing the remaining triples
	# query = "INSERT DATA { " + triples + "}"
	# r = requests.post(endpoint, data={'view':'HTML', 'query': query, 'format':'HTML', 'outputformat':'SPARQL/XML' , 'handle':'plain', 'submit':'Update' }) 
	# # print r
	
	# Create directory for temporary files 
	# if not os.path.exists('D:/tempFiles/'):
	#     os.makedirs('D:/tempFiles/')

	payload = {'dbname': 'endpoint', 'username': 'Ivo', 'password':'gps', 'port':'5432', 'hostname':'localhost', 'dbengine':'postgis'}
	session = requests.Session()
	r = session.post('http://localhost:8083/strabon-endpoint-3.3.2-SNAPSHOT/DBConnect', data=payload)
	# with open('D:/tempFiles/sensors{0}.xml'.format(SOS.organisation.replace(' ', '')), "w") as f:
	#   # print type(g.serialize(format="turtle"))
	#   f.write(unicode(g.serialize(format="turtle")))
	g.serialize('sensors{0}.xml'.format(SOS.organisation.replace(' ', '')),format="turtle")
	g = Graph()
	# print 'file:///{0}/sensors{1}.xml'.format(os.getcwd(),SOS.organisation.replace(' ', ''))
	r = session.post(endpoint[:-5]+'Store', data={'view':'HTML', 'format':'Turtle', 'url':'file:///{0}/sensors{1}.xml'.format(os.getcwd(),SOS.organisation.replace(' ', '')), 'fromurl':'Store from URI' }) 



	# if str(r) != '<Response [200]>':
	#     print "Response: {0}".format(r)
	#     # print query
	#     print r.text

	# bar.update(countTriples)

	postPURLbatch(purlBatch,'admin', 'password')

	return

