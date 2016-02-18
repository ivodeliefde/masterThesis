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
from postPURLS import postPURLbatch

BaseURI = "http://localhost:3030/masterThesis/" # SHOULD BE REPLACED WITH PURL ADDRESS!
# endpoint = 'http://localhost:8089/parliament/sparql?' 
endpoint = "http://localhost/strabon-endpoint-3.3.2-SNAPSHOT/Query"
purlBatch = 'purlBatch.xml'

def getData(dbms_name, table, user, password, AdmUnit=True):
	# Connect to the Postgres database
	conn = psycopg2.connect(host="localhost", port='5433', database=dbms_name, user=user, password=password) 
	cur = conn.cursor()
	# print conn.encoding
	conn.set_client_encoding('UTF-8')


	if AdmUnit == True:
		# Retrieve the names and geometries of the administrative unites
		cur.execute("select name, ST_astext(geom) from {0};".format(table))
	else:
		# Retrieve the ID, landcover type and geometries of the CORINE dataset
		cur.execute("select id, code_12, ST_astext(geom) from {0};".format(table))

	data = cur.fetchall()

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

		if not os.path.exists('{0}/'.format( AdmUnitType.lower() ) ):
			os.makedirs('{0}/'.format( AdmUnitType.lower() ))

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
		
			if AdmUnitType == 'municipality':
				parentProvince = geomInGeoms(geometry, provinces)
				if len(parentProvince) > 1:
					'Municipality {0} is in multiple provinces: {1}'.format(row[0], parentProvince)
				else:
					parentName = parentProvince[0].decode('utf-8').lower()
					parentName = unicodedata.normalize('NFC', unicode(parentName))
					if '"' in parentName:
						parentName = parentName('"', '')
					parentName = parentName.replace(' ', '_')
					p = Graph()
					# print parentName
					
					parent = URIRef(u'{0}province/{1}'.format( BaseURI, parentName ) )

					g.add( ( parent, dc.hasPart, thing ) )

					g.add( ( thing, dc.isPartOf, parent ) )


						
					
			elif AdmUnitType == 'province':
				# print 'checking out parent country' 
				p = Graph()
				parent = URIRef('{0}{1}/{2}'.format( BaseURI, 'country', inCountry[0][0] ) )
				Paddress = str(parent).replace(BaseURI,'')

				p.parse(Paddress, format='turtle')
					
				p.add( ( parent, dc.hasPart, thing ) )

				p.serialize(u'{0}'.format(Paddress), format='turtle')
				
				g.add( ( parent, dc.hasPart, thing ) )



				# send data to enpoint for municipalities only (provinces/countries have geometries too large to send this way)
				triples = u""

				for s,p,o in g.triples((None, None, None)):
					if str(type(o)) == "<class 'rdflib.term.Literal'>":
						triples += u'<{0}> <{1}> "{2}" .'.format(s,p,o)
					else:
						# print type(o)
						triples += u'<{0}> <{1}> <{2}> .'.format(s,p,o)


				query = u"INSERT DATA { " + triples + "}"
				r = requests.post(endpoint, data={'view':'HTML', 'query': query, 'format':'HTML', 'outputformat':'SPARQL/XML' , 'handle':'plain', 'submit':'Update' }) 
				# print r
				if str(r) != '<Response [200]>':
					print "Response: {0}".format(r)
				
				# Write the graph to a RDF file in the turtle format
				
				g.serialize(u'{0}/{1}'.format( AdmUnitType.lower(), name ) , format='turtle')
				g = Graph()

			bar.update(i)

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

	print "Creating linked data from CORINE 2012 Legend"
	if not os.path.exists('landcover/legend/'):
		os.makedirs('landcover/legend/')

	i = 0
	with progressbar.ProgressBar(max_value=len(CLC_legend)) as bar:
		for key, value in CLC_legend.iteritems():
			# Linking URI as subclass of Landcover definition on DBPedia
			g.add( ( URIRef("{0}landcover/legend/CLC_{1}".format(BaseURI, key) ), RDFS.subClassOf , dbpedia.Land_cover ) )
			g.add( ( URIRef("{0}landcover/legend/CLC_{1}".format(BaseURI, key) ), FOAF.name , Literal(value) ) )
			g.serialize("landcover/legend/CLC_{0}".format(key), format='turtle')
			g = Graph()
			bar.update(i)
			i += 1


	print "Creating linked data from CORINE 2012 dataset"
	with progressbar.ProgressBar(max_value=len(table)) as bar:
		for i, row in enumerate(table):
			ID, Landcover, geometry = row

			thing = URIRef("{0}landcover/{1}".format( BaseURI, ID ) )

			g.add( (thing, RDF.type, URIRef("{0}landcover/legend/CLC_{1}".format(BaseURI, Landcover) ) ) )
			g.add( (thing, geom.hasGeometry, Literal("<http://www.opengis.net/def/crs/EPSG/0/4258>{0}".format(geometry), datatype=geom.wktLiteral ) ) )

			overlaps = [geomInGeoms(geometry, NL_provinces), geomInGeoms(geometry, BE_provinces), geomInGeoms(geometry, NL_municipalities), geomInGeoms(geometry, BE_municipalities)]
			for j, featureList in enumerate(overlaps):
				for feature in featureList:
					parentName = feature[0].decode('utf-8').lower()
					parentName = unicodedata.normalize('NFC', unicode(parentName))
					
					if '"' in parentName:
						parentName = parentName('"', '')
					parentName = parentName.replace(' ', '_')

					if j < 3:
						featureURI = URIRef(u'{0}{1}/{2}'.format( BaseURI, 'province', parentName ) )
					else:
						featureURI = URIRef(u'{0}{1}/{2}'.format( BaseURI, 'municipality', parentName ) )
					

					g.add( ( thing, geom.intersects, featureURI) )


			triples = ''
			# send data to enpoint
			for s,p,o in g.triples((None, None, None)):
				# print s,p,o
				if str(type(o)) == "<class 'rdflib.term.Literal'>":
					triples += u'<{0}> <{1}> "{2}" . '.format(s,p,o)
				elif str(type(o)) == "<class 'rdflib.term.URIRef'>":
					triples += u'<{0}> <{1}> <{2}> . '.format(s,p,o)
				else:
					print type(o)
			
			query = "INSERT DATA { " + triples + "}"
			r = requests.post(endpoint, data={'view':'HTML', 'query': query, 'format':'HTML', 'outputformat':'SPARQL/XML' , 'handle':'plain', 'submit':'Update' }) 
			# print r
			if str(r) != '<Response [200]>':
				print "Response: {0}".format(r), "{0}".format(thing)

			# Write the graph to a RDF file in the turtle format
			# g.serialize("{0}.ttl".format('landcover/{0}'.format(ID)), format='turtle')
			g = Graph()

			if i % 500 == 0:
				bar.update(i)
	
	return

def EEA2RDF(table, resolution):
	# global NL_provinces
	# global BE_provinces
	# global NL_country
	# global BE_country

	# GeoSPARQL vocabulary
	geom = rdflib.Namespace("http://www.opengis.net/ont/geosparql#")
	# DBPedia
	dbpedia = rdflib.Namespace("http://dbpedia.com/resource/")
	# Dublin core
	dc = rdflib.Namespace('http://purl.org/dc/terms/')

	g = Graph()
	
	global outputFile
	global BaseURI

	print "Creating linked data from EEA refernce GRID {0}".format(resolution)
	if not os.path.exists('raster/'):
		os.makedirs('raster/')

	with progressbar.ProgressBar(max_value=len(table)) as bar:
		raster = URIRef('{0}raster/{1}'.format(BaseURI, resolution))
		g.add( ( raster, RDF.type, dbpedia.Raster ) )
		CreatePurls([(raster, 'raster', resolution)])

		for i, row in enumerate(table):
			name, geometry = row
			cellURI = URIRef('{0}raster/{1}'.format(BaseURI, name))
			g.add( ( cellURI, FOAF.name, Literal(name) ) )
			g.add( ( cellURI, dc.isPartOf , raster ) )
			g.add( ( cellURI, geom.hasGeometry, Literal("<http://www.opengis.net/def/crs/EPSG/0/4258>{0}".format(geometry), datatype=geom.wktLiteral )  ) )
			CreatePurls([(cellURI, 'raster',name)])
			bar.update(i)

			triples = u''
			# send data to enpoint
			for s,p,o in g.triples((None, None, None)):
				# print s,p,o
				if str(type(o)) == "<class 'rdflib.term.Literal'>":
					triples += u'<{0}> <{1}> "{2}" . '.format(s,p,o)
				elif str(type(o)) == "<class 'rdflib.term.URIRef'>":
					triples += u'<{0}> <{1}> <{2}> . '.format(s,p,o)
				else:
					print type(o)
			query = u"INSERT DATA { " + triples + "}"
			# r = requests.post(endpoint, data={'view':'HTML', 'query': query, 'format':'HTML', 'outputformat':'SPARQL/XML' , 'handle':'plain', 'submit':'Update' }) 
			# # print r
			# if str(r) != '<Response [200]>':
			# 	print "Response: {0}".format(r)
			# 	print query
			# 	print r.text
		
		# Write the graph to a RDF file in the turtle format
		try:
			unicode(name)
		except:
			name = name.decode('utf-8')

		g.serialize(u'raster/{0}'.format(resolution), format='turtle')
		g = Graph()

		

	return 

def CreatePurls(UriList):
	global purlBatch

	if UriList == 'open':
		with open(purlBatch,'w') as f:
			f.write('<purls>')
	elif UriList == 'close':
		with open(purlBatch,'a') as f:
			f.write('<\purls>')
	else:
		purls = ''
		for each in UriList:
			URI, domain, name = each
			purls += '<purl> <id>/{0}/{1}</id> <type>302</type> <maintainers> <uid>IdeLiefde</uid> </maintainers> <target> <url>{2}</url> </target> </purl>\n'.format(domain, name, URI)
		with open(purlBatch,'a') as f:
			f.write(purls)

	return


if (__name__ == "__main__"):
# Open the purl batch
	CreatePurls('open')

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

# Create linked data of landcover
  	Landcover = getData("Masterthesis", "corine_nl_be", "postgres", "gps", False)
  	LandcoverTable2RDF(Landcover)

# Close the purl batch
  	CreatePurls('close')

# send PURLS to PURLZ server
	postPURLbatch(purlBatch,'admin', 'password')
