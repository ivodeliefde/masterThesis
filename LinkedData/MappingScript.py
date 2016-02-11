# encoding: utf-8
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

BaseURI = "http://localhost:3030/masterThesis/" # SHOULD BE REPLACED WITH PURL ADDRESS!
endpoint = 'http://localhost:8089/parliament/sparql?' 

def getData(dbms_name, table, user, password, AdmUnit=True):
	# Connect to the Postgres database
	conn = psycopg2.connect(host="localhost", port='5433', database=dbms_name, user=user, password=password) 
	cur = conn.cursor()

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
			try:
				name = row[0].lower()
				if '"' in name:
					name = name.replace('"', '')
				name = name.replace(' ', '_')
			except:
				print 'error:',row[0]
			
			thing = URIRef('{0}{1}/{2}'.format( BaseURI, AdmUnitType.lower(), name ) )

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
					p = Graph()
					parent = URIRef('{0}{1}/{2}'.format( BaseURI, 'province', parentProvince[0].replace(' ', '_') ) )
					Paddress = str(parent).replace(BaseURI,'')

					p.parse(Paddress, format='turtle')
					
					p.add( ( parent, dc.hasPart, thing ) )

					p.serialize(Paddress, format='turtle')
					
					g.add( ( thing, dc.isPartOf, parent ) )

				# send data to enpoint for municipalities only (provinces/countries have geometries too large to send this way)
				triples = ""

				for s,p,o in g.triples((None, None, None)):
					triples += u'<{0}> <{1}> "{2}" .'.format(s,p,o)
				query = "INSERT DATA { " + triples + "}"
				r = requests.post(endpoint, data={'update': query}) 
				if str(r) == '<Response [500]>':
					print u"".format(r), u"".format(thing)
						
					
			elif AdmUnitType == 'province':
				# print 'checking out parent country' 
				p = Graph()
				parent = URIRef('{0}{1}/{2}'.format( BaseURI, 'country', inCountry[0][0] ) )
				Paddress = str(parent).replace(BaseURI,'')

				p.parse(Paddress, format='turtle')
					
				p.add( ( parent, dc.hasPart, thing ) )

				p.serialize(Paddress, format='turtle')
				
				g.add( ( parent, dc.hasPart, thing ) )

			
			# Write the graph to a RDF file in the turtle format
			try:
				unicode(name)
			except:
				name = name.decode('utf-8')
			
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
	with progressbar.ProgressBar(max_value=len(table)) as bar:
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
			g.add( (thing, geom.hasGeometry, Literal("<http://www.opengis.net/def/crs/EPSG/0/4258> {0}^^geo:wktLiteral".format(geometry) ) ) )

			# send data to enpoint
			triples = ""
			for s,p,o in g.triples((None, None, None)):
				triples += '<{0}> <{1}> "{2}" .'.format(s,p,o)
			query = "INSERT DATA { " + triples + "}"
			r = requests.post(endpoint, data={'update': query}) 

			# Write the graph to a RDF file in the turtle format
			# g.serialize("{0}.ttl".format('landcover/{0}'.format(ID)), format='turtle')
			g = Graph()

			if i % 500 == 0:
				bar.update(i)
	
	return

if (__name__ == "__main__"):

# Create linked data of countries
	NL_country = getData("Masterthesis", "nl_country", "postgres", "gps")
	AdminUnitTable2RDF(NL_country, 'Netherlands', 'country')
	# BE_country = getData("Masterthesis", "be_country", "postgres", "postgres")
	# AdminUnitTable2RDF(BE_country, 'Belgium', 'country')

# Create linked data of provinces
	NL_provinces = getData("Masterthesis", "nl_provinces", "postgres", "gps")
	AdminUnitTable2RDF(NL_provinces, 'Netherlands', 'province')
	# BE_provinces = getData("Masterthesis", "be_provinces", "postgres", "postgres")
	# AdminUnitTable2RDF(BE_provinces, 'Belgium', 'province')

# Create linked data of municipalities
	NL_municipalities = getData("Masterthesis", "nl_municipalities", "postgres", "gps")
	AdminUnitTable2RDF(NL_municipalities, 'Netherlands', 'municipality')
	# BE_municipalities = getData("Masterthesis", "be_municipalities", "postgres", "postgres")
	# AdminUnitTable2RDF(BE_municipalities, 'Belgium', 'municipality')

# # Create linked data of landcover
  	# Landcover = getData("Masterthesis", "corine_nl_be", "postgres", "postgres", False)
  	# LandcoverTable2RDF(Landcover)

# Create linked data of EEA reference grid cells


