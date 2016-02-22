# -*- coding: utf-8 -*-
from rdflib import URIRef, BNode, Literal, Graph
from rdflib.namespace import RDF, RDFS, FOAF
import rdflib
import psycopg2
import  progressbar
import time
import os
import unicodedata
import requests
from shapely import *
from shapely.wkt import loads
from postPURLS import postPURLbatch, CreatePurls

import pyttsx
engine = pyttsx.init()

BaseURI = "http://localhost:8099/masterThesis_tudelft/" 
# endpoint = 'http://localhost:8089/parliament/sparql?' 
endpoint = "http://localhost/strabon-endpoint-3.3.2-SNAPSHOT/Query"

purlBatch = 'D:/purlBatches/purlBatch'

def getData(dbms_name, table, user, password, AdmUnit=True):
	# Connect to the Postgres database
	conn = psycopg2.connect(host="localhost", port='5433', database=dbms_name, user=user, password=password) 
	conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

	cur = conn.cursor()

	# print conn.encoding
	conn.set_client_encoding('UTF-8')

	if AdmUnit == True:
		# Retrieve the names and geometries of the administrative unites
		query = "select name, ST_astext(geom) from {0};".format(table)
		
	else:
		# Retrieve the ID, landcover type and geometries of the CORINE dataset
		query = "select id, code_12, ST_astext(geom) from {0};".format(table)

	cur.execute(query)
	data = cur.fetchall()

	# conn.commit()

	cur.close()
	conn.close()
	
	return data

# dminUnitTable2RDF takes a table with administrative units which all have a name and a geometry as input and stores it in an RDF file
def AdminUnitTable2RDF(table, country, AdmUnitType):
	if AdmUnitType == 'municipality':
		if country == 'Netherlands':
			global NL_provinces
			provinces = NL_provinces
		elif country == 'Belgium':
			global BE_provinces
			provinces = BE_provinces
	elif AdmUnitType == 'province':
		if country == 'Netherlands':
			global NL_country
			inCountry = NL_country
		elif country == 'Belgium':
			global BE_country
			inCountry = BE_country

	# GeoSPARQL vocabulary
	geom = rdflib.Namespace("http://www.opengis.net/ont/geosparql#")
	# DBPedia
	dbpedia = rdflib.Namespace("http://dbpedia.com.com/resource/")
	# Dublin core
	dc = rdflib.Namespace('http://purl.org/dc/terms/')

	# Create a graph
	g = Graph()
	
	global endpoint
	global BaseURI

	# Add administrative units with links to the graph
	print "Creating linked data from {0} {1} dataset".format(AdmUnitType, country)
	with progressbar.ProgressBar(max_value=len(table)) as bar:

		# if not os.path.exists('{0}/'.format( AdmUnitType.lower() ) ):
		# 	os.makedirs('{0}/'.format( AdmUnitType.lower() ))
		triples = u""
		for i, row in enumerate(table):
			geometry = row[1]
			# print row
			# try:
			# 	print type(row[0]), row[0]
			name = row[0].decode('utf-8').lower()
			# 	print type(name)
			# except:
			# name = unicodedata.normalize('NFC', unicode(name))
			# name = name.encode('utf-8')
			try:
				if '"' in name:
					name = name.replace('"', '')
				name = name.replace(' ', '_')
			except:
				print 'error:',row[0]
			
			
			if name == 'limburg':
				thing = URIRef(u'{0}{1}/{2}({3})'.format( BaseURI, AdmUnitType.lower(), name, country ) )
			else:
				thing = URIRef(u'{0}{1}/{2}'.format( BaseURI, AdmUnitType.lower(), name ) )

			if AdmUnitType.lower() == "country":
				g.add( (thing, RDF.type, dbpedia.Country) )
			elif AdmUnitType.lower() == "province":
				g.add( (thing, RDF.type, dbpedia.Province) )
			elif AdmUnitType.lower() == "municipality":
				g.add( (thing, RDF.type, dbpedia.Municipality) )

			g.add( (thing, FOAF.name, Literal(row[0])) )
			
			g.add( (thing, geom.hasGeometry, Literal("<http://www.opengis.net/def/crs/EPSG/0/4258>{0}".format(geometry), datatype=geom.wktLiteral ) ) )
			
			CreatePurls([thing],purlBatch)

			if AdmUnitType == 'municipality':
				parentProvince = geomInGeoms(geometry, provinces)
				if len(parentProvince) > 1:
					'Municipality {0} is in multiple provinces: {1}'.format(row[0], parentProvince)
				else:
					parentName = parentProvince[0].decode('utf-8')
					parentName = unicodedata.normalize('NFC', unicode(parentName))
					if '"' in parentName:
						parentName = parentName('"', '')
					parentName = parentName.replace(' ', '_')
					
					parent = URIRef(u'{0}province/{1}'.format( BaseURI, parentName ) )

					g.add( ( parent, dc.hasPart, thing ) )

					g.add( ( thing, dc.isPartOf, parent ) )
					
			elif AdmUnitType == 'province':
				# print 'checking out parent country' 
				
				parentName =  inCountry[0][0].decode('utf-8')
				parentName = unicodedata.normalize('NFC', unicode(parentName))
				if '"' in parentName:
					parentName = parentName('"', '')

				parent = URIRef('{0}{1}/{2}'.format( BaseURI, 'country', parentName ) )
					
				g.add( ( parent, dc.hasPart, thing ) )

				g.add( ( thing, dc.isPartOf, parent ) )


			for s,p,o in g.triples((None, None, None)):
				if str(type(o)) == "<class 'rdflib.term.Literal'>":
					triples += u'<{0}> <{1}> "{2}" . \n'.format(s,p,o)
				else:
					# print type(o)
					triples += u'<{0}> <{1}> <{2}> . \n'.format(s,p,o)
			g = Graph()


			if i % 10 == 0:
				sendTriplesToEndpoint(triples)
				triples = u''
			
			bar.update(i+1)
				# Write the graph to a RDF file in the turtle format
				
				# g.serialize(u'{0}/{1}'.format( AdmUnitType.lower(), name ) , format='turtle')
				
		if len(triples) > 0:
			sendTriplesToEndpoint(triples)
		bar.update(i+1)	
		# g.serialize('AdmUnits.ttl', format='turtle')			

	return

def geomInGeoms(geomWKT, geoms):
	# print geomWKT
	theGeom = loads(geomWKT)
	# print theGeom
	parents = []

	for row in geoms:
		name, GeomWKT = row[0], row[1]
		aGeom = loads(GeomWKT)
		if aGeom.contains(theGeom) or aGeom.intersects(theGeom):
			parents.append(name)

	return parents

# LandcoverTable2RDF takes a table with landcover data which all have a name and a geometry as input and stores it in an RDF file
def LandcoverTable2RDF(table):
	global NL_provinces
	global BE_provinces
	global NL_country
	global BE_country

	# GeoSPARQL vocabulary
	geom = rdflib.Namespace("http://www.opengis.net/ont/geosparql#")
	# DBPedia
	dbpedia = rdflib.Namespace("http://dbpedia.com/resource/")

	# Read the CORINE Land cover legend file and store it in a Python dictionary
	CLC_legend = {}
	with open("clc_legend.csv", 'r') as legend:
		for i, line in enumerate(legend):
			if i > 0:
				lineList = line.split(';')
				CLC_legend[lineList[1]] = lineList[2]
	legend.close()

	# Create a graph
	g = Graph()
	
	global outputFile
	global BaseURI
	global endpoint
	global purlBatch

	print "Creating linked data from CORINE 2012 Legend"
	# if not os.path.exists('landcover/legend/'):
	# 	os.makedirs('landcover/legend/')

	j = 0
	with progressbar.ProgressBar(max_value=len(CLC_legend)) as bar:
		for key, value in CLC_legend.iteritems():
			# Linking URI as subclass of Landcover definition on DBPedia
			legendType = URIRef("{0}landcover/legend/CLC_{1}".format(BaseURI, key) )
			g.add( ( legendType, RDFS.subClassOf , dbpedia.Land_cover ) )
			g.add( ( legendType, FOAF.name , Literal(value) ) )
			# g.serialize("landcover/legend/CLC_{0}".format(key), format='turtle')
			CreatePurls([legendType],purlBatch)
			g = Graph()
			bar.update(i)
			j += 1


	print "Creating linked data from CORINE 2012 dataset"
	with progressbar.ProgressBar(max_value=len(table)) as bar:
		triples = ''
		for i, row in enumerate(table):
			
			ID, Landcover, geometry = row

			thing = URIRef("{0}landcover/{1}".format( BaseURI, ID ) )
			CreatePurls([thing],purlBatch)
			g.add( (thing, RDF.type, URIRef("{0}landcover/legend/CLC_{1}".format(BaseURI, Landcover) ) ) )
			g.add( (thing, geom.hasGeometry, Literal("<http://www.opengis.net/def/crs/EPSG/0/4258>{0}".format(geometry), datatype=geom.wktLiteral ) ) )

			# overlaps = [geomInGeoms(geometry, NL_provinces), geomInGeoms(geometry, BE_provinces), geomInGeoms(geometry, NL_municipalities), geomInGeoms(geometry, BE_municipalities)]
			# for j, featureList in enumerate(overlaps):
			# 	for feature in featureList:
			# 		parentName = feature[0].decode('utf-8').lower()
			# 		parentName = unicodedata.normalize('NFC', unicode(parentName))
					
			# 		if '"' in parentName:
			# 			parentName = parentName('"', '')
			# 		parentName = parentName.replace(' ', '_')

			# 		if j < 3:
			# 			parentURI = URIRef(u'{0}{1}/{2}'.format( BaseURI, 'province', parentName ) )
			# 		else:
			# 			parentURI = URIRef(u'{0}{1}/{2}'.format( BaseURI, 'municipality', parentName ) )
					

			# 		g.add( ( thing, geom.intersects, parentURI) )


			
			# send data to enpoint
			for s,p,o in g.triples((None, None, None)):
				# print s,p,o
				if str(type(o)) == "<class 'rdflib.term.Literal'>":
					triples += u'<{0}> <{1}> "{2}" . \n'.format(s,p,o)
				elif str(type(o)) == "<class 'rdflib.term.URIRef'>":
					triples += u'<{0}> <{1}> <{2}> . \n'.format(s,p,o)
				else:
					print type(o)
			g = Graph()
			

			# Write the graph to a RDF file in the turtle format
			# g.serialize("{0}.ttl".format('landcover/{0}'.format(ID)), format='turtle')
			
			if i % 200 == 0:
				sendTriplesToEndpoint(triples)
				triples = ''
				bar.update(i+1)

		if len(triples) > 0:
			sendTriplesToEndpoint(triples)

			bar.update(i+1)

			
			
	
	return

def EEA2RDF(table, resolution):
	# global NL_provinces
	# global BE_provinces
	# global NL_country
	# global BE_country

	# GeoSPARQL vocabulary
	geom = rdflib.Namespace("http://www.opengis.net/ont/geosparql#")
	# DBPedia
	dbpedia = rdflib.Namespace("http://dbpedia.org/resource/")
	# Dublin core
	dc = rdflib.Namespace('http://purl.org/dc/terms/')

	g = Graph()
	
	global outputFile
	global BaseURI
	global purlBatch

	print "Creating linked data from EEA reference GRID {0}".format(resolution)
	# if not os.path.exists('raster/'):
	# 	os.makedirs('raster/')

	with progressbar.ProgressBar(max_value=len(table)) as bar:
		raster = URIRef('{0}raster/{1}'.format(BaseURI, resolution))
		g.add( ( raster, RDF.type, dbpedia.Raster ) )
		CreatePurls([raster],purlBatch)
		
		triples = u''
		for i, row in enumerate(table):
			name, geometry = row
			cellURI = URIRef('{0}raster/{1}'.format(BaseURI, name))
			g.add( ( raster, RDF.type, dbpedia.Raster ) )
			g.add( ( cellURI, FOAF.name, Literal(name) ) )
			g.add( ( cellURI, dc.isPartOf , raster ) )
			g.add( ( cellURI, geom.hasGeometry, Literal("<http://www.opengis.net/def/crs/EPSG/0/4258>{0}".format(geometry), datatype=geom.wktLiteral )  ) )
			CreatePurls([cellURI],purlBatch)
			

			
			# send data to enpoint
			for s,p,o in g.triples((None, None, None)):
				# print s,p,o
				if str(type(o)) == "<class 'rdflib.term.Literal'>":
					triples += u'<{0}> <{1}> "{2}" . \n'.format(s,p,o)
				elif str(type(o)) == "<class 'rdflib.term.URIRef'>":
					triples += u'<{0}> <{1}> <{2}> . \n'.format(s,p,o)
				else:
					print type(o)
			
			g = Graph()

			if i % 20 == 0:
				sendTriplesToEndpoint(triples)
				triples = u''
			bar.update(i+1)
		# Write the graph to a RDF file in the turtle format
		# try:
		# 	unicode(name)
		# except:
		# 	name = name.decode('utf-8')

		# g.serialize(u'raster/{0}'.format(resolution), format='turtle')
		# g = Graph()
		if len(triples) > 0:
			sendTriplesToEndpoint(triples)

		bar.update(i+1)
		
	return 

def sendTriplesToEndpoint(triples):
	query = u"INSERT DATA { " + triples + "}"
	r = requests.post(endpoint, data={'view':'HTML', 'query': query, 'format':'HTML', 'outputformat':'SPARQL/XML' , 'handle':'plain', 'submit':'Update' }) 
	# print r
	if str(r) != '<Response [200]>':
		# print "Response: {0}".format(r)
		# print r.text
		with open('D:/manualTriples.ttl', 'a') as f:
			f.write(triples)
	return 

def sendFailedTriples(fileName):
	
	with open(fileName, 'r') as f:
		# try sending rejected triples to endpoint one by one
		with progressbar.ProgressBar(max_value=len(f.readlines())) as bar:
			for i, line in enumerate(f):
				sendTriplesToEndpoint(line)
				bar.update(i+1)



if (__name__ == "__main__"):
	# try:
	# Open the purl batch
	CreatePurls('open', purlBatch)

# Create linked data of EEA reference grid cells
	Grid100 = getData("Masterthesis", "raster100km_4258", "postgres", "gps")
	EEA2RDF(Grid100, '100km')
	Grid10 = getData("Masterthesis", "raster10km_4258", "postgres", "gps")
	EEA2RDF(Grid10, '10km')

# Create linked data of countries
	NL_country = getData("Masterthesis", "nl_country", "postgres", "gps")
	AdminUnitTable2RDF(NL_country, 'Netherlands', 'country')
	BE_country = getData("Masterthesis", "be_country", "postgres", "gps")
	AdminUnitTable2RDF(BE_country, 'Belgium', 'country')

# Create linked data of provinces
	BE_provinces = getData("Masterthesis", "be_provinces", "postgres", "gps")
	AdminUnitTable2RDF(BE_provinces, 'Belgium', 'province')
	NL_provinces = getData("Masterthesis", "nl_provinces", "postgres", "gps")
	AdminUnitTable2RDF(NL_provinces, 'Netherlands', 'province')

# Create linked data of municipalities
	BE_municipalities = getData("Masterthesis", "be_municipalities", "postgres", "gps")
	AdminUnitTable2RDF(BE_municipalities, 'Belgium', 'municipality')
	NL_municipalities = getData("Masterthesis", "nl_municipalities", "postgres", "gps")
	AdminUnitTable2RDF(NL_municipalities, 'Netherlands', 'municipality')

# # Create linked data of landcover
#   	Landcover = getData("Masterthesis", "corine_nl_be", "postgres", "gps", False)
#   	LandcoverTable2RDF(Landcover)

  	sendFailedTriples(u'D:/manualTriples.ttl')
# send PURLS to PURLZ server
	postPURLbatch(purlBatch,'admin', 'password')
	
	# except:# IOError as (errno, strerror):
	# 	engine.say('Program ended unexpectedly')
	# 	engine.runAndWait()
	# 	#print errno, strerror

